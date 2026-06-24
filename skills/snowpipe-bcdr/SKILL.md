---
name: "snowpipe-bcdr"
description: "Use when designing or operating Snowpipe disaster recovery on Azure ADLS Gen2 — choosing between dual-pipe, RA-GRS, active-active, or Failover Group patterns, and running failover/failback/catchup. Triggers: snowpipe BCDR, snowpipe disaster recovery, snowpipe failover, dual pipe, active-active pipe, RA-GRS snowpipe, GZRS snowpipe, snowpipe catchup, pipe failback, snowpipe high availability, failover group snowpipe, snowpipe RPO RTO."
metadata:
  category: data
  source:
    repository: "https://github.com/Snowflake-Labs/coco-skills"
    path: "skills/snowpipe-bcdr"
    license_path: "skills/snowpipe-bcdr/LICENSE"
---

# Snowpipe BCDR on Azure

## Overview

This skill helps developers and data engineers design, implement, and operate Snowpipe business continuity / disaster recovery on **Azure ADLS Gen2**. Six patterns are supported — pick one based on your RPO, RTO, edition, and cost tolerance.

| # | Pattern | RPO | RTO | Cost | Complexity |
|---|---------|-----|-----|------|------------|
| 1 | Manual Catchup (single pipe) | Min–hrs | 30–90 min | Lowest | Low |
| 2 | Active-Active + Dedup | Zero | ~1 min | Highest | High |
| 3 | RA-GRS Read Pattern | Near-zero | 5–15 min | Medium | Medium |
| 4 | Active-Passive (SF + GRS) | Near-zero | 5–15 min | Medium | Medium |
| 5 | Snowflake-Only Failover Group | Near-zero | 5–15 min | Low–Med | Low |
| 6 | Dual Storage, Dual Pipes | Near-zero | 5–10 min | Medium | Medium |

Options 2–6 require **Business Critical Edition** for Failover Groups. On lower editions, only Option 1 applies.

## Decision

```
Business Critical?
├── No → Option 1
└── Yes
    ├── Zero data loss?           → Option 2
    ├── Azure is the failure?     → Option 4 or 6
    ├── Snowflake is the failure? → Option 5
    ├── Have RA-GRS?              → Option 3
    └── Budget constrained?       → Option 1 or 5
```

This skill is **Azure ADLS Gen2 only**. AWS S3 / GCS variants are out of scope.

## Core Rules

1. **Single writer per file set.** Only one pipe active per file set, except Option 2 (which dedups).
2. **Storage integration must allow both URLs:**
   ```sql
   STORAGE_ALLOWED_LOCATIONS = (
     'azure://<primary>.blob.core.windows.net/<container>/',
     'azure://<secondary>.blob.core.windows.net/<container>/'
   );
   ```
3. **`COPY_HISTORY` is replicated** in Failover Groups but only retains 14 days. For longer history, maintain a `FILE_LOAD_HISTORY` backup table.
4. **`ALTER PIPE ... REFRESH` is hard-capped at 7 days.** For older files, use `DIRECTORY(@stage)` + `COPY INTO`.
5. **Inbound notification integrations (`DIRECTION = INBOUND`) do NOT replicate.** After failover-group promotion you must recreate them with the same name in the DR account, re-establish Service Principal trust, and create the DR-region Event Grid subscription.

## Workflow

### Step 1 — Confirm prerequisites
- Edition (Business Critical for Options 2–6)
- Azure storage type (LRS / GRS / RA-GRS / GZRS / RA-GZRS)
- Event Grid + Storage Queue exists in target regions

### Step 2 — Implement chosen option

Each option follows the same shape: storage integration → stage → pipe (with `AUTO_INGEST=TRUE` and notification integration) → monitoring views → catchup procedure.

**Option 2 dedup hash columns:**
```sql
MD5(METADATA$FILENAME)                          AS FILE_HASH,
MD5(CONCAT_WS('|', $1, $2, $3, $4, $5))         AS RECORD_HASH,
'PRIMARY'                                       AS SOURCE_REGION
```
Dedup with a Dynamic Table: `QUALIFY ROW_NUMBER() OVER (PARTITION BY FILE_HASH, RECORD_HASH ORDER BY LOAD_TIMESTAMP) = 1`.

**Option 6 dual pipe pattern:**
```sql
CREATE PIPE PIPE_PRIMARY   AUTO_INGEST=TRUE INTEGRATION='NOTIF_INT_A' AS
  COPY INTO TARGET_TABLE (..., 'PRIMARY' AS _source_region)   FROM @STAGE_PRIMARY;
CREATE PIPE PIPE_SECONDARY AUTO_INGEST=TRUE INTEGRATION='NOTIF_INT_B' AS
  COPY INTO TARGET_TABLE (..., 'SECONDARY' AS _source_region) FROM @STAGE_SECONDARY;
ALTER PIPE PIPE_SECONDARY SET PIPE_EXECUTION_PAUSED = TRUE;
```

⚠️ STOPPING POINT: Show planned `CREATE STORAGE INTEGRATION`, `CREATE PIPE`, and `ALTER FAILOVER GROUP` statements to the user and wait for approval before executing.

### Step 3 — Validate

```sql
SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('pipe_name')):executionState::STRING  AS state,
       PARSE_JSON(SYSTEM$PIPE_STATUS('pipe_name')):pendingFileCount::NUMBER AS pending;
```

Monitor pending files (`>1000` for `>15 min`), error rate from `SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY` (`>5%/hr`), and load latency (`>30 min`).

### Step 4 — Failover / failback / catchup

```sql
ALTER PIPE pipe_primary   SET PIPE_EXECUTION_PAUSED = TRUE;
-- record checkpoint from COPY_HISTORY
ALTER PIPE pipe_secondary SET PIPE_EXECUTION_PAUSED = FALSE;
ALTER PIPE pipe_secondary REFRESH MODIFIED_AFTER = '<checkpoint-15min>';
```

⚠️ STOPPING POINT: Confirm the failover decision and the checkpoint timestamp with the user before pausing the primary pipe.

Catchup choices: `ALTER PIPE … REFRESH` (≤7 days), `COPY INTO … FROM @stage` (any age), or a cursor proc that diffs `DIRECTORY(@stage)` against `COPY_HISTORY` for an audit trail.

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Both pipes running | Duplicate loads | Pause standby; use a failover proc |
| Secondary URL missing from integration | `ACCESS_DENIED` on failover | Recreate integration with both URLs |
| Relying on `COPY_HISTORY` past 14 days | Catchup finds nothing | Maintain `FILE_LOAD_HISTORY` table |
| No DR Event Grid subscription | `pendingFileCount = 0` post-failover | Create matching Event Grid + queue in DR region |
| `PIPE REFRESH` for old files | Files >7 days skipped silently | Switch to `DIRECTORY(@stage)` + `COPY INTO` |
| Pipe recreated without `AUTO_INGEST=TRUE` | Pipe stops auto-loading | Include `AUTO_INGEST=TRUE` and `INTEGRATION=` |
| Inbound notification integration not recreated post-failover | Pipe healthy but `pendingFileCount=0` | Recreate `DIRECTION=INBOUND` integration in DR account, re-grant Service Principal |

## Stopping Points

- Step 2 — wait for approval before running `CREATE`/`ALTER` for storage integrations, pipes, and failover groups.
- Step 4 — confirm the failover decision and checkpoint timestamp before pausing the active pipe.

## References

- [Stage, Pipe, and Load History Replication](https://docs.snowflake.com/en/user-guide/account-replication-stages-pipes-load-history)
- [Automating Snowpipe for Azure Blob Storage](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-auto-azure)
