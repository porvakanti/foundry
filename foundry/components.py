"""Shared UI pieces: the top bar, agent cards, badges and metric strips.

Cards are a hybrid on purpose. The visual body is one HTML block so it can
match the design spec, but the actions are real Streamlit buttons inside a
keyed container - a plain ``<a href>`` would trigger a browser navigation and
drop the reviewer's session. The container key is what the CSS hooks onto to
make button-and-markup read as a single card.
"""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from foundry import concierge, nav, theme
from foundry.auth import current_email, initials, logout
from foundry.config import VIEWER_ROLE
from foundry.repo import Agent, get_repo

MATURITY_BADGE = {
    "scaled": ("Scaled", "var(--okSoft)", "var(--ok)"),
    "pilot": ("Pilot", "var(--purSoft)", "var(--pur)"),
    "idea": ("Idea", "var(--chip)", "var(--ink2)"),
}

MATURITY_LABEL = {
    "scaled": "Scaled · production",
    "pilot": "Pilot · scale-up contender",
    "idea": "Idea · in voting",
}

NOTIFICATIONS = [
    ("Access approved", "Lena Fischer approved your access to Contract IQ", "2h"),
    ("New in P2P", "Idea submitted: Invoice Dispute Resolver - vote now", "1d"),
    ("August review results", "PO Chaser won and is being promoted to production", "3d"),
]


def esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


# --------------------------------------------------------------------------
# small html fragments
# --------------------------------------------------------------------------

def badge(label: str, bg: str, fg: str, dot: str | None = None) -> str:
    dot_html = f'<span class="vf-dot" style="background:{dot}"></span>' if dot else ""
    return f'<span class="vf-badge" style="background:{bg};color:{fg}">{dot_html}{esc(label)}</span>'


def platform_badge(agent: Agent) -> str:
    return badge(agent.platform, "var(--chip)", "var(--ink2)", theme.PLATFORM_VAR[agent.platform])


def restricted_badge() -> str:
    return badge("Restricted", "var(--redSoft)", "var(--red2)")


def monogram(agent: Agent) -> str:
    return (
        f'<div class="vf-mono" style="background:{theme.PLATFORM_TINT[agent.platform]};'
        f'color:{theme.PLATFORM_VAR[agent.platform]}">{esc(agent.monogram)}</div>'
    )


def pulse_line(agent: Agent) -> str:
    if not agent.pulse:
        return ""
    return (
        f'<div class="vf-pulse"><span class="vf-pulse-dot"></span>{esc(agent.pulse)}</div>'
    )


def metric_cell(value: Any, label: str, colour: str = "var(--ink)") -> str:
    return (
        f'<div><div class="vf-metric-v" style="color:{colour}">{esc(value)}</div>'
        f'<div class="vf-metric-k">{esc(label)}</div></div>'
    )


def stars(count: int) -> str:
    return "★" * count + "☆" * (5 - count)


def section_header(title: str, subtitle: str, see_all: tuple[str, str] | None = None) -> None:
    """A band heading with an optional 'See all →' on the right."""
    left, right = st.columns([6, 1], vertical_alignment="bottom")
    with left:
        st.markdown(
            f'<div class="vf-sec-title">{esc(title)}</div>'
            f'<div class="vf-sec-sub">{esc(subtitle)}</div>',
            unsafe_allow_html=True,
        )
    with right:
        if see_all:
            label, category = see_all
            if st.button(label, key=f"seeall_{category}", use_container_width=True):
                nav.open_library(category)


