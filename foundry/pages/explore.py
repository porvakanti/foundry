"""Explore — the marketplace home.

Hero, the three submission CTAs, the winner ticker, a personalised "For you"
row, then the three maturity bands.
"""

from __future__ import annotations

import streamlit as st

from foundry import components as ui
from foundry import nav, scoring, theme
from foundry.auth import require_auth
from foundry.config import NEXT_REVIEW, VIEWER_ROLE
from foundry.repo import get_repo

#: Why the Concierge picked each tile for this role. Phase 2 derives these
#: from the reviewer's own usage and their team's, not a hardcoded list.
FOR_YOU = {
    "poc": "Built inside P2P operations — your team ships this",
    "spl": "41 colleagues in your market ask it spend questions",
    "sob": "Peers in your role use this weekly",
    "tst": "New P2P-adjacent idea — needs your vote",
}

CTAS = [
    ("idea", "+", "Submit an idea", "No build needed — just the problem",
     "var(--cta1)", "var(--cta1b)", "var(--redSoft)", "var(--red)"),
    ("agent", "◆", "Publish your Copilot agent", "Surface what you built to all of VP&C",
     "var(--cta2)", "var(--cta2b)", "var(--purSoft)", "var(--pur)"),
    ("scale", "↗", "Nominate an agent to scale", "Put it forward for the monthly review",
     "var(--cta3)", "var(--cta3b)", "var(--teaSoft)", "var(--tea)"),
]


def render() -> None:
    require_auth()
    theme.apply()
    ui.header()

    agents = get_repo().list_agents()
    voted = ui.voted_ids()
    ranks = scoring.pilot_ranks(agents)

    _hero()
    _ctas()
    _ticker()
    _for_you(agents, voted, ranks)

    scaled = [a for a in agents if a.maturity == "scaled"]
    pilots = scoring.ranked_pilots(agents)
    ideas = [a for a in agents if a.maturity == "idea"]

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    ui.section_header("Scaled & deployed", "Production agents with full support and SLAs",
                      see_all=("See all →", "scaled"))
    ui.card_row(scaled, ui.scaled_card, ctx="home_scaled")

    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    ui.section_header("Copilot pilots",
                      "Competing for the next scale-up · vote for what goes to production",
                      see_all=("See all →", "pilot"))
    ui.card_row(pilots, ui.pilot_card, ctx="home_pilot", ranks=ranks, voted=voted)

    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    ui.section_header("New ideas", "Vote on what gets built next — top ideas get a build sprint",
                      see_all=("See all →", "idea"))
    ui.card_row(ideas, ui.idea_card, ctx="home_idea", voted=voted)

    _footer()


