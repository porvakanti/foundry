"""Guest access from a signed link, for showing the marketplace to a room.

The problem this solves is a stage one. Put a QR on a screen in front of a few
hundred people and ask them to vote, and the shared username, the password and
their email address stand between the scan and the thing you want them to do.
Most of the room never arrives.

So the QR carries a token. Scanning it signs you straight in as a guest.

What a guest is allowed to do is what makes this safe enough to use:

* browse Explore, the Library and the Leaderboard, and vote
* nothing else. Submit, Governance and access requests all still require the
  ordinary sign-in, because those write things attributable to a person.

The token is a bearer credential in a URL, and anyone in the room can
photograph the screen. That is an accepted trade for an internal event with
illustrative data, and the reason the token expires on its own. It is not a
way to secure the app, and when SSO is switched on the app stops accepting
guest tokens entirely.

Format is ``<expiry>.<signature>``: an epoch second, and an HMAC of it under
EVENT_SECRET. Nothing is stored, so it survives a restart and needs no
database. Without EVENT_SECRET the whole mechanism is off, which is the right
way to fail.
"""

from __future__ import annotations

import hmac
import secrets
import time
from hashlib import sha256

from foundry.config import event_secret, guest_hours, sso_enabled

#: Query parameter carrying the token.
PARAM = "k"

#: Session-state key holding the guest's throwaway identity.
IDENTITY = "guest_identity"


def enabled() -> bool:
    """Guest links work only while we are not relying on an identity provider."""
    return bool(event_secret()) and not sso_enabled()


def _sign(expiry: int, secret: str) -> str:
    return hmac.new(secret.encode(), str(expiry).encode(), sha256).hexdigest()[:32]


def mint(hours: int | None = None) -> str:
    """A token valid for the next few hours. Empty when guest access is off."""
    secret = event_secret()
    if not secret or sso_enabled():
        return ""
    expiry = int(time.time()) + (hours or guest_hours()) * 3600
    return f"{expiry}.{_sign(expiry, secret)}"


def verify(token: str) -> bool:
    """Whether a token is well formed, correctly signed and still in date."""
    secret = event_secret()
    if not secret or sso_enabled() or not token:
        return False
    expiry_text, _, signature = token.partition(".")
    if not signature:
        return False
    try:
        expiry = int(expiry_text)
    except ValueError:
        return False
    if expiry < time.time():
        return False
    return hmac.compare_digest(signature, _sign(expiry, secret))


def new_identity() -> str:
    """A throwaway name for a guest, so their vote is theirs and countable.

    One identity per browser session, which in practice means one vote per
    phone. Reloading the page earns a new one; for a room voting live that is
    an acceptable looseness, and it is the reason guests cannot do anything
    that writes a person's name against a decision.
    """
    return f"guest-{secrets.token_hex(4)}"
