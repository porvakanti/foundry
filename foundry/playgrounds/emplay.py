"""Emplay — the supplier-built Sourcing Copilot platform."""

from __future__ import annotations

from foundry.repo import Agent


class EmplayPlayground:
    """Deep-link to Emplay; the surface can't be framed here.

    Emplay is a third-party platform behind the supplier's own login, so
    the marketplace shows a sample transcript and hands the reviewer over
    rather than pretending to embed it.
    """

    embeddable = False
    open_label = "Open in Emplay ↗"

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key

    def send(self, agent: Agent, message: str) -> str:
        """Send a turn to the agent and return its reply.

        Phase 2: call the Emplay conversational API if the supplier exposes one under
        the platform SLA. Until that is contracted, the detail page stays in
        sample-transcript mode.
        """
        raise NotImplementedError("EmplayPlayground is a Phase 2 stub")

    def deep_link(self, agent: Agent) -> str:
        """URL that opens this agent in its own platform.

        Phase 2: the tenant's Emplay workspace URL for this agent.
        """
        raise NotImplementedError("EmplayPlayground is a Phase 2 stub")
