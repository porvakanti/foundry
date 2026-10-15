"""Diagram 01: logical architecture, capabilities and domain boundaries.

Run `python build.py` from this directory to regenerate every diagram.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcpkit import *
import gcpkit

OUT_DIR = os.environ.get("DIAGRAM_OUT",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diagrams"))

OUT = os.path.join(OUT_DIR, "01-logical-architecture.svg")
d = Diagram(1800, 1120)
d.text(40, 38, "Agent Marketplace - Logical architecture", size=20, bold=True)
d.text(40, 60, "Capabilities and domain boundaries. The physical mapping is in diagram 02.", size=11.5, color=GREY_S)

# consumers
d.group(40, 96, 1720, 140, "Consumers", color=GREY_B, fill=GREY_F, fill_op=0.5)
for cx, ic, lb, sb in [
    (280, "onprem/client/users.png", "VP&C employees", "Discover, try, vote, submit, request access"),
    (720, "onprem/client/user.png", "Agent owners", "Approve access, declare monthly metrics"),
    (1160, "onprem/client/client.png", "AI Portfolio Board", "The register of what runs and who owns it"),
    (1560, "gcp/analytics/looker.png", "Reporting", "Reads the governed views, never the app"),
]:
    d.icon(cx, 128, ic, lb, sb, size=32, chars=24)

# presentation tier
d.group(40, 270, 400, 250, "Presentation tier", color=GBLUE, fill=GBLUE, fill_op=0.04,
        icon="gcp/compute/run.png", sub="Streamlit frontend, Cloud Run")
d.icon(140, 326, "gcp/devtools/service-catalog.png", "Rendering and navigation", size=30, chars=18)
d.icon(330, 326, "gcp/security/iap.png", "Session context", size=30, chars=18)
d.add('<rect x="62" y="424" width="356" height="76" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>' % GREY_B)
d.text(78, 446, "No business logic, no data access", size=10, bold=True)
d.wrap(78, 464, "Every operation is dispatched to the AI Orchestration Gateway with the end user's "
       "own bearer token.", 56, size=9, color=GREY_S, lh=11.5)

# gateway
d.group(480, 270, 300, 250, "Orchestration boundary", color=GGREEN_D, fill=GGREEN, fill_op=0.04,
        icon="gcp/api/api-gateway.png", sub="Existing AIB control point")
d.icon(630, 330, "gcp/api/api-gateway.png", "AI Orchestration Gateway", size=34, chars=22)
d.add('<rect x="500" y="414" width="260" height="88" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>' % OLD_ if False else
      '<rect x="500" y="414" width="260" height="88" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>' % GREY_B)
d.text(516, 434, "Responsible AI Service", size=10, bold=True, color=GGREEN_D)
for i, t in enumerate(["Safety filters and guardrails", "PII and data-privacy screening",
                       "Prompt-injection defences", "Policy verification"]):
    d.litem(516, 452 + i * 13, t, size=8.6, color=GREY_S)

# backend capabilities
d.group(820, 270, 560, 560, "Backend domain services", color=GBLUE, fill=GBLUE, fill_op=0.04,
        icon="gcp/compute/run.png",
        sub="One deployable, modular domain boundaries. The only tier with a data path.")
caps = [
    ("Catalogue", "The inventory of agents and their lifecycle state"),
    ("Submission and intake", "Ideas, published agents and scale nominations"),
    ("Review and approval workflow", "Triage, access decisions, promotion"),
    ("Search and taxonomy", "Classification, filtering, the Concierge entry point"),
    ("Portfolio and relationship", "How agents relate to functions, owners and each other"),
    ("Voting and feedback", "Community signal, one vote per person per agent"),
    ("Notification", "Owner and requester notifications"),
    ("Audit", "Every state change, immutable"),
    ("AI-assisted intake and recommendation", "The only capability that calls a model"),
]
for i, (n, s_) in enumerate(caps):
    y = 332 + i * 54
    d.add('<rect x="842" y="%s" width="516" height="46" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1"/>'
          % (y, GREY_B))
    d.text(858, y + 19, n, size=10.5, bold=True, color=PURPLE if i == 8 else GREY_T)
    d.text(858, y + 34, s_, size=8.8, color=GREY_S)

# model
d.group(1420, 270, 340, 250, "Model access", color=PURPLE, fill=PURPLE, fill_op=0.04,
        icon="gcp/ml/vertex-ai.png", sub="Brokered, never direct")
d.icon(1520, 330, "gcp/api/api-gateway.png", "LLM Router", "Shared AIB core", size=30, chars=16)
d.icon(1670, 330, "gcp/ml/vertex-ai.png", "LLM Proxy", "Approved models", size=30, chars=16)
d.add('<rect x="1440" y="424" width="300" height="76" rx="5" fill="%s" fill-opacity="0.05" stroke="%s" stroke-width="1.1"/>'
      % (GGREEN, GGREEN_D))
d.text(1456, 444, "Scope of model usage", size=10, bold=True, color=GGREEN_D)
d.wrap(1456, 462, "AI-assisted intake and recommendation only. Prompt = user text plus catalogue text.",
       48, size=8.8, color=GREY_T, lh=11)

# data
d.group(1420, 560, 340, 470, "Persistent data", color=GREY_B, fill="#FFFFFF",
        icon="gcp/analytics/bigquery.png", sub="BigQuery, governed. Confidential, CMEK.")
doms = ["Agent catalogue", "Submissions", "Users and application role mappings",
        "Votes and feedback", "Activity and audit records", "Notifications and requests",
        "Taxonomy and classifications", "Similarity and relationship outputs"]
for i, t in enumerate(doms):
    d.litem(1442, 616 + i * 22, t, size=9.2, color=GREY_T)
d.add('<rect x="1440" y="800" width="300" height="86" rx="5" fill="%s" fill-opacity="0.5" stroke="%s" stroke-width="1"/>'
      % (GREY_F, GREY_B))
d.text(1456, 820, "Also in the data layer", size=9.5, bold=True, color=GREY_S)
d.litem(1456, 838, "Cloud Storage: attachments, exports, staging", size=8.6)
d.litem(1456, 854, "Secret Manager: secrets and runtime config", size=8.6)
d.litem(1456, 870, "Cloud Logging: application, security, telemetry", size=8.6)
d.add('<rect x="1440" y="900" width="300" height="46" rx="5" fill="%s" fill-opacity="0.06" stroke="%s" stroke-width="1"/>'
      % (GRED, GRED_D))
d.text(1456, 920, "Retention enforced as partition expiry", size=9, bold=True, color=GRED_D)
d.text(1456, 936, "Per table. See the DPIA for the schedule.", size=8.5, color=GREY_S)

# agent platforms
d.group(40, 560, 740, 240, "Agent platforms", color=GYELLOW, fill=GYELLOW, fill_op=0.04,
        sub="Where the agents actually run. Catalogued and linked, never operated by this system.")
for i, (ic, lb, sb) in enumerate([
        ("saas/chat/teams.png", "Microsoft Copilot Studio", "Most VP&C-built agents"),
        ("saas/saas.png", "Emplay Zinger", "Supplier platform"),
        ("gcp/ml/vertex-ai.png", "Vertex AI applications", "Vodafone-built"),
        ("gcp/analytics/looker.png", "Looker", "Spend and analytics")]):
    d.icon(150 + i * 180, 620, ic, lb, sb, size=30, chars=18)

# exclusion
d.group(40, 840, 740, 190, "Not connected, on any path", color=GGREEN_D, fill=GGREEN, fill_op=0.04)
d.wrap(62, 886, "SAP, Ariba, SAP Datasphere, contract stores and spend systems are not integrated with this "
       "application. No supplier record, contract, purchase order, invoice, price or spend figure is read, "
       "stored or transmitted by it at any point. The marketplace describes agents; it does not operate them. "
       "This exclusion is what bounds the data classification and the privacy assessment.",
       110, size=9.5, color=GREY_T, lh=13)

# flows
d.line([(240, 236), (240, 264)], GBLUE, bidir=True)
d.line([(444, 390), (474, 390)], GGREEN_D, bidir=True)
d.line([(784, 390), (814, 390)], GGREEN_D, bidir=True)
d.line([(1384, 360), (1414, 350)], PURPLE, dash="6 4")
d.line([(1384, 700), (1414, 700)], GBLUE, bidir=True)
d.line([(1160, 830), (1160, 1030), (790, 1030)], GYELLOW, dash="5 3", arrow=False)
d.text(900, 1024, "deep link and brokered trial turn", size=9, color="#9A7B00")
d.tag(248, 242, "HTTPS, identity at the edge", color=GREY_S)
d.tag(1218, 676, "governed read / write", color=GBLUE)
d.save(OUT)
