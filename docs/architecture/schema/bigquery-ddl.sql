-- =====================================================================
-- VP&C Agent Marketplace - BigQuery schema
-- Project : vf-grp-aib-prd-scm-vpc-xx   (xx = lab | nl | live)
-- Dataset : agent_marketplace
-- Owner   : Procurement AI Operations
-- Class   : Confidential  |  CMEK  |  user and market-level filtering
--
-- Written and read ONLY by the Agent Marketplace Backend service.
-- The Streamlit frontend has no grant on this dataset and no credential
-- for it; every read and write arrives through the AI Orchestration
-- Gateway carrying the end user's own bearer token.
--
-- Design rules:
--   1. dim_* hold curated current state. Everything a user does is an
--      append-only fct_* event. No read-modify-write anywhere, so N Cloud
--      Run instances cannot lose a concurrent write.
--   2. Current state is derived in views, not stored. "One vote per person
--      per agent" is a property of the view, not a constraint somebody can
--      forget to enforce.
--   3. Identity is pseudonymised wherever the business function does not
--      need the real address. Tables that do need it say why, per column.
--   4. Retention is partition expiry on the table, so deletion is platform
--      behaviour rather than a job someone has to maintain and evidence.
--   5. No prompt or response content is persisted anywhere.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS agent_marketplace
OPTIONS (location = 'europe-west4',          -- CONFIRM against the AIB region
         default_kms_key_name = 'projects/<kms-project>/locations/europe-west4/keyRings/<ring>/cryptoKeys/<key>');


-- ---------------------------------------------------------------------
-- 1. CATALOGUE AND TAXONOMY  (no personal data beyond the named owner)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_marketplace.dim_agent (
  agent_id              STRING    NOT NULL OPTIONS (description = 'Stable slug. Never reused.'),
  name                  STRING    NOT NULL,
  tagline               STRING,
  about                 STRING,
  maturity              STRING    NOT NULL OPTIONS (description = 'scaled | pilot | idea'),
  platform              STRING    NOT NULL OPTIONS (description = 'Copilot | Emplay | GCP | Looker | ...'),
  function_area         STRING    NOT NULL,
  market                STRING             OPTIONS (description = 'Drives market-level row filtering. NULL = group-wide.'),
  is_restricted         BOOL      NOT NULL DEFAULT FALSE,
  audience              STRING,
  owner_upn             STRING    NOT NULL OPTIONS (description = 'Accountable owner. A business contact, not a secret.'),
  owner_name            STRING    NOT NULL,
  owner_role            STRING,
  how_steps             ARRAY<STRING>,
  sample_prompts        ARRAY<STRING>,
  deep_link             STRING             OPTIONS (description = 'Where the agent actually runs.'),
  hours_saved_per_month INT64              OPTIONS (description = 'Owner-attested. Impact component.'),
  pilot_users           INT64              OPTIONS (description = 'Adoption component.'),
  rating_avg            FLOAT64            OPTIONS (description = 'Satisfaction component.'),
  rating_count          INT64,
  status                STRING    NOT NULL DEFAULT 'published'
                                           OPTIONS (description = 'draft | published | retired'),
  published_at          TIMESTAMP,
  retired_at            TIMESTAMP,
  updated_at            TIMESTAMP NOT NULL,
  updated_by            STRING    NOT NULL
)
CLUSTER BY maturity, function_area
OPTIONS (description = 'Curated agent catalogue. System of record. Written only by the curation pipeline and the approval workflow, never by the runtime service account.');


CREATE TABLE IF NOT EXISTS agent_marketplace.dim_taxonomy (
  term_id               STRING    NOT NULL,
  scheme                STRING    NOT NULL OPTIONS (description = 'function | capability | data_sensitivity | platform'),
  term                  STRING    NOT NULL,
  parent_term_id        STRING,
  description           STRING,
  updated_at            TIMESTAMP NOT NULL
)
OPTIONS (description = 'Controlled vocabulary behind search, filtering and classification. No personal data.');


