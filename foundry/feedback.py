"""Reviewer feedback, captured in-app and persisted outside the container.

Community Cloud's filesystem is ephemeral: it is wiped when the app sleeps or
redeploys. That is survivable for demo votes, but not for a review round -
losing your boss's comments overnight is exactly the failure this has to avoid.

So GitHub is the durable store. Each piece of feedback is filed as an issue on
the repo, which means it is free, owned by us, notifies the maintainer, and can
be replied to in the tool the team already uses. The local JSON file is a cache
so the app can show feedback back immediately without an API round trip.

Configure with two secrets:

    GITHUB_TOKEN = "github_pat_..."     # fine-grained, Issues: read & write
    GITHUB_REPO  = "porvakanti/foundry"

Without them the store still works and writes to JSON only - feedback is then
as ephemeral as everything else, and the Governance page says so.

NOTE: the repository must be PRIVATE before this is used for real. Issues on a
public repo are world-readable, and candid feedback from a reviewer is not.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

from foundry.config import DATA_DIR, setting

FEEDBACK_FILE = DATA_DIR / "feedback.json"
API_ROOT = "https://api.github.com"
REQUEST_TIMEOUT = 10

#: What a reviewer can tell us about, beyond free text.
TOPICS = [
    "Something is broken",
    "Hard to understand",
    "Missing an agent or feature",
    "Like it / keep it",
    "General comment",
]


@dataclass
class Feedback:
    """One reviewer's comment, with the context it was written in."""

    who: str
    page: str
    topic: str
    text: str
    stars: int | None = None
    agent_id: str | None = None
    agent_name: str | None = None
    created_at: str = ""
    synced: bool = False
    issue_url: str | None = None
    id: str = ""

    def title(self) -> str:
        subject = self.agent_name or self.page
        return f"[feedback] {subject} - {self.topic}"

    def issue_body(self) -> str:
        rating = f"{self.stars}/5" if self.stars else "not rated"
        lines = [
            self.text.strip() or "_(no comment)_",
            "",
            "---",
            f"- **From:** {self.who}",
            f"- **Where:** {self.page}",
            f"- **Topic:** {self.topic}",
            f"- **Rating:** {rating}",
        ]
        if self.agent_name:
            lines.append(f"- **Agent:** {self.agent_name} (`{self.agent_id}`)")
        lines.append(f"- **When:** {self.created_at}")
        lines.append("")
        lines.append("_Filed from the VP&C Agent Marketplace pilot._")
        return "\n".join(lines)


