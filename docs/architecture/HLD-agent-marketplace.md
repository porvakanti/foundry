# High Level Design: VP&C Agent Marketplace

**Submitted for:** AI Portfolio Board review, and Security and Privacy assessment
**Ask:** Approval to deploy into Production
**Target platform:** Google Cloud, AI Booster landing zone
**Status:** Draft for review
**Owner:** Praveen Orvakanti, AI Domain, VP&C

| Item | Value |
| --- | --- |
| Current state | Deployed and running in the AI Booster lab environment on GCP |
| Model usage | Gemini, reached only through the Vodafone-hosted AIB gateway |
| Source | Vodafone internal repository |
| Data classification sought | **CONFIRM** - proposed Vodafone Internal |
| Data residency | **CONFIRM** - proposed europe-west4, matching Data Hub |
| Personal data in scope | Vodafone employee work email, name and role. No customer and no supplier personal data. |

### Companion diagrams

| Ref | Diagram | What it answers |
| --- | --- | --- |
| D1 | `diagrams/01-logical-architecture.svg` | What the capabilities are and how they relate |
| D2 | `diagrams/02-deployment-architecture.svg` | What is actually deployed, in which project, behind which control |
| D3 | `diagrams/03-data-flow.svg` | What data moves where, and which trust boundaries it crosses |
| D4 | `diagrams/04-catalogue-data-lifecycle.svg` | Where the agent information lives and how it reaches the UI |
| - | `schema/bigquery-ddl.sql` | The executable schema, with retention and classification in the DDL |

Diagrams use the official Google Cloud product icon set and follow Google's architecture
diagramming conventions: containment carries meaning (organisation, service perimeter,
project), services are icons rather than boxes, and numbered steps match the request-path
narrative beside each figure. Source SVGs are editable; 2x PNG exports sit beside them.

---

## 1. Executive summary

VP&C now builds AI agents in several places at once: Copilot Studio, supplier platforms such as
Emplay Zinger, Looker, and Vodafone-built services on GCP. That is a success, and it has a cost.
Nobody can see the full set, which means nobody can say with confidence what is running, who owns
it, what data it reaches, or what it costs.

The Agent Marketplace is the front door that makes that set visible. An employee can discover
every agent in one place, try one before committing to it, request access to a restricted one,
and put forward an idea or nominate a pilot to be scaled. Owners and the AI Portfolio Board get
the register that today does not exist.

**The architectural point that bounds this entire assessment: the marketplace is a catalogue and
a front door, not a runtime.** Agents continue to execute on their own platforms under their own
approvals. The marketplace describes them, links to them, scores them and governs access to them.
No supplier record, contract, purchase order, invoice, price or spend figure is read, stored or
transmitted by this application at any point.

That boundary is why the risk profile here is materially lower than for the agent use cases that
have come to this board previously, and it is the first thing a reviewer should test.

---

## 2. Scope

### 2.1 In scope

- A Streamlit application on Cloud Run presenting six functions: Explore, Library, Agent detail,
  Leaderboard, Submit, Governance.
- A curated catalogue of VP&C AI agents held in Data Hub (BigQuery).
- Community signals: votes, submissions, access requests, all persisted to Data Hub.
- A Concierge search that matches a free-text task description to agents, using Gemini through the
  AIB gateway.
- A monthly scoring model (Impact 40, Adoption 30, Satisfaction 20, Community 10) computed in SQL
  over the governed views.
- Access-request workflow for restricted agents: request, owner or admin decision, audit record.

### 2.2 Explicitly out of scope

| Not in scope | Where it lives instead |
| --- | --- |
| Executing agents | The agent's own platform, under its own approval |
| Proxying or storing agent conversations | The platform that served the turn |
| Any supplier, contract, PO, invoice or spend data | SAP, Ariba, Datasphere. Never read by this app. |
| Customer personal data | Not touched in any flow |
| Model training or fine-tuning | No Vodafone data is used for training |
| Authentication | Delegated entirely to the platform; see section 5.1 |

### 2.3 Users

| Role | Population | Capability |
| --- | --- | --- |
| VP&C employee | All of VP&C | Browse, search, try unrestricted agents, vote, submit, request access |
| Agent owner | Named per agent | The above, plus approve or deny access to their agent and declare monthly metrics |
| Marketplace admin | Small named group | The above, plus catalogue curation and the governance queue |
| AI Portfolio Board | Board members | Read the register and the portfolio reporting |

