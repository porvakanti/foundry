"""Page registry and navigation helpers.

Streamlit's own navigation is used (``st.navigation(position="hidden")``) so we
can render the marketplace's top bar ourselves while still getting real
client-side page switching - which matters because a raw ``<a href>`` would
reload the browser and drop the reviewer's session.

Agent detail is registered but never linked in the nav; it is reached by
selecting a tile, which stores the id in session state and switches page.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

#: Populated by ``app.py`` at startup: key -> StreamlitPage.
PAGES: dict[str, Any] = {}

#: The items that appear in the top bar, in order.
NAV_ITEMS = [
    ("explore", "Explore"),
    ("library", "The Library"),
    ("leaderboard", "Leaderboard"),
    ("submit", "Submit"),
    ("governance", "Governance"),
]


def register(key: str, page: Any) -> None:
    PAGES[key] = page


def page(key: str) -> Any:
    return PAGES[key]


def goto(key: str, **state: Any) -> None:
    """Switch page, optionally seeding session state for the destination."""
    for name, value in state.items():
        st.session_state[name] = value
    st.switch_page(PAGES[key])


def open_agent(agent_id: str) -> None:
    """Open an agent's detail page."""
    st.session_state["agent_id"] = agent_id
    st.session_state["chat"] = []
    st.session_state["chat_typing"] = False
    st.query_params["id"] = agent_id
    st.switch_page(PAGES["agent"])


def selected_agent_id() -> str | None:
    """The agent the detail page should show - session state, then the URL."""
    return st.session_state.get("agent_id") or st.query_params.get("id")


def open_library(category: str = "all", **filters: Any) -> None:
    st.session_state["library_cat"] = category
    st.session_state.update(filters)
    st.switch_page(PAGES["library"])


def open_submit(track: str) -> None:
    st.session_state["submit_track"] = track
    st.session_state["submit_done"] = False
    st.switch_page(PAGES["submit"])
