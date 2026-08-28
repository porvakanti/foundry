"""Stage mode: the marketplace, built for a room rather than a laptop.

The normal pages assume a screen at arm's length. In front of a few hundred
people the type is too small, the cards read as noise, and the story is buried
in a grid. This is the same data and the same numbers, rendered as a sequence
of full screens with type that scales from a phone to a stadium display.

Every size here is a clamp() against viewport width, so one layout serves the
projector, the presenter's laptop and the phones in the audience without a
breakpoint in sight.

Reached at /stage. It is registered like the agent detail page: navigable, but
deliberately absent from the top bar, so nobody lands on it by accident.
"""

from __future__ import annotations

import streamlit as st

from foundry import components as ui
from foundry import nav, scoring, stagecast, theme
from foundry.auth import require_auth
from foundry.repo import get_repo

#: How often the live scenes re-read the vote counts, in seconds.
TICK = 3


def render() -> None:
    require_auth()
    theme.apply()
    _stage_css()

    scene = _current_scene()
    _keyboard_bridge()

    with st.container(key="stage_root"):
        {
            "open": _scene_open,
            "shelf": _scene_shelf,
            "production": _scene_production,
            "race": _scene_race,
            "next": _scene_next,
            "ask": _scene_ask,
        }[scene]()

    _toolbar(scene)


# --------------------------------------------------------------------------
# navigation
# --------------------------------------------------------------------------

def _current_scene() -> str:
    scene = st.query_params.get("scene") or stagecast.SCENE_KEYS[0]
    return scene if scene in stagecast.SCENE_KEYS else stagecast.SCENE_KEYS[0]


def _goto(index: int) -> None:
    index = max(0, min(index, len(stagecast.SCENE_KEYS) - 1))
    st.query_params["scene"] = stagecast.SCENE_KEYS[index]
    st.rerun()


def _toolbar(scene: str) -> None:
    """Presenter controls. Small on purpose: the audience should not read them."""
    index = stagecast.SCENE_KEYS.index(scene)
    with st.container(key="stage_bar"):
        back, prev, dots, nxt, exit_ = st.columns([1.1, 0.9, 4, 0.9, 1.1],
                                                  vertical_alignment="center")
        with back:
            if st.button("Exit stage", key="stage_exit", use_container_width=True):
                st.query_params.clear()
                nav.goto("explore")
        with prev:
            if st.button("‹", key="stage_prev", use_container_width=True,
                         disabled=index == 0, help="Previous"):
                _goto(index - 1)
        with dots:
            marks = "".join(
                f'<span style="width:{"26px" if i == index else "9px"};height:9px;'
                f'border-radius:99px;background:{"var(--red)" if i == index else "var(--line)"};'
                f'display:inline-block;margin:0 4px;transition:width .2s ease"></span>'
                for i in range(len(stagecast.SCENE_KEYS))
            )
            st.markdown(
                f'<div style="text-align:center">{marks}'
                f'<div style="font-size:10.5px;color:var(--ink4);margin-top:6px;'
                f'letter-spacing:.06em">{index + 1} / {len(stagecast.SCENE_KEYS)} '
                f'&nbsp;·&nbsp; {ui.esc(stagecast.SCENES[index].label)}</div></div>',
                unsafe_allow_html=True,
            )
        with nxt:
            if st.button("›", key="stage_next", use_container_width=True,
                         disabled=index == len(stagecast.SCENE_KEYS) - 1, help="Next"):
                _goto(index + 1)
        with exit_:
            icon = "Lights up" if theme.is_dark() else "Lights down"
            if st.button(icon, key="stage_theme", use_container_width=True):
                theme.toggle_theme()
                st.rerun()


