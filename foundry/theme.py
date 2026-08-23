"""Vodafone visual identity for the marketplace.

One global CSS block, injected once per rerun by :func:`apply`. Everything the
components render leans on the custom properties defined here, so the
light/dark switch is a single variable swap — exactly how the HTML design spec
in ``design/`` does it.
"""

from __future__ import annotations

import base64
from functools import lru_cache

import streamlit as st

from foundry.config import LOGO_FILE

# --- Brand constants -------------------------------------------------------

RED = "#E60000"
DARK_RED = "#820000"
PURPLE = "#9C2AA0"
TEAL = "#007C92"
TURQUOISE = "#00B0CA"
ORANGE = "#EB9700"
LEMON = "#A8B400"

#: Platform → accent colour variable, matching the dot on every card.
PLATFORM_VAR = {
    "Copilot": "var(--pur)",
    "Emplay": "var(--tea)",
    "GCP": "var(--org)",
    "Looker": "var(--cyn)",
}

#: Platform → soft tint used behind the monogram tile on a card.
PLATFORM_TINT = {
    "Copilot": "var(--purSoft)",
    "Emplay": "var(--teaSoft)",
    "GCP": "var(--orgSoft)",
    "Looker": "var(--cynSoft)",
}

LIGHT = {
    "bg": "#FAF9F7", "bg2": "#FBFAF8", "bg3": "#F8F6F2",
    "hdr": "rgba(250,249,247,.92)", "card": "#FFFFFF", "panel": "#1A1A1A",
    "chip": "#F1EFEA",
    "ink": "#1A1A1A", "ink2": "#3C3A34", "ink3": "#8A8781", "ink4": "#9B9891",
    "line": "#E2DFD9", "line2": "#F0EEE9", "line3": "#ECEAE5",
    "ok": "#5B8F22", "okSoft": "#EFF6E8", "lemon": "#A8B400",
    "red": RED, "red2": "#C00000", "redSoft": "#FBEDED", "redBd": "rgba(230,0,0,.25)",
    "pur": PURPLE, "purSoft": "#F5EAF6",
    "tea": TEAL, "teaSoft": "#E8F3F5",
    "org": ORANGE, "orgSoft": "#FDF3E3",
    "cyn": TURQUOISE, "cynSoft": "#E5F7FA",
    "heroGrad": "linear-gradient(120deg,#FDEEEC 0%,#F9EFF7 45%,#EAF3F5 100%)",
    "heroBtn": "rgba(255,255,255,.7)", "heroBtnBd": "rgba(0,0,0,.1)",
    "cta1": "linear-gradient(135deg,#FFF7F7,#FDEDEC)", "cta1b": "#F4D9D7",
    "cta2": "linear-gradient(135deg,#FCF8FD,#F6ECF7)", "cta2b": "#E6D3E8",
    "cta3": "linear-gradient(135deg,#F6FBFC,#E9F4F6)", "cta3b": "#CFE4E8",
    "shadow": "0 1px 2px rgba(0,0,0,.04)",
    "shadowUp": "0 12px 28px rgba(0,0,0,.09)",
}

DARK = {
    "bg": "#141416", "bg2": "#222226", "bg3": "#26262A",
    "hdr": "rgba(21,21,23,.92)", "card": "#1E1E21", "panel": "#2E2E33",
    "chip": "#2A2A2E",
    "ink": "#F2F2F4", "ink2": "#C6C6CC", "ink3": "#9A9AA2", "ink4": "#82828A",
    "line": "#35353B", "line2": "#2C2C31", "line3": "#2A2A2E",
    "ok": "#9AD468", "okSoft": "rgba(91,143,34,.22)", "lemon": "#B9C64A",
    "red": RED, "red2": "#FF9090", "redSoft": "rgba(230,0,0,.18)", "redBd": "rgba(230,0,0,.35)",
    "pur": "#DD9BE4", "purSoft": "rgba(156,42,160,.24)",
    "tea": "#4FC3D6", "teaSoft": "rgba(0,124,146,.24)",
    "org": "#F2B24D", "orgSoft": "rgba(235,151,0,.22)",
    "cyn": "#5ED2E4", "cynSoft": "rgba(0,176,202,.22)",
    "heroGrad": "linear-gradient(120deg,#2A1518 0%,#241526 45%,#12222A 100%)",
    "heroBtn": "rgba(255,255,255,.08)", "heroBtnBd": "rgba(255,255,255,.2)",
    "cta1": "linear-gradient(135deg,#2A191B,#241417)", "cta1b": "#40292C",
    "cta2": "linear-gradient(135deg,#241A26,#1F1421)", "cta2b": "#3C2B3F",
    "cta3": "linear-gradient(135deg,#16262A,#122024)", "cta3b": "#27444A",
    "shadow": "0 1px 2px rgba(0,0,0,.3)",
    "shadowUp": "0 12px 28px rgba(0,0,0,.45)",
}


def is_dark() -> bool:
    return st.session_state.get("theme", "light") == "dark"


def toggle_theme() -> None:
    st.session_state["theme"] = "light" if is_dark() else "dark"