class FeedbackStore:
    """JSON cache, mirrored to GitHub issues when credentials are present."""

    _lock = threading.Lock()

    def __init__(self, path: Path = FEEDBACK_FILE) -> None:
        self.path = path
        #: Why the last GitHub write failed, for the Governance status panel.
        self.last_error: str | None = None

    # -- configuration ---------------------------------------------------
    @property
    def token(self) -> str:
        return setting("GITHUB_TOKEN", "")

    @property
    def repo(self) -> str:
        return setting("GITHUB_REPO", "")

    @property
    def durable(self) -> bool:
        """Whether feedback will outlive the container."""
        return bool(self.token and self.repo)

    # -- local cache -----------------------------------------------------
    def _read(self) -> list[dict[str, Any]]:
        try:
            with self.path.open(encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

    def _write(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2, ensure_ascii=False)
        tmp.replace(self.path)

    def list(self) -> list[Feedback]:
        return [Feedback(**row) for row in self._read()]

    def count(self) -> int:
        return len(self._read())

    # -- writing ---------------------------------------------------------
    def add(self, entry: Feedback) -> Feedback:
        """Persist one piece of feedback. Never raises - losing a comment to a
        network error is worse than losing the durability guarantee, so a failed
        push is recorded as unsynced rather than surfaced as a crash."""
        entry.created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        if self.durable:
            url = self._push_to_github(entry)
            if url:
                entry.synced, entry.issue_url = True, url

        with self._lock:
            rows = self._read()
            entry.id = f"fb-{len(rows) + 1:04d}"
            rows.append(asdict(entry))
            self._write(rows)
        return entry

    def _push_to_github(self, entry: Feedback) -> str | None:
        payload = json.dumps({
            "title": entry.title(),
            "body": entry.issue_body(),
            "labels": ["feedback", "pilot"],
        }).encode()
        request = urllib.request.Request(
            f"{API_ROOT}/repos/{self.repo}/issues",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "vpc-agent-marketplace",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                self.last_error = None
                return json.load(response).get("html_url")
        except urllib.error.HTTPError as exc:
            self.last_error = _explain(exc.code, self.repo, _detail(exc))
            return None
        except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError) as exc:
            self.last_error = f"Could not reach GitHub: {exc}"
            return None

    def check_connection(self) -> tuple[bool, str]:
        """Probe the configured repo and say plainly what is wrong.

        A failed feedback write is deliberately silent for the person writing
        it, so without this the only symptom of a bad token is "nothing
        happened". This turns that into an answer.
        """
        if not self.token and not self.repo:
            return False, ("GITHUB_TOKEN and GITHUB_REPO are not set, so feedback "
                           "is kept on the app only and lost when it restarts.")
        if not self.token:
            return False, "GITHUB_REPO is set but GITHUB_TOKEN is missing."
        if not self.repo:
            return False, "GITHUB_TOKEN is set but GITHUB_REPO is missing."
        if "/" not in self.repo:
            return False, f'GITHUB_REPO should look like "owner/repo", not "{self.repo}".'

        request = urllib.request.Request(
            f"{API_ROOT}/repos/{self.repo}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "vpc-agent-marketplace",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                repo = json.load(response)
            if not repo.get("has_issues", True):
                return False, (f"{self.repo} is reachable, but Issues are disabled on it. "
                               "Turn them on in the repository settings.")
            visibility = "private" if repo.get("private") else "PUBLIC"
            note = ("" if repo.get("private") else
                    "  Warning: this repository is public, so feedback issues are "
                    "readable by anyone.")
            return True, f"Connected to {self.repo} ({visibility}).{note}"
        except urllib.error.HTTPError as exc:
            return False, _explain(exc.code, self.repo, _detail(exc))
        except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError) as exc:
            return False, f"Could not reach GitHub: {exc}"

    def retry_unsynced(self) -> int:
        """Push anything that was written while GitHub was unreachable."""
        if not self.durable:
            return 0
        pushed = 0
        with self._lock:
            rows = self._read()
            for row in rows:
                if row.get("synced"):
                    continue
                url = self._push_to_github(Feedback(**row))
                if url:
                    row["synced"], row["issue_url"] = True, url
                    pushed += 1
            if pushed:
                self._write(rows)
        return pushed


def _detail(exc: urllib.error.HTTPError) -> str:
    """The server's own explanation, which beats any guess made from the code.

    Anything between the app and GitHub - a corporate proxy, a gateway - can
    answer instead of GitHub and will say so here, which is worth showing
    verbatim rather than reinterpreting.
    """
    try:
        body = json.loads(exc.read().decode("utf-8", "replace"))
    except (json.JSONDecodeError, ValueError, OSError):
        return ""
    message = body.get("message", "") if isinstance(body, dict) else ""
    return f" Response: {message}" if message else ""


def _explain(status: int, repo: str, detail: str = "") -> str:
    """Turn a status code into something actionable, plus what the server said."""
    guess = {
        401: "The token was rejected (401). It is wrong, expired, or revoked.",
        403: (f"Forbidden (403). Usually the token lacks Issues: read & write on "
              f"{repo}, or a rate limit was hit."),
        404: (f"{repo} not found (404). Either the name is wrong, or the token was "
              f"not granted access to it. A fine-grained token must list the "
              f"repository explicitly."),
        410: f"Issues are disabled on {repo} (410). Turn them on in the settings.",
        422: "The issue contents were rejected (422).",
    }.get(status, f"HTTP {status}.")
    return guess + detail


@st.cache_resource
def get_feedback_store() -> FeedbackStore:
    return FeedbackStore()
