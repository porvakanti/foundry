"""Leaderboard — how a pilot earns promotion to production.

Scored by the Evaluation Agent against four weighted criteria. The headline
number is the score published for this cycle; the expander recomputes the same
formula from the inputs we hold so a reviewer can see where it comes from.
"""

from __future__ import annotations

import streamlit as st

from foundry import components as ui
from foundry import nav, scoring, theme
from foundry.auth import require_auth
from foundry.config import NEXT_REVIEW
from foundry.repo import get_repo

PAST_WINNERS = [
    ("AUG", "PO Chaser", "scaling now"),
    ("JUL", "Spend Lens", "in production"),
    ("JUN", "Contract IQ", "in production"),
]


def render() -> None:
    require_auth()
    theme.apply()
    ui.header("Leaderboard")

    agents = get_repo().list_agents()
    pilots = scoring.ranked_pilots(agents)
    breakdowns = scoring.compute_scores(pilots)
    voted = ui.voted_ids()

    head, review = st.columns([3, 1], vertical_alignment="center")
    with head:
        ui.page_title(
            "Scale-up leaderboard",
            "Every Copilot pilot is scored monthly. The winner gets promoted to a "
            "fully supported production agent.",
            back="← Home", back_key="board_back",
        )
    with review:
        st.markdown(
            f'<div class="vf-panel-dark" style="text-align:center">'
            f'<div style="font-size:9.5px;letter-spacing:.09em;opacity:.65;font-weight:600">'
            f'NEXT REVIEW</div>'
            f'<div style="font-size:24px;font-weight:800;letter-spacing:-.03em;margin-top:2px">'
            f'{ui.esc(NEXT_REVIEW)}</div></div>',
            unsafe_allow_html=True,
        )

    _evaluation_banner()
    _criteria()
    _podium(pilots, voted)
    _table(pilots, breakdowns)
    _past_winners()


def _evaluation_banner() -> None:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    with st.container(border=True, key="eval_banner"):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:11px">'
            f'{theme.orbit_logo(22)}'
            f'<div style="font-size:13px;line-height:1.55"><b>Scored by the Evaluation Agent</b>'
            f'<span style="color:var(--ink3)"> — recomputed 21 Aug from usage telemetry, '
            f'validated hours saved and CSAT. 1 anomaly flagged for human review.</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


def _criteria() -> None:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    cols = st.columns(4, gap="medium")
    for col, (weight, name, desc, colour) in zip(cols, scoring.CRITERIA):
        with col:
            st.markdown(
                f'<div class="vf-kpi" style="height:100%">'
                f'<div style="display:flex;align-items:baseline;gap:7px">'
                f'<span style="font-size:21px;font-weight:800;letter-spacing:-.03em;'
                f'color:{colour}">{weight}</span>'
                f'<span style="font-size:13px;font-weight:700">{ui.esc(name)}</span></div>'
                f'<div style="font-size:11.5px;color:var(--ink3);margin-top:6px;'
                f'line-height:1.5">{ui.esc(desc)}</div></div>',
                unsafe_allow_html=True,
            )


