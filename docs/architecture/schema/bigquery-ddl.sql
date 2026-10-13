-- =====================================================================
-- VP&C Agent Marketplace - BigQuery schema (Data Hub)
-- Dataset: vpc_agent_marketplace
--
-- Design rules this schema follows:
--   1. Curated state lives in dim_* tables. Everything a user does is an
--      append-only event in fct_*. The app never does read-modify-write,
--      so concurrent writes from N Cloud Run instances cannot lose data.
--   2. Current state is derived in views, not stored. One vote per person
--      per agent is a read-time rule (latest action wins), not a lock.
--   3. Identity is pseudonymised by default. fct_vote and fct_concierge_query
--      carry an HMAC of the email, never the address. Tables that need a real
--      address to function (access requests, sign-in audit) hold it and say why.
--   4. Every event table is day-partitioned with an expiry, so retention is
--      enforced by the platform rather than by a job somebody has to remember.
--   5. No prompt or response content is persisted. Playground and Concierge
--      rows carry metadata only.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS vpc_agent_marketplace
OPTIONS (location = 'europe-west4');     -- CONFIRM: must match the Data Hub region


-- ---------------------------------------------------------------------
-- 1. CATALOGUE (system of record)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.dim_agent (
  agent_id            STRING    NOT NULL OPTIONS (description = 'Stable slug, e.g. "poc". Never reused.'),
  name                STRING    NOT NULL,
  tagline             STRING,
  about               STRING,
  maturity            STRING    NOT NULL OPTIONS (description = 'scaled | pilot | idea'),
  platform            STRING    NOT NULL OPTIONS (description = 'Copilot | Emplay | GCP | Looker | ...'),
  function            STRING    NOT NULL OPTIONS (description = 'Sourcing | Contracts | P2P | Supplier Mgmt | Analytics | Governance'),
  is_restricted       BOOL      NOT NULL DEFAULT FALSE,
  audience            STRING             OPTIONS (description = 'Who the agent is intended for. Free text, shown on the card.'),
  owner_upn           STRING    NOT NULL OPTIONS (description = 'Accountable owner. Business contact, not a secret.'),
  owner_name          STRING    NOT NULL,
  owner_role          STRING,
  how_steps           ARRAY<STRING>      OPTIONS (description = 'The three "how it works" steps.'),
  sample_prompts      ARRAY<STRING>,
  deep_link           STRING             OPTIONS (description = 'Where the agent actually runs. Teams, Looker, Zinger, console.'),
  -- Owner-declared facts, refreshed at each monthly review
  hours_saved_per_month INT64            OPTIONS (description = 'Owner-validated. Feeds the Impact component.'),
  pilot_users         INT64              OPTIONS (description = 'Feeds the Adoption component.'),
  rating_avg          FLOAT64            OPTIONS (description = 'Feeds the Satisfaction component.'),
  rating_count        INT64,
  -- Lifecycle
  status              STRING    NOT NULL DEFAULT 'published'
                                         OPTIONS (description = 'draft | published | retired'),
  published_at        TIMESTAMP,
  retired_at          TIMESTAMP,
  updated_at          TIMESTAMP NOT NULL,
  updated_by          STRING    NOT NULL
)
CLUSTER BY maturity, function
OPTIONS (description = 'Curated agent catalogue. System of record. Written only by the curation pipeline and the governance approval flow.');


CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.fct_catalogue_change (
  change_id           STRING    NOT NULL,
  agent_id            STRING    NOT NULL,
  change_type         STRING    NOT NULL OPTIONS (description = 'created | updated | published | retired'),
  changed_fields      ARRAY<STRING>,
  before_json         JSON               OPTIONS (description = 'Prior row. Retained for audit of catalogue tampering.'),
  after_json          JSON,
  actor_upn           STRING    NOT NULL,
  event_ts            TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 2555,   -- 7 years: this is the audit trail
         description = 'Immutable history of every catalogue mutation.');


