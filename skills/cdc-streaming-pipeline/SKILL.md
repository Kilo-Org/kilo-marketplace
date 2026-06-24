---
name: "cdc-streaming-pipeline"
description: "Build a real-time change-data-capture pipeline from a transactional database (Aurora DSQL, Aurora Postgres, RDS) to Redshift Serverless, S3, or any other sink, via Kinesis Data Streams (or MSK). Covers producer setup, consumer Lambda correctness, the append-only event log + reconstruction pattern, schema-drift handling with SUPER + JSON_PARSE, and the operational gotchas (Redshift Data API parameter caps, async statement polling, poison-record handling, retry-and-bisect). Use when the user asks for \"CDC to Redshift\", \"stream change data capture\", \"Aurora CDC\", \"DSQL CDC\", \"Postgres replication to S3\", or \"build a Lambda consumer for Kinesis CDC\". Aurora DSQL public-preview specifics are flagged; the rest is source-agnostic."
metadata:
  category: data
  source:
    repository: "https://github.com/jaingxyz/aws-data-skills"
    path: "skills/cdc-streaming-pipeline"
    license_path: "LICENSE"
---

# CDC streaming pipeline (Kinesis -> Redshift Serverless / S3)

This skill captures the lived patterns for building a real-time CDC pipeline:
a transactional source publishes change events to Kinesis, a Lambda consumer
applies them to a sink (Redshift Serverless event log, or S3 / Iceberg via
Firehose). It is source-agnostic: the producer-side notes are split into
"any CDC source" and "Aurora DSQL preview" callouts.

## When to use

- You are wiring up a CDC pipeline from Aurora DSQL, Aurora Postgres, or RDS
  to Kinesis Data Streams (or MSK) with a Lambda consumer.
- You need to write the consumer Lambda that pushes CDC rows into Redshift
  Serverless via the Redshift Data API.
- You are deciding how to model CDC events at the sink (append-only vs
  in-place upsert, how to absorb schema drift).
- You want the operational gotchas (parameter limits, async statement
  polling, retries, poison records) before you debug them.

## When NOT to use

- You only need the lakehouse / cold-path target (S3 Tables, Iceberg,
  Redshift external schema, federated Glue catalogs). Use the
  `firehose-iceberg-pipeline` and `lakehouse-redshift` skills for those.
- You want generic Redshift Serverless setup unrelated to CDC (workgroup
  sizing, RPU pricing, snapshot policy). Out of scope here.
- You are doing batch ETL / DMS full-load. CDC is for ongoing change
  capture; bulk loads belong elsewhere.
- You need EMR / Glue / Spark transforms inside the stream. This skill
  uses Lambda + Redshift Data API.

If you ARE building the cold path on top of this hot path, ALSO load
`firehose-iceberg-pipeline` (it covers the Firehose -> S3 Tables -> Iceberg
side) and `lakehouse-redshift` (it covers the Redshift external schema +
hot/cold UNION view).

## Architecture in one paragraph

Source DB -> CDC stream (DSQL CDC, DMS, Debezium, or an RDS native CDC
mechanism) -> Kinesis Data Stream -> Lambda event source mapping ->
parameterized INSERTs into a Redshift Serverless append-only `cdc_events`
log table -> per-source-table `*_current` views reconstruct current state
via `ROW_NUMBER() OVER (PARTITION BY pk ORDER BY commit_ts DESC)`.

## 1. The append-only event log + reconstruction pattern

This is the single most important design choice. Use it.

### Why append-only

CDC delivery is **unordered and may duplicate**. Two facts together kill
naive `INSERT ... ON CONFLICT ... UPDATE` upserts:

1. Records can arrive out of commit order (especially across Kinesis
   shards, but also within a shard during retries).
2. The same record can be delivered more than once (Lambda batch retry,
   producer retry, BisectBatchOnFunctionError).

Append-only writes are idempotent under both. Every CDC event becomes a
new row; current state is reconstructed at read time by picking the
latest commit timestamp per primary key. Late-arriving older events are
discarded by the window function, not by re-doing an UPDATE.

### `cdc_events` table DDL (Redshift Serverless)

Generic shape that absorbs any source table by routing all events to a
single SUPER column:

