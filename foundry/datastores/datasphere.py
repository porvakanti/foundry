"""SAP Datasphere adapter — governed analytics for the scoring model.

Datasphere is where the harmonised spend and usage models live, so the
Evaluation Agent's inputs — hours saved, adoption, CSAT — are read from
here rather than recomputed in the app.
"""

from __future__ import annotations

from typing import Any

from foundry.repo import Agent


class DatasphereRepo:
    """Pilot scoring inputs read from governed Datasphere views.

    Expects a Datasphere space, a database user with SELECT on the exposed
    views, and the HANA client driver installed.
    """

    def __init__(self, host: str, space: str, user: str, password: str) -> None:
        self.host = host
        self.space = space
        self.user = user
        self.password = password

    # -- agents ----------------------------------------------------------
    def list_agents(self) -> list[Agent]:
        """Return every marketplace tile.

        Phase 2: SELECT from the AGENT_CATALOGUE view joined to AGENT_KPI_MONTHLY so
        every tile carries validated impact numbers, not self-reported ones.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    def get_agent(self, agent_id: str) -> Agent | None:
        """Return one tile by id, or None.

        Phase 2: Same select filtered by agent id.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    # -- votes -----------------------------------------------------------
    def record_vote(self, agent_id: str, voter: str) -> bool:
        """Record one vote per reviewer per agent; False if already cast.

        Phase 2: Datasphere is read-mostly: write votes to the operational store and
        let them land here through the normal replication.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    def voted_agents(self, voter: str) -> set[str]:
        """Agent ids this reviewer has already voted for.

        Phase 2: SELECT from the replicated votes view.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    # -- access requests -------------------------------------------------
    def add_request(self, agent_id: str, agent_name: str, requester: str, reason: str) -> None:
        """File an access request against a restricted agent.

        Phase 2: Not served from Datasphere — raise and route access requests through
        the operational adapter.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    def list_requests(self) -> list[dict[str, Any]]:
        """Every access request, newest last.

        Phase 2: Not served from Datasphere.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    def set_request_status(self, request_id: str, status: str, decided_by: str) -> None:
        """Mark a request approved or denied.

        Phase 2: Not served from Datasphere.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    # -- submissions -----------------------------------------------------
    def add_submission(self, track: str, payload: dict[str, Any], submitter: str) -> None:
        """Persist an idea / agent publication / scale nomination.

        Phase 2: Not served from Datasphere.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    def list_submissions(self) -> list[dict[str, Any]]:
        """Every submission received.

        Phase 2: Not served from Datasphere.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")

    # -- login log -------------------------------------------------------
    def log_login(self, email: str) -> None:
        """Record a reviewer login for adoption stats.

        Phase 2: SELECT/INSERT against the adoption fact table if login stats are to be
        reported next to spend KPIs.
        """
        raise NotImplementedError("DatasphereRepo is a Phase 2 stub")