-- ---------------------------------------------------------------------
-- 2. COMMUNITY EVENTS (append-only)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.fct_vote (
  event_id            STRING    NOT NULL OPTIONS (description = 'Client-generated UUID. Also the Storage Write API dedupe key.'),
  agent_id            STRING    NOT NULL,
  voter_hash          STRING    NOT NULL OPTIONS (description = 'HMAC-SHA256(lower(email), pepper from Secret Manager). Not reversible without the pepper.'),
  action              STRING    NOT NULL OPTIONS (description = 'cast | withdraw. Latest action per (agent_id, voter_hash) wins.'),
  event_ts            TIMESTAMP NOT NULL,
  app_version         STRING
)
PARTITION BY DATE(event_ts)
CLUSTER BY agent_id
OPTIONS (partition_expiration_days = 730,
         description = 'One row per vote action. Never updated, never deleted in place.');


CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.fct_access_request (
  event_id            STRING    NOT NULL,
  request_id          STRING    NOT NULL OPTIONS (description = 'Groups the request with its decision.'),
  agent_id            STRING    NOT NULL,
  event_type          STRING    NOT NULL OPTIONS (description = 'requested | approved | denied | revoked'),
  requester_upn       STRING    NOT NULL OPTIONS (description = 'Business need: the owner has to know who is asking. Purpose-limited to access administration.'),
  requester_name      STRING,
  requester_role      STRING,
  reason              STRING             OPTIONS (description = 'Free text from the requester. Shown to the owner and the approver only.'),
  decided_by_upn      STRING,
  event_ts            TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts)
CLUSTER BY agent_id, request_id
OPTIONS (partition_expiration_days = 1095,
         description = 'Access request lifecycle. Current status is the latest event per request_id.');


CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.fct_submission (
  submission_id       STRING    NOT NULL,
  track               STRING    NOT NULL OPTIONS (description = 'idea | publish_agent | nominate_to_scale'),
  title               STRING    NOT NULL,
  payload             JSON      NOT NULL OPTIONS (description = 'Track-specific fields as submitted.'),
  submitter_upn       STRING    NOT NULL,
  status              STRING    NOT NULL OPTIONS (description = 'new | accepted | rejected | merged'),
  triaged_by_upn      STRING,
  event_ts            TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 1095,
         description = 'Inbound submissions. Promoted into dim_agent by the curation step on acceptance.');


-- ---------------------------------------------------------------------
-- 3. TELEMETRY (metadata only, no content)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.fct_sign_in (
  event_id            STRING    NOT NULL,
  user_upn            STRING    NOT NULL OPTIONS (description = 'From the verified IAP assertion. Needed for the access audit the AI Board asks for.'),
  event_ts            TIMESTAMP NOT NULL
  -- Deliberately no IP address and no user agent. Neither is needed for any
  -- marketplace function, and Cloud Armor plus the LB access logs already hold
  -- what an incident investigation would need, under their own retention.
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 395,
         description = 'Who used the marketplace and when. Adoption reporting and access audit.');


CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.fct_concierge_query (
  event_id            STRING    NOT NULL,
  user_hash           STRING    NOT NULL OPTIONS (description = 'HMAC as per fct_vote. The query text is more sensitive than the identity, so the identity is dropped.'),
  query_text          STRING             OPTIONS (description = 'User-typed task description. Free text, so treat as potentially containing anything. See HLD section on Concierge privacy.'),
  matched_agent_ids   ARRAY<STRING>,
  matcher             STRING    NOT NULL OPTIONS (description = 'keyword | gemini-via-aib'),
  latency_ms          INT64,
  event_ts            TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_ts)
OPTIONS (partition_expiration_days = 90,
         description = 'Search quality telemetry. Shortest retention in the schema because the text is unconstrained user input.');


