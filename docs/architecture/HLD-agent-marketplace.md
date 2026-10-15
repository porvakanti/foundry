# High Level Design: VP&C Agent Marketplace

**Submitted for:** AI Portfolio Board, Security assessment, Privacy assessment, Vodafone Group review
**Ask of the Board:** Approval to deploy into Production
**Pattern:** Reusable AIB architecture on Google Cloud
**Status:** For review
**Document owner:** Praveen Orvakanti, AI Domain, VP&C
**Service owner:** Procurement AI Operations

| Item | Value |
| --- | --- |
| Current state | Frontend and backend split, running in the AIB lab environment |
| Projects | `vf-grp-aib-prd-mirror` (web), `vf-grp-aib-prd-scm-vpc-xx` (backend, xx = lab / nl / live), `vf-grp-aib-prd-proxy` (LLM proxy, existing) |
| Entry point | `abc.vodafone.com/app` |
| Model access | Approved enterprise models via the AI Orchestration Gateway and LLM Proxy. No direct model endpoint. |
| Data classification | **Confidential** |
| Encryption | CMEK |
| Data residency | europe-west4 (**CONFIRM** against the AIB standard) |
| Environments | lab / non-live / live |
| Personal data | Vodafone employee work email, name, role and user-written free text. No customer and no supplier personal data. |

### Artefacts in this pack

| Ref | Artefact | Answers |
| --- | --- | --- |
| D1 | `diagrams/01-logical-architecture.svg` | What the capabilities are and where the domain boundaries sit |
| D2 | `diagrams/02-deployment-architecture.svg` | What is deployed, in which project, behind which control |
| D3 | `diagrams/03-data-flow.svg` | What data crosses which trust boundary, and its classification |
| D4 | `diagrams/04-catalogue-data-lifecycle.svg` | How agent information enters the catalogue and reaches the UI |
| D5 | `diagrams/05-sequence-flows.svg` | The three request sequences, end to end |
| - | `DPIA-agent-marketplace.md` | The privacy assessment |
| - | `security-control-matrix.md` | Control-by-control: inherited from AIB, or implemented by us |
| - | `api-contract.md` | The frontend-to-backend interface across the gateway |
| - | `schema/bigquery-ddl.sql` | The executable schema, with retention and purpose in the DDL |

---

## 1. Executive summary

VP&C builds AI agents in several places at once: Copilot Studio, supplier platforms such as Emplay
Zinger, Looker, and Vodafone-built services on GCP. That is a success, and it has a cost. Nobody
can see the full set, so nobody can say with confidence what is running, who owns it, what data it
reaches or what it costs.

The Agent Marketplace is the front door that makes that set visible. An employee can discover every
agent in one place, try one before committing, request access to a restricted one, and put forward
an idea or nominate a pilot to be scaled. Owners and the AI Portfolio Board get the register that
does not exist today.

**The architectural statement that bounds this entire assessment: the marketplace is a catalogue
and a front door, not a runtime.** Agents continue to execute on their own platforms under their
own approvals. No supplier record, contract, purchase order, invoice, price or spend figure is
read, stored or transmitted by this application at any point. SAP, Ariba and SAP Datasphere are
not integrated with it.

Two consequences the Board should note. First, the risk profile is materially lower than the agent
use cases previously reviewed, because the sensitive procurement data simply is not in scope.
Second, this use case is itself a governance instrument: it is the register the Board has been
asking for.

The solution follows the reusable AIB pattern. The web tier is new; the orchestration, Responsible
AI and model-serving tiers are existing approved AIB components whose controls we inherit rather
than rebuild.

---

## 2. Scope

### 2.1 In scope

A two-tier application on the AIB landing zone:

- **Presentation tier**: a Streamlit frontend on Cloud Run in `vf-grp-aib-prd-mirror`. Renders the
  UI and nothing else. It holds no database credential and opens no connection to the data layer.
- **Application tier**: the Agent Marketplace Backend on Cloud Run in
  `vf-grp-aib-prd-scm-vpc-xx`, reached only through the AI Orchestration Gateway. Nine domain
  services inside one deployable:

