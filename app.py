"""Foundry — the VP&C Agent Marketplace pilot.

Run with ``streamlit run app.py``.

Navigation is registered here and rendered by ``foundry.components.header``:
Streamlit's own nav is hidden so the marketplace can draw its own top bar while
still getting real client-side page switching. Agent detail is registered but
never linked — it is reached by opening a tile.
"""

from __future__ import annotations

import streamlit as st

from foundry import nav, theme
from foundry.auth import is_authenticated, render_login
from foundry.pages import agent, explore, governance, leaderboard, library, submit

st.set_page_config(
    page_title="VP&C Agent Marketplace",
    page_icon=str(theme.LOGO_FILE) if theme.LOGO_FILE.exists() else "🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    # The login gate runs before navigation so an unauthenticated visitor never
    # sees a page shell. Phase 2 replaces this with an Entra ID SSO redirect.
    if not is_authenticated():
        render_login()
        return

    pages = [
        st.Page(explore.render, title="Explore", url_path="explore", default=True),
        st.Page(library.render, title="The Library", url_path="library"),
        st.Page(leaderboard.render, title="Leaderboard", url_path="leaderboard"),
        st.Page(submit.render, title="Submit", url_path="submit"),
        st.Page(governance.render, title="Governance", url_path="governance"),
        st.Page(agent.render, title="Agent", url_path="agent"),
    ]
    for key, page in zip(
        ["explore", "library", "leaderboard", "submit", "governance", "agent"], pages
    ):
        nav.register(key, page)

    st.navigation(pages, position="hidden").run()


if __name__ == "__main__":
    main()