---

## 3. Logical architecture (D1)

Five layers, reading left to right in D1.

**Agent platforms.** Where agents actually run. Unchanged by this project. The marketplace holds a
deep link and, where the platform supports it, brokers a single trial turn.

**Catalogue inputs.** Three, and only three, ways an agent enters the catalogue: a versioned seed
file merged by pull request, a user submission through the Submit page, or an owner's monthly
declaration of metrics. Section 6.2 covers each.

**Data Hub.** BigQuery. The single system of record and the single governed boundary. Curated state
in `dim_agent`; everything a user does is an append-only event; everything the application and the
Evaluation Agent read is a view.

**Application.** Python and Streamlit on Cloud Run. Stateless by construction: no durable state on
the instance, so an instance can be destroyed at any moment without loss. This is a deliberate
change from the pilot, which kept votes in a file on local disk and would have fragmented the
count the first time the service scaled past one instance.

**Consumers.** Browsers over HTTPS, plus the Evaluation Agent and Looker reading the governed views
directly rather than scraping the application.

---

## 4. Deployment architecture (D2)

| Concern | Decision | Rationale |
| --- | --- | --- |
| Compute | Cloud Run, `min-instances = 1`, ingress restricted to the load balancer | Serverless scaling with no cold start on the first visitor of the day; no VM estate to patch |
| Ingress | External HTTPS LB, Cloud Armor, Identity-Aware Proxy, Serverless NEG | One path in, with WAF and identity enforced before application code runs |
| Identity | Microsoft Entra ID over SAML into a Workforce Identity Pool, enforced by IAP | Matches the AIB pattern already used by the Emplay solution. **CONFIRM** this is the AIB standard. |
| Data | BigQuery in the Data Hub project, CMEK, partitioned with expiry | One governed store; retention enforced by the platform, not by a job |
| Model access | Private Service Connect to the AIB AI Gateway, which fronts Gemini | The application holds no model credential and reaches no model endpoint directly |
| Perimeter | VPC Service Controls around BigQuery, Secret Manager, Artifact Registry, Logging | A stolen service-account token is useless from outside the perimeter |
| Secrets | Secret Manager: HMAC pepper and the gateway credential. No user-managed service-account keys. | Nothing secret in the image, the repo or an environment variable at build time |
| Images | Artifact Registry, built by Cloud Build from the internal repository | Provenance for every deployed artefact |

The web tier and the data and AI tiers are separated, mirroring the constraint called out on the
Emplay deployment diagram. The application reaches BigQuery only through its own service account
over Private Google Access, and reaches the model only through the PSC endpoint.

---

## 5. Security architecture

### 5.1 Authentication

There is none in the application, by design. IAP terminates the identity check at the edge and
passes a signed assertion; the application verifies the JWT signature and audience and reads the
email claim. It therefore has no login page, no password store, no session cookie of its own and
no credential to leak.

Three controls that existed in the pilot have been removed and must not return: the shared
username and password, the email allowlist, and the signed guest token in a QR link used for the
All Hands event. All three were pilot-grade and are superseded by platform identity.

### 5.2 Authorisation

| Decision point | Enforced by | Notes |
| --- | --- | --- |
| Can this person reach the marketplace at all | IAP, on a Google group | Group membership is the single front gate |
| Can this person see a restricted agent's detail | Application, from `dim_agent.is_restricted` and the access grants | Request flow, then an owner or admin decision |
| Can this person approve a request | Application, from the marketplace admin group | **CONFIRM** group naming with the AIB landing zone standard |
| Can this person's query read a BigQuery table | IAM on the service account, authorised views only | The app cannot read base tables, only views |

The application's service account is granted read on the views and append on the event tables. It
holds no grant that would let it modify `dim_agent`. Catalogue change is a separate, controlled
path (section 6.2), which means a compromise of the running application cannot silently rewrite
the register.

### 5.3 Encryption, logging, supply chain

In transit TLS 1.2 or better everywhere, including inside the perimeter. At rest, Google-managed
encryption with CMEK on the BigQuery dataset and Artifact Registry. Audit: Admin Activity and
Data Access logs enabled on the Data Hub project, which is what evidences who read which table.
Supply chain: dependencies pinned, images built from the internal repository by Cloud Build,
vulnerability scanning on push. The dependency surface is deliberately tiny (Streamlit, the Google
Cloud client libraries and one QR library).

