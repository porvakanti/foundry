"""Submit - three tracks, one form.

An idea, a Copilot agent you built, or a nomination to scale. The fields
differ per track; everything persists to ``data/submissions.json``.
"""

from __future__ import annotations

import streamlit as st

from foundry import components as ui
from foundry import nav, theme
from foundry.auth import current_email, require_auth
from foundry.repo import get_repo

TRACKS = {
    "idea": ("+", "An idea", "Just the problem - no build needed",
             "var(--redSoft)", "var(--red)"),
    "agent": ("◆", "A Copilot agent", "Gets a tile + enters the monthly scoring",
              "var(--purSoft)", "var(--pur)"),
    "scale": ("↗", "Ready to scale", "Nominate for production support",
              "var(--teaSoft)", "var(--tea)"),
}

FIELDS = {
    "idea": [
        ("What problem should an agent solve?",
         "e.g. Chasing suppliers for missing onboarding documents eats ~4 hrs/week…", True),
        ("Who feels this pain?", "e.g. Supplier governance, ~12 people", False),
        ("What would good look like?", "e.g. A weekly digest with drafted chase emails", False),
    ],
    "agent": [
        ("Agent name", "e.g. PO Chaser", False),
        ("Link to your Copilot agent", "https://copilotstudio.microsoft.com/…", False),
        ("What does it do?",
         "One paragraph - what it automates, for whom, with what data", True),
        ("Function", "Sourcing / Contracts / P2P / Supplier Mgmt / Analytics / Governance", False),
        ("Who should have access?", "e.g. All of VP&C, or a specific team (RBAC applies)", False),
    ],
    "scale": [
        ("Which agent?", "Pick from your published pilots, e.g. PO Chaser", False),
        ("Evidence of impact", "Hours saved, adoption, CSAT - link your metrics", True),
        ("Current pilot users", "e.g. 38 across P2P operations", False),
        ("Owner sign-off", "Name of the accountable lead", False),
    ],
}

CTA = {"idea": "Submit idea", "agent": "Publish agent", "scale": "Nominate to scale"}

SUCCESS = {
    "idea": ("Idea submitted",
             "It's now live in the New Ideas band for the community to vote on. "
             "Top ideas each quarter get a build sprint."),
    "agent": ("Agent published",
              "The AI team will sandbox it, add a marketplace tile, and it enters this "
              "month's scale-up scoring. You'll hear back within a day."),
    "scale": ("Nomination in",
              "The nomination goes to the monthly review board with your evidence "
              "attached. Decisions land right after the review."),
}

NEXT_STEPS = [
    "The VP&C AI team reviews your submission within 1 working day",
    "Agents get a sandbox check: data access, responsible-AI screen, RBAC setup",
    "A marketplace tile goes live and the community can try it and vote",
    "Monthly review: top-scoring pilot is promoted to production",
]

WEIGHTS = [("Impact (hours saved)", "40%"), ("Adoption", "30%"),
           ("User satisfaction", "20%"), ("Community votes", "10%")]


def render() -> None:
    require_auth()
    theme.apply()
    ui.header("Submit")

    ui.page_title("Put something on the marketplace",
                  "Three tracks, one form. Everything lands with the VP&C AI team "
                  "within a day.",
                  back="← Home", back_key="submit_back")
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        _track_picker()
        if st.session_state.get("submit_done"):
            _success()
        else:
            _form()
    with right:
        _what_happens_next()
        _scoring_panel()


def _track_picker() -> None:
    track = st.session_state.get("submit_track", "agent")
    cols = st.columns(3, gap="small")
    for col, (key, (glyph, title, sub, tint, fg)) in zip(cols, TRACKS.items()):
        selected = key == track
        with col:
            with st.container(border=True, key=f"card_track_{key}"):
                st.markdown(
                    f'<div class="vf-mono" style="background:{tint};color:{fg};font-size:15px">'
                    f'{glyph}</div>'
                    f'<div style="font-weight:700;font-size:13.5px;margin-top:9px">'
                    f'{ui.esc(title)}</div>'
                    f'<div style="font-size:11.5px;color:var(--ink3);margin-top:3px;'
                    f'line-height:1.45;min-height:32px">{ui.esc(sub)}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Selected" if selected else "Choose",
                             key=f"track_pick_{key}", use_container_width=True,
                             type="primary" if selected else "secondary",
                             disabled=selected):
                    st.session_state["submit_track"] = key
                    st.session_state["submit_done"] = False
                    st.rerun()


