"""Agent detail — the page a tile opens into.

Badges and copy on the left, the playground on the right. Which playground you
get depends on the agent: a live sandbox chat for embeddable platforms, a
sample transcript plus a deep link for the ones we can't frame, a lock panel
for restricted agents, and an upvote panel for ideas that don't exist yet.
"""

from __future__ import annotations

import time

import streamlit as st

from foundry import components as ui
from foundry import nav, theme
from foundry.auth import current_email, require_auth
from foundry.playgrounds import get_playground
from foundry.repo import Agent, get_repo

TYPING_DELAY_SECONDS = 0.9


def render() -> None:
    require_auth()
    theme.apply()
    ui.header("Agent detail")

    sent_for = st.session_state.pop("access_sent", None)
    if sent_for:
        st.success(
            f"Request sent — the owner of {sent_for} has been notified. "
            "You'll get a Teams message when it's approved."
        )

    agent_id = nav.selected_agent_id()
    agent = get_repo().get_agent(agent_id) if agent_id else None
    if agent is None:
        st.markdown(
            '<div class="vf-panel" style="text-align:center;padding:40px">'
            'That agent no longer exists.</div>', unsafe_allow_html=True)
        if st.button("← All agents"):
            nav.open_library("all")
        return

    if st.button("← All agents", key="agent_back"):
        nav.open_library("all")

    _title_block(agent)
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    st.divider()

    left, right = st.columns([1.25, 1], gap="large")
    with left:
        _about(agent)
        _how_it_works(agent)
        _try_asking(agent)
        _owner_card(agent)
    with right:
        _playground(agent)
        _metrics(agent)
        _reviews(agent)


def _title_block(agent: Agent) -> None:
    label = ui.MATURITY_LABEL[agent.maturity]
    bg, fg = ui.MATURITY_BADGE[agent.maturity][1], ui.MATURITY_BADGE[agent.maturity][2]
    badges = (
        ui.platform_badge(agent)
        + ui.badge(label, bg, fg)
        + f'<span class="vf-meta">{ui.esc(agent.function)}</span>'
        + (ui.restricted_badge() if agent.locked else "")
    )
    head, action = st.columns([3, 1], vertical_alignment="center")
    with head:
        st.markdown(
            f'<div class="vf-fade"><div style="display:flex;gap:7px;align-items:center;'
            f'flex-wrap:wrap;margin-bottom:10px">{badges}</div>'
            f'<div style="font-size:38px;font-weight:800;letter-spacing:-.04em;'
            f'line-height:1.05">{ui.esc(agent.name)}</div>'
            f'<div style="font-size:14.5px;color:var(--ink2);margin-top:10px;'
            f'line-height:1.55;max-width:620px">{ui.esc(agent.tagline)}</div></div>',
            unsafe_allow_html=True,
        )
    with action:
        playground = get_playground(agent.platform)
        if agent.locked:
            if st.button("Request access", type="primary", use_container_width=True,
                         key="req_top"):
                _request_dialog(agent)
        elif not agent.is_idea:
            st.link_button(playground.open_label, agent.deep_link or "#",
                           use_container_width=True,
                           help="Phase 2 wires this to the real platform deep link")


def _about(agent: Agent) -> None:
    st.markdown(
        f'<div style="font-size:17px;font-weight:800;letter-spacing:-.02em">About</div>'
        f'<div style="font-size:14px;color:var(--ink2);line-height:1.65;margin-top:8px">'
        f'{ui.esc(agent.about)}</div>',
        unsafe_allow_html=True,
    )


def _how_it_works(agent: Agent) -> None:
    steps = "".join(
        f'<div style="display:flex;gap:12px;margin-top:12px">'
        f'<div style="width:22px;height:22px;border-radius:99px;background:var(--chip);'
        f'color:var(--ink2);font-size:11px;font-weight:700;display:grid;place-items:center;'
        f'flex:none">{i}</div>'
        f'<div style="font-size:13.5px;color:var(--ink2);line-height:1.55">{ui.esc(step)}</div>'
        f'</div>'
        for i, step in enumerate(agent.how, start=1)
    )
    st.markdown(
        f'<div style="margin-top:26px;font-size:17px;font-weight:800;letter-spacing:-.02em">'
        f'How it works</div>{steps}',
        unsafe_allow_html=True,
    )


def _try_asking(agent: Agent) -> None:
    if not agent.sample_prompts:
        return
    st.markdown(
        '<div style="margin-top:26px;font-size:17px;font-weight:800;letter-spacing:-.02em">'
        'Try asking</div>', unsafe_allow_html=True)
    for i, prompt in enumerate(agent.sample_prompts):
        if st.button(f"“{prompt}”", key=f"prompt_{agent.id}_{i}",
                     use_container_width=True):
            _ask(agent, prompt)


