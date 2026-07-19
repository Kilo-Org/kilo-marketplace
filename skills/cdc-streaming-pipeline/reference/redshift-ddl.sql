-- Reference Redshift Serverless DDL for the CDC pipeline sink.
--
-- Pattern: append-only event log + materialized "current state" views.
--
-- Why this pattern?
--   * CDC delivery is UNORDERED and may DUPLICATE. Appending is safe
--     under both. Naive in-place upserts are not.
--   * In Aurora DSQL public preview, both INSERT and UPDATE arrive as
--     op="c", so we cannot distinguish them at write time. Window
--     functions on the event log dedupe by primary key + commit
--     timestamp.
--   * The SUPER type lets the same table absorb schema drift from any
--     source table without DDL changes.

-- 1. Append-only CDC event log.
-- Every Kinesis record produces one row here.
CREATE TABLE IF NOT EXISTS cdc_events (
    event_id          BIGINT IDENTITY(1,1) PRIMARY KEY,
    source_table      VARCHAR(100) NOT NULL,
    operation         VARCHAR(10)  NOT NULL,            -- "c", "u", or "d"
    record_id         VARCHAR(50)  NOT NULL,            -- source row primary key
    event_data        SUPER,                             -- full row state for c/u, PK only for d
    commit_timestamp  TIMESTAMP    NOT NULL,             -- source-side commit time
    ingested_at       TIMESTAMP    NOT NULL DEFAULT GETDATE()
)
DISTSTYLE KEY
DISTKEY (record_id)
SORTKEY (source_table, commit_timestamp);

-- Lambda's IAM-mapped database user is auto-created on first
-- redshift-serverless:GetCredentials call. Granting to PUBLIC keeps the
-- demo simple. In production, grant to a specific role created to match
-- the Lambda's IAM identity (typically "IAMR:<role-name>") and drop the
-- PUBLIC grant.
GRANT INSERT, SELECT ON cdc_events TO PUBLIC;

-- 2. Current-state view per source table.
-- Pattern: pick the latest event per record_id; treat "d" as a tombstone.
-- Replace `orders` and the projected fields with whatever the source table
-- carries. Add one of these views per source table.

CREATE OR REPLACE VIEW orders_current AS
SELECT
    record_id                            AS order_id,
    event_data."customer_id"::VARCHAR    AS customer_id,
    event_data."total_cents"::BIGINT     AS total_cents,
    event_data."status"::VARCHAR         AS status,
    event_data."payment_method"::VARCHAR AS payment_method,
    event_data."ship_country"::VARCHAR   AS ship_country,
    commit_timestamp                     AS last_change_at
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY record_id
               ORDER BY commit_timestamp DESC
           ) AS rn
    FROM cdc_events
    WHERE source_table = 'orders'
)
WHERE rn = 1
  AND operation <> 'd';

GRANT SELECT ON orders_current TO PUBLIC;