| Domain service | Responsibility |
| --- | --- |
| Catalogue | The inventory of agents and their lifecycle state |
| Submission and intake | Ideas, published agents and scale nominations |
| Review and approval workflow | Triage, access decisions, promotion to production |
| Search and taxonomy | Classification, filtering, the Concierge entry point |
| Portfolio and relationship | How agents relate to functions, owners and each other |
| Voting and feedback | Community signal, one vote per person per agent |
| Notification | Owner and requester notifications |
| Audit | Every state change, immutably recorded |
| AI-assisted intake and recommendation | The only capability that calls a model |

- **Persistent data**: BigQuery as the governed store, Cloud Storage for permitted attachments,
  exports and ingestion staging, Secret Manager for secrets and runtime configuration, Cloud
  Logging and Monitoring for application, security and telemetry.

### 2.2 Explicitly out of scope

| Not in scope | Where it lives instead |
| --- | --- |
| Executing agents | The agent's own platform, under its own approval |
| Proxying or storing agent conversations | The platform that served the turn |
| Any supplier, contract, PO, invoice or spend data | SAP, Ariba, Datasphere. Never read by this app. |
| Customer personal data | Not touched on any flow |
| Model training or fine-tuning | No Vodafone data is used to train or tune any model |
| Authentication | Delegated entirely to the platform. See section 5.1. |

### 2.3 Users

| Role | Capability | Enforced by |
| --- | --- | --- |
| VP&C employee | Browse, search, try unrestricted agents, vote, give feedback, submit, request access | `user_group_app` in Cloud IAM, enforced at IAP |
| Agent owner | The above, plus approve or deny access to their own agents and attest monthly metrics | `dim_user_role.app_role = 'owner'` |
| Curator | The above, plus catalogue curation and submission triage | `dim_user_role.app_role = 'curator'` |
| AI Portfolio Board | Read the register and portfolio reporting | `dim_user_role.app_role = 'board_reader'` |

---

## 3. Logical architecture (D1)

Five tiers, left to right in D1.

**Presentation tier.** Rendering and session context only. No business logic and no data access.
Every operation is dispatched to the AI Orchestration Gateway carrying the end user's own bearer
token.

**Orchestration boundary.** The existing AI Orchestration Gateway. External load balancing, Cloud
Armor, Cloud IAM, IAP, and the Responsible AI Service: safety filters and guardrails, PII and
data-privacy screening, prompt-injection defences, policy verification. These are approved AIB
controls, inherited by this use case.

**Application tier.** The nine domain services above, in one deployable with modular domain
boundaries. This is the only tier with a path to the data layer.

**Model access.** The shared LLM Router and the LLM Proxy project. Approved governed enterprise
models only; no direct Vertex AI endpoint and no model credential held by this application.

**Persistent data.** BigQuery, Cloud Storage, Secret Manager, Cloud Logging. Confidential, CMEK,
with user and market-level filtering applied through authorised views.

---

## 4. Deployment architecture (D2)

| Concern | Decision | Rationale |
| --- | --- | --- |
| Web entry | `abc.vodafone.com` into the WebApp Gateway Project, then `abc.vodafone.com/app` | The established AIB web pattern |
| Frontend | Cloud Run, Serverless NEG, ingress restricted to the load balancer | Serverless scaling, no VM estate to patch |
| Identity | Entra ID SSO over SAML into a WorkForce Pool, enforced by IAP against `user_group_app` | The AIB standard; the application never sees a credential |
| Frontend to backend | Only via the AI Orchestration Gateway, `Authorization: Bearer <end-user token>` | One governed boundary; authorisation evaluated per person, not per service account |
| Backend | Cloud Run behind an Internal LB, reached over Private Service Connect | No internet path to the backend at all |
| Data | BigQuery with CMEK, partition expiry and authorised views | One governed store; retention enforced by the platform |
| Attachments | Cloud Storage, private bucket, signed access through the backend only | Submissions can carry a document; it never becomes a public object |
| Model access | Shared LLM Router to the LLM Proxy project | Inherits Responsible AI screening and token accounting |
| Perimeter | VPC Service Controls around the backend project and the data layer | A stolen credential is unusable from outside the perimeter |
| Environments | lab / non-live / live, separated by project suffix | Established AIB separation |