CREATE TABLE IF NOT EXISTS agent_marketplace.dim_agent_taxonomy (
  agent_id              STRING    NOT NULL,
  term_id               STRING    NOT NULL,
  assigned_by           STRING    NOT NULL OPTIONS (description = 'curator | model | owner'),
  confidence            FLOAT64            OPTIONS (description = 'Populated when assigned_by = model.'),
  assigned_at           TIMESTAMP NOT NULL
)
OPTIONS (description = 'Agent to taxonomy assignment. Model-assigned terms carry a confidence and are reviewable.');


-- ---------------------------------------------------------------------
-- 2. ACCESS AND ROLES
--
-- NOTE FOR REVIEW: group membership in Cloud IAM remains the authoritative
-- access control. This table holds APPLICATION role assignments only
-- (curator, agent owner, board reader). It must not become a second
-- source of truth for who may reach the service.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_marketplace.dim_user_role (
  user_upn              STRING    NOT NULL OPTIONS (description = 'Work email from the verified IAP assertion.'),
  app_role              STRING    NOT NULL OPTIONS (description = 'curator | owner | board_reader'),
  market                STRING             OPTIONS (description = 'Scopes what the role can see. NULL = group-wide.'),
  granted_by            STRING    NOT NULL,
  granted_at            TIMESTAMP NOT NULL,
  revoked_at            TIMESTAMP
)
OPTIONS (description = 'Application-level role assignment. Service entry remains governed by Cloud IAM group user_group_app.');


-- ---------------------------------------------------------------------
-- 3. APPEND-ONLY EVENT TABLES
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_marketplace.fct_vote (
  event_id              STRING    NOT NULL OPTIONS (description = 'Client UUID. Also the Storage Write API dedupe key.'),
  agent_id              STRING    NOT NULL,
  voter_hash            STRING    NOT NULL OPTIONS (description = 'HMAC-SHA256(lower(upn), pepper from Secret Manager). Not reversible without the pepper.'),
  action                STRING    NOT NULL OPTIONS (description = 'cast | withdraw. Latest per (agent_id, voter_hash) wins.'),
  event_ts              TIMESTAMP NOT NULL,
  app_version           STRING
)
PARTITION BY DATE(event_ts) CLUSTER BY agent_id
OPTIONS (partition_expiration_days = 730,
         description = 'One row per vote action. Never updated, never deleted in place.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_feedback (
  event_id              STRING    NOT NULL,
  agent_id              STRING    NOT NULL,
  author_hash           STRING    NOT NULL OPTIONS (description = 'HMAC as per fct_vote.'),
  stars                 INT64              OPTIONS (description = '1 to 5.'),
  comment               STRING             OPTIONS (description = 'Free text written by a user. Pseudonymous. See DPIA section 5.'),
  event_ts              TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts) CLUSTER BY agent_id
OPTIONS (partition_expiration_days = 730,
         description = 'Reviews and ratings. Pseudonymous: the author is not directly identifiable from this table.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_submission (
  event_id              STRING    NOT NULL,
  submission_id         STRING    NOT NULL OPTIONS (description = 'Groups a submission with its triage decisions.'),
  track                 STRING    NOT NULL OPTIONS (description = 'idea | publish_agent | nominate_to_scale'),
  event_type            STRING    NOT NULL OPTIONS (description = 'submitted | accepted | rejected | merged'),
  title                 STRING,
  payload               JSON               OPTIONS (description = 'Track-specific fields as submitted. Free text written by an identified person.'),
  attachment_uri        STRING             OPTIONS (description = 'gs:// object in the permitted-attachments bucket. Never a public URL.'),
  submitter_upn         STRING    NOT NULL OPTIONS (description = 'Needed so the curator can go back to the author.'),
  decided_by_upn        STRING,
  event_ts              TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts) CLUSTER BY submission_id
OPTIONS (partition_expiration_days = 1095,
         description = 'Submission and triage lifecycle. Current state is the latest event per submission_id.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_access_request (
  event_id              STRING    NOT NULL,
  request_id            STRING    NOT NULL,
  agent_id              STRING    NOT NULL,
  event_type            STRING    NOT NULL OPTIONS (description = 'requested | approved | denied | revoked'),
  requester_upn         STRING    NOT NULL OPTIONS (description = 'The owner has to know who is asking. Purpose-limited to access administration.'),
  requester_name        STRING,
  requester_role        STRING,
  reason                STRING             OPTIONS (description = 'Free text from the requester. Visible to the owner and curators only.'),
  decided_by_upn        STRING,
  event_ts              TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts) CLUSTER BY agent_id, request_id
