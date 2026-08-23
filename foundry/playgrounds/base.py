"""The playground contract.

Every agent tile can be tried from its detail page. How that works depends on
the platform the agent actually runs on:

* **Embeddable** platforms (Copilot Studio, GCP) get a live chat panel.
* **Non-embeddable** platforms (Emplay, Looker) show a sample transcript and
  deep-link out, because their surfaces can't be framed inside the marketplace.

For the pilot every adapter is a stub: :class:`CannedPlayground` replays the
agent's ``canned_reply`` so reviewers can feel the flow without any platform
credentials. Phase 2 fills in :meth:`Playground.send` per platform.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from foundry.repo import Agent


@runtime_checkable
class Playground(Protocol):
    """A conversational surface for one agent platform."""

    #: Whether the platform can be rendered inside the marketplace.
    embeddable: bool

    #: Label for the button that deep-links to the owning platform.
    open_label: str

    def send(self, agent: Agent, message: str) -> str:
        """Send ``message`` to ``agent`` and return the reply text."""
        ...


class CannedPlayground:
    """Pilot stand-in: returns the agent's scripted reply after a beat.

    This is what the pilot actually runs on. It keeps the detail page honest —
    the panel is labelled "sandbox · no real data" — while the real adapters
    below stay unimplemented.
    """

    embeddable = True
    open_label = "Open agent ↗"

    def send(self, agent: Agent, message: str) -> str:
        if not agent.canned_reply:
            return "Noted — this agent is still an idea, so no live responses yet."
        return agent.canned_reply


def get_playground(platform: str) -> Playground:
    """Return the adapter for a platform.

    Phase 2: return the real adapter here once its ``send`` is implemented and
    credentials are wired up. Until then every platform resolves to the canned
    stub, but keeps the platform's own ``embeddable`` and ``open_label``.
    """
    from foundry.playgrounds import copilot, emplay
    from foundry.playgrounds import gcp as gcp_pg
    from foundry.playgrounds import looker

    real: dict[str, type] = {
        "Copilot": copilot.CopilotPlayground,
        "Emplay": emplay.EmplayPlayground,
        "GCP": gcp_pg.GCPPlayground,
        "Looker": looker.LookerPlayground,
    }
    adapter = real.get(platform)
    stub = CannedPlayground()
    if adapter is not None:
        stub.embeddable = adapter.embeddable
        stub.open_label = adapter.open_label
    return stub