**Added by this design, beyond the base AIB pattern:** the VPC Service Controls perimeter around
the backend and data layer, the authorised-view access model, partition-expiry retention, and
pseudonymisation of identity in the community-signal tables.

---

## 5. Security architecture

### 5.1 Authentication

There is none in the application, by design. Entra ID authenticates the user with SSO and MFA, the
WorkForce Pool federates that identity into Google Cloud, and IAP enforces `user_group_app` before
any application code runs. The frontend reads the verified assertion and trusts nothing else. It
has no login page, no password store and no session cookie of its own.

Three pilot-grade mechanisms were removed and must not return: a shared username and password, an
email allowlist in application config, and a signed guest token in a QR link used for an internal
event. All three are superseded by platform identity.

### 5.2 Authorisation

| Decision | Enforced by | Notes |
| --- | --- | --- |
| Can this person reach the service | Cloud IAM group `user_group_app`, at IAP | The single front gate |
| Can this call reach the backend | AI Orchestration Gateway, on the end-user bearer token | Per person, not per service account |
| Can this person see a restricted agent | Backend, from `dim_agent.is_restricted` and `vw_access_state` | Request, then owner or curator decision |
| Can this person curate or approve | `dim_user_role` | Application role, separate from service entry |
| Which market's rows are visible | `vw_marketplace_agent_scoped`, an authorised view | Row filtering in the data layer, not in application code |
| Can the runtime read a table | IAM on the backend service account, authorised views only | The backend cannot read base tables and cannot write `dim_agent` |

A compromise of the running backend therefore cannot silently rewrite the register: catalogue
change is a separate controlled path, and every change leaves an immutable `fct_activity_audit`
row.

### 5.3 Inherited versus implemented

Set out control by control in `security-control-matrix.md`. The short version: the orchestration
boundary, Responsible AI screening, model serving and the identity chain are **existing approved
AIB components**. What is new for this use case is the web tier, the backend service, the data
model and the perimeter around it. The review surface is the blue components in D2.

### 5.4 Threat model, abbreviated

| Threat | Control |
| --- | --- |
| Unauthenticated access | IAP; no application-level auth path exists to bypass |
| Frontend compromise leads to data access | The frontend holds no data credential and no data path exists from it. See D5. |
| Backend reached directly, bypassing the gateway | Internal LB plus Private Service Connect; no internet route |
| Privilege escalation to approve one's own access request | Approver is the named owner or a curator; requester and approver both recorded |
| Catalogue tampering | Runtime service account has no write grant on `dim_agent`; every change audited for seven years |
| Data exfiltration from BigQuery | VPC Service Controls, authorised views, Data Access logs |
| Prompt injection via a user query | Gateway prompt-injection defences, then the output is used only to rank catalogue entries. The model executes nothing and calls no tool. |
| Prompt injection via agent descriptions | As above, plus catalogue text arrives only through the controlled write paths |
| Sensitive content pasted into a free-text field | Gateway PII screening on anything leaving the application tier; shortest retention on the free-text tables |
| Secret leakage | Secret Manager; no keys in images; no user-managed service-account keys |

---

## 6. Data architecture (D4)

### 6.1 Where the information lives

BigQuery, in `vf-grp-aib-prd-scm-vpc-xx`, is the system of record. Eight domains: agent catalogue,
submissions, users and application role mappings, votes and feedback, activity and audit records,
notifications and requests, taxonomy and classifications, similarity and relationship outputs.

An alternative was considered and rejected: Firestore for hot state with BigQuery as an analytics
sink. It performs better on paper, but it splits the system of record across two stores with two
access models, two retention mechanisms and two lineage stories to defend. At this data volume the
single governed store wins. If read latency ever binds, the answer is a cache in front of BigQuery,
not a second source of truth.

### 6.2 How information gets in: three write paths

| Path | Who | Control | Write |
| --- | --- | --- | --- |
| **A. Seed** | Platform team | Pull request, two-person rule, CI validates the schema | `MERGE` into `dim_agent`, idempotent on `agent_id` |
| **B. Submission** | Anyone in VP&C | Appended to `fct_submission`, then curator triage | `MERGE` on acceptance only |
| **C. Attestation** | The named agent owner, monthly | Owner attests the figure; not self-serve | `MERGE`, metric columns only |

