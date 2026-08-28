"""Content and helpers for stage mode.

Kept out of the page module so the scene list stays readable and can be
reordered without touching layout code.
"""

from __future__ import annotations

import re
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


def qr_svg(url: str, scale: int = 9) -> str:
    """An inline SVG QR code, so nothing has to be fetched from the network.

    Two things here are what make a phone camera actually read it.

    Segno emits width and height but no viewBox. Sizing the element with CSS
    then resizes the canvas without resizing the drawing, which crops the
    finder patterns off the right and bottom edge and leaves a QR that no
    scanner can decode. A viewBox derived from the emitted size makes CSS
    scaling behave.

    The code is always dark on white with a quiet zone, whatever the app theme
    is doing. A light-on-dark QR is an inverted code: some readers cope, plenty
    do not, and a code that fails for a third of a room is not worth the
    aesthetic consistency.
    """
    svg = segno.make(url, error="m").svg_inline(
        scale=scale, dark="#1A1A1A", light="#FFFFFF", border=4,
    )
    match = re.match(r'<svg width="(\d+(?:\.\d+)?)" height="(\d+(?:\.\d+)?)"', svg)
    if match:
        width, height = match.group(1), match.group(2)
        svg = svg.replace(
            f'<svg width="{width}" height="{height}"',
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"',
            1,
        )
    return svg
