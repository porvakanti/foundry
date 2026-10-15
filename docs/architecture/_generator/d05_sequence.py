"""Diagram 05: request sequences.

Run `python build.py` from this directory to regenerate every diagram.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcpkit import *
import gcpkit

OUT_DIR = os.environ.get("DIAGRAM_OUT",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diagrams"))

OUT = os.path.join(OUT_DIR, "05-sequence-flows.svg")
d = Diagram(1760, 1180)
d.text(40, 38, "Agent Marketplace - Request sequences", size=20, bold=True)
d.text(40, 60, "The three flows a reviewer should trace. Note which lifelines never touch the data layer.",
       size=11.5, color=GREY_S)

LANES = [
    (120, "onprem/client/users.png", "Browser", GREY_S),
    (320, "gcp/security/iap.png", "IAP", GBLUE),
    (545, "gcp/compute/run.png", "Frontend\n(Streamlit)", GBLUE),
    (800, "gcp/api/api-gateway.png", "AI Orchestration\nGateway", GGREEN_D),
    (1055, "gcp/compute/run.png", "Backend\n(Cloud Run)", GBLUE),
    (1300, "gcp/analytics/bigquery.png", "BigQuery", GREY_S),
    (1540, "gcp/ml/vertex-ai.png", "LLM Proxy", GGREEN_D),
]
TOP, BOT = 190, 1090
for x, ic, lb, c in LANES:
    d.add('<image href="data:image/png;base64,%s" x="%s" y="96" width="30" height="30"/>'
          % (__import__("gcpkit")._b64(ic), x - 15))
    for i, part in enumerate(lb.split("\n")):
        d.text(x, 144 + i * 12, part, size=10, bold=True, anchor="middle", color=c)
    d.add('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="4 4"/>'
          % (x, TOP - 10, x, BOT, GREY_B))

X = {n.split("\n")[0]: x for x, _, n, _ in LANES}

def phase(y, h, title, sub, color):
    d.add('<rect x="48" y="%s" width="1680" height="%s" rx="6" fill="%s" fill-opacity="0.03" '
          'stroke="%s" stroke-width="1.1" stroke-dasharray="6 4"/>' % (y, h, color, color))
    d.text(62, y + 20, title, size=11.5, bold=True, color=color)
    d.text(62, y + 35, sub, size=9, color=GREY_S)

def msg(y, a, b, label, color=GREY_S, dash=None, note=None):
    x1, x2 = X[a], X[b]
    d.line([(x1, y), (x2, y)], color, dash=dash)
    mid = (x1 + x2) / 2
    d.text(mid, y - 6, label, size=9, color=color, anchor="middle")
    if note:
        d.text(mid, y + 12, note, size=8.5, color=GREY_S, anchor="middle", italic=True)

# ---------- A ----------
phase(200, 290, "A   Rendering a page", "The catalogue reaches the browser without the frontend ever opening a database connection.", GBLUE)
msg(262, "Browser", "IAP", "GET /app  with the Entra session", GBLUE)
msg(296, "IAP", "Frontend", "forward + signed JWT", GBLUE, note="identity verified before app code runs")
msg(342, "Frontend", "AI Orchestration", "GET /catalogue   Authorization: Bearer <end-user>", GGREEN_D)
msg(376, "AI Orchestration", "Backend", "forward over Private Service Connect", GGREEN_D,
    note="Responsible AI and policy verification applied at the boundary")
msg(422, "Backend", "BigQuery", "SELECT on an authorised view", GBLUE)
msg(452, "BigQuery", "Backend", "rows", GREY_S, dash="4 3")
msg(478, "Backend", "Frontend", "catalogue JSON (via the gateway)", GGREEN_D, dash="4 3")

# ---------- B ----------
phase(512, 250, "B   Casting a vote", "An append, not an update. No lock, and no lost write when several instances accept votes at once.", GRED_D)
msg(572, "Browser", "Frontend", "POST vote", GRED_D)
msg(606, "Frontend", "AI Orchestration", "POST /vote   Authorization: Bearer <end-user>", GGREEN_D)
msg(640, "AI Orchestration", "Backend", "forward", GGREEN_D)
msg(678, "Backend", "BigQuery", "append fct_vote via the Storage Write API", GRED_D,
    note="event_id is the dedupe key; the count is derived at read time")
msg(722, "Backend", "Frontend", "202 Accepted + new count", GREY_S, dash="4 3")
d.text(545, 748, "optimistic UI update, cache key invalidated", size=8.5, color=GREY_S,
       anchor="middle", italic=True)

# ---------- C ----------
phase(792, 280, "C   Concierge search", "The only flow that reaches a model. Nothing from the data layer travels with the prompt.", PURPLE)
msg(852, "Browser", "Frontend", "task description typed by the user", PURPLE)
msg(886, "Frontend", "AI Orchestration", "POST /search   Authorization: Bearer <end-user>", GGREEN_D)
msg(920, "AI Orchestration", "Backend", "forward, after PII screening and prompt-injection defence", GGREEN_D)
msg(962, "Backend", "LLM Proxy", "prompt = user task + catalogue text", PURPLE,
    note="approved governed enterprise model; no Vodafone data used for training")
msg(1006, "LLM Proxy", "Backend", "ranked agent ids and reasons", GREY_S, dash="4 3")
msg(1034, "Backend", "BigQuery", "append fct_concierge_query (metadata, 90 day retention)", GREY_S)
msg(1062, "Backend", "Frontend", "results", GREY_S, dash="4 3")

d.group(48, 1104, 1680, 62, "What the sequences prove", color=GGREEN_D, fill=GGREEN, fill_op=0.04)
d.text(64, 1148, "The Frontend lifeline and the BigQuery lifeline are never joined by an arrow in any flow. "
       "Every data and model operation crosses the AI Orchestration Gateway carrying the end user's own "
       "token, so authorisation is evaluated per person rather than per service account.",
       size=9.5, color=GREY_T)
d.save(OUT)
