"""Content and helpers for stage mode.

Kept out of the page module so the scene list stays readable and can be
reordered without touching layout code.
"""

from __future__ import annotations

from dataclasses import dataclass

import segno

from foundry.config import setting


@dataclass
class Scene:
    """One full screen of the stage sequence."""

    key: str
    label: str        # shown in the presenter toolbar, never on the screen
    kicker: str       # small line above the headline


SCENES = [
    Scene("open", "Open", "VP&C"),
    Scene("shelf", "The shelf", "What is on it today"),
    Scene("production", "In production", "Scaled and supported"),
    Scene("race", "The race", "Competing to be next"),
    Scene("next", "What is next", "You decide"),
    Scene("ask", "The ask", "Monday morning"),
]

SCENE_KEYS = [s.key for s in SCENES]


def app_url() -> str:
    """Where the QR codes point. Set APP_URL for the room."""
    return setting("APP_URL", "https://vpc-agent-marketplace.streamlit.app")


def qr_svg(url: str, dark: str, scale: int = 9) -> str:
    """An inline SVG QR code, so nothing has to be fetched from the network."""
    return segno.make(url, error="m").svg_inline(scale=scale, dark=dark, light=None)