def _podium(pilots, voted) -> None:
    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    top = pilots[:3]
    cols = st.columns(len(top) or 1, gap="medium")
    for i, (col, agent) in enumerate(zip(cols, top)):
        leading = i == 0
        with col:
            key = ("card_podium_lead" if leading
                   else f"card_podium_{agent.id}")
            with st.container(border=True, key=key):
                st.markdown(
                    '<div>'
                    f'<div style="display:flex;align-items:center;gap:9px">'
                    f'<span style="font-size:22px;font-weight:800;letter-spacing:-.03em">'
                    f'#{i + 1}</span>{ui.monogram(agent)}'
                    f'<div style="flex:1"></div>'
                    f'{ui.badge("LEADING", "var(--red)", "#fff") if leading else ""}</div>'
                    f'<div style="font-size:17px;font-weight:800;letter-spacing:-.02em;'
                    f'margin-top:10px">{ui.esc(agent.name)}</div>'
                    f'<div style="font-size:11.5px;opacity:.72;margin-top:2px">'
                    f'by {ui.esc(agent.owner)} · {ui.esc(agent.function)}</div>'
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                    f'margin-top:14px"><span style="font-size:9.5px;letter-spacing:.07em;'
                    f'font-weight:600;opacity:.7">IMPACT SCORE</span>'
                    f'<span style="font-size:20px;font-weight:800">{agent.impact_score}</span></div>'
                    f'<div class="vf-track" style="margin-top:6px">'
                    f'<span style="width:{agent.impact_score}%"></span></div>'
                    f'<div style="display:flex;gap:16px;margin-top:12px;font-size:11.5px;'
                    f'opacity:.8"><span><b>{agent.hours_saved_per_month}</b> hrs saved/mo</span>'
                    f'<span><b>{agent.pilot_users}</b> users</span>'
                    f'<span>▲ {agent.votes}</span></div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Open →", key=f"podium_go_{agent.id}", use_container_width=True):
                    nav.open_agent(agent.id)


def _table(pilots, breakdowns) -> None:
    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    rows = "".join(
        f'<tr style="border-top:1px solid var(--line2)">'
        f'<td style="padding:11px 8px;font-weight:800;'
        f'color:{"var(--red)" if i == 0 else "var(--ink)"}">{i + 1}</td>'
        f'<td style="padding:11px 8px"><div style="font-weight:700;font-size:13px">'
        f'{ui.esc(a.name)}</div><div class="vf-meta">{ui.esc(a.owner)}</div></td>'
        f'<td style="padding:11px 8px;font-size:12.5px;color:var(--ink2)">'
        f'{ui.esc(a.function)}</td>'
        f'<td style="padding:11px 8px;min-width:130px">'
        f'<div style="display:flex;align-items:center;gap:8px">'
        f'<div class="vf-track" style="flex:1"><span style="width:{a.impact_score}%"></span></div>'
        f'<span style="font-size:12px;font-weight:700;white-space:nowrap">'
        f'{a.impact_score} / 100</span></div></td>'
        f'<td style="padding:11px 8px;font-size:12.5px">{a.hours_saved_per_month}</td>'
        f'<td style="padding:11px 8px;font-size:12.5px">{a.pilot_users}</td>'
        f'<td style="padding:11px 8px;font-size:12.5px">▲ {a.votes}</td>'
        f'<td style="padding:11px 8px;font-size:12.5px;color:var(--ink3)">{ui.esc(a.trend)}</td>'
        f'</tr>'
        for i, a in enumerate(pilots)
    )
    header = "".join(
        f'<th style="text-align:left;padding:9px 8px;font-size:9.5px;letter-spacing:.07em;'
        f'color:var(--ink4);font-weight:600">{h}</th>'
        for h in ["#", "AGENT", "FUNCTION", "IMPACT", "HRS/MO", "USERS", "VOTES", "TREND"]
    )
    st.markdown(
        f'<div class="vf-panel" style="padding:6px 12px 12px">'
        f'<table style="width:100%;border-collapse:collapse"><thead><tr>{header}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>',
        unsafe_allow_html=True,
    )

    with st.expander("How the Evaluation Agent computes these scores"):
        st.markdown(
            "Each component is normalised 0–100 across the pilot cohort, then weighted "
            "**40% impact · 30% adoption · 20% satisfaction · 10% community**. "
            "A pilot with no ratings yet is placed at the cohort mean for satisfaction, "
            "so being new is not the same as being disliked."
        )
        for agent in pilots:
            breakdown = breakdowns.get(agent.id)
            if not breakdown:
                continue
            parts = " · ".join(
                f"{label} {value:.0f} → {contribution:.1f}"
                for label, value, contribution in breakdown.components()
            )
            st.markdown(
                f"<div style='font-size:12.5px;padding:6px 0;border-bottom:1px solid var(--line2)'>"
                f"<b>{ui.esc(agent.name)}</b> — {parts} · "
                f"<b>recomputed {breakdown.total:.1f}</b> "
                f"<span class='vf-meta'>(published {agent.impact_score})</span></div>",
                unsafe_allow_html=True,
            )


def _past_winners() -> None:
    st.markdown(
        "<div style='height:26px'></div>"
        "<div class='vf-metric-k' style='margin-bottom:8px'>PAST WINNERS</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3, gap="medium")
    for col, (month, name, tag) in zip(cols, PAST_WINNERS):
        with col:
            st.markdown(
                f'<div class="vf-kpi" style="display:flex;align-items:center;gap:11px">'
                f'<span style="font-size:11px;font-weight:800;letter-spacing:.06em;'
                f'color:var(--ink4)">{month}</span>'
                f'<div><div style="font-size:13.5px;font-weight:700">{ui.esc(name)}</div>'
                f'<div class="vf-meta">{ui.esc(tag)}</div></div></div>',
                unsafe_allow_html=True,
            )
