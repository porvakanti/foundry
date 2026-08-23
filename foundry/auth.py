"""Pilot-grade authentication.

Deliberately simple: one shared credential for all reviewers, then a Vodafone
email address so we know who is voting and can count adoption. No email is
ever sent — the domain check is the gate.

PHASE 2 REPLACES THIS ENTIRELY with Entra ID SSO. At that point the reviewer's
identity, their group memberships and therefore their agent entitlements all
come from the token, and `require_auth` becomes a token check.
"""

from __future__ import annotations

import re
from hmac import compare_digest

import streamlit as st

from foundry import theme
from foundry.config import allowed_domain, setting
from foundry.repo import get_repo

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated")) and bool(st.session_state.get("email"))


def current_email() -> str:
    return st.session_state.get("email", "")


def initials() -> str:
    """Display initials derived from the email local part."""
    local = current_email().split("@")[0]
    parts = [p for p in re.split(r"[._-]+", local) if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return (local[:2] or "VF").upper()


def is_admin() -> bool:
    """Whether this reviewer may open Governance.

    An unset ADMIN_EMAILS means "not configured" rather than "nobody", so a
    fresh deploy is never locked out of the admin view — Governance says so
    with a banner when that is the case.
    """
    from foundry.config import admin_emails

    admins = admin_emails()
    return not admins or current_email().lower() in admins


def logout() -> None:
    for key in ("authenticated", "email", "password_ok"):
        st.session_state.pop(key, None)


def check_credentials(user: str, password: str) -> bool:
    expected_user = setting("AUTH_USER", "vpc")
    expected_pass = setting("AUTH_PASS", "")
    if not expected_pass:
        # No password configured: refuse rather than let anyone in.
        return False
    return compare_digest(user.strip(), expected_user) and compare_digest(password, expected_pass)


def check_email(email: str) -> tuple[bool, str]:
    """Validate format and domain. Returns ``(ok, message)``."""
    email = email.strip()
    domain = allowed_domain()
    if not EMAIL_RE.match(email):
        return False, "That doesn't look like an email address — check the format and try again."
    if not email.lower().endswith("@" + domain):
        return False, (
            f"The marketplace pilot is open to @{domain} addresses only. "
            "Use your Vodafone address, or ask the VP&C AI team to add you."
        )
    return True, ""


def require_auth() -> None:
    """Guard every page. Sends unauthenticated visitors back to the login."""
    if not is_authenticated():
        st.session_state["_next"] = True
        render_login()
        st.stop()


def render_login() -> None:
    """Two-step login: shared credential, then Vodafone email."""
    theme.apply()
    st.markdown(
        f"""
        <div class="vf-fade" style="max-width:420px;margin:6vh auto 20px;text-align:center">
          <div style="display:flex;justify-content:center;margin-bottom:14px">{theme.orbit_logo(52)}</div>
          <div style="font-size:30px;font-weight:800;letter-spacing:-.03em;line-height:1.1">
            Agent Marketplace
          </div>
          <div style="font-size:13.5px;color:var(--ink3);margin-top:8px;line-height:1.5">
            Every VP&amp;C agent, in one place. Sign in with the reviewer credentials
            the VP&amp;C AI team shared with you.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        if not st.session_state.get("password_ok"):
            _render_credentials_step()
        else:
            _render_email_step()

        st.markdown(
            "<div style='text-align:center;font-size:11px;color:var(--ink4);margin-top:22px;line-height:1.5'>"
            "Pilot access only · no real supplier or contract data<br>"
            "Phase 2 replaces this sign-in with Vodafone SSO"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_credentials_step() -> None:
    with st.form("login_credentials"):
        st.markdown("<div style='font-weight:700;font-size:15px;margin-bottom:6px'>Sign in</div>",
                    unsafe_allow_html=True)
        user = st.text_input("Username", placeholder="Reviewer username")
        password = st.text_input("Password", type="password", placeholder="Shared pilot password")
        submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)

    if submitted:
        if check_credentials(user, password):
            st.session_state["password_ok"] = True
            st.rerun()
        elif not setting("AUTH_PASS", ""):
            st.error(
                "No pilot password is configured. Set AUTH_USER and AUTH_PASS "
                "(see .streamlit/secrets.toml.example) and reload."
            )
        else:
            st.error("Those credentials don't match. Check with the VP&C AI team.")


def _render_email_step() -> None:
    domain = allowed_domain()
    st.markdown(
        f"<div style='font-weight:700;font-size:15px;margin-bottom:2px'>Almost there</div>"
        f"<div style='font-size:12.5px;color:var(--ink3);margin-bottom:10px;line-height:1.5'>"
        f"Tell us who you are so your votes and requests are attributed. "
        f"We don't send anything — your @{domain} address is the gate.</div>",
        unsafe_allow_html=True,
    )
    with st.form("login_email"):
        email = st.text_input("Vodafone email", placeholder=f"firstname.lastname@{domain}")
        submitted = st.form_submit_button("Enter the marketplace", type="primary",
                                          use_container_width=True)

    if submitted:
        ok, message = check_email(email)
        if ok:
            st.session_state["authenticated"] = True
            st.session_state["email"] = email.strip().lower()
            try:
                get_repo().log_login(st.session_state["email"])
            except Exception:
                # Never block a reviewer because the login log is unwritable.
                pass
            st.rerun()
        else:
            st.error(message)

    if st.button("← Back", use_container_width=True):
        st.session_state.pop("password_ok", None)
        st.rerun()