@lru_cache(maxsize=1)
def logo_data_uri() -> str:
    """The Vodafone roundel as a data URI so it survives CSS injection."""
    try:
        return "data:image/png;base64," + base64.b64encode(LOGO_FILE.read_bytes()).decode()
    except OSError:
        return ""


def orbit_logo(size: int = 34) -> str:
    """The orbit mark: the roundel as hub, three dots circling it."""
    uri = logo_data_uri()
    inner = int(size * 0.58)
    img = (
        f'<img src="{uri}" alt="Vodafone" style="position:absolute;left:50%;top:50%;'
        f'transform:translate(-50%,-50%);width:{inner}px;height:{inner}px">' if uri else ""
    )
    return f"""
<div style="position:relative;width:{size}px;height:{size}px;flex:none">
  <svg width="{size}" height="{size}" viewBox="0 0 64 64" class="vf-orbit">
    <circle cx="32" cy="32" r="28" fill="none" stroke="{RED}" stroke-width="2.5" opacity=".35"/>
    <circle cx="32" cy="4.5" r="4" fill="{RED}"/>
    <circle cx="56" cy="46" r="4" fill="{RED}" opacity=".65"/>
    <circle cx="8" cy="46" r="4" fill="{RED}" opacity=".4"/>
  </svg>{img}
</div>"""


def _vars(palette: dict[str, str]) -> str:
    return "\n".join(f"  --{k}: {v};" for k, v in palette.items())


def apply() -> None:
    """Inject the global stylesheet. Call once, first thing on every page."""
    palette = DARK if is_dark() else LIGHT
    st.markdown(_CSS.replace("__VARS__", _vars(palette)), unsafe_allow_html=True)


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap');

:root {
__VARS__
}