def _owner_card(agent: Agent) -> None:
    with st.container(border=True, key="owner_card"):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<div class="vf-avatar" style="width:38px;height:38px;font-size:13px;'
            f'background:{theme.PLATFORM_VAR[agent.platform]}">'
            f'{ui.esc(agent.owner_initials)}</div>'
            f'<div><div style="font-weight:700;font-size:13.5px">{ui.esc(agent.owner)}</div>'
            f'<div style="font-size:11.5px;color:var(--ink3);margin-top:1px">'
            f'{ui.esc(agent.owner_role)} · agent owner</div></div></div>',
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------
# playground
# --------------------------------------------------------------------------

def _ask(agent: Agent, text: str) -> None:
    st.session_state.setdefault("chat", [])
    st.session_state["chat"].append(("u", text))
    st.session_state["chat_typing"] = True
    st.rerun()


def _bubble(who: str, text: str) -> str:
    mine = who == "u"
    dark = theme.is_dark()
    bg = ("#E9E9EE" if dark else "#1A1A1A") if mine else "var(--card)"
    fg = ("#141416" if dark else "#FFFFFF") if mine else "var(--ink)"
    border = "none" if mine else "1px solid var(--line)"
    radius = "14px 14px 4px 14px" if mine else "14px 14px 14px 4px"
    align = "flex-end" if mine else "flex-start"
    return (
        f'<div style="display:flex;justify-content:{align};margin:8px 0">'
        f'<div style="max-width:84%;background:{bg};color:{fg};border:{border};'
        f'border-radius:{radius};padding:10px 13px;font-size:13px;line-height:1.55">'
        f'{ui.esc(text)}</div></div>'
    )


def _playground(agent: Agent) -> None:
    if agent.locked:
        _lock_panel(agent)
        return
    if agent.is_idea:
        _idea_panel(agent)
        return

    playground = get_playground(agent.platform)
    if playground.embeddable:
        _live_playground(agent, playground)
    else:
        _sample_transcript(agent, playground)


def _panel_head(title: str, note: str) -> str:
    return (
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'gap:10px;padding-bottom:10px;border-bottom:1px solid var(--line2)">'
        f'<div style="display:flex;align-items:center;gap:7px">'
        f'<span class="vf-pulse-dot"></span>'
        f'<span style="font-weight:700;font-size:13.5px">{ui.esc(title)}</span></div>'
        f'<span style="font-size:11px;color:var(--ink4)">{ui.esc(note)}</span></div>'
    )


def _live_playground(agent: Agent, playground) -> None:
    """Sandbox chat. Replies come from the canned stub until Phase 2 lands."""
    st.session_state.setdefault("chat", [])
    messages = st.session_state["chat"]

    with st.container(border=True, key="playground"):
        st.markdown(_panel_head("Playground", "sandbox · no real data"),
                    unsafe_allow_html=True)

        if not messages and not st.session_state.get("chat_typing"):
            st.markdown(
                f'<div style="padding:26px 8px;text-align:center;color:var(--ink4);'
                f'font-size:12.5px;line-height:1.6">Ask {ui.esc(agent.name)} something, '
                f'or pick one of the sample prompts.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "".join(_bubble(who, text) for who, text in messages),
                unsafe_allow_html=True,
            )

        if st.session_state.get("chat_typing"):
            st.markdown(
                f'<div style="font-size:12px;color:var(--ink4);padding:4px 2px">'
                f'{ui.esc(agent.name)} is thinking…</div>',
                unsafe_allow_html=True,
            )
            time.sleep(TYPING_DELAY_SECONDS)
            reply = playground.send(agent, messages[-1][1] if messages else "")
            st.session_state["chat"].append(("a", reply))
            st.session_state["chat_typing"] = False
            st.rerun()

        typed = st.chat_input(f"Message {agent.name}…", key=f"chat_{agent.id}")

    if typed:
        _ask(agent, typed)


def _sample_transcript(agent: Agent, playground) -> None:
    """Platforms we can't frame: show what it looks like, then hand over."""
    with st.container(border=True, key="playground"):
        st.markdown(_panel_head("See it in action", f"runs in {agent.platform}"),
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="vf-metric-k" style="margin:10px 0 2px">SAMPLE TRANSCRIPT</div>',
            unsafe_allow_html=True,
        )
        opener = agent.sample_prompts[0] if agent.sample_prompts else ""
        st.markdown(_bubble("u", opener) + _bubble("a", agent.canned_reply),
                    unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:12px;color:var(--ink3);line-height:1.55;margin-top:10px">'
            "This agent can't be embedded here — the marketplace deep-links you to it.</div>",
            unsafe_allow_html=True,
        )
        st.link_button(playground.open_label, agent.deep_link or "#",
                       use_container_width=True,
                       help="Phase 2 wires this to the real platform deep link")


def _lock_panel(agent: Agent) -> None:
    with st.container(border=True, key="lock_panel"):
        st.markdown(
            f'<div style="font-weight:800;font-size:16px;letter-spacing:-.02em">'
            f"You don't have access yet</div>"
            f'<div style="font-size:13px;color:var(--ink2);line-height:1.6;margin-top:8px">'
            f'{ui.esc(agent.name)} is restricted to {ui.esc(agent.audience)}. Request access '
            f'and {ui.esc(agent.owner)} will review it — typical turnaround is 1 working '
            f'day.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Request access", type="primary", use_container_width=True,
                     key="req_panel"):
            _request_dialog(agent)