```sql
CREATE TABLE IF NOT EXISTS cdc_events (
    event_id          BIGINT IDENTITY(1,1) PRIMARY KEY,
    source_table      VARCHAR(100) NOT NULL,
    operation         VARCHAR(10)  NOT NULL,    -- "c" or "d"
    record_id         VARCHAR(50)  NOT NULL,    -- source row primary key
    event_data        SUPER,                     -- full row state
    commit_timestamp  TIMESTAMP    NOT NULL,    -- source-side commit time
    ingested_at       TIMESTAMP    NOT NULL DEFAULT GETDATE()
)
DISTSTYLE KEY
DISTKEY (record_id)
SORTKEY (source_table, commit_timestamp);

-- Lambda's IAM-mapped DB user is auto-created on first GetCredentials.
-- Granting to PUBLIC keeps the demo simple. In production, grant to a
-- specific role matching the IAM identity (typically "IAMR:<role-name>")
-- and drop the PUBLIC grant.
GRANT INSERT, SELECT ON cdc_events TO PUBLIC;
```

Why these choices:

- `BIGINT IDENTITY` gives a stable event ordering for debugging without
  participating in correctness (correctness comes from `commit_timestamp`).
- `record_id VARCHAR(50)`: stringify all PKs at the consumer. UUIDs,
  bigints, composite keys all serialize cleanly.
- `event_data SUPER`: lets a single table absorb any source schema. New
  source tables work with zero DDL changes.
- `DISTKEY(record_id)` colocates all events for a given row on the same
  slice, so the `ROW_NUMBER` window in current-state views runs locally.
- `SORTKEY(source_table, commit_timestamp)`: zone maps prune by table
  and time on every per-table view query.

### Current-state view DDL (Redshift Serverless flavor with SUPER)

One view per source table. `event_data."col"::TYPE` is the SUPER subscript
+ cast pattern. (Use the SQL standard cast `::`; `CAST(... AS TYPE)` works
too but is verbose.)

```sql
CREATE OR REPLACE VIEW orders_current AS
SELECT
    record_id                            AS order_id,
    event_data."customer_id"::VARCHAR    AS customer_id,
    event_data."total_cents"::BIGINT     AS total_cents,
    event_data."status"::VARCHAR         AS status,
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
```

Key points:

- Filter `source_table` BEFORE the window function (the planner pushes it
  down; the explicit predicate also keeps zone-map pruning effective).
- `WHERE operation <> 'd'` is the tombstone. Deletes still produce the
  latest event for that PK; the view just hides them.
- The cast `event_data."col"::TYPE` extracts a SUPER field. Quote the
  field name; case-sensitive.

### Aurora DSQL preview gotcha: only `c` and `d` ops

In the DSQL CDC public preview, the `op` field on every event is one of:

- `c` for CREATE (both inserts and updates arrive as `c`)
- `d` for DELETE

There is **no `u` op**. The reconstruction pattern handles this correctly
because the latest `c` per `record_id` wins regardless of whether the
source operation was an insert or an update. Don't write code that special-
cases `op == 'u'`; it will never fire on DSQL today.

For non-DSQL sources (Debezium, DMS), expect `c`, `u`, `d` (and possibly
`r` for snapshot reads). The same `ROW_NUMBER` reconstruction works as
long as you record `commit_timestamp` and treat any of `c | u` as "row
exists with this state".

## 2. Producer-side gotchas

### Aurora DSQL preview: no CFN resource type for the CDC stream

DSQL CDC is in public preview and does NOT yet have a CloudFormation
resource type. You cannot put the CDC stream in a CFN template. Create
it via the AWS CLI (or SDK) AFTER the cluster + Kinesis stream + IAM
role exist:

```bash
aws dsql create-stream \
    --cluster-identifier "${DSQL_CLUSTER_ID}" \
    --target-definition "$(printf '{"kinesis":{"streamArn":"%s","roleArn":"%s"}}' \
        "${KINESIS_STREAM_ARN}" "${DSQL_CDC_ROLE_ARN}")" \
    --ordering UNORDERED \
    --format JSON \
    --region "${AWS_REGION}"
```

Make the script idempotent. Reuse an existing stream rather than failing:

