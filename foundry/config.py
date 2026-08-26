"""Paths and environment configuration.

Settings resolve in this order: Streamlit secrets, then environment
variables, then the default baked in here. That lets the same code run from
`.streamlit/secrets.toml` locally and from Community Cloud secrets or plain
env vars on an internal server.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DESIGN_DIR = ROOT / "design"

AGENTS_FILE = DATA_DIR / "agents.json"
REQUESTS_FILE = DATA_DIR / "requests.json"
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"
VOTES_FILE = DATA_DIR / "votes.json"
LOGINS_FILE = DATA_DIR / "logins.csv"

LOGO_FILE = DESIGN_DIR / "assets" / "vf_logo.png"

#: Shown on Explore and the Leaderboard as the next monthly scale-up review.
NEXT_REVIEW = "12 Sep"

#: Hardcoded for the pilot; Phase 2 reads it from the directory profile.
VIEWER_ROLE = "P2P Operations"

FUNCTIONS = ["Sourcing", "Contracts", "P2P", "Supplier Mgmt", "Analytics", "Governance"]
PLATFORMS = ["Copilot", "Emplay", "GCP", "Looker"]


def setting(key: str, default: str = "") -> str:
    """Read a config value from Streamlit secrets, then the environment."""
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        # No secrets.toml present — normal when running from env vars only.
        pass
    return os.environ.get(key, default)


def reviewer_emails() -> list[str]:
    """The people invited to review the pilot.

    Mirrors the viewer allowlist configured in the app's Community Cloud
    settings. Holding a copy here lets the app reject an address that belongs
    to nobody in the pilot, rather than accepting any @vodafone.com string
    someone happens to type. Leave unset to keep the pilot open to the whole
    domain.
    """
    raw = setting("REVIEWER_EMAILS", "")
    seen: list[str] = []
    for email in raw.split(","):
        email = email.strip().lower()
        if email and email not in seen:
            seen.append(email)
    return seen


def access_contact() -> str:
    """Who an uninvited reviewer should ask for access."""
    return setting("ACCESS_CONTACT", "Praveen")


def allowed_domain() -> str:
    return setting("ALLOWED_EMAIL_DOMAIN", "vodafone.com").lower().lstrip("@")
