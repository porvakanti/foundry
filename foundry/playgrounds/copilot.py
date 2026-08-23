"""Microsoft Copilot Studio agents — the bulk of the pilot inventory."""

from __future__ import annotations

from foundry.repo import Agent


class CopilotPlayground:
    """Chat with a Copilot Studio agent from inside the marketplace.

    Copilot Studio agents can be embedded, so these get the live chat
    panel. Conversations are per-reviewer and must not leak between
    sessions, so the token is minted per marketplace session.
    """

    embeddable = True
    open_label = "Open in Teams ↗"

    def __init__(self, environment_id: str, tenant_id: str) -> None:
        self.environment_id = environment_id
        self.tenant_id = tenant_id

    def send(self, agent: Agent, message: str) -> str:
        """Send a turn to the agent and return its reply.

        Phase 2: open a Direct Line conversation against the agent's published
        channel, post the activity, and poll the watermark until the bot
        replies. Carry the reviewer's identity so Copilot applies their own
        data permissions rather than a shared service account's.
        """
        raise NotImplementedError("CopilotPlayground is a Phase 2 stub")

    def deep_link(self, agent: Agent) -> str:
        """URL that opens this agent in its own platform.

        Phase 2: the Teams deep link for the published agent, or the Copilot Studio
        canvas URL for the owner.
        """
        raise NotImplementedError("CopilotPlayground is a Phase 2 stub")