CREATE TABLE IF NOT EXISTS vpc_agent_marketplace.fct_playground_turn (
  event_id            STRING    NOT NULL,
  agent_id            STRING    NOT NULL,
  user_hash           STRING    NOT NULL,
  platform            STRING    NOT NULL OPTIONS (description = 'Which downstream platform served the turn.'),
  outcome             STRING    NOT NULL OPTIONS (description = 'ok | refused | error | timeout'),
  latency_ms          INT64,
  prompt_tokens       INT64,
  completion_tokens   INT64,
  event_ts            TIMESTAMP NOT NULL
  -- No prompt text and no response text. The conversation stays with the
  -- platform that served it, under that platform's own approved controls.
)
PARTITION BY DATE(event_ts)
CLUSTER BY agent_id
OPTIONS (partition_expiration_days = 395,
         description = 'Playground usage. Feeds the Adoption component and the cost model.');


-- ---------------------------------------------------------------------
-- 4. DERIVED VIEWS (what the app and the Evaluation Agent read)
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW vpc_agent_marketplace.vw_agent_vote AS
WITH latest AS (
  SELECT agent_id, voter_hash, action,
         ROW_NUMBER() OVER (PARTITION BY agent_id, voter_hash ORDER BY event_ts DESC) AS rn
  FROM vpc_agent_marketplace.fct_vote
)
SELECT agent_id, COUNTIF(action = 'cast') AS votes
FROM latest WHERE rn = 1
GROUP BY agent_id;


CREATE OR REPLACE VIEW vpc_agent_marketplace.vw_access_state AS
SELECT request_id, agent_id, requester_upn, requester_name, requester_role, reason,
       event_type AS status, decided_by_upn, event_ts AS last_event_ts
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY event_ts DESC) AS rn
  FROM vpc_agent_marketplace.fct_access_request
)
WHERE rn = 1;


-- The single query the marketplace reads on a page load.
CREATE OR REPLACE VIEW vpc_agent_marketplace.vw_marketplace_agent AS
SELECT a.*, IFNULL(v.votes, 0) AS votes
FROM vpc_agent_marketplace.dim_agent a
LEFT JOIN vpc_agent_marketplace.vw_agent_vote v USING (agent_id)
WHERE a.status = 'published';


-- The published 40/30/20/10 formula, min-max normalised across the pilot
-- cohort. This is the reference implementation: the leaderboard and the
-- Evaluation Agent must both read it, so there is exactly one definition.
CREATE OR REPLACE VIEW vpc_agent_marketplace.vw_pilot_score AS
WITH pilots AS (
  SELECT agent_id, name,
         IFNULL(hours_saved_per_month, 0) AS impact_raw,
         IFNULL(pilot_users, 0)           AS adoption_raw,
         IFNULL(rating_avg, AVG(rating_avg) OVER ()) AS satisfaction_raw,
         votes                            AS community_raw
  FROM vpc_agent_marketplace.vw_marketplace_agent
  WHERE maturity = 'pilot'
),
bounds AS (
  SELECT MIN(impact_raw) mi, MAX(impact_raw) xi,
         MIN(adoption_raw) ma, MAX(adoption_raw) xa,
         MIN(satisfaction_raw) ms, MAX(satisfaction_raw) xs,
         MIN(community_raw) mc, MAX(community_raw) xc
  FROM pilots
),
scaled AS (
  SELECT p.agent_id, p.name,
    IF(b.xi = b.mi, 100, (p.impact_raw       - b.mi) / (b.xi - b.mi) * 100) AS impact,
    IF(b.xa = b.ma, 100, (p.adoption_raw     - b.ma) / (b.xa - b.ma) * 100) AS adoption,
    IF(b.xs = b.ms, 100, (p.satisfaction_raw - b.ms) / (b.xs - b.ms) * 100) AS satisfaction,
    IF(b.xc = b.mc, 100, (p.community_raw    - b.mc) / (b.xc - b.mc) * 100) AS community
  FROM pilots p CROSS JOIN bounds b
)
SELECT agent_id, name, impact, adoption, satisfaction, community,
       ROUND(0.4 * impact + 0.3 * adoption + 0.2 * satisfaction + 0.1 * community, 1) AS total_score
FROM scaled
ORDER BY total_score DESC;
