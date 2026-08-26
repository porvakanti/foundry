"""Governance & RBAC - the admin view.

Who is waiting for access to a restricted agent, and what the standing policy
is for every governed agent. Open to every invited reviewer: seeing the RBAC
queue is part of what the pilot is asking people to review.
"""

from __future__ import annotations

import streamlit as st

from foundry import components as ui
from foundry import theme
from foundry.auth import current_email, require_auth
from foundry.feedback import get_feedback_store
from foundry.repo import display_name, get_repo

AVG_APPROVAL = "0.8d"


def render() -> None:
    require_auth()
    theme.apply()
    ui.header("Governance")

    repo = get_repo()
    agents = repo.list_agents()
    requests = repo.list_requests()

    ui.page_title("Governance & RBAC", back="← Home", back_key="gov_back",
                  badge_html=ui.badge("ADMIN VIEW", "var(--redSoft)", "var(--red)"))

    governed = [a for a in agents if a.maturity != "idea"]
    pending = [r for r in requests if r["status"] == "pending"]

    _kpis(len(pending), len(agents), sum(a.locked for a in agents))
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    queue, policies = st.columns([1.15, 1], gap="large")
    with queue:
        _request_queue(requests, len(pending))
    with policies:
        _policy_table(governed)

    _feedback_panel()


def _kpis(pending: int, governed: int, restricted: int) -> None:
    cells = [
        (str(pending), "PENDING REQUESTS", "var(--red)"),
        (str(governed), "AGENTS GOVERNED", "var(--ink)"),
        (str(restricted), "ROLE-RESTRICTED", "var(--ink)"),
        (AVG_APPROVAL, "AVG APPROVAL TIME", "var(--tea)"),
    ]
    cols = st.columns(4, gap="medium")
    for col, (value, label, colour) in zip(cols, cells):
        with col:
            st.markdown(
                f'<div class="vf-kpi"><div class="vf-kpi-v" style="color:{colour}">'
                f'{ui.esc(value)}</div><div class="vf-kpi-k">{ui.esc(label)}</div></div>',
                unsafe_allow_html=True,
            )


def _request_queue(requests: list[dict], pending: int) -> None:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:9px;margin-bottom:10px">'
        f'<span style="font-weight:800;font-size:15px;letter-spacing:-.02em">'
        f'Pending access requests</span>'
        f'{ui.badge(str(pending), "var(--redSoft)", "var(--red)")}</div>',
        unsafe_allow_html=True,
    )

    if not requests:
        st.markdown(
            '<div class="vf-panel" style="color:var(--ink3);font-size:13px">'
            'Nothing waiting - the queue is clear.</div>', unsafe_allow_html=True)
        return

    ordered = sorted(requests, key=lambda r: (r["status"] != "pending", r["id"]))
    for req in ordered:
        _request_row(req)


def _request_row(req: dict) -> None:
    name = req.get("requester_name") or display_name(req["requester"])
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "VF"
    when = req.get("age_label") or "just now"

    # Approve/Deny get their own top-level columns rather than a nested pair:
    # columns only nest one level deep, and a container does not reset that.
    with st.container(border=True, key=f"card_req_{req['id']}"):
        body, approve_col, deny_col = st.columns([2.2, 0.62, 0.55],
                                                 vertical_alignment="center")
        with body:
            st.markdown(
                f'<div style="display:flex;gap:11px;align-items:flex-start">'
                f'<div class="vf-avatar" style="background:var(--pur);flex:none">'
                f'{ui.esc(initials)}</div>'
                f'<div style="min-width:0">'
                f'<div style="font-size:13.5px;font-weight:700">{ui.esc(name)} → '
                f'{ui.esc(req["agent_name"])}</div>'
                f'<div style="font-size:12px;color:var(--ink3);margin-top:3px;line-height:1.5">'
                f'“{ui.esc(req["reason"])}” · {ui.esc(req.get("requester_role", "Reviewer"))} '
                f'· {ui.esc(when)}</div></div></div>',
                unsafe_allow_html=True,
            )
        pending = req["status"] == "pending"
        with approve_col:
            if pending:
                if st.button("Approve", key=f"ok_{req['id']}", type="primary",
                             use_container_width=True):
                    get_repo().set_request_status(req["id"], "approved", current_email())
                    st.rerun()
            else:
                approved = req["status"] == "approved"
                st.markdown(
                    '<div style="text-align:right">'
                    + ui.badge(
                        "APPROVED" if approved else "DENIED",
                        "var(--okSoft)" if approved else "var(--redSoft)",
                        "var(--ok)" if approved else "var(--red2)",
                    )
                    + "</div>",
                    unsafe_allow_html=True,
                )
        with deny_col:
            if pending and st.button("Deny", key=f"no_{req['id']}",
                                     use_container_width=True):
                get_repo().set_request_status(req["id"], "denied", current_email())
                st.rerun()