Every one writes an immutable `fct_activity_audit` row with before, after, actor and timestamp,
retained seven years.

### 6.3 How information gets out

The catalogue service reads a single authorised view, `vw_marketplace_agent_scoped`, cached in the
backend for 300 seconds. A BigQuery round trip therefore happens at most twelve times an hour per
instance. The Evaluation Agent and Looker read the same governed views directly; they never read
through the application and never see a base table.

### 6.4 Votes, and why they are append-only

The requirement is one vote per person per agent, under concurrent load, across an unknown number
of Cloud Run instances.

A vote is written as an **event**, not an update: one row appended to `fct_vote` carrying the
agent, an HMAC of the voter's work email, and the action. The count is derived at read time by
taking the latest action per voter. Writes use the BigQuery Storage Write API with the
client-generated `event_id` as the dedupe key.

Consequences, because a reviewer will ask:

- No read-modify-write, so no lock, and concurrent instances cannot lose a vote.
- "One vote per person" is a property of the view, not a constraint someone can forget.
- A user can change their mind and the history is preserved.
- The behaviour is identical at one instance and at fifty.

### 6.5 Schema

Full DDL in `schema/bigquery-ddl.sql`, with purpose and retention declared per table and per
column. Retention is set as `partition_expiration_days`, so deletion is platform behaviour rather
than a scheduled job someone has to maintain and evidence.

**One item flagged for the reviewer.** `dim_user_role` holds application roles (curator, owner,
board reader). It deliberately does **not** govern who may reach the service: that remains Cloud
IAM group membership enforced at IAP. The distinction matters, because a role table in a warehouse
must not become a second source of truth for access control.

---

## 7. Data flows and privacy (D3)

Ten numbered flows, tabulated in D3 with data, classification, purpose and retention. The full
assessment is in `DPIA-agent-marketplace.md`. Headlines:

- Personal data in scope is Vodafone employee work email, name and role, plus free text that users
  write themselves.
- Where identity is needed only to deduplicate, it is replaced by `HMAC-SHA256(lower(upn), pepper)`
  with the pepper in Secret Manager. An analyst with query access to `fct_vote` or `fct_feedback`
  cannot tell who voted or who wrote a review.
- Where a real address is functionally necessary (access requests, submissions, notifications,
  audit) it is held, and the purpose is documented per column in the DDL.
- Retention runs from 90 days (Concierge query text) to seven years (audit).
- No international transfer. Everything stays in the Vodafone Google Cloud organisation in the EU,
  including inference.

---

## 8. AI usage and Responsible AI

| Question | Answer |
| --- | --- |
| Which models | Approved governed enterprise models, served through the LLM Proxy project |
| How reached | Backend to shared LLM Router to LLM Proxy. No direct model endpoint, no model credential in this application. |
| Used for what | One capability: AI-assisted intake and recommendation. Matching a typed task to agents, and flagging probable duplicates at submission. |
| What is in the prompt | The user's task or submission text, plus name, tagline, about text and taxonomy of catalogue entries |
| What is not | Any supplier, contract, PO, invoice, price or spend data. None of it exists in this system, so none can reach a model through it. |
| Autonomy | None. The model ranks and explains. It takes no action, writes no record and calls no tool. |
| Human oversight | Output is a ranked list on a search page, or a duplicate hint to a curator. A person decides. |
| Failure mode | A poor search result or a missed duplicate. No decision the model makes affects a person, a supplier or a payment. |
| Training | No Vodafone data is used to train or fine-tune any model |
| Guardrails | Inherited from the Responsible AI Service: safety filters, PII and data-privacy screening, prompt-injection defences, policy verification |
| Fallback | Deterministic keyword and taxonomy matching if the gateway is unavailable, so search degrades rather than fails |

Under an EU AI Act screening this is a minimal-risk internal search and recommendation feature: it
does not evaluate people, does not determine access to a service for a person, and takes no
autonomous action. **CONFIRM the classification with Legal.**

One point the Board should hold us to. The marketplace publishes a monthly score that promotes one
pilot over another. That score is computed in SQL from attested metrics and votes, with published
weights, in a view anyone can read. **It is not model-generated, and it should stay that way.** The
moment a model ranks colleagues' work, the fairness conversation becomes a different one and this
document would need to come back to the Board.

