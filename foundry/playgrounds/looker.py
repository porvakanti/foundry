"""Looker - the conversational layer over the certified spend models."""

from __future__ import annotations

from foundry.repo import Agent


class LookerPlayground:
    """Deep-link into Looker; answers belong next to their charts.

    Looker answers come with a chart and the exact filters used, which is
    the whole point of Spend Lens - flattening that to a text bubble would
    lose the traceability. So the marketplace deep-links out.
    """

    embeddable = False
    open_label = "Open in Looker ↗"

    def __init__(self, base_url: str, client_id: str, client_secret: str) -> None:
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret

    def send(self, agent: Agent, message: str) -> str:
        """Send a turn to the agent and return its reply.

        Phase 2: either embed a signed Looker URL in an iframe, or call the Looker
        conversational API and render the returned query alongside the answer
        so numbers stay traceable to the certified model.
        """
        raise NotImplementedError("LookerPlayground is a Phase 2 stub")

    def deep_link(self, agent: Agent) -> str:
        """URL that opens this agent in its own platform.

        Phase 2: a signed embed URL for the dashboard or Explore behind this agent.
        """
        raise NotImplementedError("LookerPlayground is a Phase 2 stub")
