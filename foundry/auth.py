"""Pilot-grade authentication.

Two steps, and it is worth being precise about what each one is for.

1. A shared username and password. One credential for everyone in VP&C.
2. Who you are, used to attribute your votes and access requests.

Step 2 is NOT a security check on its own and the UI does not pretend
otherwise. A typed address can be anyone's, so it is checked against the list
of people invited to the app. Real access control lives in the app's Community
Cloud viewer allowlist, which verifies each person's identity before Streamlit
serves the app at all.

Note that ``st.user`` cannot help here: since Streamlit 1.42 it no longer
exposes the viewer's Community Cloud account email, so the signed-in identity
is not readable from inside the app without a configured identity provider.

PHASE 2 REPLACES THIS ENTIRELY with Entra ID SSO. At that point the reviewer's
identity, their group memberships and therefore their agent entitlements all
come from the token, and `require_auth` becomes a token check.
"""

from __future__ import annotations

import re
from hmac import compare_digest

import streamlit as st

from foundry import theme
from foundry.config import access_contact, allowed_domain, allowed_emails, setting
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
    """Whether this person may open Governance.

    Everyone invited can, deliberately: seeing the RBAC queue and access
    policies is part of what the pilot is asking people to look at. Membership
    of ALLOWED_EMAILS is the only gate, so there is no second list to keep in
    step with the first.

    Phase 2 reverses this - with Entra ID SSO the admin view belongs to the
    VP&C AI team's group, not to everyone who can open the app.
    """
    return is_authenticated()


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
    """Validate format, domain, and membership of the invited list.

    The list is what stops a valid-looking address that belongs to nobody:
    without it, any @vodafone.com string would be accepted. Leaving
    ALLOWED_EMAILS unset keeps the app open to the whole domain, which is the
    sensible default before the audience is known.
    """
    email = email.strip()
    domain = allowed_domain()
    if not EMAIL_RE.match(email):
        return False, "That doesn't look like an email address - check the format and try again."
    if not email.lower().endswith("@" + domain):
        return False, (
            f"The marketplace is open to @{domain} addresses only. "
            "Use your Vodafone address, or ask the VP&C AI team to add you."
        )
    invited = allowed_emails()
    if invited and email.lower() not in invited:
        return False, (
            f"You're not authorised to access this yet. "
            f"Please reach out to {access_contact()} for access."
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
    first_step = not st.session_state.get("password_ok")
    strapline = (
        '<div style="font-size:13.5px;color:var(--ink3);margin-top:8px;line-height:1.5">'
        'Every VP&amp;C agent, in one place.</div>' if first_step else ""
    )
    st.markdown(
        f"""
        <div class="vf-fade" style="max-width:420px;margin:6vh auto 20px;text-align:center">
          <div style="display:flex;justify-content:center;margin-bottom:14px">{theme.orbit_logo(52)}</div>
          <div style="font-size:30px;font-weight:800;letter-spacing:-.03em;line-height:1.1">
            Agent Marketplace
          </div>
          {strapline}
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
            "<div style='text-align:center;font-size:11px;color:var(--ink4);margin-top:22px'>"
            "Pilot access only · no real supplier or contract data"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_credentials_step() -> None:
    with st.form("login_credentials"):
        st.markdown("<div style='font-weight:700;font-size:15px;margin-bottom:6px'>Sign in</div>",
                    unsafe_allow_html=True)
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
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
    """Ask who is signing in, and check them against the invited list."""
    st.markdown(
        "<div style='font-weight:700;font-size:15px;margin-bottom:2px'>Who are you?</div>"
        "<div style='font-size:12.5px;color:var(--ink3);margin-bottom:10px;line-height:1.5'>"
        "So your votes and access requests are attributed to you. "
        "We don't send anything to this address.</div>",
        unsafe_allow_html=True,
    )

    with st.form("login_email"):
        email = st.text_input("Your Vodafone email")
        submitted = st.form_submit_button("Enter the marketplace", type="primary",
                                          use_container_width=True)

    if submitted:
        ok, message = check_email(email)
        if ok:
            _sign_in(email)
        else:
            st.error(message)

    if st.button("← Back", use_container_width=True):
        st.session_state.pop("password_ok", None)
        st.rerun()


def _sign_in(email: str) -> None:
    st.session_state["authenticated"] = True
    st.session_state["email"] = email.strip().lower()
    try:
        get_repo().log_login(st.session_state["email"])
    except Exception:
        # Never block a sign-in because the login log is unwritable.
        pass
    st.rerun()