def page_title(title: str, subtitle: str = "", back: str | None = None,
               back_key: str = "back", badge_html: str = "") -> None:
    """Breadcrumb + heading block used by every non-home page."""
    if back:
        if st.button(back, key=back_key):
            nav.goto("explore")
    st.markdown(
        f'<div class="vf-fade"><div style="font-size:34px;font-weight:800;letter-spacing:-.035em;'
        f'line-height:1.1;margin:6px 0 0;display:flex;align-items:center;gap:12px;'
        f'flex-wrap:wrap">{esc(title)}{badge_html}</div>'
        + (f'<div style="font-size:14px;color:var(--ink3);margin-top:8px;max-width:640px;'
           f'line-height:1.5">{esc(subtitle)}</div>' if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# header
# --------------------------------------------------------------------------

def header() -> None:
    """The sticky-style top bar: brand, Concierge search, bell, theme, avatar."""
    topbar = st.container(key="topbar")
    brand, search, bell, mode, avatar = topbar.columns(
        [3.1, 4.2, 0.8, 0.8, 0.8], vertical_alignment="center"
    )

    with brand:
        st.markdown(
            f'<div class="vf-brand">{theme.orbit_logo(34)}'
            f'<div class="vf-brand-name">Agent Marketplace</div></div>',
            unsafe_allow_html=True,
        )

    with search:
        st.text_input(
            "Search",
            key="q",
            placeholder="Search, or describe a task, then press ↵ - the Concierge matches agents",
            label_visibility="collapsed",
        )

    with bell:
        with st.popover("🔔", use_container_width=True):
            st.markdown("**Notifications**")
            for title, detail, when in NOTIFICATIONS:
                st.markdown(
                    f'<div style="padding:8px 0;border-bottom:1px solid var(--line2)">'
                    f'<div style="font-size:13px;font-weight:600">{esc(title)}</div>'
                    f'<div style="font-size:12px;color:var(--ink3);margin-top:2px;'
                    f'line-height:1.45">{esc(detail)}</div>'
                    f'<div style="font-size:10.5px;color:var(--ink4);margin-top:3px">'
                    f'{esc(when)} ago</div></div>',
                    unsafe_allow_html=True,
                )

    with mode:
        icon = "☀" if theme.is_dark() else "☾"
        if st.button(icon, key="theme_toggle", use_container_width=True,
                     help="Switch between light and dark"):
            theme.toggle_theme()
            st.rerun()

    with avatar:
        with st.popover(initials(), use_container_width=True):
            st.markdown(
                f'<div style="font-size:13px;font-weight:600">{esc(current_email())}</div>'
                f'<div style="font-size:11.5px;color:var(--ink3);margin-top:2px">'
                f'{esc(VIEWER_ROLE)}</div>',
                unsafe_allow_html=True,
            )
            if st.button("Sign out", key="signout", use_container_width=True):
                logout()
                st.rerun()

    _nav_row()
    st.markdown(
        '<div style="height:1px;background:var(--line3);margin:2px 0 18px"></div>',
        unsafe_allow_html=True,
    )
    _concierge_panel()


def _nav_row() -> None:
    """The page links.

    Keyed so the stylesheet can keep this row horizontal on a narrow screen
    while every other column group stacks: eight stacked rows of nav would
    push the page itself off the phone.
    """
    items = list(nav.NAV_ITEMS)
    with st.container(key="topnav"):
        cols = st.columns(len(items) + 3)
        for col, (key, label) in zip(cols, items):
            with col:
                st.page_link(nav.page(key), label=label)


def _concierge_panel() -> None:
    """Top-3 task matches, shown inline under the header as you type.

    The design spec floats this as a dropdown over the page; Streamlit has no
    overlay for it, so it becomes an inline panel in the same position.
    """
    query = st.session_state.get("q", "")
    if len(query.strip()) < concierge.MIN_QUERY_LEN:
        return

    agents = get_repo().list_agents()
    hits = concierge.match(query, agents)

    with st.container(border=True, key="concierge_panel"):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding-bottom:8px;'
            f'border-bottom:1px solid var(--line2);margin-bottom:6px">{theme.orbit_logo(16)}'
            f'<span style="font-size:11px;font-weight:700;letter-spacing:.04em;'
            f'color:var(--ink2)">CONCIERGE</span>'
            f'<span style="font-size:11.5px;color:var(--ink4)">matching agents to your task…'
            f'</span></div>',
            unsafe_allow_html=True,
        )
        if not hits:
            st.markdown(
                '<div style="font-size:12.5px;color:var(--ink3);padding:6px 2px">'
                'No direct match - try describing the task differently, or browse '
                'the Library.</div>',
                unsafe_allow_html=True,
            )
            return
        for hit in hits:
            row, action = st.columns([6, 1], vertical_alignment="center")
            with row:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0">'
                    f'{monogram(hit.agent)}'
                    f'<div><div style="font-size:13.5px;font-weight:700">'
                    f'{esc(hit.agent.name)}'
                    f'{" " + restricted_badge() if hit.agent.locked else ""}</div>'
                    f'<div style="font-size:11.5px;color:var(--ink4);margin-top:1px">'
                    f'{esc(hit.reason)} · {esc(hit.agent.function)}</div></div></div>',
                    unsafe_allow_html=True,
                )
            with action:
                if st.button("Open →", key=f"conc_{hit.agent.id}", use_container_width=True):
                    st.session_state["q"] = ""
                    nav.open_agent(hit.agent.id)


