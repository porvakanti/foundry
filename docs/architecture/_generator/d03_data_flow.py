"""Diagram 03: data flow and trust boundaries.

Run `python build.py` from this directory to regenerate every diagram.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcpkit import *
import gcpkit

OUT_DIR = os.environ.get("DIAGRAM_OUT",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diagrams"))

OUT = os.path.join(OUT_DIR, "03-data-flow.svg")
d = Diagram(1900, 1240)
d.text(40, 38, "Agent Marketplace - Data flow and trust boundaries", size=20, bold=True)
d.text(40, 60, "Every arrow that crosses a boundary is numbered and tabulated. Full detail in the DPIA.",
       size=11.5, color=GREY_S)

Y, H = 110, 450
def band(x, w, tag, title, sub, color):
    d.group(x, Y, w, H, "%s   %s" % (tag, title), color=color, dash="6 4", fill=color, fill_op=0.03, sub=sub)

band(40, 215, "B1", "User device", "Managed endpoint", GREY_S)
d.icon(147, Y + 76, "onprem/client/users.png", "Browser", "No marketplace data persists on the device", size=36, chars=22)

band(285, 255, "B2", "Presentation tier", "vf-grp-aib-prd-mirror", GBLUE)
d.icon(360, Y + 76, "gcp/security/iap.png", "IAP", size=32, chars=14)
d.icon(480, Y + 76, "gcp/compute/run.png", "Frontend", "Streamlit", size=32, chars=14)
d.add('<rect x="305" y="%s" width="215" height="92" rx="5" fill="%s" fill-opacity="0.06" stroke="%s" stroke-width="1.1"/>'
      % (Y + 190, GGREEN, GGREEN_D))
d.text(319, Y + 212, "No data path from here", size=9.5, bold=True, color=GGREEN_D)
d.wrap(319, Y + 230, "The frontend holds no database credential and appears on no flow that reaches the data layer.",
       30, size=8.6, color=GREY_T, lh=10.5)

band(570, 265, "B3", "Orchestration boundary", "Existing AIB, approved", GGREEN_D)
d.icon(702, Y + 76, "gcp/api/api-gateway.png", "AI Orchestration Gateway", "Bearer context forwarded", size=34, chars=20)
d.add('<rect x="590" y="%s" width="225" height="112" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>'
      % (Y + 180, GREY_B))
d.text(604, Y + 202, "Responsible AI Service", size=9.5, bold=True, color=GGREEN_D)
for i, t in enumerate(["Safety filters and guardrails", "PII and data-privacy screening",
                       "Prompt-injection defences", "Policy verification"]):
    d.text(604, Y + 220 + i * 15, "─ " + t, size=8.4, color=GREY_S)

band(855, 245, "B4", "Application tier", "vf-grp-aib-prd-scm-vpc-xx", GBLUE)
d.icon(977, Y + 76, "gcp/compute/run.png", "Backend", "The only component with a data path", size=34, chars=20)

band(1120, 330, "B5", "Data Hub", "BigQuery, CMEK, Confidential", GREY_S)
d.icon(1200, Y + 70, "gcp/analytics/bigquery.png", "BigQuery", size=36, chars=14)
d.add('<rect x="1140" y="%s" width="290" height="236" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>'
      % (Y + 150, GREY_B))
d.text(1154, Y + 172, "DOMAIN", size=8.3, bold=True, color=GREY_S)
d.text(1416, Y + 172, "PERSONAL DATA", size=8.3, bold=True, color=GREY_S, anchor="end")
for i, (t, cls, c) in enumerate([
        ("Agent catalogue", "none", GGREEN_D),
        ("Taxonomy and classifications", "none", GGREEN_D),
        ("Similarity and relationships", "none", GGREEN_D),
        ("Votes and feedback", "pseudonymous", GYELLOW),
        ("Submissions", "identified", GRED_D),
        ("Users and role mappings", "identified", GRED_D),
        ("Notifications and requests", "identified", GRED_D),
        ("Activity and audit records", "identified", GRED_D)]):
    yy = Y + 196 + i * 26
    d.text(1154, yy, t, size=9, color=GREY_T)
    d.text(1416, yy, cls, size=8.5, color=c, bold=True, anchor="end")

band(1480, 190, "B6", "Model platform", "AIB, approved", PURPLE)
d.icon(1575, Y + 76, "gcp/ml/vertex-ai.png", "LLM Proxy", "Approved enterprise models", size=32, chars=18)
d.add('<rect x="1498" y="%s" width="154" height="100" rx="5" fill="%s" fill-opacity="0.05" stroke="%s" stroke-width="1.1"/>'
      % (Y + 190, GGREEN, GGREEN_D))
d.text(1510, Y + 210, "Never crosses", size=9.2, bold=True, color=GGREEN_D)
d.wrap(1510, Y + 228, "No row from B5 reaches B6. Prompt is user text plus catalogue text.",
       22, size=8.4, color=GREY_T, lh=10.5)

band(1700, 160, "B7", "Agent platforms", "Separately approved", GYELLOW)
for i, (ic, lb) in enumerate([("saas/chat/teams.png", "Copilot Studio"),
                              ("saas/saas.png", "Emplay Zinger"),
                              ("gcp/analytics/looker.png", "Looker and Vertex AI")]):
    d.icon(1780, Y + 70 + i * 104, ic, lb, size=28, chars=18)

# flows
def f(n, pts, color, sx, sy, dash=None):
    d.line(pts, color, dash=dash)
    d.step(sx, sy, n, color=color)

f(1, [(254, Y + 92), (344, Y + 92)], GBLUE, 299, Y + 92)
f(2, [(376, Y + 92), (464, Y + 92)], GBLUE, 420, Y + 92)
f(3, [(512, Y + 92), (684, Y + 92)], GGREEN_D, 598, Y + 92)
f(4, [(720, Y + 92), (960, Y + 92)], GGREEN_D, 840, Y + 92)
d.line([(994, Y + 104), (1066, Y + 104), (1066, Y + 250), (1136, Y + 250)], GBLUE)
for _n, _y in ((5, Y + 150), (6, Y + 186), (7, Y + 222)):
    d.step(1066, _y, _n, color=GBLUE)
f(8, [(1040, Y + 60), (1040, Y - 8), (1575, Y - 8), (1575, Y + 66)], PURPLE, 1320, Y - 8, dash="6 4")
f(9, [(147, Y + 60), (147, Y - 26), (1780, Y - 26), (1780, Y + 62)], GYELLOW, 960, Y - 26)
f(10, [(1270, Y + H), (1270, Y + H + 44)], GREY_S, 1294, Y + H + 22)
d.icon(1270, Y + H + 48, "gcp/analytics/looker.png", "Evaluation Agent and Looker", "Read-only on governed views",
       size=30, chars=28)

# table
TY = 700
d.text(40, TY, "What travels on each flow", size=14, bold=True)
cols = [(40, "#"), (82, "FLOW"), (470, "DATA"), (960, "PERSONAL DATA"), (1160, "PURPOSE"), (1520, "RETENTION")]
for x, h in cols:
    d.text(x, TY + 26, h, size=8.5, bold=True, color=GREY_S)
d.add('<line x1="40" y1="%s" x2="1850" y2="%s" stroke="%s" stroke-width="1"/>' % (TY + 34, TY + 34, GREY_B))
rows = [
 ("1","Browser to IAP","Entra identity assertion","Yes: work email, display name","Authenticate the user","LB logs, 30 days"),
 ("2","IAP to Frontend","Signed JWT carrying the verified email","Yes: work email","Establish the session","Not stored"),
 ("3","Frontend to Gateway","API call with the end user's bearer token","Yes: work email in the token","Authorise per user, not per service","Not stored"),
 ("4","Gateway to Backend","Same call, after Responsible AI screening","Yes: work email in the token","Execute the domain operation","Gateway logs, per AIB policy"),
 ("5","Backend to BigQuery","Catalogue and taxonomy read on an authorised view","No","Render the marketplace","Read only"),
 ("6","Backend to BigQuery","Append a vote: agent, HMAC of email, cast or withdraw","Pseudonymous","One vote per person per agent","24 months"),
 ("7","Backend to BigQuery","Append submission, access request, notification, audit","Yes","Workflow and audit","13 to 84 months, see DPIA"),
 ("8","Backend to LLM Proxy","User's typed task plus catalogue text","Pseudonymous","AI-assisted intake and recommendation","90 days (query log)"),
 ("9","Browser to agent platform","Browser redirect. No marketplace payload travels.","No","Hand the user to the real agent","That platform's policy"),
 ("10","Analytics to BigQuery","Aggregates from the governed views","No","Scoring and portfolio reporting","Read only"),
]
for i, r in enumerate(rows):
    y = TY + 56 + i * 29
    if i % 2 == 0:
        d.add('<rect x="40" y="%s" width="1810" height="27" fill="%s"/>' % (y - 16, GREY_F))
    c = GRED_D if r[3].startswith("Yes") else (GYELLOW if r[3].startswith("Pseudo") else GGREEN_D)
    for (x, _), v in zip(cols, r):
        d.text(x, y + 3, v, size=9.6, color=c if v == r[3] else GREY_T, bold=(v == r[0]))

d.group(40, TY + 365, 890, 105, "Exclusion that bounds the assessment", color=GGREEN_D, fill=GGREEN, fill_op=0.05)
d.wrap(56, TY + 408, "No supplier record, contract, purchase order, invoice, price or spend figure is read, stored "
       "or transmitted on any path. The marketplace describes agents; it does not operate them. "
       "SAP, Ariba and Datasphere are not integrated.", 104, size=9.5, color=GREY_T, lh=12.5)
d.group(960, TY + 365, 890, 105, "Where the residual privacy risk sits", color=GYELLOW, fill=GYELLOW, fill_op=0.05)
d.wrap(976, TY + 408, "Flow 7 carries free text written by an identified person (access-request reasons, submission "
       "detail). Flow 8 is the only free text that leaves the application tier, and it is screened for PII at "
       "the gateway before it goes. Both are assessed in the DPIA.", 104, size=9.5, color=GREY_T, lh=12.5)
d.save(OUT)