OPTIONS (partition_expiration_days = 1095,
         description = 'Access request lifecycle. Current status is the latest event per request_id.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_notification (
  event_id              STRING    NOT NULL,
  recipient_upn         STRING    NOT NULL OPTIONS (description = 'Delivery address. Required to send the notification.'),
  channel               STRING    NOT NULL OPTIONS (description = 'email | teams | in_app'),
  template_id           STRING    NOT NULL OPTIONS (description = 'Template reference. The rendered body is NOT stored.'),
  related_object        STRING             OPTIONS (description = 'agent_id, request_id or submission_id.'),
  outcome               STRING    NOT NULL OPTIONS (description = 'queued | sent | failed | suppressed'),
  event_ts              TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 395,
         description = 'Notification dispatch record. Template reference only, so no message body is retained.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_activity_audit (
  event_id              STRING    NOT NULL,
  actor_upn             STRING    NOT NULL OPTIONS (description = 'Who did it. Required for the audit trail the AI Board relies on.'),
  action                STRING    NOT NULL OPTIONS (description = 'catalogue.update | access.approve | submission.accept | role.grant | ...'),
  object_type           STRING    NOT NULL,
  object_id             STRING    NOT NULL,
  before_json           JSON,
  after_json            JSON,
  event_ts              TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts) CLUSTER BY action
OPTIONS (partition_expiration_days = 2555,
         description = 'Immutable activity and audit record, seven years. This is what proves the register was not quietly edited.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_sign_in (
  event_id              STRING    NOT NULL,
  user_upn              STRING    NOT NULL OPTIONS (description = 'From the verified IAP assertion. Adoption reporting and access audit.'),
  event_ts              TIMESTAMP NOT NULL
  -- Deliberately no IP address and no user agent. Neither is needed for any
  -- marketplace function; the load balancer logs already hold what an
  -- incident investigation would need, under their own retention.
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 395,
         description = 'Who used the marketplace and when.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_concierge_query (
  event_id              STRING    NOT NULL,
  user_hash             STRING    NOT NULL OPTIONS (description = 'HMAC. The query text is more sensitive than the identity, so the identity is dropped.'),
  query_text            STRING             OPTIONS (description = 'User-typed task description. Unconstrained free text: shortest retention in the schema.'),
  matched_agent_ids     ARRAY<STRING>,
  matcher               STRING    NOT NULL OPTIONS (description = 'keyword | model'),
  model_id              STRING,
  latency_ms            INT64,
  event_ts              TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 90,
         description = 'Search quality telemetry. No model response text is stored.');


CREATE TABLE IF NOT EXISTS agent_marketplace.fct_model_call (
  event_id              STRING    NOT NULL,
  capability            STRING    NOT NULL OPTIONS (description = 'Which domain service called a model.'),
  user_hash             STRING    NOT NULL,
  model_id              STRING    NOT NULL,
  outcome               STRING    NOT NULL OPTIONS (description = 'ok | refused_by_rai | error | timeout'),
  prompt_tokens         INT64,
  completion_tokens     INT64,
  latency_ms            INT64,
  event_ts              TIMESTAMP NOT NULL
  -- Metadata only. Prompt and completion text are never written here; the
  -- AI Orchestration Gateway holds whatever record its own policy requires.
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 395,
         description = 'Model usage and cost telemetry. No prompt or response content.');


-- ---------------------------------------------------------------------
-- 4. DERIVED OUTPUTS
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_marketplace.fct_agent_similarity (
  agent_id              STRING    NOT NULL,
  related_agent_id      STRING    NOT NULL,
  similarity            FLOAT64   NOT NULL OPTIONS (description = '0 to 1.'),
  basis                 STRING    NOT NULL OPTIONS (description = 'taxonomy_overlap | embedding | co_usage'),
  computed_at           TIMESTAMP NOT NULL
)
PARTITION BY DATE(computed_at) CLUSTER BY agent_id
OPTIONS (partition_expiration_days = 190,
         description = 'Similarity and relationship outputs. Recomputed, never hand-edited. Used for duplicate detection at intake.');