html, body, [class*="st-"], button, input, textarea, select {
  font-family: 'Figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}
.stApp { background: var(--bg); color: var(--ink); }

/* Streamlit chrome we don't want: the toolbar, the deploy button, the footer. */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
[data-testid="stAppViewBlockContainer"], .block-container {
  max-width: 1200px; padding: 12px 32px 80px !important;
}
/* Streamlit's own header is an invisible fixed overlay once emptied — without
   this it swallows clicks on the marketplace's top bar underneath it. */
[data-testid="stHeader"], .stAppHeader { background: transparent; height: 0; }
[data-testid="stHeader"], [data-testid="stHeader"] *,
.stAppHeader, .stAppHeader * { pointer-events: none !important; }
h1, h2, h3, h4 { font-family: 'Figtree', system-ui, sans-serif; color: var(--ink); }
a { color: inherit; text-decoration: none; }

@keyframes orbitSpin { to { transform: rotate(360deg); } }
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.vf-orbit { animation: orbitSpin 24s linear infinite; transform-origin: 50% 50%; }
.vf-fade { animation: fadeUp .4s ease both; }

/* --- header ------------------------------------------------------------ */
.vf-brand { display: flex; align-items: center; gap: 10px; }
.vf-brand-name { font-weight: 700; font-size: 15px; letter-spacing: -.01em; white-space: nowrap; color: var(--ink); }
.vf-avatar {
  width: 30px; height: 30px; border-radius: 99px; background: var(--tea); color: #fff;
  display: grid; place-items: center; font-size: 12px; font-weight: 700;
}

/* --- cards ------------------------------------------------------------- */
.vf-card {
  display: block; background: var(--card); border: 1px solid var(--line);
  border-radius: 16px; padding: 16px; height: 100%;
  box-shadow: var(--shadow); transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
a.vf-card:hover { transform: translateY(-2px); box-shadow: var(--shadowUp); border-color: var(--redBd); }
.vf-card-title { font-weight: 700; font-size: 15px; letter-spacing: -.01em; color: var(--ink); margin: 10px 0 4px; }
.vf-card-tag { font-size: 12.5px; line-height: 1.45; color: var(--ink3); min-height: 36px; }
.vf-mono {
  width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  font-size: 12px; font-weight: 700; letter-spacing: -.02em;
}
.vf-pulse { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--ink4); margin-top: 10px; }
.vf-pulse-dot { width: 6px; height: 6px; border-radius: 99px; background: var(--lemon); flex: none; }

/* --- badges / pills ---------------------------------------------------- */
.vf-badge {
  display: inline-flex; align-items: center; gap: 5px; font-size: 10.5px; font-weight: 600;
  letter-spacing: .02em; border-radius: 99px; padding: 3px 9px; white-space: nowrap;
}
.vf-dot { width: 6px; height: 6px; border-radius: 99px; flex: none; }
.vf-meta { font-size: 11px; color: var(--ink4); }
.vf-restricted { color: var(--red2); background: var(--redSoft); }

/* --- metric strips ----------------------------------------------------- */
.vf-metrics { display: flex; gap: 18px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--line2); }
.vf-metric-v { font-size: 15px; font-weight: 700; color: var(--ink); letter-spacing: -.02em; }
.vf-metric-k { font-size: 9.5px; letter-spacing: .06em; color: var(--ink4); font-weight: 600; }
.vf-track { height: 5px; border-radius: 99px; background: var(--line2); overflow: hidden; }
.vf-track > span { display: block; height: 100%; border-radius: 99px; background: linear-gradient(90deg, #E60000, #9C2AA0); }

/* --- section headers --------------------------------------------------- */
.vf-sec-title { font-size: 19px; font-weight: 800; letter-spacing: -.02em; color: var(--ink); margin: 0; }
.vf-sec-sub { font-size: 12.5px; color: var(--ink3); margin-top: 3px; }
.vf-seeall { font-size: 12.5px; font-weight: 600; color: var(--red); white-space: nowrap; }

/* --- panels ------------------------------------------------------------ */
.vf-panel { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px; }
.vf-panel-dark { background: var(--panel); color: #fff; border-radius: 16px; padding: 18px; }
.vf-kpi { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; }
.vf-kpi-v { font-size: 26px; font-weight: 800; letter-spacing: -.03em; }
.vf-kpi-k { font-size: 10px; letter-spacing: .07em; color: var(--ink4); font-weight: 600; margin-top: 2px; }

/* --- Streamlit widgets, dressed to match ------------------------------- */
.stButton > button, .stFormSubmitButton > button, .stLinkButton > a {
  border-radius: 10px; border: 1px solid var(--line); background: var(--card); color: var(--ink);
  font-weight: 600; font-size: 13px; transition: all .15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover { border-color: var(--redBd); color: var(--red); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: var(--red); border-color: var(--red); color: #fff;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
  background: #820000; border-color: #820000; color: #fff;
}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stChatInput"] textarea {
  background: var(--card); border-radius: 10px; color: var(--ink); font-size: 13.5px;
}
[data-baseweb="input"], [data-baseweb="textarea"] { border-color: var(--line) !important; background: var(--card) !important; }
[data-testid="stChatInput"] { background: var(--card); border-radius: 12px; border: 1px solid var(--line); }
hr, [data-testid="stDivider"] hr { border-color: var(--line2); }
[data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -.02em; }

/* Popovers are used as the bell and the avatar menu: drop the chevron so the
   trigger reads as an icon button rather than a dropdown. */
[data-testid="stPopoverButton"] [data-testid="stIconMaterial"] { display: none !important; }
[data-testid="stPopoverButton"] { min-width: 0; padding-left: 4px; padding-right: 4px; }

/* Button labels must never wrap mid-word ("Appro / ve"). */
.stButton > button p, .stFormSubmitButton > button p, [data-testid="stPopoverButton"] p {
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* Nav links in the custom top bar. */
[data-testid="stPageLink"] a { padding: 4px 6px; background: transparent !important; opacity: 1 !important; }
[data-testid="stPageLink"] a span, [data-testid="stPageLink"] a p,
[data-testid="stPageLink"] a div {
  color: var(--ink2) !important; font-size: 13.5px !important; font-weight: 600 !important;
}
[data-testid="stPageLink"] a:hover span, [data-testid="stPageLink"] a:hover p,
[data-testid="stPageLink"] a:hover div { color: var(--red) !important; }
[data-testid="stPageLink"] a[aria-current="page"] span,
[data-testid="stPageLink"] a[aria-current="page"] p,
[data-testid="stPageLink"] a[aria-current="page"] div { color: var(--ink) !important; font-weight: 700 !important; }

/* Cards: every keyed agent card container is the card frame itself. */
[class*="st-key-agentcard_"], [class*="st-key-foryou_"], [class*="st-key-cta_"],
[class*="st-key-track_"], [class*="st-key-podium_"], [class*="st-key-req_"] {
  border-radius: 16px !important; border-color: var(--line) !important;
  background: var(--card); transition: border-color .18s ease, box-shadow .18s ease;
}
[class*="st-key-agentcard_"]:hover, [class*="st-key-foryou_"]:hover {
  border-color: var(--redBd) !important; box-shadow: var(--shadowUp);
}

/* The hero action row continues the hero gradient beneath the banner. */
.st-key-hero_actions {
  background: var(--heroGrad); border-radius: 0 0 28px 28px;
  padding: 0 44px 34px !important; margin: -1px 0 0 !important;
  border: 1px solid rgba(230,0,0,.08); border-top: none;
}

/* Podium leader: the dark card IS the container. */
.st-key-podium_lead {
  background: var(--panel) !important; border-color: var(--panel) !important; color: #fff;
}
.st-key-podium_lead .vf-track { background: rgba(255,255,255,.15); }
.st-key-podium_lead .stButton > button {
  background: rgba(255,255,255,.12) !important; color: #fff !important;
  border-color: rgba(255,255,255,.28) !important;
}
.st-key-podium_lead .stButton > button:hover {
  background: rgba(255,255,255,.2) !important; color: #fff !important;
  border-color: rgba(255,255,255,.45) !important;
}
.st-key-podium_lead .stButton > button p { color: #fff !important; }

/* Selected submission track. */
.st-key-track_selected { border-color: var(--ink) !important; border-width: 2px !important; }
</style>

"""