### 5.4 Threat model, abbreviated

| Threat | Control |
| --- | --- |
| Unauthenticated access | IAP; no application-level auth path exists to bypass |
| Account takeover of an employee | Entra conditional access and MFA; marketplace actions are low-impact and fully audited |
| Privilege escalation to approve one's own access request | Approver is the named owner or an admin; requester and approver are both recorded in `fct_access_request` |
| Catalogue tampering | App service account cannot write `dim_agent`; every change leaves a `fct_catalogue_change` row with before and after |
| Data exfiltration from BigQuery | VPC Service Controls perimeter; authorised views; Data Access logs |
| Prompt injection via the Concierge | The model output is used only to rank catalogue entries, never to execute anything. Worst case is a bad search result. |
| Prompt injection via agent descriptions | Same. Catalogue text is curated through the controlled write paths. |
| Secret leakage | Secret Manager, no keys in the image, no user-managed service-account keys |

---

## 6. Data architecture (D4)

### 6.1 Where the agent information lives

**Data Hub (BigQuery), dataset `vpc_agent_marketplace`, is the system of record.** The application
holds no durable copy of the catalogue.

This was a genuine choice. The alternative was Firestore for hot application state with BigQuery as
an analytics sink, which performs better on paper. It was rejected because it splits the system of
record across two stores with two access models, two retention mechanisms and two lineage stories
to explain to this board. At a few hundred catalogue rows and a few thousand events a month, the
single governed store wins on every axis that matters here. If read latency ever becomes the
binding constraint, the answer is a cache in front of BigQuery, not a second source of truth.

### 6.2 How information gets in: three write paths

| Path | Who | Control | Write |
| --- | --- | --- | --- |
| **A. Seed** | Platform team | Pull request review, two-person rule, CI validates against the schema | `MERGE` into `dim_agent`, idempotent on `agent_id` |
| **B. Submission** | Anyone in VP&C | Appended to `fct_submission`, then governance triage: accept, reject or merge | `MERGE` on acceptance only |
| **C. Declaration** | The named agent owner, monthly | Owner attestation. Not self-serve, and recorded against the person. | `MERGE`, metric columns only; catalogue prose untouched |

Every one of the three writes a `fct_catalogue_change` row carrying before, after, actor and
timestamp, retained seven years. That record is what lets anyone prove the register was not quietly
edited, which is the control this board should care about most in a tool whose entire purpose is to
be the register.

### 6.3 How information gets out: the read path

A page load reads a single view, `vw_marketplace_agent`, which joins the catalogue to live vote
counts. The result is cached in-process for 300 seconds, so a BigQuery round trip happens at most
twelve times an hour per instance. Cost is immaterial and p95 render stays inside the 1.5 second
budget.

Downstream consumers, the Evaluation Agent and Looker, read the same governed views directly. They
never read through the application and never see a base table.

### 6.4 Votes, and why they are append-only

The requirement is one vote per person per agent, under concurrent load, across an unknown number
of Cloud Run instances.

A vote is written as an **event**, not an update: one row appended to `fct_vote` carrying the agent,
an HMAC of the voter's email, and the action, cast or withdraw. The count is derived at read time
by taking the latest action per voter and counting the casts. Writes use the BigQuery Storage Write
API with the client-generated `event_id` as the dedupe key.

Consequences worth stating plainly, because they answer the obvious review question:

- There is no read-modify-write, so there is no lock, and concurrent instances cannot lose a vote.
- The "one vote per person" rule is a property of the view, not of a constraint somebody could
  forget to enforce.
- A user can change their mind, and the history of that is preserved.
- The vote count survived the move off the single-instance pilot without a migration.

Immediately after a vote the application updates the session optimistically and invalidates that
agent's cache key, so the user sees their own vote at once rather than up to 300 seconds later.

### 6.5 Schema

Full DDL in `schema/bigquery-ddl.sql`. Summary:

| Table | Shape | Personal data | Retention |
| --- | --- | --- | --- |
| `dim_agent` | Current state, one row per agent | Owner name and work email, as a business contact | Life of the service |
| `fct_catalogue_change` | Append-only | Actor work email | 7 years |
| `fct_vote` | Append-only | Pseudonymous, HMAC only | 24 months |
| `fct_access_request` | Append-only | Yes: email, name, role, free-text reason | 36 months |
| `fct_submission` | Append-only | Submitter work email | 36 months |
| `fct_sign_in` | Append-only | Yes: email, timestamp. No IP, no user agent. | 13 months |
| `fct_concierge_query` | Append-only | Pseudonymous, free-text query | 90 days |
| `fct_playground_turn` | Append-only | Pseudonymous. Metadata only, no prompt or response text. | 13 months |

