# Data Protection Impact Assessment: VP&C Agent Marketplace

**Status:** Draft for Privacy review
**Controller:** Vodafone Procurement & Connectivity
**Service owner:** Procurement AI Operations
**Document owner:** Praveen Orvakanti, AI Domain, VP&C
**Companion:** `HLD-agent-marketplace.md`, and `diagrams/03-data-flow.svg` for the numbered flows

This assessment covers the Agent Marketplace only. It does not cover the agents the marketplace
catalogues: each of those carries its own approval.

---

## 1. Is a DPIA required?

Screening against the usual triggers:

| Trigger | Present? | Note |
| --- | --- | --- |
| Large-scale processing of special category data | No | None processed |
| Systematic monitoring of individuals | No | Usage telemetry is for adoption reporting, not behaviour monitoring of staff |
| Automated decision-making with legal or similarly significant effect | No | The model ranks search results. No decision about a person is automated. |
| Innovative technology | Yes | Generative AI is used for one capability |
| Processing of employee personal data at scale | Yes | All of VP&C is in the potential user population |
| Customer or supplier personal data | No | Out of scope by design, see section 3 |

Two triggers present, so the assessment proceeds. The conclusion in section 9 is that residual
risk is low.

---

## 2. What the system does

An internal catalogue and front door for the AI agents built across VP&C. Employees discover
agents, try unrestricted ones, vote, leave feedback, submit ideas, and request access to
restricted ones. Owners approve access and attest monthly metrics. A monthly score promotes one
pilot to production.

The processing is incidental to that purpose: the system needs to know who is using it so a vote
counts once, an access request can be answered, and an audit trail exists.

---

## 3. The exclusion that bounds this assessment

No supplier record, contract, purchase order, invoice, price or spend figure is read, stored or
transmitted by this application on any path. SAP, Ariba and SAP Datasphere are not integrated with
it. The marketplace describes agents; it does not operate them, and it does not proxy or retain
the conversations users have with them on their own platforms.

This is an architectural property, not a policy promise: there is no connection, credential or
network path from this system to those stores. It is visible in diagrams 02 and 03.

---

## 4. Personal data inventory

All data subjects are **Vodafone employees**. No customer, consumer or supplier-contact data.

| # | Data element | Where it is held | Purpose | Necessity | Retention |
| --- | --- | --- | --- | --- | --- |
| 1 | Work email, display name | IAP assertion in transit; `fct_sign_in` | Authenticate; adoption reporting; access audit | Required to operate an access-controlled internal service | 13 months |
| 2 | Work email, name, role | `fct_access_request` | Let the agent owner decide on an access request | The owner cannot decide without knowing who is asking | 36 months |
| 3 | Free-text reason | `fct_access_request.reason` | Justify the access request to the owner | Written by the requester, for the owner | 36 months |
| 4 | Work email | `fct_submission.submitter_upn` | Let a curator go back to the author of an idea | Triage requires a contactable author | 36 months |
| 5 | Free text and attachments | `fct_submission.payload`, Cloud Storage | The content of the idea or nomination | That is the submission | 36 months |
| 6 | Work email as agent owner | `dim_agent.owner_upn`, `owner_name` | Accountability, and the route for access requests | A register without an owner is not a register | Life of the service |
| 7 | Work email, application role | `dim_user_role` | Application role assignment (curator, owner, board reader) | Needed to authorise curation and approval | Life of the role + 12 months |
| 8 | Work email | `fct_notification.recipient_upn` | Deliver the notification | Cannot notify without an address | 13 months |
| 9 | Work email as actor | `fct_activity_audit.actor_upn` | Audit of every state change | Required for the assurance the AI Board relies on | 7 years |
| 10 | HMAC of work email | `fct_vote`, `fct_feedback`, `fct_concierge_query`, `fct_model_call` | Deduplicate per person without identifying them | Pseudonymisation applied wherever identity is not needed | 90 days to 24 months |
| 11 | Free-text review comment | `fct_feedback.comment` | Peer feedback on an agent | Pseudonymous | 24 months |
| 12 | Free-text task description | `fct_concierge_query.query_text`, and in transit to the model | Match a task to agents | Pseudonymous; shortest retention in the schema | 90 days |

**Lawful basis.** Legitimate interest: administration of an internal tool used to manage the
organisation's own AI estate, with no significant effect on the individual.
**CONFIRM the basis with Privacy.** The above is the drafting position, not a legal opinion.

---

## 5. Pseudonymisation