def _hero() -> None:
    st.markdown(
        """
        <div class="vf-fade" style="position:relative;border-radius:28px;
             background:var(--heroGrad);border:1px solid rgba(230,0,0,.08);
             padding:40px 44px 26px;overflow:hidden;margin:8px 0 0;
             border-bottom:none;border-radius:28px 28px 0 0">
          <div style="position:absolute;top:-140px;right:-100px;width:460px;height:460px;
               border-radius:99em;background:radial-gradient(circle,rgba(230,0,0,.10),transparent 65%);
               pointer-events:none"></div>
          <div style="position:absolute;bottom:-160px;left:30%;width:420px;height:420px;
               border-radius:99em;background:radial-gradient(circle,rgba(0,124,146,.09),transparent 65%);
               pointer-events:none"></div>
          <div style="position:relative;display:grid;
               grid-template-columns:minmax(0,1fr) clamp(200px,26vw,320px);
               gap:28px;align-items:center">
          <div>
            <div style="font-size:clamp(32px,4.2vw,48px);line-height:1.05;letter-spacing:-.035em;
                 font-weight:800">Every VP&amp;C agent.<br>
              <span style="background:linear-gradient(90deg,#E60000,#9C2AA0 60%,#007C92);
                    -webkit-background-clip:text;background-clip:text;color:transparent">
                One marketplace.</span></div>
            <div style="font-size:14.5px;color:var(--ink2);margin-top:16px;line-height:1.6;
                 max-width:520px">
              Discover, try and scale the AI agents built across Vodafone Procurement &amp;
              Connectivity — from production platforms to the Copilot agent your colleague
              built last week.</div>
          </div>
          <div style="display:flex;flex-direction:column;gap:12px">
            <div style="background:var(--card);border-radius:14px;padding:12px 14px;
                 box-shadow:var(--shadowUp);transform:translateX(6px)">
              <div style="display:flex;align-items:center;gap:9px">
                <div class="vf-mono" style="background:var(--purSoft);color:var(--pur);
                     width:28px;height:28px;font-size:10.5px">PC</div>
                <div><div style="font-size:12.5px;font-weight:700">PO Chaser</div>
                <div style="font-size:10.5px;color:var(--pur)">#1 this month</div></div></div>
              <div class="vf-track" style="margin-top:9px"><span style="width:86%"></span></div>
              <div style="font-size:10px;color:var(--ink4);margin-top:6px;letter-spacing:.04em">
                IMPACT 86 · ▲ 214</div>
            </div>
            <div style="background:var(--card);border-radius:99px;padding:8px 14px;
                 box-shadow:var(--shadow);display:flex;align-items:center;gap:8px;
                 align-self:flex-start">
              <span class="vf-pulse-dot"></span>
              <span style="font-size:11.5px;font-weight:600">Onboarding Buddy replied</span>
              <span style="font-size:10.5px;color:var(--ink4)">now</span>
            </div>
            <div style="background:var(--panel);color:#fff;border-radius:14px;padding:12px 14px;
                 box-shadow:var(--shadowUp);transform:translateX(-6px)">
              <div style="display:flex;align-items:center;gap:9px">
                <div class="vf-mono" style="background:var(--cynSoft);color:var(--cyn);
                     width:28px;height:28px;font-size:10.5px">SL</div>
                <div style="font-size:12.5px;font-weight:700">Spend Lens</div></div>
              <div style="margin-top:8px"><span style="font-size:19px;font-weight:800;
                   letter-spacing:-.03em">655</span>
                <span style="font-size:9.5px;letter-spacing:.07em;opacity:.7"> USERS / MO</span>
              </div>
            </div>
          </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="hero_actions"):
        browse, submit, _ = st.columns([1.15, 1, 3.4])
        with browse:
            if st.button("Browse the Library →", type="primary", use_container_width=True):
                nav.open_library("all")
        with submit:
            if st.button("Submit yours", use_container_width=True):
                nav.open_submit("agent")


def _ctas() -> None:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    cols = st.columns(3, gap="medium")
    for col, (track, glyph, title, sub, card, border, tint, fg) in zip(cols, CTAS):
        with col:
            with st.container(border=True, key=f"cta_{track}"):
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:11px">'
                    f'<div class="vf-mono" style="background:{tint};color:{fg};font-size:15px">'
                    f'{glyph}</div>'
                    f'<div><div style="font-weight:700;font-size:13.5px">{ui.esc(title)}</div>'
                    f'<div style="font-size:11.5px;color:var(--ink3);margin-top:1px">'
                    f'{ui.esc(sub)}</div></div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Start →", key=f"cta_go_{track}", use_container_width=True):
                    nav.open_submit(track)


def _ticker() -> None:
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    with st.container(border=True, key="ticker"):
        text, action = st.columns([5, 1], vertical_alignment="center")
        with text:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
                f'{ui.badge("AUG WINNER", "var(--redSoft)", "var(--red)")}'
                f'<span style="font-size:13px;font-weight:600">PO Chaser is being promoted '
                f'to a fully supported production agent</span>'
                f'<span class="vf-meta">· Next review {ui.esc(NEXT_REVIEW)}</span></div>',
                unsafe_allow_html=True,
            )
        with action:
            if st.button("Leaderboard →", key="ticker_board", use_container_width=True):
                nav.goto("leaderboard")


def _for_you(agents, voted, ranks) -> None:
    by_id = {a.id: a for a in agents}
    picks = [by_id[i] for i in FOR_YOU if i in by_id]
    if not picks:
        return

    st.markdown(
        f'<div style="height:28px"></div>'
        f'<div class="vf-sec-title">For you</div>'
        f'<div class="vf-sec-sub">picked by the Concierge for your role · '
        f'{ui.esc(VIEWER_ROLE)}</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(picks), gap="medium")
    for col, agent in zip(cols, picks):
        with col:
            with st.container(border=True, key=f"foryou_{agent.id}"):
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px">'
                    f'{ui.monogram(agent)}'
                    f'<div style="min-width:0"><div style="font-weight:700;font-size:13.5px">'
                    f'{ui.esc(agent.name)}</div>'
                    f'<div style="font-size:11.5px;color:var(--ink4);margin-top:2px;'
                    f'line-height:1.4">{ui.esc(FOR_YOU[agent.id])}</div></div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Open →", key=f"foryou_go_{agent.id}", use_container_width=True):
                    nav.open_agent(agent.id)


def _footer() -> None:
    st.markdown(
        '<div style="margin-top:56px;padding-top:20px;border-top:1px solid var(--line3);'
        'display:flex;gap:18px;flex-wrap:wrap;font-size:11.5px;color:var(--ink4)">'
        '<span>VP&amp;C Agent Marketplace · internal</span>'
        '<span>Governance &amp; RBAC</span><span>Responsible AI policy</span>'
        '<span>Support</span></div>',
        unsafe_allow_html=True,
    )