# --------------------------------------------------------------------------
# voting
# --------------------------------------------------------------------------

def voted_ids() -> set[str]:
    """Agents this reviewer has already upvoted (one vote per agent)."""
    return get_repo().voted_agents(current_email())


def _vote_button(agent: Agent, ctx: str, already: bool) -> None:
    label = f"▲ {agent.votes}"
    if st.button(label, key=f"vote_{ctx}_{agent.id}", use_container_width=True,
                 disabled=already,
                 help="You've already voted for this agent" if already
                 else "Upvote - votes are 10% of the monthly score",
                 type="primary" if already else "secondary"):
        if get_repo().record_vote(agent.id, current_email()):
            st.rerun()


# --------------------------------------------------------------------------
# cards
# --------------------------------------------------------------------------

def _card_head(agent: Agent, trailing: str = "") -> str:
    bits = [monogram(agent), '<div style="flex:1"></div>', trailing or platform_badge(agent),
            f'<span class="vf-meta">{esc(agent.function)}</span>']
    if agent.locked:
        bits.append(restricted_badge())
    return (
        '<div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap">'
        + "".join(bits) + "</div>"
    )


def _card_body(agent: Agent) -> str:
    return (
        f'<div class="vf-card-title">{esc(agent.name)}</div>'
        f'<div class="vf-card-tag">{esc(agent.tagline)}</div>'
        f'{pulse_line(agent)}'
    )


def scaled_card(agent: Agent, ctx: str = "home") -> None:
    """Production agent: adoption numbers, no competition."""
    with st.container(border=True, key=f"card_agent_{ctx}_{agent.id}"):
        m = agent.metrics
        st.markdown(
            _card_head(agent) + _card_body(agent)
            + '<div class="vf-metrics">'
            + metric_cell(m.get("monthly_users", "-"), "MONTHLY USERS")
            + metric_cell(m.get("tasks_per_month", "-"), "TASKS / MO")
            + metric_cell(m.get("csat", "-"), "CSAT", "var(--tea)")
            + "</div>",
            unsafe_allow_html=True,
        )
        if st.button("Open →", key=f"open_{ctx}_{agent.id}", use_container_width=True):
            nav.open_agent(agent.id)


