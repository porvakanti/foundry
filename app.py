"""Foundry - the VP&C Agent Marketplace pilot.

Run with ``streamlit run app.py``.

Navigation is registered here and rendered by ``foundry.components.header``:
Streamlit's own nav is hidden so the marketplace can draw its own top bar while
still getting real client-side page switching. Agent detail and stage mode are
registered but never linked: the first is reached by opening a tile, the second
by going to /stage.
"""

from __future__ import annotations

import streamlit as st

from foundry import nav, theme
from foundry.pages import (agent, explore, governance, leaderboard, library, stage,
                           submit)

st.set_page_config(
    page_title="VP&C Agent Marketplace",
    page_icon=str(theme.LOGO_FILE) if theme.LOGO_FILE.exists() else "🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    # Navigation is registered even when signed out, and each page guards itself
    # with require_auth(). Gating before st.navigation meant Streamlit never
    # learned the requested path and reset the URL to "/", so signing in from a
    # deep link landed on Explore instead: opening /stage for a presentation and
    # arriving somewhere else. Phase 2 replaces the gate with an Entra ID SSO
    # redirect, which keeps the same property.
    pages = [
        # The default page is served at "/", so it must not also claim a url_path:
        # Streamlit would not route /explore and answered it with a blocking
        # "Page not found" modal over the app.
        st.Page(explore.render, title="Explore", default=True),
        st.Page(library.render, title="The Library", url_path="library"),
        st.Page(leaderboard.render, title="Leaderboard", url_path="leaderboard"),
        st.Page(submit.render, title="Submit", url_path="submit"),
        st.Page(governance.render, title="Governance", url_path="governance"),
        st.Page(agent.render, title="Agent", url_path="agent"),
        st.Page(stage.render, title="Stage", url_path="stage"),
    ]
    for key, page in zip(
        ["explore", "library", "leaderboard", "submit", "governance", "agent", "stage"],
        pages,
    ):
        nav.register(key, page)

    st.navigation(pages, position="hidden").run()


if __name__ == "__main__":
    main()
