"""Gamification rules, tiered by maturity.

* **Scaled** agents are not scored. They are in production, so the marketplace
  shows adoption only - no competition, nothing to win.
* **Pilots** are scored monthly by the Evaluation Agent and the winner is
  promoted to production. The weights are fixed:
  ``0.4 * impact + 0.3 * adoption + 0.2 * satisfaction + 0.1 * community``,
  each component normalised 0-100 across the pilot cohort.
* **Ideas** carry upvotes only; the top ideas each quarter get a build sprint.

``data/agents.json`` stores ``impact_score``: the figure the Evaluation Agent
published for the current cycle (21 Aug), which is what the leaderboard shows.
:func:`compute_scores` is the reference implementation of the same formula over
the inputs we hold, used for the component breakdown on the leaderboard and
ready for Phase 2 to run against live telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass

from foundry.repo import Agent

WEIGHTS = {"impact": 0.4, "adoption": 0.3, "satisfaction": 0.2, "community": 0.1}

CRITERIA = [
    ("40%", "Impact", "Hours saved per month, validated by the owner's team", "var(--red)"),
    ("30%", "Adoption", "Active pilot users and repeat usage", "var(--pur)"),
    ("20%", "Satisfaction", "In-agent thumbs and pilot-user CSAT", "var(--tea)"),
    ("10%", "Community", "Marketplace votes from all of VP&C", "var(--org)"),
]


@dataclass
class ScoreBreakdown:
    """One pilot's score, component by component."""

    agent_id: str
    impact: float
    adoption: float
    satisfaction: float
    community: float
    total: float

    def components(self) -> list[tuple[str, float, float]]:
        """``(label, normalised value, weighted contribution)`` per criterion."""
        return [
            ("Impact", self.impact, self.impact * WEIGHTS["impact"]),
            ("Adoption", self.adoption, self.adoption * WEIGHTS["adoption"]),
            ("Satisfaction", self.satisfaction, self.satisfaction * WEIGHTS["satisfaction"]),
            ("Community", self.community, self.community * WEIGHTS["community"]),
        ]


def _normalise(values: list[float]) -> list[float]:
    """Min-max each component onto 0-100 across the cohort."""
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [100.0 for _ in values]
    return [(v - low) / (high - low) * 100 for v in values]


def compute_scores(pilots: list[Agent]) -> dict[str, ScoreBreakdown]:
    """Score a pilot cohort with the published weights."""
    if not pilots:
        return {}

    rated = [a.rating_avg for a in pilots if a.rating_avg is not None]
    # A pilot with no ratings yet sits at the cohort mean rather than at zero,
    # so being new isn't the same as being disliked.
    fallback = sum(rated) / len(rated) if rated else 0.0

    impact = _normalise([float(a.hours_saved_per_month) for a in pilots])
    adoption = _normalise([float(a.pilot_users) for a in pilots])
    satisfaction = _normalise([float(a.rating_avg if a.rating_avg is not None else fallback)
                               for a in pilots])
    community = _normalise([float(a.votes) for a in pilots])

    out: dict[str, ScoreBreakdown] = {}
    for i, agent in enumerate(pilots):
        total = (impact[i] * WEIGHTS["impact"] + adoption[i] * WEIGHTS["adoption"]
                 + satisfaction[i] * WEIGHTS["satisfaction"] + community[i] * WEIGHTS["community"])
        out[agent.id] = ScoreBreakdown(
            agent_id=agent.id, impact=impact[i], adoption=adoption[i],
            satisfaction=satisfaction[i], community=community[i], total=total,
        )
    return out


def ranked_pilots(agents: list[Agent]) -> list[Agent]:
    """Pilots ordered as the leaderboard shows them: published score, then votes."""
    pilots = [a for a in agents if a.maturity == "pilot"]
    pilots.sort(key=lambda a: (-a.impact_score, -a.votes, a.name))
    return pilots


def pilot_ranks(agents: list[Agent]) -> dict[str, int]:
    """Agent id → rank, 1-based."""
    return {a.id: i + 1 for i, a in enumerate(ranked_pilots(agents))}