---

## 9. Well-Architected review

Against the Google Cloud Architecture Framework pillars.

**Operational excellence.** Infrastructure as code, deployed by pipeline from the internal
repository; no console changes in production. Three environments. Cloud Logging, Cloud Monitoring
with SLOs and alerting, Error Reporting. Runbook for the four failure modes that matter: gateway
unavailable, backend unavailable, BigQuery unavailable, bad catalogue deploy.
*Gap:* no formal on-call rota. Proposed business-hours support by the AI Domain team. **CONFIRM
acceptable for this service tier.**

**Security, privacy and compliance.** Sections 5 and 7, plus the control matrix and the DPIA.
Principal decisions: identity delegated to the platform, one governed boundary between tiers, a
perimeter around the data, least privilege such that the runtime cannot rewrite the register,
pseudonymisation by default, retention enforced in the DDL.

**Reliability.** Both Cloud Run services are multi-zone with `min-instances = 1`. Both are
stateless, so instance loss costs nothing. Graceful degradation: if the gateway is down, search
falls back to keyword and taxonomy matching; if BigQuery is briefly unavailable, cached catalogue
reads continue to serve. BigQuery time travel gives seven days; table snapshots for the catalogue.
Proposed RPO 24 hours, RTO 4 hours. *Gap:* no cross-region DR, proposed as accepted risk given the
criticality tier. **CONFIRM against the Vodafone service tiering standard.**

**Cost optimisation.** Material costs are two Cloud Run services at `min-instances = 1`, BigQuery
storage (small) and query (bounded by the 300 second cache), Cloud Storage for attachments, and
model tokens metered at the gateway. The design choices that hold cost down are the read cache and
the decision not to run a second datastore.

**Performance optimisation.** Budget: p95 page render under 1.5 seconds, p95 Concierge response
under 3 seconds. Levers if missed: BI Engine on the dataset, a longer cache TTL, Memorystore in
front of BigQuery. None are needed at current data volume.

---

## 10. Assumptions and open items

| # | Item | Owner | Blocking? |
| --- | --- | --- | --- |
| 1 | Region europe-west4 confirmed against the AIB standard | AIB platform | Yes |
| 2 | Gateway interface, auth model and prompt-logging policy documented | AIB platform | Yes, for section 8 and the DPIA |
| 3 | Lawful basis, and the audit-table erasure exemption | Privacy | Yes, for the DPIA |
| 4 | EU AI Act classification as minimal risk | Legal | Yes |
| 5 | WebApp Gateway Project name and ownership | AIB platform | No |
| 6 | Service tier, and whether RPO 24h / RTO 4h is accepted | Service management | No |
| 7 | Business-hours support model accepted | Service management | No |
| 8 | CMEK key ring and key naming | Platform | No |
| 9 | Confirmation that `dim_user_role` is accepted as application-role only | Security | No |

**Dependencies:** backend project provisioned with the VPC-SC perimeter amended to include it;
gateway endpoint and client registration; WorkForce Pool and `user_group_app` configured; CMEK key
ring; Cloud Storage bucket with uniform bucket-level access.

---

## 11. What changed from the pilot

Stated plainly, because reviewers who saw the pilot will ask.

| Pilot | Now |
| --- | --- |
| Shared username and password in environment variables | Removed. Entra ID SSO through the WorkForce Pool and IAP. |
| Email allowlist in application config | Removed. Cloud IAM group `user_group_app`. |
| Signed guest token in a QR link, for an internal event | Removed. Not present in the production design. |
| Single Streamlit service holding all logic and data access | Frontend and backend split. The frontend has no data path. |
| Votes and requests in JSON files on local disk | Append-only tables in BigQuery |
| Seeded, illustrative agent inventory | Real VP&C agents |
| No model usage | Approved enterprise models through the gateway, for one capability |
| Public repository | Vodafone internal repository |

One item remains open and should be closed alongside approval: the credential used by the pilot
was committed to the public repository and remains in its git history. It is no longer used by
anything, but it should be formally rotated and the exposure recorded rather than left to be found.
