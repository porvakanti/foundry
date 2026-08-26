"""Reviewer feedback, captured in-app and persisted outside the container.

Community Cloud's filesystem is ephemeral: it is wiped when the app sleeps or
redeploys. That is survivable for demo votes, but not for a review round —
losing your boss's comments overnight is exactly the failure this has to avoid.

So GitHub is the durable store. Each piece of feedback is filed as an issue on
the repo, which means it is free, owned by us, notifies the maintainer, and can
be replied to in the tool the team already uses. The local JSON file is a cache
so the app can show feedback back immediately without an API round trip.

Configure with two secrets:

    GITHUB_TOKEN = "github_pat_..."     # fine-grained, Issues: read & write
    GITHUB_REPO  = "porvakanti/foundry"

Without them the store still works and writes to JSON only — feedback is then
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
        return f"[feedback] {subject} — {self.topic}"

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
        """Persist one piece of feedback. Never raises — losing a comment to a
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
                return json.load(response).get("html_url")
        except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
            # Unreachable, unauthorised, or rate limited — keep the comment locally.
            return None

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


@st.cache_resource
def get_feedback_store() -> FeedbackStore:
    return FeedbackStore()
