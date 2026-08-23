"""Google Cloud adapter — BigQuery for analytics, Firestore for app state.

Reads the agent catalogue and usage telemetry from BigQuery (the same
warehouse the Evaluation Agent scores pilots from) and keeps mutable app
state — votes, access requests, submissions — in Firestore, which gives
us per-document writes without a read-modify-write race.
"""

from __future__ import annotations

from typing import Any

from foundry.repo import Agent


class GCPRepo:
    """Agent catalogue in BigQuery, marketplace state in Firestore.

    Expects Application Default Credentials, or a service account with
    ``roles/bigquery.dataViewer`` on the catalogue dataset and
    ``roles/datastore.user`` on the Firestore database.
    """

    def __init__(self, project: str, dataset: str = "vpc_marketplace", firestore_database: str = "(default)") -> None:
        self.project = project
        self.dataset = dataset
        self.firestore_database = firestore_database

    # -- agents ----------------------------------------------------------
    def list_agents(self) -> list[Agent]:
        """Return every marketplace tile.

        Phase 2: SELECT the catalogue view in BigQuery, join the latest telemetry
        snapshot for users/tasks/CSAT, and hydrate one Agent per row.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    def get_agent(self, agent_id: str) -> Agent | None:
        """Return one tile by id, or None.

        Phase 2: Same query filtered by agent id — or a Firestore document read if the
        catalogue is mirrored there for latency.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    # -- votes -----------------------------------------------------------
    def record_vote(self, agent_id: str, voter: str) -> bool:
        """Record one vote per reviewer per agent; False if already cast.

        Phase 2: Firestore transaction on votes/{agent_id}/voters/{voter} so a double
        click cannot double count.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    def voted_agents(self, voter: str) -> set[str]:
        """Agent ids this reviewer has already voted for.

        Phase 2: Collection-group query over votes filtered by voter.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    # -- access requests -------------------------------------------------
    def add_request(self, agent_id: str, agent_name: str, requester: str, reason: str) -> None:
        """File an access request against a restricted agent.

        Phase 2: Write an access_requests document with status='pending' and fan out a
        Pub/Sub notification to the agent owner.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    def list_requests(self) -> list[dict[str, Any]]:
        """Every access request, newest last.

        Phase 2: Query access_requests ordered by requested_at.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    def set_request_status(self, request_id: str, status: str, decided_by: str) -> None:
        """Mark a request approved or denied.

        Phase 2: Update the document and stamp decided_at / decided_by for the audit log.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    # -- submissions -----------------------------------------------------
    def add_submission(self, track: str, payload: dict[str, Any], submitter: str) -> None:
        """Persist an idea / agent publication / scale nomination.

        Phase 2: Write a submissions document and notify the VP&C AI team channel.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    def list_submissions(self) -> list[dict[str, Any]]:
        """Every submission received.

        Phase 2: Query submissions ordered by submitted_at.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")

    # -- login log -------------------------------------------------------
    def log_login(self, email: str) -> None:
        """Record a reviewer login for adoption stats.

        Phase 2: Stream the row into the BigQuery logins table rather than a CSV.
        """
        raise NotImplementedError("GCPRepo is a Phase 2 stub")