def _policy_table(governed: list) -> None:
    st.markdown(
        '<div style="font-weight:800;font-size:15px;letter-spacing:-.02em;'
        'margin-bottom:10px">Access policies</div>',
        unsafe_allow_html=True,
    )
    header = "".join(
        f'<th style="text-align:left;padding:8px;font-size:9.5px;letter-spacing:.07em;'
        f'color:var(--ink4);font-weight:600">{h}</th>'
        for h in ["AGENT", "AUDIENCE", "POLICY"]
    )
    rows = "".join(
        f'<tr style="border-top:1px solid var(--line2)">'
        f'<td style="padding:11px 8px"><div style="display:flex;align-items:center;gap:7px">'
        f'<span class="vf-dot" style="background:{theme.PLATFORM_VAR[a.platform]}"></span>'
        f'<span style="font-size:13px;font-weight:700">{ui.esc(a.name)}</span></div></td>'
        f'<td style="padding:11px 8px;font-size:12px;color:var(--ink2);line-height:1.45">'
        f'{ui.esc(a.audience[:1].upper() + a.audience[1:])}</td>'
        f'<td style="padding:11px 8px">'
        + ui.badge("RESTRICTED" if a.locked else "OPEN",
                   "var(--redSoft)" if a.locked else "var(--okSoft)",
                   "var(--red2)" if a.locked else "var(--ok)")
        + "</td></tr>"
        for a in governed
    )
    st.markdown(
        f'<div class="vf-panel" style="padding:6px 12px 12px">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def _feedback_panel() -> None:
    """What colleagues have told us, newest first."""
    store = get_feedback_store()
    entries = list(reversed(store.list()))

    st.markdown(
        f'<div style="height:28px"></div>'
        f'<div style="display:flex;align-items:center;gap:9px;margin-bottom:10px">'
        f'<span style="font-weight:800;font-size:15px;letter-spacing:-.02em">'
        f'Feedback from colleagues</span>'
        f'{ui.badge(str(len(entries)), "var(--purSoft)", "var(--pur)")}</div>',
        unsafe_allow_html=True,
    )

    if store.durable:
        unsynced = sum(1 for e in entries if not e.synced)
        if unsynced:
            cols = st.columns([3, 1])
            with cols[0]:
                st.warning(f"{unsynced} not yet filed to GitHub - the API was "
                           "unreachable when they were written.")
            with cols[1]:
                if st.button("Retry sync", use_container_width=True):
                    pushed = store.retry_unsynced()
                    st.toast(f"Filed {pushed} to GitHub.", icon="✅")
                    st.rerun()
    else:
        st.info(
            "Feedback is being kept on the app only, so it is lost when the app "
            "sleeps or redeploys. Set GITHUB_TOKEN and GITHUB_REPO in secrets to "
            "file each one as an issue instead.",
            icon="ℹ️",
        )

    if not entries:
        st.markdown(
            '<div class="vf-panel" style="color:var(--ink3);font-size:13px">'
            'Nothing yet. The Feedback button is in the header on every page.</div>',
            unsafe_allow_html=True)
        return

    for entry in entries:
        rating = f'{"★" * entry.stars}{"☆" * (5 - entry.stars)}' if entry.stars else ""
        where = f"{entry.page} · {entry.agent_name}" if entry.agent_name else entry.page
        link = (f' · <a href="{ui.esc(entry.issue_url)}" target="_blank" '
                f'style="color:var(--red)">issue ↗</a>' if entry.issue_url else "")
        st.markdown(
            f'<div class="vf-panel" style="margin-bottom:8px">'
            f'<div style="display:flex;justify-content:space-between;gap:12px;'
            f'align-items:baseline;flex-wrap:wrap">'
            f'<span style="font-size:13px;font-weight:700">{ui.esc(entry.topic)}</span>'
            f'<span style="color:var(--org);font-size:12px">{rating}</span></div>'
            f'<div style="font-size:13px;color:var(--ink2);line-height:1.55;margin-top:6px">'
            f'{ui.esc(entry.text) or "<i>no comment</i>"}</div>'
            f'<div class="vf-meta" style="margin-top:6px">{ui.esc(entry.who)} · '
            f'{ui.esc(where)} · {ui.esc(entry.created_at[:16].replace("T", " "))}'
            f'{link}</div></div>',
            unsafe_allow_html=True,
        )