Retention is set as `partition_expiration_days` on the table, so deletion happens by platform
behaviour rather than by a scheduled job somebody has to maintain and evidence.

---

## 7. Data flows, classification and privacy (D3)

D3 numbers all ten flows and tabulates what travels on each. The DPIA-relevant positions:

### 7.1 Personal data inventory

| Data element | Where | Purpose | Lawful basis | Retention |
| --- | --- | --- | --- | --- |
| Work email, display name | IAP assertion, `fct_sign_in` | Authenticate; adoption reporting; access audit | Legitimate interest, internal tooling administration | 13 months |
| Work email as agent owner | `dim_agent` | Accountability and the access-request route | Legitimate interest | Life of the service |
| HMAC of work email | `fct_vote`, `fct_concierge_query` | Enforce one vote per person; search quality | Legitimate interest | 24 months / 90 days |
| Email, name, role, free-text reason | `fct_access_request` | Let the owner make an access decision | Legitimate interest | 36 months |
| Free-text task description | `fct_concierge_query`, and in transit to the model | Match a task to agents | Legitimate interest | 90 days |

**CONFIRM the lawful basis with Privacy.** The above is the drafting position, not a legal opinion.

### 7.2 Pseudonymisation

Where identity is needed only to deduplicate, the email is replaced by
`HMAC-SHA256(lower(email), pepper)` with the pepper held in Secret Manager. An analyst with query
access to `fct_vote` cannot tell who voted for what. Where a real address is functionally necessary,
which is access requests and the sign-in audit, it is held and the purpose is documented per column
in the DDL.

### 7.3 Data subject rights

Access and erasure are satisfiable. Given a work email the platform team can locate every row for
that person: directly in the identified tables, and via the HMAC in the pseudonymous ones. Erasure
uses `DELETE` on the partitioned tables; `fct_catalogue_change` is retained under the audit
exemption. **CONFIRM** the handling of the audit table with Privacy.

### 7.4 Residual privacy risk

Two places, both called out deliberately:

1. **`fct_access_request.reason`** is the only free-text field stored against an identified person.
   Mitigation: visible only to the agent owner and marketplace admins, 36 month retention, and
   on-screen guidance that it is read by the owner.
2. **The Concierge query** is the only free text that leaves the application tier. A user could type
   anything into a search box. Mitigations: 90 day retention, pseudonymous storage, the AIB gateway's
   own Responsible AI filtering, and the fact that the payload goes no further than the Vodafone
   boundary.

### 7.5 International transfer

None. Everything stays in the Vodafone Google Cloud organisation in the EU, including inference.
**CONFIRM** against the Data Hub and AIB region.

---

## 8. AI usage and Responsible AI

| Question | Answer |
| --- | --- |
| Which model | Gemini, served by Vertex AI inside the Vodafone boundary |
| How reached | Only through the AIB AI Gateway over Private Service Connect. No direct Vertex call, no model credential in the application. |
| Used for what | One function only: Concierge search. Matching a typed task description to agents in the catalogue. |
| What is in the prompt | The user's task description, plus name, tagline, about text and function of catalogue entries |
| What is not | Any supplier, contract, PO, invoice, price or spend data. None of it is in scope for this application, so none can reach a model through it. |
| Autonomy | None. The model ranks and explains. It takes no action, writes nothing and calls no tool. |
| Human oversight | The output is a ranked list on a search page. The user chooses. |
| Failure mode | A poor search result. There is no decision the model can make that affects a person, a supplier or a payment. |
| Training | No Vodafone data is used to train or fine-tune any model |
| Guardrails | The gateway's Responsible AI filters; prompt and token accounting at the gateway |
| Fallback | Deterministic keyword matching if the gateway is unavailable, so search degrades rather than fails |

Under an EU AI Act screening this is a minimal-risk internal search feature, not a high-risk system:
it does not evaluate people, does not determine access to a service for a person, and takes no
autonomous action. **CONFIRM the classification with Legal.**

