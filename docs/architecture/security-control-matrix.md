# Security control matrix: VP&C Agent Marketplace

**Purpose.** Tell a reviewer, control by control, which controls this use case **inherits** from
already-approved AIB components and which are **implemented** for it. The review surface is the
second group.

Legend: **I** inherited from approved AIB platform  |  **N** new, implemented by this use case
|  **S** shared, configured by us on an inherited service

---

## 1. Identity and access

| # | Control | Type | Implementation | Evidence |
| --- | --- | --- | --- | --- |
| 1.1 | User authentication | I | Entra ID SSO, SAML, MFA | Entra conditional access policy |
| 1.2 | Federation into Google Cloud | I | WorkForce Pool | AIB landing zone configuration |
| 1.3 | Service entry authorisation | S | IAP on Cloud IAM group `user_group_app` | IAP configuration, group membership |
| 1.4 | No application-managed credentials | N | No login page, no password store, no session cookie of its own | Code review; `auth` module reads the IAP assertion only |
| 1.5 | Per-user authorisation on every backend call | N | End-user bearer token forwarded through the gateway; the backend authorises the caller, not a service account | `api-contract.md`; D5 sequences |
| 1.6 | Application roles | N | `dim_user_role`, separate from service entry | DDL; section 6.5 of the HLD |
| 1.7 | Row-level scoping by market | N | `vw_marketplace_agent_scoped`, an authorised view | DDL |
| 1.8 | Least-privilege service accounts | N | Backend may read views and append to event tables. No write grant on `dim_agent`. | IAM policy export |
| 1.9 | No user-managed service-account keys | N | Workload identity only | Org policy `constraints/iam.disableServiceAccountKeyCreation` |

## 2. Network

| # | Control | Type | Implementation | Evidence |
| --- | --- | --- | --- | --- |
| 2.1 | WAF and rate limiting at the edge | S | Cloud Armor on the external load balancer | Cloud Armor policy |
| 2.2 | TLS in transit | I | Managed certificate, TLS 1.2 or better, including inside the perimeter | LB configuration |
| 2.3 | Single ingress path to the frontend | N | Serverless NEG; Cloud Run ingress restricted to the load balancer | Cloud Run ingress setting |
| 2.4 | No internet path to the backend | N | Internal load balancer reached over Private Service Connect | VPC and PSC configuration |
| 2.5 | Data services unreachable from the internet | N | Private Google Access; no public IP on any data service | VPC configuration |
| 2.6 | Egress containment | N | VPC Service Controls perimeter around the backend project and data layer | Access Context Manager policy |

## 3. Data

| # | Control | Type | Implementation | Evidence |
| --- | --- | --- | --- | --- |
| 3.1 | Classification | N | Confidential, recorded on the dataset and in the DDL | Dataset labels |
| 3.2 | Encryption at rest | N | CMEK on BigQuery, Cloud Storage and Artifact Registry | KMS key policy |
| 3.3 | Access through authorised views only | N | The backend has no grant on base tables | IAM policy export |
| 3.4 | Pseudonymisation | N | HMAC-SHA256 with a Secret Manager pepper on votes, feedback, queries and model telemetry | DDL; DPIA section 5 |
| 3.5 | Retention enforced by the platform | N | `partition_expiration_days` per table | DDL |
| 3.6 | No prompt or response content persisted | N | `fct_model_call` and `fct_concierge_query` hold metadata only | DDL |
| 3.7 | Attachments isolated | N | Private bucket, uniform bucket-level access, access only through the backend, file-type allowlist | Bucket IAM and configuration |
| 3.8 | Immutable audit of state change | N | `fct_activity_audit`, append-only, seven years | DDL |
| 3.9 | Who-read-what auditing | S | BigQuery Data Access logs enabled on the dataset | Audit log configuration |

## 4. AI

| # | Control | Type | Implementation | Evidence |
| --- | --- | --- | --- | --- |
| 4.1 | Approved models only | I | LLM Proxy project, governed enterprise models | AIB model catalogue |
| 4.2 | No direct model endpoint from the application | N | All calls through the shared LLM Router | `api-contract.md` |
| 4.3 | Safety filters and guardrails | I | Responsible AI Service | AIB RAI configuration |
| 4.4 | PII and data-privacy screening on egress | I | Responsible AI Service | AIB RAI configuration |
| 4.5 | Prompt-injection defences | I | Responsible AI Service | AIB RAI configuration |
| 4.6 | Policy verification | I | Responsible AI Service | AIB RAI configuration |
| 4.7 | Token accounting and cost attribution | I | Gateway metering | Gateway reporting |
| 4.8 | No training on Vodafone data | I | Enterprise model terms | AIB model terms |
| 4.9 | Model confined to one capability | N | AI-assisted intake and recommendation only; no autonomy, no tool calls | HLD section 8 |
| 4.10 | Deterministic fallback | N | Keyword and taxonomy matching when the gateway is unavailable | Code; HLD section 9 |

## 5. Software supply chain

| # | Control | Type | Implementation | Evidence |
| --- | --- | --- | --- | --- |
| 5.1 | Source in the Vodafone internal repository | N | Internal Git, branch protection, two-person rule | Repository settings |
| 5.2 | Build provenance | N | Cloud Build from the internal repo into Artifact Registry | Build configuration |
| 5.3 | Vulnerability scanning | S | Artifact Registry scanning on push | Scan results |
| 5.4 | Pinned dependencies | N | Lockfile; deliberately small dependency surface | `requirements.txt` |
| 5.5 | No secrets in images or source | N | Secret Manager only; secret scanning in CI | CI configuration |
| 5.6 | Infrastructure as code | N | No console changes in production | Terraform state |

## 6. Operations

| # | Control | Type | Implementation | Evidence |
| --- | --- | --- | --- | --- |
| 6.1 | Environment separation | I | lab / non-live / live, by project | Project inventory |
| 6.2 | Application and security logging | S | Cloud Logging | Log sinks |
| 6.3 | Monitoring and alerting | N | SLOs, error budget, alert policies | Monitoring configuration |
| 6.4 | Posture management | I | Security Command Centre | SCC findings |
| 6.5 | Admin activity auditing | I | Cloud Audit Logs | Audit log configuration |
| 6.6 | Backup and recovery | N | BigQuery time travel (7 days) plus catalogue table snapshots | Snapshot schedule |

---

## 7. Known gaps, declared

| Gap | Position | Owner |
| --- | --- | --- |
| No formal on-call rota | Business-hours support by the AI Domain team, proportionate to the service tier | Service management |
| No cross-region disaster recovery | Accepted risk at the proposed criticality tier | Service management |
| Pilot credential remains in the history of a public repository | No longer used by anything. To be formally rotated and the exposure recorded. | AI Domain |
| Gateway prompt-logging policy not yet documented for this use case | Requested from the AIB platform team; affects DPIA section 4 row 12 | AIB platform |

Declaring these is deliberate. A reviewer who finds an undeclared gap discounts everything else in
the pack.
