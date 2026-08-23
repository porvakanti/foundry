"""Google Cloud agents — Contract IQ and the ESG scout."""

from __future__ import annotations

from foundry.repo import Agent


class GCPPlayground:
    """Chat with a Vertex AI / Agent Builder agent.

    Runs in our own GCP project, so it is embeddable. Contract IQ is
    role-restricted: the caller's entitlement must be checked before a
    turn is sent, not just before the panel is rendered.
    """

    embeddable = True
    open_label = "Open agent ↗"

    def __init__(self, project: str, location: str = "europe-west1", agent_id: str = "") -> None:
        self.project = project
        self.location = location
        self.agent_id = agent_id

    def send(self, agent: Agent, message: str) -> str:
        """Send a turn to the agent and return its reply.

        Phase 2: call ``detectIntent`` on the Dialogflow CX / Agent Builder session
        and return the fulfilment text, forwarding the reviewer's identity so
        row-level access on the contract index is enforced.
        """
        raise NotImplementedError("GCPPlayground is a Phase 2 stub")

    def deep_link(self, agent: Agent) -> str:
        """URL that opens this agent in its own platform.

        Phase 2: the Agent Builder console URL, or the internal web app fronting it.
        """
        raise NotImplementedError("GCPPlayground is a Phase 2 stub")