def _form() -> None:
    track = st.session_state.get("submit_track", "agent")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    with st.form(f"submit_{track}", border=True):
        values: dict[str, str] = {}
        for i, (label, placeholder, multiline) in enumerate(FIELDS[track]):
            widget = st.text_area if multiline else st.text_input
            values[label] = widget(label, placeholder=placeholder, key=f"{track}_field_{i}")

        send, note = st.columns([1, 2], vertical_alignment="center")
        with send:
            submitted = st.form_submit_button(CTA[track], type="primary",
                                              use_container_width=True)
        with note:
            st.markdown('<div class="vf-meta">Reviewed within 1 working day</div>',
                        unsafe_allow_html=True)

    if submitted:
        first_label = FIELDS[track][0][0]
        if not values[first_label].strip():
            st.error(f"“{first_label}” is needed before this can go to the AI team.")
            return
        get_repo().add_submission(track, values, current_email())
        st.session_state["submit_done"] = True
        st.rerun()


def _success() -> None:
    track = st.session_state.get("submit_track", "agent")
    title, body = SUCCESS[track]
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.container(border=True, key="submit_success"):
        st.markdown(
            f'<div style="text-align:center;padding:14px 8px">'
            f'<div style="font-size:26px">✓</div>'
            f'<div style="font-size:19px;font-weight:800;letter-spacing:-.02em;margin-top:6px">'
            f'{ui.esc(title)}</div>'
            f'<div style="font-size:13px;color:var(--ink2);line-height:1.6;margin-top:8px;'
            f'max-width:420px;margin-left:auto;margin-right:auto">{ui.esc(body)}</div></div>',
            unsafe_allow_html=True,
        )
        back, again = st.columns(2)
        with back:
            if st.button("Back to marketplace", use_container_width=True, key="succ_home"):
                st.session_state["submit_done"] = False
                nav.goto("explore")
        with again:
            if st.button("Submit another", type="primary", use_container_width=True,
                         key="succ_again"):
                st.session_state["submit_done"] = False
                for key in list(st.session_state):
                    if "_field_" in key:
                        st.session_state.pop(key, None)
                st.rerun()


def _what_happens_next() -> None:
    steps = "".join(
        f'<div style="display:flex;gap:11px;margin-top:12px">'
        f'<div style="width:21px;height:21px;border-radius:99px;background:var(--chip);'
        f'color:var(--ink2);font-size:10.5px;font-weight:700;display:grid;'
        f'place-items:center;flex:none">{i}</div>'
        f'<div style="font-size:12.5px;color:var(--ink2);line-height:1.5">{ui.esc(step)}</div>'
        f'</div>'
        for i, step in enumerate(NEXT_STEPS, start=1)
    )
    st.markdown(
        f'<div class="vf-panel"><div style="font-weight:700;font-size:14px">'
        f'What happens next</div>{steps}</div>',
        unsafe_allow_html=True,
    )


def _scoring_panel() -> None:
    rows = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:7px 0;'
        f'border-bottom:1px solid rgba(255,255,255,.1);font-size:12.5px">'
        f'<span style="opacity:.8">{ui.esc(label)}</span><b>{weight}</b></div>'
        for label, weight in WEIGHTS
    )
    st.markdown(
        f'<div class="vf-panel-dark" style="margin-top:16px">'
        f'<div style="font-weight:700;font-size:14px;margin-bottom:6px">'
        f'How pilots are scored</div>{rows}'
        f'<div style="font-size:11.5px;opacity:.72;line-height:1.5;margin-top:12px">'
        f'Top agent each month is promoted to production with full support, SLA and '
        f'RBAC rollout.</div></div>',
        unsafe_allow_html=True,
    )