def pilot_card(agent: Agent, ctx: str = "home", ranks: dict[str, int] | None = None,
               voted: set[str] | None = None) -> None:
    """Copilot pilot: impact bar, rank and the upvote that feeds the score."""
    voted = voted if voted is not None else voted_ids()
    rank = (ranks or {}).get(agent.id, 0)
    with st.container(border=True, key=f"card_agent_{ctx}_{agent.id}"):
        rank_badge = badge(f"#{rank}", "var(--chip)", "var(--ink2)") if rank else ""
        st.markdown(
            _card_head(agent, trailing=rank_badge) + _card_body(agent)
            + '<div class="vf-metrics" style="display:block">'
            + '<div style="display:flex;justify-content:space-between;align-items:baseline">'
            + '<span class="vf-metric-k">IMPACT SCORE</span>'
            + f'<span class="vf-metric-v">{agent.impact_score}</span></div>'
            + f'<div class="vf-track" style="margin-top:6px">'
              f'<span style="width:{agent.impact_score}%"></span></div>'
            + f'<div class="vf-meta" style="margin-top:8px">by {esc(agent.owner)}</div>'
            + "</div>",
            unsafe_allow_html=True,
        )
        open_col, vote_col = st.columns([2, 1])
        with open_col:
            if st.button("Open →", key=f"open_{ctx}_{agent.id}", use_container_width=True):
                nav.open_agent(agent.id)
        with vote_col:
            _vote_button(agent, ctx, agent.id in voted)


def idea_card(agent: Agent, ctx: str = "home", voted: set[str] | None = None) -> None:
    """Idea: no build yet, just the problem and the votes behind it."""
    voted = voted if voted is not None else voted_ids()
    with st.container(border=True, key=f"card_agent_{ctx}_{agent.id}"):
        st.markdown(
            f'<div class="vf-card-title" style="margin-top:0">{esc(agent.name)}</div>'
            f'<div class="vf-card-tag">{esc(agent.tagline)}</div>'
            f'<div class="vf-meta" style="margin-top:10px">{esc(agent.function)} · '
            f'proposed by {esc(agent.owner)}</div>',
            unsafe_allow_html=True,
        )
        open_col, vote_col = st.columns([2, 1])
        with open_col:
            if st.button("Open →", key=f"open_{ctx}_{agent.id}", use_container_width=True):
                nav.open_agent(agent.id)
        with vote_col:
            _vote_button(agent, ctx, agent.id in voted)


def library_card(agent: Agent, ctx: str = "lib", voted: set[str] | None = None) -> None:
    """The Library's unified card - same shape whatever the maturity."""
    voted = voted if voted is not None else voted_ids()
    label, bg, fg = MATURITY_BADGE[agent.maturity]
    if agent.maturity == "scaled":
        meta = f"{agent.metrics.get('monthly_users', '-')} users/mo · CSAT {agent.metrics.get('csat', '-')}"
    elif agent.maturity == "pilot":
        meta = f"Impact {agent.impact_score} · ▲ {agent.votes}"
    else:
        meta = f"▲ {agent.votes} votes"

    with st.container(border=True, key=f"card_agent_{ctx}_{agent.id}"):
        st.markdown(
            _card_head(agent, trailing=platform_badge(agent) + badge(label, bg, fg))
            + _card_body(agent)
            + f'<div class="vf-metrics" style="justify-content:space-between">'
              f'<span class="vf-meta">{esc(meta)}</span>'
              f'<span class="vf-meta">{esc(agent.function)}</span></div>',
            unsafe_allow_html=True,
        )
        if agent.maturity == "scaled":
            if st.button("Open →", key=f"open_{ctx}_{agent.id}", use_container_width=True):
                nav.open_agent(agent.id)
        else:
            open_col, vote_col = st.columns([2, 1])
            with open_col:
                if st.button("Open →", key=f"open_{ctx}_{agent.id}", use_container_width=True):
                    nav.open_agent(agent.id)
            with vote_col:
                _vote_button(agent, ctx, agent.id in voted)


def card_row(agents: list[Agent], render, per_row: int = 3, **kwargs: Any) -> None:
    """Lay agents out in rows of equal-width cards.

    The design spec scrolls these horizontally; Streamlit has no horizontal
    scroller, so the band wraps into rows of three instead - same content,
    same order, no hack.
    """
    for start in range(0, len(agents), per_row):
        chunk = agents[start:start + per_row]
        cols = st.columns(per_row, gap="medium")
        for col, agent in zip(cols, chunk):
            with col:
                render(agent, **kwargs)

