"""Data access for the marketplace.

Everything the app reads or writes goes through :class:`AgentRepo`. The pilot
ships :class:`JSONFileRepo`; the adapters under ``foundry/datastores/`` implement
the same protocol against real systems in Phase 2, so swapping the backing
store is a one-line change in :func:`get_repo`.
"""

from __future__ import annotations

import csv
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import streamlit as st

from foundry.config import (
    AGENTS_FILE,
    LOGINS_FILE,
    REQUESTS_FILE,
    SUBMISSIONS_FILE,
    VOTES_FILE,
)

MATURITY_ORDER = {"scaled": 0, "pilot": 1, "idea": 2}


@dataclass
class Agent:
    """One marketplace tile, in the shape ``data/agents.json`` stores it."""

    id: str
    name: str
    tagline: str
    about: str
    maturity: str            # scaled | pilot | idea
    platform: str            # Copilot | Emplay | GCP | Looker
    function: str
    locked: bool
    audience: str
    owner: str
    owner_role: str
    owner_initials: str
    how: list[str]
    sample_prompts: list[str]
    canned_reply: str
    metrics: dict[str, Any]
    pulse: str
    reviews: list[dict[str, Any]] = field(default_factory=list)
    rating_avg: float | None = None
    rating_count: int = 0
    votes: int = 0
    impact_score: int = 0
    hours_saved_per_month: int = 0
    pilot_users: int = 0
    trend: str = "— 0"
    deep_link: str | None = None

    @property
    def monogram(self) -> str:
        return "".join(w[0] for w in self.name.split()[:2]).upper()

    @property
    def is_idea(self) -> bool:
        return self.maturity == "idea"

    @property
    def haystack(self) -> str:
        """Text the Concierge matches a task description against."""
        return " ".join([self.name, self.tagline, self.about, self.function]).lower()


@runtime_checkable
class AgentRepo(Protocol):
    """The storage contract every backend must satisfy."""

    def list_agents(self) -> list[Agent]: ...
    def get_agent(self, agent_id: str) -> Agent | None: ...
    def record_vote(self, agent_id: str, voter: str) -> bool: ...
    def voted_agents(self, voter: str) -> set[str]: ...
    def add_request(self, agent_id: str, agent_name: str, requester: str, reason: str) -> None: ...
    def list_requests(self) -> list[dict[str, Any]]: ...
    def set_request_status(self, request_id: str, status: str, decided_by: str) -> None: ...
    def add_submission(self, track: str, payload: dict[str, Any], submitter: str) -> None: ...
    def list_submissions(self) -> list[dict[str, Any]]: ...
    def log_login(self, email: str) -> None: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def display_name(email: str) -> str:
    """Best-effort human name from an email local part."""
    local = email.split("@")[0]
    parts = [p for p in local.replace("-", ".").replace("_", ".").split(".") if p]
    return " ".join(p.capitalize() for p in parts) or email


