"""The Library — the full inventory, filtered.

Tabs by maturity, then chips by function and platform. The design spec's chips
map cleanly onto ``st.pills``, so those are used rather than reimplemented.
"""

from __future__ import annotations

import streamlit as st

from foundry import components as ui
from foundry import concierge, scoring, theme
from foundry.auth import require_auth
from foundry.config import FUNCTIONS, PLATFORMS
from foundry.repo import get_repo

CATEGORIES = {"all": "All", "scaled": "Scaled", "pilot": "Pilots", "idea": "Ideas"}


def render() -> None:
    require_auth()
    theme.apply()
    ui.header("The Library")

    agents = get_repo().list_agents()
    voted = ui.voted_ids()

    ui.page_title("The Agent Library", "Every agent in VP&C, in one shelf.",
                  back="← Home", back_key="lib_back")
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    counts = {
        "all": len(agents),
        "scaled": sum(a.maturity == "scaled" for a in agents),
        "pilot": sum(a.maturity == "pilot" for a in agents),
        "idea": sum(a.maturity == "idea" for a in agents),
    }
    labels = {key: f"{label} ({counts[key]})" for key, label in CATEGORIES.items()}

    current = st.session_state.get("library_cat", "all")
    chosen = st.segmented_control(
        "Maturity",
        options=list(CATEGORIES),
        format_func=lambda k: labels[k],
        default=current if current in CATEGORIES else "all",
        key="library_cat_control",
        label_visibility="collapsed",
    )
    category = chosen or "all"
    st.session_state["library_cat"] = category

    fn_col, plat_col = st.columns(2)
    with fn_col:
        st.markdown('<div class="vf-metric-k" style="margin-bottom:4px">FUNCTION</div>',
                    unsafe_allow_html=True)
        function = st.pills("Function", FUNCTIONS, selection_mode="single",
                            key="lib_fn", label_visibility="collapsed")
    with plat_col:
        st.markdown('<div class="vf-metric-k" style="margin-bottom:4px">PLATFORM</div>',
                    unsafe_allow_html=True)
        platform = st.pills("Platform", PLATFORMS, selection_mode="single",
                            key="lib_plat", label_visibility="collapsed")

    shown = _apply_filters(agents, category, function, platform,
                           st.session_state.get("q", ""))

    st.markdown(
        f'<div class="vf-meta" style="margin:16px 0 10px">'
        f'{len(shown)} of {len(agents)} agents</div>',
        unsafe_allow_html=True,
    )

    if not shown:
        st.markdown(
            '<div class="vf-panel" style="text-align:center;padding:40px 18px;'
            'color:var(--ink3);font-size:13.5px">No agents match these filters.</div>',
            unsafe_allow_html=True,
        )
        return

    ui.card_row(shown, ui.library_card, ctx="lib", voted=voted)


def _apply_filters(agents, category, function, platform, query):
    """Maturity, then chips, then the header search box — in that order."""
    ordered = _order(agents, category)
    if function:
        ordered = [a for a in ordered if a.function == function]
    if platform:
        ordered = [a for a in ordered if a.platform == platform]
    return concierge.filter_agents(query, ordered)


def _order(agents, category):
    """Pilots always read in leaderboard order; the rest keep repo order."""
    pilots = scoring.ranked_pilots(agents)
    scaled = [a for a in agents if a.maturity == "scaled"]
    ideas = [a for a in agents if a.maturity == "idea"]
    return {"all": scaled + pilots + ideas, "scaled": scaled,
            "pilot": pilots, "idea": ideas}[category]
