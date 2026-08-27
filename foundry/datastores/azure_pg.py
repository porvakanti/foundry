"""Azure Database for PostgreSQL adapter - the likely Phase 2 default.

A plain relational home for marketplace state, close to the Microsoft
estate the Copilot agents already live in. Transactions give us the
one-vote-per-user guarantee for free, which the JSON store only
approximates.
"""

from __future__ import annotations

from typing import Any

from foundry.repo import Agent


class AzurePostgresRepo:
    """Marketplace state in Azure Database for PostgreSQL.

    Expects a connection string (Entra ID token auth preferred over a
    password) and the schema created by the Phase 2 migration.
    """

    def __init__(self, dsn: str, schema: str = "marketplace") -> None:
        self.dsn = dsn
        self.schema = schema

    # -- agents ----------------------------------------------------------
    def list_agents(self) -> list[Agent]:
        """Return every marketplace tile.

        Phase 2: SELECT from agents, aggregating votes in a lateral join so the tile
        count is always consistent with the votes table.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    def get_agent(self, agent_id: str) -> Agent | None:
        """Return one tile by id, or None.

        Phase 2: SELECT ... WHERE id = %s.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    # -- votes -----------------------------------------------------------
    def record_vote(self, agent_id: str, voter: str) -> bool:
        """Record one vote per reviewer per agent; False if already cast.

        Phase 2: INSERT ... ON CONFLICT (agent_id, voter) DO NOTHING; the rowcount tells
        us whether the vote was new.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    def voted_agents(self, voter: str) -> set[str]:
        """Agent ids this reviewer has already voted for.

        Phase 2: SELECT agent_id FROM votes WHERE voter = %s.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    # -- access requests -------------------------------------------------
    def add_request(self, agent_id: str, agent_name: str, requester: str, reason: str) -> None:
        """File an access request against a restricted agent.

        Phase 2: INSERT into access_requests with status 'pending'.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    def list_requests(self) -> list[dict[str, Any]]:
        """Every access request, newest last.

        Phase 2: SELECT from access_requests ORDER BY requested_at.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    def set_request_status(self, request_id: str, status: str, decided_by: str) -> None:
        """Mark a request approved or denied.

        Phase 2: UPDATE access_requests SET status, decided_at = now(), decided_by.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    # -- submissions -----------------------------------------------------
    def add_submission(self, track: str, payload: dict[str, Any], submitter: str) -> None:
        """Persist an idea / agent publication / scale nomination.

        Phase 2: INSERT into submissions with the track-specific fields as JSONB.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    def list_submissions(self) -> list[dict[str, Any]]:
        """Every submission received.

        Phase 2: SELECT from submissions ORDER BY submitted_at.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")

    # -- login log -------------------------------------------------------
    def log_login(self, email: str) -> None:
        """Record a reviewer login for adoption stats.

        Phase 2: INSERT into logins - replaces the CSV entirely.
        """
        raise NotImplementedError("AzurePostgresRepo is a Phase 2 stub")
