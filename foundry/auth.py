"""Who gets in, and as what.

Three ways in, tried in that order by :func:`require_auth`.

1. **The identity provider**, when SSO is on. The host has already
   authenticated the visitor and the app adopts that identity.
2. **A signed guest link** from the stage QR, when SSO is off. Scanning goes
   straight in as an anonymous guest who can browse and vote, and nothing else.
   See :mod:`foundry.guest`.
3. **The pilot sign-in**: a shared username and password, then who you are.

Step 3's second half is not a security check on its own, and the UI does not
pretend otherwise. A typed address could be anyone's, so it is checked against
the list of people invited to the app. On Community Cloud the real gate is the
viewer allowlist, which verifies identity before Streamlit serves the app at
all.

``st.user`` is only useful once an identity provider is configured. Since
Streamlit 1.42 it does not expose a Community Cloud account email on its own,
which is why the pilot sign-in exists at all.

PHASE 2 RETIRES THE PILOT SIGN-IN. With Entra ID SSO the identity, the group
memberships and therefore the agent entitlements all come from the token, and
the shared credential goes away.
"""

from __future__ import annotations

import re
from hmac import compare_digest

import streamlit as st

from foundry import guest, theme
from foundry.config import (access_contact, allowed_domain, allowed_emails, setting,
                            sso_enabled)
from foundry.repo import get_repo

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated")) and bool(st.session_state.get("email"))


def is_guest() -> bool:
    """Signed in from a scanned link rather than as a named colleague."""
    return bool(st.session_state.get("is_guest"))


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
    return is_authenticated() and not is_guest()


def logout() -> None:
    for key in ("authenticated", "email", "password_ok", "is_guest", guest.IDENTITY):
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
    """Guard every page.

    Three ways in, tried in order: an existing session, the identity provider
    once SSO is switched on, and a signed guest link from a scanned QR. Failing
    all three, the sign-in page.
    """
    if is_authenticated():
        return
    if sso_enabled() and _sso_sign_in():
        return
    if _guest_sign_in():
        return
    render_login()
    st.stop()


def _sso_sign_in() -> bool:
    """Adopt the identity the hosting environment has already established.

    Reads Streamlit's st.user, which carries an OIDC identity once auth is
    configured in secrets. That is the only source consulted today, because it
    is the only one that can be tested from here.

    If AI Booster instead fronts the app with a proxy that passes identity in a
    request header, this function is the single place to add that: read the
    header, put the address in ``email``, and the rest of the app is unchanged.
    Returning False falls through to the ordinary sign-in, so switching SSO on
    before the environment is ready degrades to what exists today rather than
    locking anyone out.
    """
    email = ""
    try:
        email = (getattr(st.user, "email", "") or "").strip().lower()
    except Exception:
        # No identity provider configured yet.
        email = ""
    if not email:
        return False
    ok, _ = check_email(email)
    if not ok:
        return False
    st.session_state["authenticated"] = True
    st.session_state["email"] = email
    st.session_state["is_guest"] = False
    _log(email)
    return True


def _guest_sign_in() -> bool:
    """Accept a signed link from the stage QR and sign in as a guest."""
    token = st.query_params.get(guest.PARAM, "")
    if not guest.verify(token):
        return False
    identity = st.session_state.get(guest.IDENTITY) or guest.new_identity()
    st.session_state[guest.IDENTITY] = identity
    st.session_state["authenticated"] = True
    st.session_state["email"] = identity
    st.session_state["is_guest"] = True
    return True


def require_member(action: str = "do this") -> None:
    """Stop a guest at anything that writes a colleague's name against a record."""
    if not is_guest():
        return
    theme.apply()
    st.markdown(
        f'<div class="vf-panel" style="text-align:center;padding:44px 20px;margin-top:24px">'
        f'<div style="font-size:19px;font-weight:800;letter-spacing:-.02em">'
        f'Sign in to {esc(action)}</div>'
        f'<div style="font-size:13px;color:var(--ink3);margin-top:8px;line-height:1.6;'
        f'max-width:430px;margin-left:auto;margin-right:auto">'
        f"You're browsing as a guest from a shared link, so you can look around "
        f"and vote. Anything that puts your name against a record needs a proper "
        f"sign-in.</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("Sign in", type="primary"):
        logout()
        st.query_params.clear()
        st.rerun()
    st.stop()


def esc(text: str) -> str:
    import html

    return html.escape(str(text), quote=True)


def _log(email: str) -> None:
    try:
        get_repo().log_login(email)
    except Exception:
        # Never block a sign-in because the login log is unwritable.
        pass


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
    st.session_state["is_guest"] = False
    _log(st.session_state["email"])
    st.rerun()
