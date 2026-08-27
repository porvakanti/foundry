# CLAUDE.md - Foundry: VP&C Agent Marketplace

## What this is
Build a working pilot of the **Agent Marketplace** for Vodafone Procurement & Connectivity (VP&C): a one-stop shop where employees discover, try and scale AI agents built across the org (Copilot Studio agents, third-party supplier agents like Emplay, and production tools on GCP/Looker).

A fully interactive HTML prototype is the **binding design spec**: `design/agent-marketplace-standalone.html` (open in any browser; light/dark theme toggle included). Screenshots of the five key screens are in `design/screenshots/`. Match its layout, copy, information architecture and interaction patterns as closely as Streamlit allows. Where Streamlit can't match it, prefer its native idioms over hacks - fidelity of FLOW beats fidelity of pixels.

## Tech stack
- **Python 3.11+, Streamlit** (multipage app via `st.Page` / `st.navigation`)
- Data layer: repository pattern with a `JSONFileRepo` default (seed data in `data/agents.json`) and **stub adapters** (interfaces only, `NotImplementedError` bodies with docstrings) for: GCP (BigQuery/Firestore), SAP, SAP Datasphere, Azure PostgreSQL. One module per store under `foundry/datastores/`.
- No other heavy dependencies. Charts: Streamlit natives. State: `st.session_state`.

## Visual identity
- Vodafone palette: red `#E60000` (primary accent), dark red `#820000`, purple `#9C2AA0`, teal `#007C92`, turquoise `#00B0CA`, fresh orange `#EB9700`, lemon `#A8B400`. Canvas warm off-white `#FAF9F7`, ink `#1A1A1A`, borders `#E2DFD9`.
- Font: Figtree (Google Fonts) via CSS injection; fall back to system sans.
- Logo: orbit mark - Vodafone roundel as hub, 3 dots orbiting (see prototype header). Asset: `design/assets/vf_logo.png`.
- Inject one global CSS block (st.markdown unsafe_allow_html) for cards, pills, chips. Keep it in `foundry/theme.py`.

## Authentication (pilot-grade, deliberately simple)
1. Login page: single shared username + password, compared against `AUTH_USER` / `AUTH_PASS` env vars (secrets.toml locally). One combination for all reviewers.
2. After password passes: ask for the user's Vodafone email; validate format AND domain `@vodafone.com` (case-insensitive). **No email is sent** - domain check is the gate.
3. Store `{email, authenticated: True}` in `st.session_state`; derive display initials from the email. Log logins to a local CSV for review stats.
4. Every page starts with a `require_auth()` guard that redirects to login.
This is NOT production auth - put a comment saying Phase 2 replaces it with Entra ID SSO.

## Data model (`data/agents.json` - seed with exactly this inventory)
Agent fields: `id, name, tagline, about, maturity(scaled|pilot|idea), platform(Copilot|Emplay|GCP|Looker), function(Sourcing|Contracts|P2P|Supplier Mgmt|Analytics|Governance), locked(bool), audience, owner, owner_role, how(list of 3 steps), sample_prompts(list), canned_reply, metrics{...per maturity}, pulse, reviews(list of {who, role, stars, text}), rating_avg, rating_count, votes, impact_score`.

Seed agents (copy content from the prototype):
- **Scaled:** Sourcing Copilot (Emplay), Contract IQ (GCP, locked), Spend Lens (Looker)
- **Pilots (Copilot):** PO Chaser (#1, score 86), Negotiation Prep (locked, 79), Onboarding Buddy (71), Savings Tracker (64), Minute Maker (55)
- **Ideas:** Tail-Spend Triage, ESG Compliance Scout, Invoice Dispute Resolver

## Pages (mirror the prototype)
1. **Explore (home)** - header w/ logo + search; hero "Every VP&C agent. One marketplace."; 3 slim CTA cards (Submit an idea / Publish your Copilot agent / Nominate to scale); winner ticker (Aug winner: PO Chaser, next review 12 Sep) linking to Leaderboard; **For you** row (hardcode role P2P Operations, reason per pick); three bands (Scaled & deployed / Copilot pilots / New ideas) as horizontal card rows with "See all →". Cards show per-maturity metrics: scaled = users/tasks/CSAT; pilots = impact bar + rank + upvote button; ideas = upvote. Each card shows a live-pulse line (e.g. "31 POs chased this week").
2. **The Library** - full inventory; tabs All/Scaled/Pilots/Ideas; filter chips by function and platform; unified cards.
3. **Agent detail** - badges (platform, maturity, function, Restricted); About / How it works (3 numbered steps) / Try asking (clickable sample prompts); **Playground**: chat UI returning the agent's `canned_reply` after a short delay (stub for real platform APIs - one adapter interface per platform in `foundry/playgrounds/`); owner card; metrics panel per maturity; reviews with stars. If `locked` and user lacks access: lock panel naming the owner + "Request access" flow (reason → confirmation; writes to a requests CSV/JSON).
4. **Leaderboard** - "Scored by the Evaluation Agent" banner; 4 criteria cards (Impact 40%, Adoption 30%, Satisfaction 20%, Community 10%); top-3 podium (#1 dark card, LEADING badge); full ranked table (impact bar, hrs/mo, users, votes, trend); past-winners strip (Aug PO Chaser, Jul Spend Lens, Jun Contract IQ).
5. **Submit** - 3 track selector (idea / Copilot agent / scale nomination), distinct form fields per track (see prototype), success state; sidebar: "What happens next" (4 steps) + scoring weights. Persist submissions to JSON/CSV.
6. **Governance (admin)** - KPI row (pending requests, agents governed, role-restricted, avg approval 0.8d); pending access-request queue with Approve/Deny; access-policy table (agent, audience, OPEN/RESTRICTED).

## Concierge search
Header search matches task descriptions to agents by keyword overlap against name+tagline+about+function; show top 3 with a "matches …" reason and Restricted flags. Stub `foundry/concierge.py` with a `match(query) -> list[Match]` function; leave a TODO to swap in an LLM call in Phase 3.

## Gamification rules (tiered by maturity)
- Scaled: adoption metrics only (no competition).
- Pilots: impact score = 0.4*impact + 0.3*adoption + 0.2*csat + 0.1*votes (normalize each 0-100); monthly review promotes the winner.
- Ideas: upvotes only; top ideas quarterly get a build sprint.
Votes: one per user (keyed by session email) per agent, stored in JSON.

## Repo layout
```
foundry/
  app.py                  # st.navigation entrypoint + auth guard
  foundry/
    auth.py  theme.py  concierge.py
    repo.py               # AgentRepo protocol + JSONFileRepo
    datastores/           # gcp.py sap.py datasphere.py azure_pg.py (stubs)
    playgrounds/          # copilot.py emplay.py gcp.py looker.py (stubs)
    pages/                # explore.py library.py agent.py leaderboard.py submit.py governance.py
  data/agents.json  data/requests.json  data/submissions.json  data/votes.json
  design/                 # the HTML spec + screenshots + logo (do not edit)
  .streamlit/secrets.toml.example
  requirements.txt  README.md
```

## Definition of done
- `streamlit run app.py` works locally with only `pip install -r requirements.txt`.
- Login gate works with env-var credentials; wrong domain rejected with a friendly message.
- All 6 pages navigable; playground chat, voting, request-access, submit and approve/deny flows all persist and survive a rerun.
- Every datastore/playground stub has a typed interface and docstring explaining what Phase 2 connects.
- README covers local run + Streamlit Community Cloud / internal server deploy, and lists the env vars.
