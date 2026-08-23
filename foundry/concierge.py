"""Concierge search — describe a task, get the agents that fit.

Pilot implementation is deliberately transparent: keyword overlap against the
agent's name, tagline, about text and function, ranked by how many of your
words it hit. The "matches x, y" reason shown under each hit is literally the
list of matched words, so a reviewer can see why an agent surfaced.

TODO (Phase 3): swap the body of :func:`match` for an LLM call — embed the
query and the agent corpus, rank by semantic similarity, and have the model
write the one-line reason. The signature below is the seam; nothing else in
the app needs to change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from foundry.repo import Agent

#: Words too common in procurement prose to be evidence of a match.
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "our", "your",
    "are", "was", "can", "how", "what", "who", "why", "when", "does", "not",
    "you", "all", "any", "get", "got", "has", "have", "need", "want", "would",
    "should", "could", "there", "their", "them", "then", "than", "some", "more",
    "agent", "agents",
}

MIN_QUERY_LEN = 3


@dataclass
class Match:
    """One Concierge hit."""

    agent: Agent
    words: list[str]
    score: int

    @property
    def reason(self) -> str:
        return "matches " + ", ".join(self.words)


def tokenize(query: str) -> list[str]:
    """Split a task description into the words worth matching on."""
    words = re.split(r"[^a-z0-9]+", query.lower())
    seen: list[str] = []
    for word in words:
        if len(word) > 2 and word not in STOPWORDS and word not in seen:
            seen.append(word)
    return seen


def match(query: str, agents: list[Agent], limit: int = 3) -> list[Match]:
    """Return up to ``limit`` agents that best fit a task description."""
    if len(query.strip()) < MIN_QUERY_LEN:
        return []

    words = tokenize(query)
    if not words:
        return []

    hits: list[Match] = []
    for agent in agents:
        hay = agent.haystack
        matched = [w for w in words if w in hay]
        if matched:
            # Name hits are stronger evidence than a mention buried in the about text.
            bonus = sum(2 for w in matched if w in agent.name.lower())
            hits.append(Match(agent=agent, words=matched, score=len(matched) + bonus))

    hits.sort(key=lambda h: (-h.score, h.agent.name))
    return hits[:limit]


def filter_agents(query: str, agents: list[Agent]) -> list[Agent]:
    """Plain substring filter used by the Library search box."""
    q = query.strip().lower()
    if not q:
        return agents
    return [
        a for a in agents
        if q in a.name.lower() or q in a.tagline.lower() or q in a.owner.lower()
    ]