```bash
existing=$(aws dsql list-streams \
    --cluster-identifier "${DSQL_CLUSTER_ID}" \
    --region "${AWS_REGION}" \
    --query 'streams[0].streamIdentifier' \
    --output text 2>/dev/null || true)

if [ -n "${existing}" ] && [ "${existing}" != "None" ]; then
    DSQL_STREAM_ID="${existing}"
else
    DSQL_STREAM_ID=$(aws dsql create-stream ... --query 'streamIdentifier' --output text)
fi

# Wait for ACTIVE before continuing.
for i in $(seq 1 60); do
    status=$(aws dsql get-stream \
        --cluster-identifier "${DSQL_CLUSTER_ID}" \
        --stream-identifier "${DSQL_STREAM_ID}" \
        --region "${AWS_REGION}" \
        --query 'status' --output text)
    case "${status}" in
        ACTIVE) break ;;
        FAILED|DELETING) echo "stream entered ${status}" >&2; exit 1 ;;
        *) sleep 5 ;;
    esac
done
```

The `--ordering UNORDERED` is the documented default. Picking `UNORDERED`
is correct for the append-only pattern; it also gives DSQL the most
freedom to parallelize across shards.

### Trust policy for the DSQL-to-Kinesis role

The CDC stream assumes an IAM role to put records to your Kinesis stream.
That role must trust the `dsql.amazonaws.com` service principal AND the
condition keys must include the cluster's resource ARN so a different
DSQL cluster cannot impersonate yours:

```yaml
DsqlCdcKinesisRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: "2012-10-17"
      Statement:
        - Effect: Allow
          Principal:
            Service: dsql.amazonaws.com
          Action: sts:AssumeRole
          Condition:
            StringEquals:
              "aws:SourceAccount": !Ref AWS::AccountId
            ArnLike:
              # DSQL passes the stream ARN (which lives under the cluster)
              # as aws:SourceArn, NOT the bare cluster ARN. Use ArnLike
              # with the /stream/* suffix so the condition actually matches.
              "aws:SourceArn": !Sub "${DsqlCluster.ResourceArn}/stream/*"
    Policies:
      - PolicyName: PutCdcToKinesis
        PolicyDocument:
          Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - kinesis:PutRecord
                - kinesis:PutRecords
                - kinesis:DescribeStreamSummary
                - kinesis:ListShards
              Resource: !GetAtt CdcStream.Arn
```

### Schema-drift handling: SUPER (or string) at the sink

Source schemas evolve. Two viable strategies:

1. **SUPER column at the sink (recommended).** The Lambda dumps the full
   row payload as JSON into `event_data SUPER`. Downstream views read
   specific fields with `event_data."col"::TYPE`. New columns appear
   automatically; missing columns return NULL when projected.
2. **Stringly-typed VARCHAR(MAX) column.** Same idea, but you `JSON_PARSE`
   at view time. SUPER is preferable: Redshift Serverless plans queries
   over SUPER more efficiently, and the field-extraction syntax is
   shorter.

What this strategy buys you:

- Adding a new source table is a producer-side change only; no Redshift
  DDL required for ingestion. You add a new `*_current` view at your
  leisure.
- Adding a column to an existing source table requires no Redshift DDL.
  Only the affected `*_current` view needs the new column added if you
  want to surface it.

## 3. Lambda consumer correctness patterns

These are non-negotiable. Each one has a "this is what breaks if you
skip it" footnote because each one was earned by debugging.

### 3.1 Parameterized SQL only. Never string-concatenate.

The Redshift Data API supports named parameters. Use them. The CDC payload
contains user-supplied data from the source DB; concatenating it into SQL
is unsafe and wrong, even within an internal pipeline.

```python
def _build_parameterized_insert(rows: list[dict]) -> tuple[str, list[dict]]:
    value_clauses = []
    parameters = []
    for i, r in enumerate(rows):
        # CAST(:ts AS BIGINT) is required: the Data API type-infers numeric
        # parameters as INTEGER, but ms-since-epoch (13 digits) overflows
        # INT4. Dividing by 1000.0 (not 1000) preserves sub-second precision
        # in commit_timestamp; integer division would truncate to whole seconds.
        value_clauses.append(
            f"(:t{i}, :op{i}, :id{i}, JSON_PARSE(:d{i}), "
            f"TIMESTAMP 'epoch' + CAST(:ts{i} AS BIGINT) / 1000.0 * INTERVAL '1 second')"
        )
        parameters.extend([
            {"name": f"t{i}",  "value": r["table"]},
            {"name": f"op{i}", "value": r["op"]},
            {"name": f"id{i}", "value": str(r["record_id"])},
            {"name": f"d{i}",  "value": json.dumps(r["row"])},
            {"name": f"ts{i}", "value": str(r["commit_ts_ms"])},
        ])
    sql = (
        "INSERT INTO cdc_events "
        "(source_table, operation, record_id, event_data, commit_timestamp) "
        f"VALUES {', '.join(value_clauses)}"
    )
    return sql, parameters
```