def _keyboard_bridge() -> None:
    """Let a presenter clicker drive the deck.

    Clickers send arrow and page keys, so they are mapped onto the toolbar
    buttons. This is a progressive enhancement running inside a component
    iframe: if the browser blocks it, the buttons still work, so the deck is
    never dependent on it.
    """
    st.components.v1.html(
        """
        <script>
        const doc = window.parent && window.parent.document;
        if (doc && !doc.__stageKeys) {
          doc.__stageKeys = true;
          const hit = (label) => {
            const buttons = doc.querySelectorAll('button');
            for (const b of buttons) {
              if (b.innerText.trim() === label && !b.disabled) { b.click(); return true; }
            }
            return false;
          };
          doc.addEventListener('keydown', (e) => {
            if (['ArrowRight','PageDown',' '].includes(e.key)) { if (hit('\\u203A')) e.preventDefault(); }
            if (['ArrowLeft','PageUp'].includes(e.key))        { if (hit('\\u2039')) e.preventDefault(); }
          });
        }
        </script>
        """,
        height=0,
    )


# --------------------------------------------------------------------------
# building blocks
# --------------------------------------------------------------------------

def _headline(kicker: str, headline: str, sub: str = "", compact: bool = False) -> None:
    """``compact`` shrinks the headline on scenes whose content is the point.

    A full-size headline plus a five-row board does not fit 1080p, and a stage
    deck that scrolls mid-sentence is worse than one with smaller type.
    """
    size = "stage-h1 compact" if compact else "stage-h1"
    st.markdown(
        f'<div class="stage-kicker">{ui.esc(kicker)}</div>'
        f'<div class="{size}">{headline}</div>'
        + (f'<div class="stage-sub">{ui.esc(sub)}</div>' if sub else ""),
        unsafe_allow_html=True,
    )


def _stat(value: str, label: str, colour: str = "var(--ink)") -> str:
    return (f'<div class="stage-stat"><div class="stage-stat-v" style="color:{colour}">'
            f'{ui.esc(value)}</div>'
            f'<div class="stage-stat-k">{ui.esc(label)}</div></div>')


# --------------------------------------------------------------------------
# scenes
# --------------------------------------------------------------------------

