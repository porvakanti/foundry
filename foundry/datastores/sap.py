"""SAP adapter — agent metadata alongside the procurement master data.

Talks to SAP over OData/RFC so agent ownership and audience can be derived
from the same org structure that governs purchasing authority, instead of
being maintained twice.
"""

from __future__ import annotations

from typing import Any

from foundry.repo import Agent


class SAPRepo:
    """Agent catalogue and ownership sourced from SAP.

    Expects an OData service endpoint plus a technical user with read
    access to the relevant CDS views.
    """

    def __init__(self, base_url: str, client: str, service_path: str = "/sap/opu/odata/sap/ZVPC_MARKETPLACE_SRV") -> None:
        self.base_url = base_url
        self.client = client
        self.service_path = service_path

    # -- agents ----------------------------------------------------------
    def list_agents(self) -> list[Agent]:
        """Return every marketplace tile.

        Phase 2: GET the AgentSet entity set, expanding owner and audience
        navigation properties, and map each entity onto Agent.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    def get_agent(self, agent_id: str) -> Agent | None:
        """Return one tile by id, or None.

        Phase 2: GET AgentSet('<id>') with the same expansions.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    # -- votes -----------------------------------------------------------
    def record_vote(self, agent_id: str, voter: str) -> bool:
        """Record one vote per reviewer per agent; False if already cast.

        Phase 2: POST to the VoteSet entity set; SAP enforces the one-vote-per-user
        key constraint, so a duplicate comes back as a 409.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    def voted_agents(self, voter: str) -> set[str]:
        """Agent ids this reviewer has already voted for.

        Phase 2: GET VoteSet filtered by the voter's business partner id.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    # -- access requests -------------------------------------------------
    def add_request(self, agent_id: str, agent_name: str, requester: str, reason: str) -> None:
        """File an access request against a restricted agent.

        Phase 2: POST an AccessRequestSet entity, which triggers the standard SAP
        approval workflow for the agent owner.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    def list_requests(self) -> list[dict[str, Any]]:
        """Every access request, newest last.

        Phase 2: GET AccessRequestSet ordered by RequestedAt.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    def set_request_status(self, request_id: str, status: str, decided_by: str) -> None:
        """Mark a request approved or denied.

        Phase 2: PATCH the entity — or better, call the workflow decision action so
        SAP's own audit trail records it.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    # -- submissions -----------------------------------------------------
    def add_submission(self, track: str, payload: dict[str, Any], submitter: str) -> None:
        """Persist an idea / agent publication / scale nomination.

        Phase 2: POST to SubmissionSet.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    def list_submissions(self) -> list[dict[str, Any]]:
        """Every submission received.

        Phase 2: GET SubmissionSet.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")

    # -- login log -------------------------------------------------------
    def log_login(self, email: str) -> None:
        """Record a reviewer login for adoption stats.

        Phase 2: Usually skipped here: login telemetry belongs in the analytics store,
        not the ERP.
        """
        raise NotImplementedError("SAPRepo is a Phase 2 stub")