Two non-obvious bits:

- `JSON_PARSE(:d{i})` converts the JSON string parameter into a SUPER
  value at insert time. Without `JSON_PARSE`, the value would be stored
  as plain text and SUPER subscripting would fail.
- `CAST(:ts{i} AS BIGINT)` is required. The Data API looks at parameter
  values and chooses INT4 by default; 13-digit millisecond timestamps
  silently overflow.

### 3.2 Redshift Data API has a 200-parameter cap. Chunk to stay under it.

The Redshift Data API rejects a single `execute_statement` with more than
200 parameters. With 5 parameters per CDC row, that means at most 40 rows
per statement.

```python
PARAMS_PER_ROW = 5
MAX_PARAMS_PER_STATEMENT = 200
ROWS_PER_CHUNK = int(os.environ.get(
    "ROWS_PER_CHUNK", MAX_PARAMS_PER_STATEMENT // PARAMS_PER_ROW
))  # 40
```

When you raise the per-row parameter count (e.g., adding columns to the
INSERT), `ROWS_PER_CHUNK` MUST come down accordingly. Don't override
`ROWS_PER_CHUNK` higher than `200 // PARAMS_PER_ROW` without revisiting
the math.

If your Kinesis event source mapping has `BatchSize: 100`, the Lambda
receives up to 100 records per invocation. With `ROWS_PER_CHUNK=40`,
that's at most 3 chunks (40 + 40 + 20). The Lambda timeout must cover
the worst case: `ceil(BatchSize / ROWS_PER_CHUNK) * STATEMENT_POLL_TIMEOUT_S`
plus boto3 overhead.

### 3.3 `execute_statement` is async. ALWAYS poll `describe_statement`.

This is the single most dangerous footgun. `redshift-data:ExecuteStatement`
returns a statement ID immediately; the SQL has not run yet. If you don't
poll for completion:

- A FAILED statement looks like a SUCCESS to the Lambda.
- The Lambda returns 200 OK to Kinesis.
- Kinesis advances the iterator past records that never landed in
  Redshift.
- You discover the data loss days later when current-state views are
  missing rows.

The poll loop:

```python
def _await_statement(statement_id: str) -> None:
    deadline = time.monotonic() + STATEMENT_POLL_TIMEOUT_S
    delay = 0.2
    while True:
        resp = redshift.describe_statement(Id=statement_id)
        status = resp.get("Status")
        if status == "FINISHED":
            return
        if status in ("FAILED", "ABORTED"):
            raise RuntimeError(
                f"Redshift statement {statement_id} ended in {status}: "
                f"{resp.get('Error', '<no error message>')}"
            )
        if time.monotonic() > deadline:
            raise RuntimeError(
                f"Redshift statement {statement_id} did not finish within "
                f"{STATEMENT_POLL_TIMEOUT_S}s (last status={status})"
            )
        time.sleep(delay)
        delay = min(delay * 2, 1.0)  # exponential backoff with cap
```

Exponential backoff caps at 1s so a long-running statement doesn't waste
Lambda execution budget on sleeps.

### 3.4 Re-raise on failure. Let Kinesis retry.

When a chunk fails, RAISE. Do not catch and return. The Kinesis event
source mapping treats a Lambda exception as a batch retry signal:

```python
for chunk_index, chunk in enumerate(chunks):
    sql, parameters = _build_parameterized_insert(chunk)
    try:
        response = redshift.execute_statement(
            WorkgroupName=WORKGROUP, Database=DATABASE,
            Sql=sql, Parameters=parameters,
        )
        statement_ids.append(response["Id"])
        _await_statement(response["Id"])
    except Exception:
        logger.exception(
            "Chunk %d/%d failed (already-submitted statement_ids=%s)",
            chunk_index + 1, len(chunks), statement_ids,
        )
        raise  # Kinesis retries the batch.
```

Logging the already-submitted statement IDs before re-raising is
important: on retry, those chunks will be inserted AGAIN. The append-only
pattern absorbs that duplication safely (later reconstruction picks the
latest by `commit_timestamp`), but operators reading CloudWatch logs need
to know what already landed.

### 3.5 Configure `BisectBatchOnFunctionError` and bounded retries

On the EventSourceMapping:

