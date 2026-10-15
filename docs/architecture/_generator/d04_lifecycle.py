"""Diagram 04: catalogue and data lifecycle, write and read paths.

Run `python build.py` from this directory to regenerate every diagram.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcpkit import *
import gcpkit

OUT_DIR = os.environ.get("DIAGRAM_OUT",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diagrams"))

OUT = os.path.join(OUT_DIR, "04-catalogue-data-lifecycle.svg")
d = Diagram(1800, 900)
d.text(40, 40, "Where the agent information lives, and how it reaches the marketplace", size=20, bold=True)
d.text(40, 60, "BigQuery is the system of record. Only the backend has a data path; the frontend holds no durable copy and no credential.",
       size=12, color=GREY_S)

# ================= WRITE =================
d.group(40, 96, 1400, 400, "Write path", color=GGREEN_D, fill=GGREEN, fill_op=0.03,
        sub="Three, and only three, ways a row enters or changes in the catalogue. "
            "Every one lands in the same table and leaves the same audit record.")
for x, h in [(76, "SOURCE"), (400, "CONTROL"), (724, "WRITE"), (1030, "SYSTEM OF RECORD"), (1240, "AUDIT")]:
    d.text(x, 160, h, size=8.5, bold=True, color=GREY_S)

rows = [
    ("A", 180, "gcp/devtools/source-repositories.png", "agents.yaml in the repo", "Bulk seed and correction",
     "gcp/devtools/code.png", "Pull request review", "Two-person rule, CI validates the schema",
     "gcp/analytics/bigquery.png", "MERGE", "Idempotent on agent_id"),
    ("B", 282, "gcp/devtools/tasks.png", "Submit page", "Anyone in VP&C",
     "gcp/security/iam.png", "Governance triage", "Accept, reject or merge. Decision recorded.",
     "gcp/analytics/bigquery.png", "MERGE on accept", "Submission keeps its own lifecycle"),
    ("C", 384, "onprem/client/user.png", "Owner declaration", "Monthly: hours, users, CSAT",
     "gcp/security/certificate-authority-service.png", "Owner attestation", "The named owner asserts it. Not self-serve.",
     "gcp/analytics/bigquery.png", "MERGE metrics only", "Catalogue prose untouched"),
]
for tag, y, i1, l1, s1, i2, l2, s2, i3, l3, s3 in rows:
    d.text(62, y + 22, tag, size=12, bold=True, color=GGREEN_D)
    d.icon(140, y, i1, l1, s1, size=32, chars=20)
    d.icon(464, y, i2, l2, s2, size=32, chars=20)
    d.icon(788, y, i3, l3, s3, size=32, chars=20)
    d.line([(214, y + 16), (388, y + 16)], GGREEN_D)
    d.line([(540, y + 16), (712, y + 16)], GGREEN_D)
    d.line([(864, y + 16), (1024, y + 16)], GGREEN_D)

d.add('<rect x="1030" y="170" width="170" height="296" rx="6" fill="#FFFFFF" stroke="%s" stroke-width="1.2"/>' % GREY_B)
d.icon(1115, 196, "gcp/analytics/bigquery.png", "dim_agent", size=38, chars=18)
d.wrap(1046, 272, "One row per agent, current state. The backend runtime service account has no write "
       "grant on it; only the curation pipeline does.", 26, size=9, color=GREY_S, lh=11.5)
d.add('<rect x="1240" y="170" width="170" height="296" rx="6" fill="#FFFFFF" stroke="%s" stroke-width="1.2"/>' % GREY_B)
d.icon(1325, 196, "gcp/analytics/data-catalog.png", "fct_catalogue_change", size=36, chars=18)
d.wrap(1256, 284, "Before, after, actor, timestamp. Immutable, seven years. This is what proves "
       "the register was not quietly edited.", 26, size=9, color=GREY_S, lh=11.5)
d.line([(1204, 318), (1234, 318)], GGREEN_D)
d.text(1219, 310, "every write", size=8.5, color=GGREEN_D, anchor="middle")

# ================= READ =================
d.group(40, 530, 1400, 330, "Read path", color=GBLUE, fill=GBLUE, fill_op=0.03,
        sub="What happens on a page load, and what happens when somebody votes.")
d.text(76, 596, "RENDERING A PAGE", size=8.5, bold=True, color=GREY_S)
for cx, ic, lb, sb in [
    (150, "gcp/compute/run.png", "Frontend request", "Via the gateway, end-user bearer token"),
    (410, "gcp/compute/run.png", "Backend cache", "300s TTL, keyed per view"),
    (690, "gcp/analytics/bigquery.png", "vw_marketplace_agent", "One query, catalogue joined with live votes"),
    (960, "gcp/compute/run.png", "Response to frontend", "JSON, rendered server-side"),
]:
    d.icon(cx, 612, ic, lb, sb, size=32, chars=22)
d.line([(200, 628), (368, 628)], GBLUE)
d.line([(452, 628), (648, 628)], GBLUE)
d.line([(732, 628), (918, 628)], GBLUE)
d.text(550, 622, "miss", size=9, color=GBLUE, anchor="middle")
d.line([(410, 606), (410, 578), (960, 578), (960, 606)], GBLUE)
d.text(685, 572, "hit: no query at all", size=9, color=GBLUE, anchor="middle")

d.text(76, 724, "CASTING A VOTE", size=8.5, bold=True, color=GREY_S)
for cx, ic, lb, sb in [
    (150, "onprem/client/user.png", "User clicks vote", "Frontend posts to the gateway"),
    (410, "gcp/compute/run.png", "Backend appends fct_vote", "Storage Write API, event_id as dedupe key"),
    (690, "gcp/compute/run.png", "Invalidate that agent's cache key", "Plus an optimistic update so the user sees it at once"),
    (960, "gcp/analytics/bigquery.png", "Count is derived", "Latest action per voter wins, at read time"),
]:
    d.icon(cx, 744, ic, lb, sb, size=32, chars=22)
d.line([(200, 760), (368, 760)], GRED_D)
d.line([(452, 760), (648, 760)], GRED_D)
d.line([(732, 760), (918, 760)], GRED_D)

# ================= side notes =================
PX = 1470
d.group(PX, 96, 290, 195, "Why append-only, not update-in-place", color=GRED_D, fill=GRED, fill_op=0.04)
d.wrap(PX + 14, 140, "The application never reads a row, changes it and writes it back. A vote is an "
       "event; the count is a view over those events. Any number of Cloud Run instances can accept "
       "votes at the same moment without a lock and without losing one. It is also why the count "
       "survived moving off the single-instance pilot.", 44, size=9.5, color=GREY_T, lh=12)

d.group(PX, 315, 290, 195, "Alternative considered", color=GREY_B, fill=GREY_F, fill_op=0.6)
d.wrap(PX + 14, 359, "Rejected: Firestore for hot state with BigQuery as an analytics sink. Faster on "
       "paper, but it splits the system of record across two stores with two access models, two "
       "retention mechanisms and two lineage stories. If read latency ever binds, add a cache in "
       "front of BigQuery, not a second source of truth.", 44, size=9.5, color=GREY_T, lh=12)

d.group(PX, 534, 290, 165, "Why BigQuery is fast enough to serve a UI", color=GGREEN_D,
        fill=GGREEN, fill_op=0.04)
d.wrap(PX + 14, 580, "A few hundred catalogue rows, cached 300 seconds, so at most twelve round trips "
       "an hour per instance. Cost is immaterial and p95 render stays inside the 1.5 second budget. "
       "BI Engine is there if the budget tightens.", 44, size=9.5, color=GREY_T, lh=12)

d.save(OUT)