def _scene_open() -> None:
    agents = get_repo().list_agents()
    _headline(
        "VP&C",
        'Every VP&amp;C agent.<br><span class="stage-grad">One marketplace.</span>',
    )
    st.markdown(
        f'<div class="stage-row">'
        f'{_stat(str(len(agents)), "AGENTS")}'
        f'{_stat(str(sum(a.maturity == "scaled" for a in agents)), "IN PRODUCTION", "var(--ok)")}'
        f'{_stat(str(sum(a.maturity == "pilot" for a in agents)), "IN PILOT", "var(--pur)")}'
        f'{_stat(str(sum(a.maturity == "idea" for a in agents)), "IDEAS", "var(--org)")}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _scene_shelf() -> None:
    agents = get_repo().list_agents()
    platforms: dict[str, int] = {}
    for agent in agents:
        platforms[agent.platform] = platforms.get(agent.platform, 0) + 1

    _headline("What is on the shelf", "Built all over VP&amp;C.",
              "Production platforms, supplier tools, and the Copilot agent a colleague "
              "built last week. One shelf.")
    chips = "".join(
        f'<div class="stage-chip" style="background:{theme.PLATFORM_TINT[name]};'
        f'color:{theme.PLATFORM_VAR[name]}">'
        f'<span class="stage-chip-n">{count}</span>{ui.esc(name)}</div>'
        for name, count in sorted(platforms.items(), key=lambda kv: -kv[1])
    )
    st.markdown(f'<div class="stage-chips">{chips}</div>', unsafe_allow_html=True)


def _scene_production() -> None:
    scaled = [a for a in get_repo().list_agents() if a.maturity == "scaled"]
    _headline("Scaled and supported", "Already doing the work.", compact=True)
    cards = "".join(
        f'<div class="stage-card">'
        f'<div class="stage-card-name">{ui.esc(a.name)}</div>'
        f'<div class="stage-card-tag">{ui.esc(a.tagline)}</div>'
        f'<div class="stage-card-row">'
        f'<span><b>{ui.esc(a.metrics.get("monthly_users", "-"))}</b> users/mo</span>'
        f'<span><b>{ui.esc(a.metrics.get("tasks_per_month", "-"))}</b> tasks/mo</span>'
        f'<span><b>{ui.esc(a.metrics.get("csat", "-"))}</b> CSAT</span>'
        f'</div></div>'
        for a in scaled
    )
    st.markdown(f'<div class="stage-cards">{cards}</div>', unsafe_allow_html=True)


@st.fragment(run_every=TICK)
def _race_board() -> None:
    """Live: re-reads votes so the ranking moves while the room votes."""
    pilots = scoring.ranked_pilots(get_repo().list_agents())
    rows = "".join(
        f'<div class="stage-race {"lead" if i == 0 else ""}">'
        f'<div class="stage-rank">{i + 1}</div>'
        f'<div class="stage-race-body">'
        f'<div class="stage-race-name">{ui.esc(a.name)}'
        f'<span class="stage-race-owner">{ui.esc(a.owner)}</span></div>'
        f'<div class="stage-track"><span style="width:{a.impact_score}%"></span></div>'
        f'</div>'
        f'<div class="stage-race-score">{a.impact_score}</div>'
        f'<div class="stage-race-votes">&#9650; {a.votes}</div>'
        f'</div>'
        for i, a in enumerate(pilots)
    )
    st.markdown(f'<div class="stage-races">{rows}</div>', unsafe_allow_html=True)


def _scene_race() -> None:
    _headline("Competing to be next", "One gets promoted every month.",
              compact=True)
    _race_board()


@st.fragment(run_every=TICK)
def _idea_board() -> None:
    ideas = sorted((a for a in get_repo().list_agents() if a.maturity == "idea"),
                   key=lambda a: -a.votes)
    cards = "".join(
        f'<div class="stage-card">'
        f'<div class="stage-idea-votes">&#9650; {a.votes}</div>'
        f'<div class="stage-card-name">{ui.esc(a.name)}</div>'
        f'<div class="stage-card-tag">{ui.esc(a.tagline)}</div>'
        f'</div>'
        for a in ideas
    )
    st.markdown(f'<div class="stage-cards">{cards}</div>', unsafe_allow_html=True)


def _scene_next() -> None:
    _headline("You decide", "Vote for what gets built next.", compact=True)
    board, code = st.columns([2.6, 1], vertical_alignment="center")
    with board:
        _idea_board()
    with code:
        _qr("Open on your phone")


def _scene_ask() -> None:
    _headline("Monday morning", "Bring us one problem.",
              "If a task on your desk should be an agent, put it on the marketplace. "
              "The top idea each quarter gets built.")
    left, code = st.columns([1.6, 1], vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="stage-steps">'
            '<div><span>1</span>Open the marketplace</div>'
            '<div><span>2</span>Submit an idea, no build needed</div>'
            '<div><span>3</span>The community votes, we build the winner</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with code:
        _qr(stagecast.app_url().replace("https://", ""))


def _qr(caption: str) -> None:
    """A scannable code sits on its own white plate in both themes.

    The URL comes from scan_url, so while SSO is off it carries a guest token
    and a scan goes straight into the marketplace rather than a sign-in form.
    """
    st.markdown(
        f'<div class="stage-qr"><div class="stage-qr-plate">'
        f'{stagecast.qr_svg(stagecast.scan_url())}</div>'
        f'<div class="stage-qr-cap">{ui.esc(caption)}</div></div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# stylesheet
# --------------------------------------------------------------------------

def _stage_css() -> None:
    """Type and layout that scale from a phone to a stadium display.

    Every size is a clamp() against viewport width rather than a breakpoint,
    so the same markup fills a projector, a laptop and a phone. Flex rows wrap
    on their own, which is what stacks the stats and cards on a narrow screen.
    """
    st.markdown(_STAGE_CSS, unsafe_allow_html=True)


_STAGE_CSS = r"""
<style>
/* Stage takes the whole viewport: the app's reading-width cap and page
   padding both get out of the way. */
[data-testid="stAppViewBlockContainer"], .block-container {
  max-width: 100% !important; padding: 1.6vh 3.5vw .6vh !important;
}
[data-testid="stMainBlockContainer"] { max-width: 100% !important; }

.st-key-stage_root {
  min-height: 74vh; display: flex; flex-direction: column;
  justify-content: center; gap: clamp(10px, 1.8vh, 30px);
}

.stage-kicker {
  font-size: clamp(10px, 1.15vw, 20px); letter-spacing: .22em; font-weight: 700;
  color: var(--red); text-transform: uppercase; margin-bottom: clamp(6px, 1.2vh, 20px);
}
.stage-h1 {
  font-size: clamp(32px, 7.4vw, 130px); line-height: 1.02; font-weight: 800;
  letter-spacing: -.035em; color: var(--ink); text-wrap: balance;
}
.stage-h1.compact { font-size: clamp(24px, 3.9vw, 68px); line-height: 1.08; }
.stage-grad {
  background: linear-gradient(90deg, #E60000, #9C2AA0 55%, #00B0CA);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.stage-sub {
  font-size: clamp(13px, 1.75vw, 30px); line-height: 1.5; color: var(--ink3);
  margin-top: clamp(8px, 1.6vh, 26px); max-width: 34ch;
}

/* stat row */
.stage-row { display: flex; flex-wrap: wrap; gap: clamp(18px, 4vw, 90px); }
.stage-stat-v {
  font-size: clamp(38px, 8vw, 150px); font-weight: 800; letter-spacing: -.05em;
  line-height: 1;
}
.stage-stat-k {
  font-size: clamp(9px, .95vw, 17px); letter-spacing: .18em; font-weight: 700;
  color: var(--ink4); margin-top: clamp(2px, .6vh, 10px);
}

/* platform chips */
.stage-chips { display: flex; flex-wrap: wrap; gap: clamp(10px, 1.6vw, 26px); }
.stage-chip {
  display: flex; align-items: center; gap: clamp(8px, 1vw, 18px);
  border-radius: 999px; padding: clamp(8px, 1.3vh, 22px) clamp(16px, 2.2vw, 42px);
  font-size: clamp(13px, 1.7vw, 30px); font-weight: 700;
}
.stage-chip-n { font-size: clamp(20px, 3.2vw, 58px); font-weight: 800; letter-spacing: -.04em; }

/* cards */
.stage-cards { display: flex; flex-wrap: wrap; gap: clamp(12px, 1.6vw, 28px); }
.stage-card {
  flex: 1 1 clamp(240px, 26vw, 460px); background: var(--card);
  border: 1px solid var(--line); border-radius: clamp(12px, 1.2vw, 22px);
  padding: clamp(14px, 1.9vw, 34px);
}
.stage-card-name {
  font-size: clamp(17px, 2.4vw, 44px); font-weight: 800; letter-spacing: -.03em;
  color: var(--ink); line-height: 1.15;
}
.stage-card-tag {
  font-size: clamp(12px, 1.25vw, 22px); color: var(--ink3); line-height: 1.45;
  margin-top: clamp(4px, .8vh, 14px);
}
.stage-card-row {
  display: flex; flex-wrap: wrap; gap: clamp(10px, 1.6vw, 30px);
  margin-top: clamp(10px, 1.6vh, 26px); padding-top: clamp(8px, 1.2vh, 20px);
  border-top: 1px solid var(--line2);
  font-size: clamp(11px, 1.1vw, 20px); color: var(--ink3);
}
.stage-card-row b { color: var(--ink); font-size: clamp(15px, 1.7vw, 30px); }
.stage-idea-votes {
  font-size: clamp(20px, 2.8vw, 52px); font-weight: 800; color: var(--org);
  letter-spacing: -.03em; line-height: 1;
}

/* the race */
.stage-races { display: flex; flex-direction: column; gap: clamp(5px, .8vh, 13px); }
.stage-race {
  display: flex; align-items: center; gap: clamp(10px, 1.6vw, 30px);
  background: var(--card); border: 1px solid var(--line);
  border-radius: clamp(10px, 1vw, 18px); padding: clamp(7px, 1.05vh, 18px) clamp(12px, 1.6vw, 30px);
}
.stage-race.lead { background: var(--panel); border-color: var(--panel); color: #fff; }
.stage-race.lead .stage-race-name, .stage-race.lead .stage-race-score { color: #fff; }
.stage-race.lead .stage-race-owner { color: rgba(255,255,255,.62); }
.stage-race.lead .stage-track { background: rgba(255,255,255,.18); }
.stage-rank {
  font-size: clamp(18px, 2.6vw, 48px); font-weight: 800; letter-spacing: -.04em;
  min-width: clamp(24px, 3vw, 62px); opacity: .55;
}
.stage-race-body { flex: 1; min-width: 0; }
.stage-race-name {
  font-size: clamp(15px, 2vw, 38px); font-weight: 700; letter-spacing: -.02em;
  color: var(--ink); display: flex; align-items: baseline; gap: clamp(6px, 1vw, 18px);
  flex-wrap: wrap;
}
.stage-race-owner {
  font-size: clamp(10px, 1.05vw, 19px); font-weight: 500; color: var(--ink4);
}
.stage-track {
  height: clamp(5px, .8vh, 14px); border-radius: 999px; background: var(--line2);
  overflow: hidden; margin-top: clamp(5px, .8vh, 13px);
}
.stage-track > span {
  display: block; height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, #E60000, #9C2AA0);
  transition: width .6s cubic-bezier(.2,.8,.2,1);
}
.stage-race-score {
  font-size: clamp(20px, 2.9vw, 56px); font-weight: 800; letter-spacing: -.04em;
  color: var(--ink);
}
.stage-race-votes {
  font-size: clamp(11px, 1.2vw, 22px); color: var(--ink4); font-weight: 600;
  min-width: clamp(46px, 5vw, 96px); text-align: right;
}

/* the ask */
.stage-steps { display: flex; flex-direction: column; gap: clamp(10px, 1.8vh, 30px); }
.stage-steps > div {
  display: flex; align-items: center; gap: clamp(10px, 1.6vw, 28px);
  font-size: clamp(14px, 1.85vw, 34px); color: var(--ink2); font-weight: 500;
}
.stage-steps span {
  flex: none; display: grid; place-items: center;
  width: clamp(26px, 3.2vw, 64px); height: clamp(26px, 3.2vw, 64px);
  border-radius: 999px; background: var(--redSoft); color: var(--red);
  font-weight: 800; font-size: clamp(13px, 1.5vw, 28px);
}

/* QR */
.stage-qr { text-align: center; }
.stage-qr-plate {
  display: inline-block; background: #fff; border-radius: clamp(8px, .9vw, 16px);
  padding: clamp(6px, .7vw, 12px); line-height: 0;
  box-shadow: 0 6px 24px rgba(0,0,0,.14);
}
.stage-qr svg { width: clamp(130px, 15vw, 300px); height: auto; display: block; }
.stage-qr-cap {
  font-size: clamp(10px, 1.05vw, 19px); color: var(--ink4); margin-top: clamp(6px, 1vh, 14px);
  letter-spacing: .06em;
}

/* presenter toolbar: legible up close, invisible from row 20 */
.st-key-stage_bar {
  border-top: 1px solid var(--line3); padding-top: 10px; margin-top: 2vh; opacity: .5;
  transition: opacity .2s ease;
}
.st-key-stage_bar:hover { opacity: 1; }
.st-key-stage_bar [data-testid^="stBaseButton"] { font-size: 12px !important; }

/* the keyboard bridge iframe must never take layout space */
.st-key-stage_root + div iframe[title="st.iframe"] { height: 0 !important; display: block; }
</style>
"""
