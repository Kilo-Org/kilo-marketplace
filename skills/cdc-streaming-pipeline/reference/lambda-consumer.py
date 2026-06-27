"""
Reference CDC consumer Lambda.

Reads CDC events from a Kinesis Data Stream and appends them to a Redshift
Serverless `cdc_events` log table via the Redshift Data API. Downstream
*_current views materialize current state from this append-only log.

Design choices, in order of importance:

  1. Append-only writes. Safe under unordered or duplicate Kinesis delivery.
     Reconstruction picks the latest event per primary key by commit
     timestamp at view time.

  2. Single sink table for all source tables. SUPER (event_data) absorbs
     schema drift; new source tables work with zero code changes.

  3. Aurora DSQL preview compat: only "c" and "d" ops. Both INSERT and
     UPDATE arrive as "c". The reconstruction view treats the latest "c"
     per record_id as current state regardless. For non-DSQL sources
     (Debezium, DMS) "u" is also accepted; the same INSERT path handles it.

  4. Parameterized SQL only. All CDC values pass through Redshift Data API
     named parameters. No string concatenation. Robust against unusual
     values in source data and the standard defense against SQL injection.

  5. Chunking. Redshift Data API caps a single execute_statement at 200
     parameters. With 5 parameters per row, batches of 40 rows max.

  6. Synchronous status check. execute_statement is async. Poll
     describe_statement until each chunk reaches FINISHED. FAILED or
     ABORTED raises a real Lambda error so the Kinesis EventSourceMapping
     retries the batch instead of silently checkpointing past lost data.

  7. Poison-record handling. Malformed payloads (missing op, missing PK,
     missing timestamp, undecodable data) are counted as `skipped` and
     logged at WARNING. They do not advance to the SQL submission step
     and do not raise (raising would block the shard on truly bad data).

Environment variables:
  REDSHIFT_WORKGROUP        Serverless workgroup name (e.g. "default-workgroup")
  REDSHIFT_DATABASE         Database name (e.g. "dev")
  ROWS_PER_CHUNK            Optional override for rows-per-statement (default 40)
  STATEMENT_POLL_TIMEOUT_S  Optional cap on per-chunk poll wait (default 25s)
"""

import base64
import binascii
import json
import logging
import os
import time

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

redshift = boto3.client("redshift-data")

WORKGROUP = os.environ["REDSHIFT_WORKGROUP"]
DATABASE = os.environ["REDSHIFT_DATABASE"]

PARAMS_PER_ROW = 5
MAX_PARAMS_PER_STATEMENT = 200
ROWS_PER_CHUNK = int(
    os.environ.get("ROWS_PER_CHUNK", MAX_PARAMS_PER_STATEMENT // PARAMS_PER_ROW)
)
STATEMENT_POLL_TIMEOUT_S = int(os.environ.get("STATEMENT_POLL_TIMEOUT_S", 25))


def _row_for_op(payload: dict):
    """Extract (op, row_dict) from a CDC payload, or None if unprocessable.

    Accepts c | u | d. DSQL preview will only ever produce c | d; non-DSQL
    sources may emit u. The downstream INSERT path is identical for c and u
    because both represent "row exists with this state at commit_timestamp".
    """
    op = payload.get("op")
    if op in ("c", "u"):
        row = payload.get("after")
    elif op == "d":
        row = payload.get("before")
    else:
        logger.warning("Skipping unknown op: %s", op)
        return None
    if not row:
        # A "d" event with no `before` block has no PK to tombstone with;
        # a "c"/"u" event with no `after` is malformed. Treat both as poison.
        logger.warning("Skipping op=%s with empty row payload", op)
        return None
    return (op, row)


def _build_parameterized_insert(rows: list[dict]) -> tuple[str, list[dict]]:
    """Build a multi-row INSERT with Redshift Data API named parameters.

    Returns (sql_string, parameters_list).
    """
    value_clauses = []
    parameters = []

    for i, r in enumerate(rows):
        # CAST(:ts AS BIGINT) is required: the Redshift Data API type-infers
        # numeric parameters as INTEGER, but DSQL CDC commit timestamps are
        # millisecond-since-epoch (13 digits) and overflow INT4. Dividing
        # by 1000.0 (not 1000) preserves sub-second precision in
        # commit_timestamp; integer division would truncate to whole seconds.
        value_clauses.append(
            f"(:t{i}, :op{i}, :id{i}, JSON_PARSE(:d{i}), "
            f"TIMESTAMP 'epoch' + CAST(:ts{i} AS BIGINT) / 1000.0 * INTERVAL '1 second')"
        )
        parameters.extend(
            [
                {"name": f"t{i}", "value": r["table"]},
                {"name": f"op{i}", "value": r["op"]},
                {"name": f"id{i}", "value": str(r["record_id"])},
                {"name": f"d{i}", "value": json.dumps(r["row"])},
                {"name": f"ts{i}", "value": str(r["commit_ts_ms"])},
            ]
        )

    sql = (
        "INSERT INTO cdc_events "
        "(source_table, operation, record_id, event_data, commit_timestamp) "
        f"VALUES {', '.join(value_clauses)}"
    )
    return sql, parameters


def _chunked(items: list, size: int):
    """Yield successive `size`-sized chunks from `items`."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _await_statement(statement_id: str) -> None:
    """Poll describe_statement until FINISHED; raise on FAILED, ABORTED, or timeout."""
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
        delay = min(delay * 2, 1.0)


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

        result = _row_for_op(payload)
        if not result:
            skipped += 1
            continue
        op, row = result

        record_id = row.get("id")
        ts_ms = payload.get("ts_ms")
        if record_id is None or ts_ms is None:
            # Skip rows without a PK or commit timestamp rather than
            # inserting record_id='' or commit_timestamp=1970-01-01.
            logger.warning(
                "Skipping op=%s payload with missing id=%r or ts_ms=%r",
                op,
                record_id,
                ts_ms,
            )
            skipped += 1
            continue

        source = payload.get("source", {})
        rows.append(
            {
                "table": source.get("table", "unknown"),
                "op": op,
                "record_id": record_id,
                "row": row,
                "commit_ts_ms": ts_ms,
            }
        )

    if not rows:
        logger.info("No processable records (skipped=%d)", skipped)
        return {"processed": 0, "skipped": skipped}

    statement_ids = []
    chunks = list(_chunked(rows, ROWS_PER_CHUNK))
    for chunk_index, chunk in enumerate(chunks):
        sql, parameters = _build_parameterized_insert(chunk)
        try:
            response = redshift.execute_statement(
                WorkgroupName=WORKGROUP,
                Database=DATABASE,
                Sql=sql,
                Parameters=parameters,
            )
            statement_id = response["Id"]
            statement_ids.append(statement_id)
            _await_statement(statement_id)
        except Exception:
            # Re-raise so Kinesis event source mapping retries the batch
            # (with BisectBatchOnFunctionError isolating the bad records).
            # `submitted_chunks` lets the operator see in CloudWatch logs
            # how many chunks already landed so they can reason about
            # potential duplicates on retry. The append-only design
            # absorbs the duplication safely.
            logger.exception(
                "Chunk %d/%d failed (already-submitted statement_ids=%s)",
                chunk_index + 1,
                len(chunks),
                statement_ids,
            )
            raise

    logger.info(
        "Wrote %d rows in %d chunks to Redshift (skipped=%d)",
        len(rows),
        len(statement_ids),
        skipped,
    )
    return {
        "processed": len(rows),
        "skipped": skipped,
        "chunks": len(statement_ids),
        "statement_ids": statement_ids,
    }