One honest caveat for the board. The marketplace publishes a monthly score that promotes one pilot
over another. That score is computed in SQL from declared metrics and votes, with published weights,
in a view anyone can read. **It is not model-generated,** and it must stay that way: the moment a
model ranks colleagues' work, the fairness conversation becomes a different one.

---

## 9. Well-Architected review

Against the Google Cloud Architecture Framework pillars.

### 9.1 Operational excellence

- Infrastructure as code, deployed by pipeline from the internal repository; no console changes in
  production.
- Three environments: lab (current), non-production, production.
- Observability: Cloud Logging, Cloud Monitoring with SLOs and alerting, Error Reporting.
- Runbook for the three failure modes that matter: gateway unavailable, BigQuery unavailable,
  bad catalogue deploy.
- **Gap:** no formal on-call rota. Proposed: business-hours support by the AI Domain team, which
  suits an internal discovery tool. **CONFIRM acceptable.**

### 9.2 Security, privacy and compliance

Covered in sections 5 and 7. Principal decisions: identity delegated to the platform, perimeter
around the data, least privilege such that the running application cannot rewrite the register,
pseudonymisation by default, retention enforced in the DDL.

### 9.3 Reliability

- Cloud Run across zones in the region; `min-instances = 1`.
- Stateless application, so instance loss costs nothing.
- Graceful degradation: if the AIB gateway is down, search falls back to keyword matching; if
  BigQuery is briefly unavailable, cached catalogue reads continue to serve.
- RPO and RTO: BigQuery time travel gives seven days; table snapshots for the catalogue.
  Proposed RPO 24 hours, RTO 4 hours. For an internal discovery tool this is proportionate.
  **CONFIRM against the Vodafone service tiering standard.**
- **Gap:** no cross-region DR. Proposed as accepted risk given the criticality tier.

### 9.4 Cost optimisation

Material costs are Cloud Run (`min-instances = 1` continuous, scaling with usage), BigQuery storage
(small) and query (bounded by the 300 second cache), and model tokens at the gateway, metered per
Concierge query. The design choices that hold cost down are the read cache and the decision not to
run a second datastore. Expected to be immaterial against the portfolio; the gateway's token
accounting gives a per-query figure once live.

### 9.5 Performance optimisation

Budget: p95 page render under 1.5 seconds, p95 Concierge response under 3 seconds. Levers if
missed: BI Engine on the dataset, a longer cache TTL, Memorystore in front of BigQuery. None are
needed at the current data volume.

---

## 10. Assumptions and open items

Items marked **CONFIRM** above, collected:

| # | Item | Owner | Blocking? |
| --- | --- | --- | --- |
| 1 | Data classification: proposed Vodafone Internal | Security | Yes, for the assessment |
| 2 | Region: europe-west4, matching Data Hub and AIB | Platform | Yes |
| 3 | Entra SAML into Workforce Identity Pool is the AIB standard pattern | AIB platform team | Yes |
| 4 | AIB gateway interface, auth model and prompt-logging policy | AIB platform team | Yes, for section 8 |
| 5 | Lawful basis and the audit-table erasure exemption | Privacy | Yes, for the DPIA |
| 6 | EU AI Act classification as minimal risk | Legal | Yes |
| 7 | Service tier, and whether RPO 24h / RTO 4h is accepted | Service management | No |
| 8 | Business-hours support model accepted | Service management | No |
| 9 | Admin group naming under the landing zone standard | Platform | No |

**Dependencies:** Data Hub dataset provisioned with CMEK; AIB gateway endpoint and credential;
Workforce Identity Pool configured; VPC Service Controls perimeter amended to include the
application project.

---

## 11. What changed from the pilot

Stated plainly, because a reviewer who saw the pilot will ask.

| Pilot | Now |
| --- | --- |
| Shared username and password in environment variables | Removed. Platform identity through IAP. |
| Email allowlist in application config | Removed. Google group membership. |
| Signed guest token in a QR link for the All Hands | Removed. Event-only mechanism, not present in the production design. |
| Votes and requests in JSON files on local disk | Append-only tables in Data Hub |
| Seeded, illustrative agent inventory | Real VP&C agents |
| No model usage; keyword search with a stub | Gemini through the AIB gateway, with keyword matching as the fallback |
| Public repository | Vodafone internal repository |

One item is outstanding and should be closed before or alongside approval: the credential used by
the pilot was committed to the public repository and remains in its git history. It is no longer
used by anything, but it should be formally rotated and the exposure recorded, rather than left to
be found.