class JSONFileRepo:
    """Flat-file store under ``data/``.

    Writes are guarded by a process-wide lock and written whole-file, which is
    plenty for a pilot on a single Streamlit instance. Note that on Streamlit
    Community Cloud the container filesystem is ephemeral: writes survive
    reruns and reconnects, but are lost when the app sleeps or redeploys.
    Phase 2 moves this to one of the adapters in ``foundry/datastores/``.
    """

    _lock = threading.Lock()

    def __init__(
        self,
        agents_file: Path = AGENTS_FILE,
        requests_file: Path = REQUESTS_FILE,
        submissions_file: Path = SUBMISSIONS_FILE,
        votes_file: Path = VOTES_FILE,
        logins_file: Path = LOGINS_FILE,
    ) -> None:
        self.agents_file = agents_file
        self.requests_file = requests_file
        self.submissions_file = submissions_file
        self.votes_file = votes_file
        self.logins_file = logins_file

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        try:
            with path.open(encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

    @classmethod
    def _write(cls, path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2, ensure_ascii=False)
        tmp.replace(path)

    # -- agents ----------------------------------------------------------
    def list_agents(self) -> list[Agent]:
        rows = self._read(self.agents_file)
        agents = [Agent(**row) for row in rows]
        tallies = self._vote_tallies()
        for agent in agents:
            agent.votes += tallies.get(agent.id, 0)
            if agent.maturity == "idea":
                agent.metrics = {**agent.metrics, "upvotes": agent.votes}
            elif agent.maturity == "pilot":
                agent.metrics = {**agent.metrics, "community_votes": agent.votes}
        agents.sort(key=lambda a: (MATURITY_ORDER[a.maturity], -a.impact_score, -a.votes))
        return agents

    def get_agent(self, agent_id: str) -> Agent | None:
        return next((a for a in self.list_agents() if a.id == agent_id), None)

    # -- votes -----------------------------------------------------------
    def _vote_tallies(self) -> dict[str, int]:
        tallies: dict[str, int] = {}
        for row in self._read(self.votes_file):
            tallies[row["agent_id"]] = tallies.get(row["agent_id"], 0) + 1
        return tallies

    def record_vote(self, agent_id: str, voter: str) -> bool:
        """One vote per reviewer per agent. Returns False if already cast."""
        with self._lock:
            rows = self._read(self.votes_file)
            if any(r["agent_id"] == agent_id and r["voter"] == voter for r in rows):
                return False
            rows.append({"agent_id": agent_id, "voter": voter, "at": _now()})
            self._write(self.votes_file, rows)
        return True

    def voted_agents(self, voter: str) -> set[str]:
        return {r["agent_id"] for r in self._read(self.votes_file) if r["voter"] == voter}

    # -- access requests -------------------------------------------------
    def add_request(self, agent_id: str, agent_name: str, requester: str, reason: str) -> None:
        with self._lock:
            rows = self._read(self.requests_file)
            rows.append({
                "id": f"req-{len(rows) + 1:04d}",
                "agent_id": agent_id,
                "agent_name": agent_name,
                "requester": requester,
                "requester_name": display_name(requester),
                "requester_role": "Marketplace reviewer",
                "age_label": "just now",
                "reason": reason,
                "status": "pending",
                "requested_at": _now(),
                "decided_at": None,
                "decided_by": None,
            })
            self._write(self.requests_file, rows)

    def list_requests(self) -> list[dict[str, Any]]:
        return self._read(self.requests_file)

    def set_request_status(self, request_id: str, status: str, decided_by: str) -> None:
        with self._lock:
            rows = self._read(self.requests_file)
            for row in rows:
                if row["id"] == request_id:
                    row["status"] = status
                    row["decided_at"] = _now()
                    row["decided_by"] = decided_by
            self._write(self.requests_file, rows)

    # -- submissions -----------------------------------------------------
    def add_submission(self, track: str, payload: dict[str, Any], submitter: str) -> None:
        with self._lock:
            rows = self._read(self.submissions_file)
            rows.append({
                "id": f"sub-{len(rows) + 1:04d}",
                "track": track,
                "fields": payload,
                "submitter": submitter,
                "submitted_at": _now(),
            })
            self._write(self.submissions_file, rows)

    def list_submissions(self) -> list[dict[str, Any]]:
        return self._read(self.submissions_file)

    # -- login log -------------------------------------------------------
    def log_login(self, email: str) -> None:
        """Append to a CSV so we can count reviewers during the pilot."""
        with self._lock:
            self.logins_file.parent.mkdir(parents=True, exist_ok=True)
            new = not self.logins_file.exists()
            with self.logins_file.open("a", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                if new:
                    writer.writerow(["timestamp", "email"])
                writer.writerow([_now(), email])


@st.cache_resource
def get_repo() -> AgentRepo:
    """The repository the whole app talks to.

    Phase 2: return one of the adapters from ``foundry.datastores`` here
    instead — nothing else in the app needs to change.
    """
    return JSONFileRepo()