```yaml
CdcEventSource:
  Type: AWS::Lambda::EventSourceMapping
  Properties:
    EventSourceArn: !GetAtt CdcStream.Arn
    FunctionName: !Ref CdcProcessorFunction
    StartingPosition: LATEST
    BatchSize: 100
    MaximumBatchingWindowInSeconds: 5
    MaximumRetryAttempts: 5
    BisectBatchOnFunctionError: true
    Enabled: true
```

What `BisectBatchOnFunctionError: true` buys you: when a batch fails, the
event source mapping retries with each half of the batch separately. A
single poison record gets isolated quickly instead of blocking the entire
batch through `MaximumRetryAttempts` retries.

What `MaximumRetryAttempts: 5` buys you: a record that consistently
fails (truly poisonous, not a transient Redshift hiccup) doesn't block
the shard forever. After 5 attempts the iterator advances. Pair this
with a Dead Letter Queue (`DestinationConfig.OnFailure`) if you want
to inspect what fell off.

### 3.6 Poison-record handling

Poison records: malformed payloads (missing `op`, missing PK, missing
timestamp, undecodable Base64). Handle them BEFORE submitting SQL. A
poison record should be:

1. Logged at WARNING with enough context to identify it (record key,
   approximate position).
2. Counted as `skipped`.
3. Not added to the SQL submission list.

Concretely:

```python
def lambda_handler(event, context):
    rows = []
    skipped = 0
    for record in event.get("Records", []):
        try:
            raw = base64.b64decode(record["kinesis"]["data"])
            payload = json.loads(raw)
        except (KeyError, TypeError, ValueError, binascii.Error) as e:
            logger.error("Failed to decode record: %s", e)
            skipped += 1
            continue

        op = payload.get("op")
        # DSQL preview: only "c" and "d" ops. For non-DSQL sources accept "u" too.
        if op == "c":
            row = payload.get("after")
        elif op == "d":
            row = payload.get("before")
        else:
            logger.warning("Skipping unknown op: %s", op)
            skipped += 1
            continue
        if not row:
            logger.warning("Skipping op=%s with empty row payload", op)
            skipped += 1
            continue

        record_id = row.get("id")
        ts_ms = payload.get("ts_ms")
        if record_id is None or ts_ms is None:
            logger.warning(
                "Skipping op=%s payload with missing id=%r or ts_ms=%r",
                op, record_id, ts_ms,
            )
            skipped += 1
            continue

        rows.append({
            "table": payload.get("source", {}).get("table", "unknown"),
            "op": op,
            "record_id": record_id,
            "row": row,
            "commit_ts_ms": ts_ms,
        })
    # ... chunk + execute + await ...
```

Why not raise on poison records: raising would force Kinesis to retry the
ENTIRE batch including the well-formed records, then bisect, ad infinitum
until `MaximumRetryAttempts` exhausts. The poison record wedges the shard
for minutes. Counting+skipping lets the well-formed records land.

The trade-off: skipped records are lost unless you also write them to an
audit S3 bucket or DLQ. That is acceptable for most CDC pipelines because
truly malformed source data is rare and almost always indicates a producer
bug, not a data-loss event.

## 4. IAM for the consumer Lambda (Redshift Serverless flavor)

The Lambda needs three things:

```yaml
LambdaExecRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Statement:
        - Effect: Allow
          Principal: { Service: lambda.amazonaws.com }
          Action: sts:AssumeRole
    ManagedPolicyArns:
      # Reads from Kinesis + writes CloudWatch logs.
      - arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: RedshiftDataAPI
        PolicyDocument:
          Statement:
            # Redshift Data API actions do NOT support resource-level
            # permissions. Resource: "*" is the only valid value.
            - Effect: Allow
              Action:
                - redshift-data:ExecuteStatement
                - redshift-data:DescribeStatement
                - redshift-data:GetStatementResult
              Resource: "*"
            # IAM auth into the Serverless workgroup, scoped to the
            # workgroup ARN.
            - Effect: Allow
              Action:
                - redshift-serverless:GetCredentials
              Resource: !GetAtt RedshiftWorkgroup.Workgroup.WorkgroupArn
```

Two specifics worth memorizing:

- **Redshift Data API actions don't support resource-level permissions.**
  Trying `Resource: !Sub "arn:aws:redshift-data:..."` will be rejected.
  `Resource: "*"` is the only valid value.
- **`redshift-serverless:GetCredentials`** is what gives the Lambda
  workgroup-level auth. The Data API requires either this for IAM auth or
  a Secrets Manager secret ARN. Prefer IAM auth; less to rotate.

