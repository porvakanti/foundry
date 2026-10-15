"""Diagram 02: deployment architecture on Google Cloud, AIB pattern.

Run `python build.py` from this directory to regenerate every diagram.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcpkit import *
import gcpkit

OUT_DIR = os.environ.get("DIAGRAM_OUT",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diagrams"))

OUT = os.path.join(OUT_DIR, "02-deployment-architecture.svg")
d = Diagram(2120, 1400)
NEW, OLD = GBLUE, GGREEN_D

d.text(40, 38, "GOOGLE CLOUD PLATFORM & AIB REFERENCE ARCHITECTURE", size=11, bold=True, color=GREY_S)
d.text(40, 64, "Agent Marketplace - Deployment architecture", size=20, bold=True)
d.text(40, 84, "Reusable AIB pattern. Frontend and backend are separate services; the frontend holds no data access.",
       size=11, color=GREY_S)

# review-surface legend
d.group(1660, 24, 430, 70, "Review surface", color=GREY_B, fill=GREY_F, fill_op=0.6)
d.add('<rect x="1676" y="58" width="13" height="13" rx="3" fill="%s" fill-opacity="0.12" stroke="%s" stroke-width="1.4"/>' % (NEW, NEW))
d.text(1696, 69, "New for this use case", size=9.5, color=GREY_T)
d.add('<rect x="1856" y="58" width="13" height="13" rx="3" fill="%s" fill-opacity="0.12" stroke="%s" stroke-width="1.4"/>' % (OLD, OLD))
d.text(1876, 69, "Existing, already approved AIB", size=9.5, color=GREY_T)

# ---------------- identity, outside ----------------
d.group(40, 150, 250, 430, "Vodafone identity", color=GREY_B, dash="5 4", fill=GREY_F, fill_op=0.5,
        sub="Existing estate")
d.icon(165, 200, "onprem/client/users.png", "Users", "Vodafone internal", size=38, chars=18)
d.icon(165, 330, "azure/identity/azure-active-directory.png", "Microsoft Entra ID", "SSO, SAML, MFA", size=36, chars=18)
d.icon(165, 450, "gcp/security/iam.png", "WorkForce Pool", "Federation into Google Cloud", size=34, chars=18)
d.line([(165, 262), (165, 322)], GREY_S)
d.line([(165, 396), (165, 442)], GREY_S)

# ---------------- Google Cloud ----------------
d.cloud(320, 120, 1770, 1130, "Google Cloud",
        "Vodafone organisation  |  environment separation: lab / non-live / live  |  no public IP on any data service")

# ============ WEB LAYER ============
d.group(350, 190, 540, 1000, "Web Layer", color=GRED_D, dash="7 4", fill=GRED, fill_op=0.02,
        sub="New for this use case")

d.group(372, 250, 496, 160, "WebApp Gateway Project", color=NEW, fill=NEW, fill_op=0.04)
d.add('<rect x="392" y="296" width="200" height="30" rx="4" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>' % GREY_B)
d.text(492, 316, "abc.vodafone.com", size=10.5, anchor="middle")
d.icon(730, 288, "gcp/network/load-balancing.png", "External Load Balancing", size=34, chars=20)
d.line([(596, 311), (700, 311)], NEW)

d.group(372, 440, 496, 730, "Use Case - WebApp Project", color=NEW, fill=NEW, fill_op=0.04,
        sub="vf-grp-aib-prd-mirror")
d.add('<rect x="392" y="496" width="210" height="30" rx="4" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>' % GREY_B)
d.text(497, 516, "abc.vodafone.com/app", size=10.5, anchor="middle")
d.icon(455, 560, "gcp/network/armor.png", "Cloud Armor", "WAF, rate limit", size=32, chars=16)
d.icon(455, 672, "gcp/security/iam.png", "Cloud IAM", "user_group_app", size=32, chars=16)
d.icon(455, 784, "gcp/security/iap.png", "Identity-Aware Proxy", "Identity before app code", size=32, chars=18)
d.group(600, 548, 252, 320, "Serverless NEG", color=NEW, fill="#FFFFFF", sub="WebApp")
d.icon(726, 600, "gcp/compute/run.png", "Agent Marketplace frontend", "Cloud Run, Streamlit", size=38, chars=20)
d.add('<rect x="618" y="712" width="216" height="140" rx="5" fill="%s" fill-opacity="0.5" stroke="%s" stroke-width="1"/>'
      % (GREY_F, GREY_B))
d.text(634, 734, "Presentation layer only", size=10, bold=True)
d.wrap(634, 752, "Renders the UI and dispatches to the AI Orchestration Gateway. "
       "Holds no database credential and opens no connection to BigQuery.", 30, size=9, color=GREY_S, lh=11)
d.line([(455, 606), (455, 664)], NEW)
d.line([(455, 718), (455, 776)], NEW)
d.line([(497, 530), (497, 552)], NEW)
d.line([(500, 800), (690, 640)], NEW)

# boundary-call contract
d.group(900, 400, 190, 150, "AIB Gateway boundary call", color=GREY_B, fill="#FFFFFF", tsize=9.5)
d.text(914, 440, "End-user (IAP) context", size=9, bold=True, color=GREY_S)
d.add('<rect x="914" y="450" width="162" height="26" rx="3" fill="%s"/>' % GREY_F)
d.text(922, 467, "Authorization: Bearer", size=9, color=GBLUE_D)
d.wrap(914, 496, "The caller's own identity is forwarded. The backend authorises per user, not per service account.",
       28, size=8.5, color=GREY_S, lh=10.5)

# ============ AIB LAYER ============
d.group(1110, 190, 950, 1000, "Existing AIB Layer", color=GRED_D, dash="7 4", fill=GRED, fill_op=0.02,
        sub="Already approved. Inherited controls, not re-reviewed here.")

d.group(1132, 250, 600, 200, "AI Orchestration Gateway", color=OLD, fill=OLD, fill_op=0.04)
for cx, ic, lb in [(1200, "gcp/network/load-balancing.png", "External LB"),
                   (1310, "gcp/network/armor.png", "Cloud Armor"),
                   (1420, "gcp/security/iam.png", "Cloud IAM"),
                   (1540, "gcp/security/iap.png", "Identity-Aware Proxy")]:
    d.icon(cx, 296, ic, lb, size=30, chars=14)
d.add('<rect x="1152" y="376" width="560" height="56" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1.1"/>' % OLD)
d.text(1166, 396, "Responsible AI Service", size=10.5, bold=True, color=OLD)
d.text(1166, 414, "Safety filters and guardrails  |  PII and data-privacy screening  |  "
                  "prompt-injection defences  |  policy verification", size=8.5, color=GREY_S)

d.group(1752, 250, 288, 200, "LLM Proxy Project", color=OLD, fill=OLD, fill_op=0.04,
        sub="vf-grp-aib-prd-proxy")
d.icon(1896, 306, "gcp/ml/vertex-ai.png", "LLM Proxy Endpoint", "Approved governed enterprise models", size=36, chars=22)

# VPC-SC perimeter around backend + data
d.group(1132, 482, 908, 688, "VPC Service Controls perimeter", color=GRED_D, dash="7 4",
        fill=GRED, fill_op=0.025, icon="gcp/security/access-context-manager.png",
        sub="Added by this design. BigQuery, Cloud Storage and Secret Manager are unreachable from outside it.")

d.group(1154, 548, 864, 300, "Backend Project - AIB GCP Projects", color=NEW, fill=NEW, fill_op=0.04,
        sub="vf-grp-aib-prd-scm-vpc-xx     xx = lab / nl / live")
d.icon(1216, 606, "gcp/network/private-service-connect.png", "Private Service Connect", size=30, chars=16)
d.icon(1216, 740, "gcp/network/load-balancing.png", "Internal LB", size=28, chars=14)
d.add('<rect x="1310" y="596" width="430" height="236" rx="5" fill="#FFFFFF" stroke="%s" stroke-width="1.3"/>' % NEW)
d.text(1326, 618, "Agent Marketplace Backend", size=11, bold=True)
d.text(1326, 633, "Cloud Run service  |  modular domain boundaries in one deployable", size=8.5, color=GREY_S)
caps = ["Catalogue service", "Submission and intake service", "Review and approval workflow",
        "Search and taxonomy service", "Portfolio and relationship service", "Voting and feedback service",
        "Notification service", "Audit service", "AI-assisted intake and recommendation"]
for i, c in enumerate(caps):
    col, row = i // 5, i % 5
    d.litem(1332 + col * 214, 660 + row * 19, c, size=8.8, color=GREY_T)
d.icon(1880, 648, "gcp/api/api-gateway.png", "Proxy Service / LLM Router", "Shared AIB core", size=32, chars=18)
d.line([(1248, 636), (1248, 730)], NEW)
d.line([(1248, 770), (1300, 770), (1300, 714)], NEW)
d.line([(1744, 700), (1840, 690)], OLD)

d.group(1154, 876, 864, 272, "Persistent Data Layer", color=NEW, fill="#FFFFFF")
d.icon(1236, 924, "gcp/analytics/bigquery.png", "BigQuery", "Governed persistent store", size=38, chars=20)
d.add('<rect x="1316" y="912" width="368" height="166" rx="5" fill="%s" fill-opacity="0.6" stroke="%s" stroke-width="1"/>'
      % (GREY_F, GREY_B))
doms = ["Agent catalogue", "Submissions", "Users and application role mappings",
        "Votes and feedback", "Activity and audit records", "Notifications and requests",
        "Taxonomy and classifications", "Similarity and relationship outputs"]
for i, t in enumerate(doms):
    d.litem(1330, 932 + i * 18, t, size=8.8, color=GREY_T)
d.add('<rect x="1316" y="1086" width="368" height="40" rx="4" fill="%s" fill-opacity="0.07" stroke="%s" stroke-width="1"/>'
      % (GRED, GRED_D))
d.text(1328, 1102, "Confidential  |  CMEK  |  user and market-level filtering", size=9, bold=True, color=GRED_D)
d.text(1328, 1117, "Retention enforced as partition expiry per table. See the DPIA.", size=8.5, color=GREY_S)
for cx, ic, lb, sb in [(1780, "gcp/storage/storage.png", "Cloud Storage", "Attachments, exports, ingestion staging"),
                       (1930, "gcp/security/secret-manager.png", "Secret Manager", "Secrets and runtime config")]:
    d.icon(cx, 912, ic, lb, sb, size=30, chars=18)
d.icon(1855, 1030, "gcp/operations/logging.png", "Cloud Logging and Monitoring",
       "Application, security and telemetry", size=30, chars=26)

# ---------------- flows ----------------
d.line([(290, 200), (330, 200), (330, 311), (386, 311)], NEW)
d.line([(290, 466), (330, 466), (330, 800), (423, 800)], NEW, dash="5 3")
d.line([(730, 330), (730, 380), (497, 380), (497, 490)], NEW)
d.line([(762, 620), (1100, 620), (1100, 330), (1176, 330)], NEW)
d.line([(1436, 440), (1436, 470), (1216, 470), (1216, 600)], OLD)
d.line([(1712, 404), (1752, 350)], OLD)
d.line([(1896, 352), (1896, 420), (1980, 420), (1980, 630), (1922, 640)], OLD, dash="6 4")
d.line([(1524, 836), (1524, 900)], NEW)

for n, x, y, c in [(1, 310, 200, NEW), (2, 330, 650, NEW), (3, 620, 380, NEW), (4, 600, 660, NEW),
                   (5, 1000, 620, NEW), (6, 1216, 540, OLD), (7, 1524, 868, NEW), (8, 1980, 520, OLD)]:
    d.step(x, y, n, color=c)

d.text(1538, 872, "governed read / write", size=9, color=NEW)
d.text(1060, 612, "approved path", size=9, color=NEW, anchor="middle")

# ---------------- numbered path strip ----------------
d.group(40, 1272, 2050, 110, "Request path", color=GREY_B, fill=GREY_F, fill_op=0.5)
narr = [
    "User opens abc.vodafone.com. Entra ID authenticates with SSO and MFA.",
    "The WorkForce Pool federates that identity into Google Cloud; IAP enforces user_group_app.",
    "Cloud Armor, then the external load balancer, then the Serverless NEG. No other route in.",
    "The Streamlit frontend renders. It has no database credential and opens no connection to BigQuery.",
    "Every data or model operation is a call to the AI Orchestration Gateway carrying the end-user bearer token.",
    "The gateway applies Responsible AI controls, then reaches the backend over Private Service Connect.",
    "The backend is the only component with a governed read/write path to the data layer.",
    "Model calls route through the shared LLM Router to the approved enterprise models in the proxy project.",
]
for i, t in enumerate(narr):
    col, row = i // 4, i % 4
    x, y = 64 + col * 1020, 1306 + row * 19
    d.step(x, y - 4, i + 1, color=NEW if i + 1 not in (6, 8) else OLD, r=7.5)
    d.text(x + 14, y, t, size=9, color=GREY_T)

d.save(OUT)