Where the business function needs only to distinguish one person from another, the work email is
replaced by `HMAC-SHA256(lower(upn), pepper)`, with the pepper held in Secret Manager and never in
the dataset. This applies to votes, feedback, Concierge queries and model-call telemetry.

The effect: an analyst with query access to those tables can count distinct voters and measure
adoption, but cannot tell who voted for what, who wrote which review, or what any named person
searched for. Re-identification requires the pepper, which is held under separate access control
and is rotatable.

Where a real address is functionally necessary, it is held and the purpose is recorded per column
in `schema/bigquery-ddl.sql`.

---

## 6. Retention

Retention is set as `partition_expiration_days` on each table. Deletion is therefore platform
behaviour: it does not depend on a scheduled job that somebody has to maintain, monitor and
evidence to an auditor.

| Retention | Tables | Reason |
| --- | --- | --- |
| 90 days | `fct_concierge_query` | Unconstrained free text; shortest justifiable period for search-quality tuning |
| 13 months | `fct_sign_in`, `fct_notification`, `fct_model_call` | One annual reporting cycle plus a margin |
| 24 months | `fct_vote`, `fct_feedback` | Two scoring cycles, so year-on-year comparison is possible |
| 36 months | `fct_access_request`, `fct_submission` | Access decisions may be queried for up to three years |
| 6 months | `fct_agent_similarity` | Derived output, recomputed |
| 7 years | `fct_activity_audit` | Audit trail of catalogue and access changes |
| Life of service | `dim_agent`, `dim_taxonomy` | Current-state reference data |

---

## 7. Data subject rights

| Right | How it is satisfied |
| --- | --- |
| Access | Given a work email, the platform team can locate every row for that person: directly in the identified tables, and via the HMAC in the pseudonymous ones. A standard query set will be held in the runbook. |
| Rectification | Catalogue entries and role assignments are editable through the application. Event rows are immutable by design; a correction is a new event. |
| Erasure | `DELETE` on the partitioned tables, plus the Cloud Storage objects referenced by the person's submissions. The HMAC rows can be located and removed using the pepper. |
| Restriction and objection | A user can withdraw a vote, and an account can be removed from `user_group_app`, which ends all processing for them. |
| Portability | Not applicable: the basis is legitimate interest, not contract or consent. |

**Exemption claimed:** `fct_activity_audit` is retained through an erasure request, as the record
of who approved what access is the control the AI Portfolio Board relies on. **CONFIRM this
exemption with Privacy.**

---

## 8. Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation | Residual |
| --- | --- | --- | --- | --- | --- |
| 1 | A user types something sensitive into the Concierge box, and it reaches a model | Medium | Medium | PII and data-privacy screening at the gateway before anything leaves the application tier; 90 day retention; pseudonymous storage; the prompt never leaves the Vodafone boundary | Low |
| 2 | A free-text access-request reason or review comment contains personal information about a third party | Low | Low | Visible only to the owner and curators; on-screen guidance that the owner reads it; bounded retention | Low |
| 3 | Attachment on a submission contains confidential or personal data | Medium | Medium | Private bucket, uniform bucket-level access, no public objects, access only through the backend; file-type allowlist; the same classification and retention as the submission | Low |
| 4 | Analyst with BigQuery access infers who voted for what | Low | Low | Pseudonymisation; authorised views; Data Access logs; the pepper is separately controlled | Low |
| 5 | Usage telemetry is repurposed as employee performance monitoring | Low | High | Purpose recorded per column; adoption reporting is aggregate; no per-person usage dashboard is built, and building one would require a change to this DPIA | Low |
| 6 | Model output is used to rank colleagues' work | Low | Medium | The monthly score is computed in SQL from attested metrics and votes, with published weights. Not model-generated. Changing that requires Board re-approval. | Low |
| 7 | Data leaves the EU | Low | High | Single region; inference inside the Vodafone boundary; VPC Service Controls blocks egress even with valid credentials | Low |
| 8 | Over-retention | Low | Low | Partition expiry per table, enforced by BigQuery rather than by a job | Low |

---

## 9. Conclusion

The processing is internal, employee-only, proportionate to the purpose and pseudonymised wherever
identity is not functionally required. The sensitive procurement data that makes neighbouring use
cases high risk is architecturally out of scope. Model usage is confined to one capability, with
no autonomy and no effect on any individual.

**Residual risk: low.** The assessment recommends approval, subject to the four CONFIRM items in
section 10 of the HLD.

Two things are worth re-testing at the first post-deployment review: whether the Concierge query
log is still needed at all after 90 days of tuning, and whether attachments on submissions are
being used as intended.