def _idea_panel(agent: Agent) -> None:
    voted = agent.id in ui.voted_ids()
    with st.container(border=True, key="idea_panel"):
        st.markdown(
            '<div style="font-weight:800;font-size:16px;letter-spacing:-.02em">'
            'This is still an idea</div>'
            '<div style="font-size:13px;color:var(--ink2);line-height:1.6;margin-top:8px">'
            'Vote it up — the top ideas each quarter get a build sprint with the '
            'VP&amp;C AI team.</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"▲ Upvote · {agent.votes}", use_container_width=True,
                     disabled=voted, type="primary" if voted else "secondary",
                     key=f"idea_vote_{agent.id}"):
            if get_repo().record_vote(agent.id, current_email()):
                st.rerun()


@st.dialog("Request access")
def _request_dialog(agent: Agent) -> None:
    st.markdown(
        f'<div style="font-size:13px;color:var(--ink2);line-height:1.6">'
        f'Your request goes to <b>{ui.esc(agent.owner)}</b> ({ui.esc(agent.owner_role)}). '
        f'Access is role-based — tell them briefly why you need it.</div>',
        unsafe_allow_html=True,
    )
    # A form, not a bare button: Streamlit only commits a text_area's value on
    # blur, so a plain button would need a first click just to wake up.
    with st.form("access_request", border=False):
        reason = st.text_area(
            "Why do you need it?", key="access_reason",
            placeholder="e.g. Quarterly contract reviews for the Fixed team",
        )
        cancel, send = st.columns(2)
        with cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)
        with send:
            sent = st.form_submit_button("Send request", type="primary",
                                         use_container_width=True)

    if cancelled:
        st.rerun()
    if sent:
        if not reason.strip():
            st.error("Add a line on why you need access — the owner reviews these by hand.")
            return
        get_repo().add_request(agent.id, agent.name, current_email(), reason.strip())
        st.session_state["access_sent"] = agent.name
        st.rerun()


# --------------------------------------------------------------------------
# metrics and reviews
# --------------------------------------------------------------------------

METRIC_LABELS = {
    "monthly_users": ("MONTHLY USERS", "var(--ink)"),
    "tasks_per_month": ("TASKS / MONTH", "var(--ink)"),
    "csat": ("CSAT", "var(--tea)"),
    "uptime": ("UPTIME", "var(--ok)"),
    "impact_score": ("IMPACT SCORE", "var(--ink)"),
    "community_votes": ("COMMUNITY VOTES", "var(--ink)"),
    "pilot_users": ("PILOT USERS", "var(--ink)"),
    "hours_saved_per_month": ("EST. HOURS SAVED / MO", "var(--ok)"),
    "upvotes": ("UPVOTES", "var(--ink)"),
    "comments": ("COMMENTS", "var(--ink)"),
    "feasibility": ("FEASIBILITY", "var(--org)"),
    "next_sprint_pick": ("NEXT SPRINT PICK", "var(--pur)"),
}


def _metrics(agent: Agent) -> None:
    title = "Adoption" if agent.maturity == "scaled" else "Evaluation this cycle"
    cells = []
    for key, value in agent.metrics.items():
        label, colour = METRIC_LABELS.get(key, (key.replace("_", " ").upper(), "var(--ink)"))
        display = f"{value} / 5" if key == "csat" else value
        cells.append(
            f'<div style="flex:1 1 40%"><div class="vf-metric-v" style="color:{colour};'
            f'font-size:20px">{ui.esc(display)}</div>'
            f'<div class="vf-metric-k">{ui.esc(label)}</div></div>'
        )
    st.markdown(
        f'<div class="vf-panel" style="margin-top:16px">'
        f'<div style="font-weight:700;font-size:13.5px;margin-bottom:12px">{ui.esc(title)}</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:16px">{"".join(cells)}</div></div>',
        unsafe_allow_html=True,
    )


def _reviews(agent: Agent) -> None:
    if not agent.reviews:
        return
    rows = "".join(
        f'<div style="padding:12px 0;border-top:1px solid var(--line2)">'
        f'<div style="color:var(--org);font-size:12px;letter-spacing:.06em">'
        f'{ui.stars(int(r["stars"]))}</div>'
        f'<div style="font-size:13px;color:var(--ink2);line-height:1.55;margin-top:5px">'
        f'“{ui.esc(r["text"])}”</div>'
        f'<div class="vf-meta" style="margin-top:5px">{ui.esc(r["who"])} · '
        f'{ui.esc(r["role"])}</div></div>'
        for r in agent.reviews
    )
    rating = (
        f'<span style="font-size:13px;font-weight:700;color:var(--org)">'
        f'★ {agent.rating_avg}</span>'
        f'<span class="vf-meta"> {agent.rating_count} ratings</span>'
        if agent.rating_avg else ""
    )
    st.markdown(
        f'<div class="vf-panel" style="margin-top:16px">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
        f'<span style="font-weight:700;font-size:13.5px">What colleagues say</span>'
        f'{rating}</div>{rows}</div>',
        unsafe_allow_html=True,
    )