-- ---------------------------------------------------------------------
-- 5. VIEWS  (the only objects the backend service account may read)
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW agent_marketplace.vw_agent_vote AS
WITH latest AS (
  SELECT agent_id, voter_hash, action,
         ROW_NUMBER() OVER (PARTITION BY agent_id, voter_hash ORDER BY event_ts DESC) AS rn
  FROM agent_marketplace.fct_vote
)
SELECT agent_id, COUNTIF(action = 'cast') AS votes
FROM latest WHERE rn = 1 GROUP BY agent_id;


CREATE OR REPLACE VIEW agent_marketplace.vw_access_state AS
SELECT request_id, agent_id, requester_upn, requester_name, requester_role, reason,
       event_type AS status, decided_by_upn, event_ts AS last_event_ts
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY event_ts DESC) AS rn
      FROM agent_marketplace.fct_access_request)
WHERE rn = 1;


CREATE OR REPLACE VIEW agent_marketplace.vw_submission_state AS
SELECT submission_id, track, title, payload, attachment_uri, submitter_upn,
       event_type AS status, decided_by_upn, event_ts AS last_event_ts
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY submission_id ORDER BY event_ts DESC) AS rn
      FROM agent_marketplace.fct_submission)
WHERE rn = 1;


-- The single read the catalogue service issues on a page load.
CREATE OR REPLACE VIEW agent_marketplace.vw_marketplace_agent AS
SELECT a.*, IFNULL(v.votes, 0) AS votes,
       ARRAY(SELECT t.term FROM agent_marketplace.dim_agent_taxonomy at
             JOIN agent_marketplace.dim_taxonomy t USING (term_id)
             WHERE at.agent_id = a.agent_id) AS terms
FROM agent_marketplace.dim_agent a
LEFT JOIN agent_marketplace.vw_agent_vote v USING (agent_id)
WHERE a.status = 'published';


-- The published 40/30/20/10 scoring formula. Defined once, here, so the
-- leaderboard and the Evaluation Agent cannot drift apart.
CREATE OR REPLACE VIEW agent_marketplace.vw_pilot_score AS
WITH pilots AS (
  SELECT agent_id, name,
         IFNULL(hours_saved_per_month, 0) AS impact_raw,
         IFNULL(pilot_users, 0)           AS adoption_raw,
         IFNULL(rating_avg, AVG(rating_avg) OVER ()) AS satisfaction_raw,
         votes                            AS community_raw
  FROM agent_marketplace.vw_marketplace_agent
  WHERE maturity = 'pilot'
),
b AS (SELECT MIN(impact_raw) mi, MAX(impact_raw) xi, MIN(adoption_raw) ma, MAX(adoption_raw) xa,
             MIN(satisfaction_raw) ms, MAX(satisfaction_raw) xs, MIN(community_raw) mc, MAX(community_raw) xc
      FROM pilots),
scaled AS (
  SELECT p.agent_id, p.name,
    IF(b.xi = b.mi, 100, (p.impact_raw       - b.mi) / (b.xi - b.mi) * 100) AS impact,
    IF(b.xa = b.ma, 100, (p.adoption_raw     - b.ma) / (b.xa - b.ma) * 100) AS adoption,
    IF(b.xs = b.ms, 100, (p.satisfaction_raw - b.ms) / (b.xs - b.ms) * 100) AS satisfaction,
    IF(b.xc = b.mc, 100, (p.community_raw    - b.mc) / (b.xc - b.mc) * 100) AS community
  FROM pilots p CROSS JOIN b
)
SELECT agent_id, name, impact, adoption, satisfaction, community,
       ROUND(0.4 * impact + 0.3 * adoption + 0.2 * satisfaction + 0.1 * community, 1) AS total_score
FROM scaled ORDER BY total_score DESC;


-- Market-level row filtering. Applied as an authorised view so the backend
-- cannot see rows outside the caller's market.
CREATE OR REPLACE VIEW agent_marketplace.vw_marketplace_agent_scoped AS
SELECT a.*
FROM agent_marketplace.vw_marketplace_agent a
WHERE a.market IS NULL
   OR a.market IN (SELECT market FROM agent_marketplace.dim_user_role
                   WHERE user_upn = SESSION_USER() AND revoked_at IS NULL);