## 5. Schema mapping: SUPER + JSON_PARSE in detail

When the Lambda inserts into `event_data SUPER`, the value passed to the
Data API is a JSON string. `JSON_PARSE` converts it to a SUPER value at
insert time:

```sql
-- INSERT side
INSERT INTO cdc_events (source_table, operation, record_id, event_data, commit_timestamp)
VALUES (:t0, :op0, :id0, JSON_PARSE(:d0), TIMESTAMP 'epoch' + ...);

-- SELECT side: subscript + cast
SELECT
    event_data."customer_id"::VARCHAR AS customer_id,
    event_data."total_cents"::BIGINT  AS total_cents
FROM cdc_events
WHERE source_table = 'orders';
```

A few rules of thumb:

- Quote field names: `event_data."customer_id"`. Without quotes,
  Redshift lowercases the identifier. Source columns are usually
  case-sensitive in JSON, so quoting is the defensive default.
- Cast at projection time: `::VARCHAR`, `::BIGINT`, `::INT`, `::BOOLEAN`,
  `::TIMESTAMP`. Without casts you get SUPER values, which most BI tools
  cannot consume directly.
- Nested fields: `event_data."address"."city"::VARCHAR`. Deeper
  subscripting works.

### Unnesting SUPER arrays with PartiQL

Redshift's PartiQL extension lets you treat a SUPER array as a virtual
table on the right-hand side of `FROM`, joining it row-by-element with
its parent. The pattern is to comma-cross-join the source row with its
array field and bind a per-element alias:

```sql
-- Suppose event_data has a "tags" array, e.g.
--   event_data = {"id": "...", "tags": ["vip","new"]}
SELECT
    e.record_id,
    e.commit_timestamp,
    t::VARCHAR  AS tag
FROM cdc_events AS e, e.event_data."tags" AS t
WHERE e.source_table = 'orders';
```

Output: one row per (event, tag) pair. The `t::VARCHAR` cast produces a
scalar; without it `t` stays SUPER.

For arrays of objects:

```sql
-- event_data = {"id": "...", "items": [{"sku":"A","qty":2}, ...]}
SELECT
    e.record_id,
    item."sku"::VARCHAR AS sku,
    item."qty"::INT     AS qty
FROM cdc_events AS e, e.event_data."items" AS item
WHERE e.source_table = 'orders';
```

Two requirements specific to PartiQL on Redshift:

- The session must enable case-sensitive identifiers when subscripting
  mixed-case JSON keys: `SET enable_case_sensitive_identifier TO TRUE;`
  (set this once per session, or use unquoted lowercase keys only).
- PartiQL unnesting works inside views too. Combine it with
  `WITH NO SCHEMA BINDING` if the view also references external Iceberg
  tables; see the `lakehouse-redshift` skill.

If you only need a single element by index, no unnest required:
`event_data."tags"[0]::VARCHAR`.

### When NOT to use SUPER

If your source schema is fixed and small, plain typed columns are
simpler and faster to query. SUPER's value comes from schema-drift
absorption; if there is no drift, you are paying SUPER's small overhead
for nothing.

## 6. Cross-references

- **Cold path / lakehouse target.** If you are also archiving CDC events
  to S3 Tables (Iceberg) for long retention or larger time-window
  analytics, ALSO load `firehose-iceberg-pipeline` (it covers Firehose
  with `IcebergDestinationConfiguration`, the transform Lambda you'll
  need because Firehose maps top-level JSON keys to Iceberg columns by
  name, and the two-phase CFN deploy required because Firehose validates
  the destination Iceberg table synchronously at create time).

- **Querying hot+cold together from Redshift Serverless.** ALSO load
  `lakehouse-redshift` for the external schema setup, the LF
  access-control mode requirement, the bucket-nested federated catalog
  ARN format, and the `WITH NO SCHEMA BINDING` view trick.

- **DSQL specifics beyond CDC.** If the user is also writing migrations
  or DDL for the source DSQL cluster, the `dsql` skill (from the
  `databases-on-aws` plugin) covers DSQL-compatible SQL and `dsql_lint`.

## Reference material

- `reference/event-source-mapping.yaml` - full CFN snippet for the
  Kinesis EventSourceMapping with all the safety knobs set.
- `reference/lambda-consumer.py` - a complete, working consumer Lambda
  that implements every pattern above.
- `reference/redshift-ddl.sql` - the `cdc_events` table + a worked
  `*_current` view example with grants.
