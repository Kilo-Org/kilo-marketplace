# Amazon Redshift Diagnostics Reference

## Cluster Health and Status

### 1. Current Cluster Configuration

```sql
SELECT
    node_type,
    node_count,
    estimated_disk_utilization_pct
FROM STV_NODE_STORAGE_CAPACITY
LIMIT 1;
```

### 2. Node Status

```sql
SELECT node, is_diskfull, IS_HEALTHY
FROM STV_NODE_STORAGE_CAPACITY;
```

### 3. Cluster Version

```sql
SELECT version();
```

### 4. Current Database Connections

```sql
SELECT
    usename,
    COUNT(*) AS connection_count,
    SUM(CASE WHEN query != '' AND query NOT LIKE 'DEALLOCATE%' THEN 1 ELSE 0 END) AS active_queries
FROM pg_stat_activity
GROUP BY usename
ORDER BY connection_count DESC;
```

### 5. Connection Details

```sql
SELECT
    pid,
    usename,
    datname,
    client_addr,
    query_start,
    DATEDIFF(second, query_start, GETDATE()) AS query_duration_sec,
    LEFT(query, 100) AS query_preview
FROM pg_stat_activity
WHERE usename != 'rdsdb'
ORDER BY query_start;
```

### 6. Kill a Running Query

```sql
SELECT pg_cancel_backend(<pid>);   -- Graceful cancel
SELECT pg_terminate_backend(<pid>); -- Force terminate
```

### 7. Disk Space by Node

```sql
SELECT
    owner AS node,
    diskno,
    used,
    capacity,
    ROUND(used::FLOAT / capacity * 100, 2) AS pct_used
FROM STV_PARTITIONS
WHERE part_begin = 0
ORDER BY owner, diskno;
```

### 8. Overall Disk Space Summary

```sql
SELECT
    SUM(used) AS total_used_mb,
    SUM(capacity) AS total_capacity_mb,
    ROUND(SUM(used)::FLOAT / SUM(capacity) * 100, 2) AS pct_used
FROM STV_PARTITIONS
WHERE part_begin = 0;
```

### 9. Node Slice Mapping

```sql
SELECT node, slice, type
FROM STV_SLICES
ORDER BY node, slice;
```

## Query History and Performance

### 10. Recent Query History (SYS View -- Recommended)

```sql
SELECT
    query_id,
    user_id,
    database_name,
    query_type,
    status,
    start_time,
    end_time,
    elapsed_time / 1000000.0 AS duration_sec,
    queue_time / 1000000.0 AS queue_sec,
    execution_time / 1000000.0 AS exec_sec,
    returned_rows,
    returned_bytes,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
ORDER BY start_time DESC
LIMIT 50;
```

### 11. Recent Query History (STL -- Legacy)

```sql
SELECT
    query,
    userid,
    database,
    starttime,
    endtime,
    DATEDIFF(second, starttime, endtime) AS duration_sec,
    aborted,
    label,
    LEFT(querytxt, 200) AS query_preview
FROM STL_QUERY
WHERE userid > 1  -- Exclude system user
ORDER BY starttime DESC
LIMIT 50;
```

### 12. Full Query Text for a Specific Query

```sql
SELECT
    query,
    sequence,
    text
FROM STL_QUERYTEXT
WHERE query = <query_id>
ORDER BY sequence;
```

### 13. Top 20 Longest-Running Queries (Last 24 Hours)

```sql
SELECT
    query_id,
    user_id,
    query_type,
    status,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    queue_time / 1000000.0 AS queue_sec,
    returned_rows,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE start_time >= DATEADD(hour, -24, GETDATE())
  AND status = 'success'
ORDER BY elapsed_time DESC
LIMIT 20;
```

### 14. Top 20 Most Resource-Intensive Queries

```sql
SELECT
    q.query,
    q.userid,
    DATEDIFF(second, q.starttime, q.endtime) AS duration_sec,
    qs.cpu_time / 1000000 AS cpu_sec,
    qs.blocks_read,
    qs.run_time / 1000000 AS exec_sec,
    LEFT(q.querytxt, 200) AS query_preview
FROM STL_QUERY q
JOIN (
    SELECT query, SUM(cpu_time) AS cpu_time, SUM(blocks_read) AS blocks_read, SUM(run_time) AS run_time
    FROM SVL_QUERY_SUMMARY
    GROUP BY query
) qs ON q.query = qs.query
WHERE q.starttime >= DATEADD(hour, -24, GETDATE())
  AND q.userid > 1
ORDER BY qs.cpu_time DESC
LIMIT 20;
```

### 15. Failed/Aborted Queries

```sql
SELECT
    query_id,
    user_id,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    status,
    error_message,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE status IN ('failed', 'canceled')
  AND start_time >= DATEADD(hour, -24, GETDATE())
ORDER BY start_time DESC
LIMIT 50;
```

### 16. Query Execution Steps Detail (SYS View)

```sql
SELECT
    query_id,
    step_name,
    segment_id,
    step_id,
    duration / 1000000.0 AS step_duration_sec,
    input_rows,
    output_rows,
    input_bytes,
    output_bytes,
    blocks_read,
    blocks_write,
    label
FROM SYS_QUERY_DETAIL
WHERE query_id = <query_id>
ORDER BY segment_id, step_id;
```

### 17. Query Plan Summary (SVL)

```sql
SELECT
    query,
    stm,
    seg,
    step,
    label,
    rows,
    bytes,
    maxtime,
    avgtime,
    is_diskbased,
    workmem
FROM SVL_QUERY_SUMMARY
WHERE query = <query_id>
ORDER BY stm, seg, step;
```

### 18. Disk-Based Query Steps (Spilling to Disk)

```sql
SELECT
    query,
    stm,
    seg,
    step,
    label,
    rows,
    bytes,
    maxtime,
    workmem,
    is_diskbased
FROM SVL_QUERY_SUMMARY
WHERE is_diskbased = 't'
  AND query IN (
      SELECT query FROM STL_QUERY
      WHERE starttime >= DATEADD(hour, -24, GETDATE())
      AND userid > 1
  )
ORDER BY maxtime DESC
LIMIT 50;
```

### 19. Query Compilation Cache

```sql
SELECT
    query,
    segment,
    compile,
    DATEDIFF(microsecond, starttime, endtime) / 1000.0 AS compile_ms
FROM SVL_COMPILE
WHERE query = <query_id>
ORDER BY segment;
```

### 20. Queries with High Compilation Overhead

```sql
SELECT
    c.query,
    COUNT(*) AS segments,
    SUM(CASE WHEN c.compile = 1 THEN 1 ELSE 0 END) AS compiled_segments,
    SUM(DATEDIFF(microsecond, c.starttime, c.endtime)) / 1000.0 AS total_compile_ms,
    LEFT(q.querytxt, 200) AS query_preview
FROM SVL_COMPILE c
JOIN STL_QUERY q ON c.query = q.query
WHERE c.starttime >= DATEADD(hour, -24, GETDATE())
  AND c.compile = 1
GROUP BY c.query, q.querytxt
ORDER BY total_compile_ms DESC
LIMIT 20;
```

### 21. Result Cache Hit Ratio

```sql
SELECT
    COUNT(CASE WHEN source_query IS NOT NULL THEN 1 END) AS cache_hits,
    COUNT(*) AS total_queries,
    ROUND(COUNT(CASE WHEN source_query IS NOT NULL THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100, 2) AS cache_hit_pct
FROM SYS_QUERY_HISTORY
WHERE start_time >= DATEADD(hour, -24, GETDATE())
  AND query_type = 'SELECT';
```

## Alert Events and Query Diagnostics

### 22. Alert Event Log (Performance Warnings)

```sql
SELECT
    event_time,
    query,
    event,
    solution,
    LEFT(event, 100) AS alert_summary
FROM STL_ALERT_EVENT_LOG
WHERE event_time >= DATEADD(hour, -24, GETDATE())
ORDER BY event_time DESC
LIMIT 50;
```

### 23. Most Common Alerts

```sql
SELECT
    event,
    solution,
    COUNT(*) AS occurrences,
    COUNT(DISTINCT query) AS unique_queries
FROM STL_ALERT_EVENT_LOG
WHERE event_time >= DATEADD(hour, -24, GETDATE())
GROUP BY event, solution
ORDER BY occurrences DESC
LIMIT 20;
```

### 24. Queries Generating Alerts

```sql
SELECT
    a.query,
    q.userid,
    a.event,
    a.solution,
    DATEDIFF(second, q.starttime, q.endtime) AS duration_sec,
    LEFT(q.querytxt, 200) AS query_preview
FROM STL_ALERT_EVENT_LOG a
JOIN STL_QUERY q ON a.query = q.query
WHERE a.event_time >= DATEADD(hour, -24, GETDATE())
ORDER BY duration_sec DESC
LIMIT 30;
```

### 25. Nested Loop Join Alerts (Major Red Flag)

```sql
SELECT
    a.query,
    q.starttime,
    DATEDIFF(second, q.starttime, q.endtime) AS duration_sec,
    a.event,
    LEFT(q.querytxt, 300) AS query_text
FROM STL_ALERT_EVENT_LOG a
JOIN STL_QUERY q ON a.query = q.query
WHERE a.event LIKE '%Nested Loop%'
  AND a.event_time >= DATEADD(day, -7, GETDATE())
ORDER BY q.starttime DESC;
```

### 26. Very Selective Filter Alerts (Possible Missing Sort Key)

```sql
SELECT
    a.query,
    a.event,
    a.solution,
    LEFT(q.querytxt, 200) AS query_preview
FROM STL_ALERT_EVENT_LOG a
JOIN STL_QUERY q ON a.query = q.query
WHERE a.event LIKE '%very selective filter%'
  AND a.event_time >= DATEADD(day, -7, GETDATE())
ORDER BY a.event_time DESC
LIMIT 20;
```

## Table Design Analysis

### 27. Comprehensive Table Information

```sql
SELECT
    "database",
    "schema",
    "table",
    diststyle,
    sortkey1,
    sortkey_num,
    sortkey1_enc,
    size AS size_mb,
    pct_used,
    tbl_rows,
    unsorted,
    stats_off,
    skew_rows,
    skew_sortkey1,
    encoded
FROM SVV_TABLE_INFO
WHERE "schema" != 'pg_internal'
ORDER BY size DESC;
```

### 28. Tables with High Unsorted Percentage (Need VACUUM SORT)

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    unsorted,
    sortkey1,
    diststyle
FROM SVV_TABLE_INFO
WHERE unsorted > 20
  AND tbl_rows > 100000
ORDER BY unsorted DESC;
```

### 29. Tables with High Row Skew (Distribution Problem)

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    diststyle,
    sortkey1,
    skew_rows,
    skew_sortkey1
FROM SVV_TABLE_INFO
WHERE skew_rows > 2.0
  AND tbl_rows > 100000
ORDER BY skew_rows DESC;
```

### 30. Tables with Stale Statistics

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    stats_off,
    size AS size_mb
FROM SVV_TABLE_INFO
WHERE stats_off > 10
  AND tbl_rows > 100000
ORDER BY stats_off DESC;
```

### 31. Distribution Key Effectiveness

```sql
SELECT
    ti."table",
    ti.diststyle,
    ti.skew_rows,
    ti.tbl_rows,
    ti.size AS size_mb,
    c.column_name AS distkey_column,
    COUNT(DISTINCT t.attval) AS distkey_ndv
FROM SVV_TABLE_INFO ti
JOIN (
    SELECT attrelid::regclass::text AS tablename, attname AS column_name
    FROM pg_attribute
    WHERE attisdistkey = 't'
) c ON ti."table" = c.tablename
LEFT JOIN (
    SELECT tablename, attval
    FROM (SELECT 1 AS attval) -- placeholder; actual NDV requires sampling
) t ON 1=0
WHERE ti.diststyle LIKE 'KEY%'
GROUP BY ti."table", ti.diststyle, ti.skew_rows, ti.tbl_rows, ti.size, c.column_name
ORDER BY ti.skew_rows DESC;
```

### 32. Identify Tables Missing Sort Keys

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    diststyle,
    sortkey_num
FROM SVV_TABLE_INFO
WHERE sortkey_num = 0
  AND tbl_rows > 1000000
ORDER BY tbl_rows DESC;
```

### 33. Identify Tables Missing Compression

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    encoded
FROM SVV_TABLE_INFO
WHERE encoded = 'N'
  AND tbl_rows > 100000
ORDER BY size DESC;
```

### 34. Column-Level Encoding Analysis

```sql
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    a.attname AS column_name,
    format_type(a.atttypid, a.atttypmod) AS data_type,
    format_encoding(a.attencodingtype::INTEGER) AS encoding,
    a.attisdistkey AS is_distkey,
    a.attsortkeyord AS sortkey_position
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'public'
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY c.relname, a.attnum;
```

### 35. ANALYZE COMPRESSION Recommendation

```sql
ANALYZE COMPRESSION public.orders;
```

### 36. Automatic Table Optimization Recommendations

```sql
SELECT
    type,
    database,
    schema,
    "table",
    ranking_info,
    condition,
    recommended_action
FROM SVV_ALTER_TABLE_RECOMMENDATIONS
ORDER BY ranking_info;
```

### 37. Table Rows vs Storage Efficiency

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    CASE WHEN tbl_rows > 0
         THEN ROUND(size::FLOAT * 1024 * 1024 / tbl_rows, 2)
         ELSE 0
    END AS bytes_per_row,
    sortkey1,
    diststyle,
    encoded
FROM SVV_TABLE_INFO
WHERE tbl_rows > 0
ORDER BY bytes_per_row DESC
LIMIT 30;
```

## Storage and Disk Usage

### 38. Disk Usage by Table (SVV_DISKUSAGE)

```sql
SELECT
    name AS table_name,
    owner,
    SUM(num_values) AS total_values,
    SUM(size) AS total_blocks,
    SUM(size) AS total_mb
FROM SVV_DISKUSAGE
GROUP BY name, owner
ORDER BY total_mb DESC
LIMIT 30;
```

### 39. Disk Usage by Schema

```sql
SELECT
    ti."schema",
    COUNT(*) AS table_count,
    SUM(ti.size) AS total_mb,
    ROUND(SUM(ti.size) / 1024.0, 2) AS total_gb,
    SUM(ti.tbl_rows) AS total_rows
FROM SVV_TABLE_INFO ti
GROUP BY ti."schema"
ORDER BY total_mb DESC;
```

### 40. Per-Column Storage Size

```sql
SELECT
    TRIM(name) AS table_name,
    TRIM(col) AS column_name,
    col AS col_num,
    SUM(num_values) AS row_count,
    SUM(size) AS disk_blocks,
    ROUND(SUM(size)::FLOAT / NULLIF(SUM(num_values), 0) * 1024 * 1024, 2) AS avg_bytes_per_value
FROM SVV_DISKUSAGE
WHERE TRIM(name) = 'orders'
GROUP BY name, col
ORDER BY disk_blocks DESC;
```

### 41. Tables with Deleted Rows (Need VACUUM DELETE)

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    CASE WHEN tbl_rows > 0 THEN
        ROUND((size * 1.0 / (SELECT MAX(size) FROM SVV_TABLE_INFO WHERE tbl_rows > 0 AND "table" = t."table")) * 100, 2)
    ELSE 0 END AS pct_estimate
FROM SVV_TABLE_INFO t
WHERE size > 100
ORDER BY size DESC
LIMIT 20;
```

### 42. Ghost Row Count (Deleted But Not Vacuumed)

```sql
SELECT
    "schema",
    "table",
    tbl_rows AS live_rows,
    size AS size_mb,
    ROUND(unsorted, 2) AS unsorted_pct
FROM SVV_TABLE_INFO
WHERE unsorted > 0 OR size > 1000
ORDER BY size DESC
LIMIT 30;
```

## Scan and Distribution Analysis

### 43. Table Scan Statistics

```sql
SELECT
    query,
    tbl,
    TRIM(tbl_name) AS table_name,
    type,
    rows,
    bytes,
    perm_table_name
FROM STL_SCAN
WHERE query = <query_id>
  AND type IN (1, 2)  -- 1=user table, 2=user temp table
ORDER BY rows DESC;
```

### 44. Data Redistribution Statistics

```sql
SELECT
    query,
    tbl,
    slice,
    type,
    rows,
    bytes
FROM STL_DIST
WHERE query = <query_id>
ORDER BY bytes DESC;
```

### 45. Queries with Heavy Redistribution (Last 24h)

```sql
SELECT
    d.query,
    SUM(d.rows) AS total_redistributed_rows,
    SUM(d.bytes) AS total_redistributed_bytes,
    LEFT(q.querytxt, 200) AS query_preview
FROM STL_DIST d
JOIN STL_QUERY q ON d.query = q.query
WHERE q.starttime >= DATEADD(hour, -24, GETDATE())
  AND q.userid > 1
GROUP BY d.query, q.querytxt
ORDER BY total_redistributed_bytes DESC
LIMIT 20;
```

### 46. Sort Operations Statistics

```sql
SELECT
    query,
    tbl,
    rows,
    bytes,
    DATEDIFF(microsecond, starttime, endtime) / 1000.0 AS sort_ms,
    is_diskbased
FROM STL_SORT
WHERE query = <query_id>
ORDER BY sort_ms DESC;
```

### 47. Disk-Based Sorts (Memory Spilling)

```sql
SELECT
    s.query,
    s.tbl,
    s.rows,
    s.bytes,
    DATEDIFF(microsecond, s.starttime, s.endtime) / 1000.0 AS sort_ms,
    LEFT(q.querytxt, 200) AS query_preview
FROM STL_SORT s
JOIN STL_QUERY q ON s.query = q.query
WHERE s.is_diskbased = 't'
  AND s.starttime >= DATEADD(hour, -24, GETDATE())
ORDER BY sort_ms DESC
LIMIT 20;
```

## Workload Management (WLM)

### 48. WLM Queue Configuration

```sql
SELECT
    service_class,
    name,
    num_query_tasks AS concurrency,
    query_working_mem AS memory_mb,
    max_execution_time,
    user_group_wild_card,
    query_group_wild_card
FROM STV_WLM_SERVICE_CLASS_CONFIG
WHERE service_class >= 5  -- User-defined queues start at 5
ORDER BY service_class;
```

### 49. Current WLM Queue State

```sql
SELECT
    service_class,
    num_queued_queries,
    num_executing_queries,
    num_executed_queries
FROM STV_WLM_SERVICE_CLASS_STATE
ORDER BY service_class;
```

### 50. Currently Queued Queries

```sql
SELECT
    query,
    service_class,
    slot_count,
    wlm_start_time,
    state,
    queue_time / 1000000.0 AS queue_sec,
    exec_time / 1000000.0 AS exec_sec
FROM STV_WLM_QUERY_STATE
WHERE state = 'Queued'
ORDER BY wlm_start_time;
```

### 51. Currently Executing Queries in WLM

```sql
SELECT
    query,
    service_class,
    slot_count,
    wlm_start_time,
    state,
    queue_time / 1000000.0 AS queue_sec,
    exec_time / 1000000.0 AS exec_sec
FROM STV_WLM_QUERY_STATE
WHERE state = 'Executing'
ORDER BY exec_time DESC;
```

### 52. WLM Query History

```sql
SELECT
    query,
    service_class,
    queue_start_time,
    exec_start_time,
    total_queue_time / 1000000.0 AS queue_sec,
    total_exec_time / 1000000.0 AS exec_sec,
    final_state
FROM STL_WLM_QUERY
WHERE queue_start_time >= DATEADD(hour, -24, GETDATE())
ORDER BY total_queue_time DESC
LIMIT 50;
```

### 53. Queries that Waited Longest in WLM Queues

```sql
SELECT
    w.query,
    w.service_class,
    w.total_queue_time / 1000000.0 AS queue_sec,
    w.total_exec_time / 1000000.0 AS exec_sec,
    LEFT(q.querytxt, 200) AS query_preview
FROM STL_WLM_QUERY w
JOIN STL_QUERY q ON w.query = q.query
WHERE w.queue_start_time >= DATEADD(hour, -24, GETDATE())
  AND w.total_queue_time > 0
ORDER BY w.total_queue_time DESC
LIMIT 20;
```

### 54. WLM Queue Throughput by Hour

```sql
SELECT
    DATE_TRUNC('hour', queue_start_time) AS hour,
    service_class,
    COUNT(*) AS query_count,
    AVG(total_queue_time / 1000000.0) AS avg_queue_sec,
    MAX(total_queue_time / 1000000.0) AS max_queue_sec,
    AVG(total_exec_time / 1000000.0) AS avg_exec_sec
FROM STL_WLM_QUERY
WHERE queue_start_time >= DATEADD(day, -1, GETDATE())
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

### 55. Query Monitoring Rule Violations

```sql
SELECT
    query,
    service_class,
    rule_name,
    action,
    LEFT(condition, 200) AS condition_detail,
    event_time
FROM STL_WLM_RULE_ACTION
WHERE event_time >= DATEADD(day, -7, GETDATE())
ORDER BY event_time DESC
LIMIT 50;
```

## Lock and Transaction Diagnostics

### 56. Current Locks

```sql
SELECT
    table_id,
    TRIM(l.lock_owner_name) AS lock_owner,
    l.lock_mode,
    l.lock_owner_pid,
    l.lock_status,
    TRIM(nsp.nspname || '.' || cls.relname) AS table_name
FROM STV_LOCKS l
LEFT JOIN pg_class cls ON l.table_id = cls.oid
LEFT JOIN pg_namespace nsp ON cls.relnamespace = nsp.oid
ORDER BY table_id;
```

### 57. Blocking Sessions

```sql
SELECT
    b.locks_held,
    b.locks_waited,
    b.pid AS blocker_pid,
    b.user_name AS blocker_user,
    LEFT(a.query, 200) AS blocker_query
FROM STV_BLOCKERS b
LEFT JOIN pg_stat_activity a ON b.pid = a.pid;
```

### 58. Open Transactions

```sql
SELECT
    xid,
    pid,
    txn_start,
    DATEDIFF(second, txn_start, GETDATE()) AS age_sec,
    lockable_object_type,
    relation,
    lock_mode,
    granted
FROM SVV_TRANSACTIONS
ORDER BY txn_start
LIMIT 30;
```

### 59. Long-Running Transactions (Blocking VACUUM)

```sql
SELECT
    t.xid,
    t.pid,
    t.txn_start,
    DATEDIFF(minute, t.txn_start, GETDATE()) AS age_min,
    a.usename,
    LEFT(a.query, 200) AS current_query
FROM SVV_TRANSACTIONS t
JOIN pg_stat_activity a ON t.pid = a.pid
WHERE DATEDIFF(minute, t.txn_start, GETDATE()) > 30
ORDER BY t.txn_start;
```

### 60. Deadlock Detection

```sql
SELECT
    query,
    xid,
    pid,
    starttime,
    LEFT(querytxt, 200) AS query_text
FROM STL_QUERY
WHERE aborted = 1
  AND querytxt LIKE '%deadlock%'
  AND starttime >= DATEADD(day, -7, GETDATE())
ORDER BY starttime DESC;
```

## COPY / Data Loading Diagnostics

### 61. COPY Load History (SYS View)

```sql
SELECT
    query_id,
    table_name,
    data_source,
    file_format,
    loaded_rows,
    loaded_bytes,
    start_time,
    end_time,
    elapsed_time / 1000000.0 AS duration_sec,
    status
FROM SYS_LOAD_HISTORY
ORDER BY start_time DESC
LIMIT 30;
```

### 62. COPY Load Errors

```sql
SELECT
    starttime,
    filename,
    line_number,
    colname,
    type,
    col_length,
    raw_field_value,
    err_reason
FROM STL_LOAD_ERRORS
ORDER BY starttime DESC
LIMIT 30;
```

### 63. COPY Error Detail (Full Raw Lines)

```sql
SELECT
    query,
    starttime,
    filename,
    line_number,
    raw_line
FROM STL_LOADERROR_DETAIL
WHERE query = <query_id>
ORDER BY line_number
LIMIT 20;
```

### 64. COPY Error Summary by Reason

```sql
SELECT
    err_reason,
    colname,
    type,
    COUNT(*) AS error_count,
    MIN(starttime) AS first_seen,
    MAX(starttime) AS last_seen
FROM STL_LOAD_ERRORS
WHERE starttime >= DATEADD(day, -7, GETDATE())
GROUP BY err_reason, colname, type
ORDER BY error_count DESC;
```

### 65. COPY Performance by File

```sql
SELECT
    query,
    filename,
    lines_scanned,
    bytes_scanned,
    DATEDIFF(microsecond, starttime, endtime) / 1000.0 AS load_ms
FROM STL_LOAD_COMMITS
WHERE query = <query_id>
ORDER BY load_ms DESC;
```

### 66. Successful COPY Operations (Last 7 Days)

```sql
SELECT
    query_id,
    table_name,
    file_format,
    loaded_rows,
    ROUND(loaded_bytes / 1024.0 / 1024.0, 2) AS loaded_mb,
    elapsed_time / 1000000.0 AS duration_sec,
    ROUND(loaded_rows / NULLIF(elapsed_time / 1000000.0, 0), 0) AS rows_per_sec
FROM SYS_LOAD_HISTORY
WHERE status = 'success'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY start_time DESC
LIMIT 30;
```

## Spectrum Diagnostics

### 67. Spectrum Query Summary

```sql
SELECT
    query,
    segment,
    assignment,
    elapsed / 1000000.0 AS elapsed_sec,
    s3_scanned_rows,
    s3_scanned_bytes,
    s3query_returned_rows,
    s3query_returned_bytes,
    files,
    avg_request_parallelism,
    max_request_parallelism
FROM SVL_S3QUERY_SUMMARY
WHERE query = <query_id>
ORDER BY segment;
```

### 68. Spectrum Partition Pruning Effectiveness

```sql
SELECT
    query,
    segment,
    assignment,
    total_partitions,
    qualified_partitions,
    ROUND(qualified_partitions::FLOAT / NULLIF(total_partitions, 0) * 100, 2) AS pct_scanned
FROM SVL_S3PARTITION
WHERE query = <query_id>
ORDER BY segment;
```

### 69. Spectrum Queries with Poor Partition Pruning

```sql
SELECT
    p.query,
    p.total_partitions,
    p.qualified_partitions,
    ROUND(p.qualified_partitions::FLOAT / NULLIF(p.total_partitions, 0) * 100, 2) AS pct_scanned,
    LEFT(q.querytxt, 200) AS query_preview
FROM SVL_S3PARTITION p
JOIN STL_QUERY q ON p.query = q.query
WHERE p.starttime >= DATEADD(day, -7, GETDATE())
  AND p.total_partitions > 10
  AND p.qualified_partitions::FLOAT / NULLIF(p.total_partitions, 0) > 0.5
ORDER BY p.total_partitions DESC
LIMIT 20;
```

### 70. Spectrum S3 Request Details

```sql
SELECT
    query,
    segment,
    key,
    status,
    transfer_size,
    DATEDIFF(microsecond, starttime, endtime) / 1000.0 AS request_ms
FROM SVL_S3LOG
WHERE query = <query_id>
ORDER BY request_ms DESC
LIMIT 50;
```

### 71. Top Spectrum Queries by Data Scanned

```sql
SELECT
    s.query,
    SUM(s.s3_scanned_bytes) / 1024.0 / 1024.0 / 1024.0 AS scanned_gb,
    SUM(s.s3_scanned_rows) AS scanned_rows,
    SUM(s.s3query_returned_rows) AS returned_rows,
    SUM(s.elapsed) / 1000000.0 AS total_elapsed_sec,
    LEFT(q.querytxt, 200) AS query_preview
FROM SVL_S3QUERY_SUMMARY s
JOIN STL_QUERY q ON s.query = q.query
WHERE q.starttime >= DATEADD(day, -7, GETDATE())
GROUP BY s.query, q.querytxt
ORDER BY scanned_gb DESC
LIMIT 20;
```

### 72. Spectrum File Size Distribution

```sql
SELECT
    query,
    segment,
    files,
    avg_request_parallelism,
    max_request_parallelism,
    ROUND(s3_scanned_bytes::FLOAT / NULLIF(files, 0) / 1024 / 1024, 2) AS avg_file_mb
FROM SVL_S3QUERY_SUMMARY
WHERE query = <query_id>;
```

## Data Sharing Diagnostics

### 73. List All Datashares

```sql
SELECT
    share_id,
    share_name,
    share_type,
    producer_account,
    producer_namespace,
    create_date,
    is_publicaccessible
FROM SVV_DATASHARES
ORDER BY create_date DESC;
```

### 74. Datashare Objects

```sql
SELECT
    share_name,
    object_type,
    object_name
FROM SVV_DATASHARE_OBJECTS
ORDER BY share_name, object_type;
```

### 75. Datashare Consumers

```sql
SELECT
    share_name,
    consumer_account,
    consumer_namespace,
    consumer_status,
    consumer_accept_time
FROM SVV_DATASHARE_CONSUMERS
ORDER BY share_name;
```

### 76. Datashare Usage Query Performance

```sql
SELECT
    query_id,
    user_id,
    elapsed_time / 1000000.0 AS duration_sec,
    returned_rows,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE query_text LIKE '%shared_db%'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY elapsed_time DESC
LIMIT 20;
```

## Concurrency Scaling Diagnostics

### 77. Concurrency Scaling Usage

```sql
SELECT
    starttime,
    endtime,
    DATEDIFF(second, starttime, endtime) AS duration_sec
FROM STL_CONCURRENCY_SCALING_USAGE
ORDER BY starttime DESC
LIMIT 30;
```

### 78. Concurrency Scaling Usage by Day

```sql
SELECT
    TRUNC(starttime) AS usage_date,
    COUNT(*) AS scaling_events,
    SUM(DATEDIFF(second, starttime, endtime)) AS total_seconds,
    ROUND(SUM(DATEDIFF(second, starttime, endtime)) / 3600.0, 2) AS total_hours
FROM STL_CONCURRENCY_SCALING_USAGE
WHERE starttime >= DATEADD(day, -30, GETDATE())
GROUP BY TRUNC(starttime)
ORDER BY usage_date DESC;
```

### 79. Queries Routed to Concurrency Scaling

```sql
SELECT
    query_id,
    user_id,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE is_concurrency_scaling = 'true'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY start_time DESC
LIMIT 30;
```

## Serverless Diagnostics

### 80. Serverless RPU Usage

```sql
SELECT
    start_time,
    end_time,
    compute_seconds,
    data_scanned,
    compute_type
FROM SYS_SERVERLESS_USAGE
ORDER BY start_time DESC
LIMIT 50;
```

### 81. Serverless Usage by Hour

```sql
SELECT
    DATE_TRUNC('hour', start_time) AS hour,
    SUM(compute_seconds) AS total_compute_sec,
    ROUND(SUM(compute_seconds) / 3600.0, 2) AS compute_hours,
    SUM(data_scanned) / 1024.0 / 1024.0 / 1024.0 AS data_scanned_gb
FROM SYS_SERVERLESS_USAGE
WHERE start_time >= DATEADD(day, -7, GETDATE())
GROUP BY 1
ORDER BY 1 DESC;
```

### 82. Serverless Daily Cost Estimation

```sql
SELECT
    TRUNC(start_time) AS usage_date,
    SUM(compute_seconds) AS total_compute_sec,
    ROUND(SUM(compute_seconds) / 3600.0, 4) AS compute_hours,
    -- Approximate cost at $0.375/RPU-hour (us-east-1 pricing, adjust per region)
    ROUND(SUM(compute_seconds) / 3600.0 * 0.375, 2) AS estimated_cost_usd
FROM SYS_SERVERLESS_USAGE
WHERE start_time >= DATEADD(day, -30, GETDATE())
GROUP BY TRUNC(start_time)
ORDER BY usage_date DESC;
```

### 83. Serverless Query Performance vs RPU Usage

```sql
SELECT
    qh.query_id,
    qh.elapsed_time / 1000000.0 AS duration_sec,
    qh.queue_time / 1000000.0 AS queue_sec,
    qh.returned_rows,
    su.compute_seconds,
    LEFT(qh.query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY qh
LEFT JOIN SYS_SERVERLESS_USAGE su
    ON qh.start_time BETWEEN su.start_time AND su.end_time
WHERE qh.start_time >= DATEADD(day, -1, GETDATE())
ORDER BY su.compute_seconds DESC NULLS LAST
LIMIT 30;
```

## Materialized View Diagnostics

### 84. Materialized View Refresh Status

```sql
SELECT
    mv_name,
    schema_name,
    db_name,
    state,
    autorefresh,
    is_stale
FROM STV_MV_INFO
ORDER BY mv_name;
```

### 85. Materialized View Refresh History

```sql
SELECT
    query_id,
    user_id,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    status,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE query_type = 'REFRESH'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY start_time DESC
LIMIT 30;
```

### 86. Materialized Views Eligible for Query Rewriting

```sql
SELECT
    schema_name,
    mv_name,
    state,
    autorefresh,
    is_stale
FROM STV_MV_INFO
WHERE state = 'Active'
  AND is_stale = 0;
```

### 87. Queries Rewritten to Use Materialized Views

```sql
SELECT
    query_id,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE query_text LIKE '%mv_%'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY start_time DESC
LIMIT 20;
```

## User and Permission Diagnostics

### 88. All Database Users

```sql
SELECT
    usesysid,
    usename,
    usecreatedb,
    usesuper,
    valuntil AS password_expiry,
    useconfig
FROM pg_user
ORDER BY usesysid;
```

### 89. User Groups and Membership

```sql
SELECT
    g.groname AS group_name,
    u.usename AS member
FROM pg_group g
CROSS JOIN pg_user u
WHERE u.usesysid = ANY(g.grolist)
ORDER BY g.groname, u.usename;
```

### 90. Schema Permissions

```sql
SELECT
    nspname AS schema_name,
    nspowner AS owner_id,
    u.usename AS owner_name,
    nspacl AS permissions
FROM pg_namespace n
LEFT JOIN pg_user u ON n.nspowner = u.usesysid
WHERE nspname NOT LIKE 'pg_%'
ORDER BY nspname;
```

### 91. Table-Level Permissions

```sql
SELECT
    schemaname,
    tablename,
    tableowner,
    has_table_privilege(usename, schemaname || '.' || tablename, 'SELECT') AS can_select,
    has_table_privilege(usename, schemaname || '.' || tablename, 'INSERT') AS can_insert,
    has_table_privilege(usename, schemaname || '.' || tablename, 'DELETE') AS can_delete
FROM pg_tables
CROSS JOIN pg_user
WHERE schemaname = 'public'
  AND usename = '<target_user>'
ORDER BY tablename;
```

### 92. Active Roles

```sql
SELECT
    role_name,
    role_id,
    role_owner
FROM SVV_ROLES
ORDER BY role_name;
```

### 93. Row-Level Security Policies

```sql
SELECT
    polname AS policy_name,
    relname AS table_name,
    polcmd AS command,
    polroles AS roles,
    polqual AS using_expr
FROM pg_policy p
JOIN pg_class c ON p.polrelid = c.oid
ORDER BY relname, polname;
```

## Query Performance Deep Dives

### 94. Query Plan vs Actual Execution

```sql
-- Step 1: Get EXPLAIN plan
EXPLAIN SELECT ...;

-- Step 2: Run the query and note the query_id
-- Step 3: Compare with actual execution
SELECT
    query,
    stm,
    seg,
    step,
    label,
    rows AS actual_rows,
    bytes AS actual_bytes,
    maxtime AS max_time_us,
    avgtime AS avg_time_us,
    is_diskbased
FROM SVL_QUERY_SUMMARY
WHERE query = <query_id>
ORDER BY stm, seg, step;
```

### 95. Identify Skewed Query Execution (Slice-Level)

```sql
SELECT
    query,
    seg,
    step,
    label,
    MIN(rows) AS min_rows,
    MAX(rows) AS max_rows,
    AVG(rows) AS avg_rows,
    CASE WHEN AVG(rows) > 0 THEN
        ROUND(MAX(rows)::FLOAT / AVG(rows), 2)
    ELSE 0 END AS skew_ratio,
    SUM(rows) AS total_rows
FROM SVL_QUERY_REPORT
WHERE query = <query_id>
GROUP BY query, seg, step, label
HAVING MAX(rows) > 0
ORDER BY skew_ratio DESC;
```

### 96. Network Distribution Cost per Query

```sql
SELECT
    query,
    SUM(CASE WHEN label LIKE '%bcast%' THEN bytes ELSE 0 END) AS broadcast_bytes,
    SUM(CASE WHEN label LIKE '%dist%' THEN bytes ELSE 0 END) AS redistribute_bytes,
    SUM(bytes) AS total_bytes
FROM SVL_QUERY_SUMMARY
WHERE query = <query_id>
GROUP BY query;
```

### 97. Hash Join Memory Usage

```sql
SELECT
    query,
    stm,
    seg,
    step,
    label,
    rows,
    bytes,
    workmem,
    is_diskbased
FROM SVL_QUERY_SUMMARY
WHERE query = <query_id>
  AND label LIKE '%hash%'
ORDER BY workmem DESC;
```

### 98. Queries Returning Excessive Rows

```sql
SELECT
    query_id,
    user_id,
    start_time,
    returned_rows,
    returned_bytes / 1024.0 / 1024.0 AS returned_mb,
    elapsed_time / 1000000.0 AS duration_sec,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE returned_rows > 1000000
  AND start_time >= DATEADD(day, -7, GETDATE())
  AND query_type = 'SELECT'
ORDER BY returned_rows DESC
LIMIT 20;
```

### 99. Queries by Hourly Pattern

```sql
SELECT
    DATE_TRUNC('hour', start_time) AS hour,
    COUNT(*) AS query_count,
    AVG(elapsed_time / 1000000.0) AS avg_duration_sec,
    MAX(elapsed_time / 1000000.0) AS max_duration_sec,
    SUM(returned_rows) AS total_returned_rows
FROM SYS_QUERY_HISTORY
WHERE start_time >= DATEADD(day, -7, GETDATE())
  AND query_type = 'SELECT'
GROUP BY 1
ORDER BY 1 DESC;
```

### 100. Query Duration Distribution (Percentiles)

```sql
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY elapsed_time / 1000000.0) AS p50_sec,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY elapsed_time / 1000000.0) AS p75_sec,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY elapsed_time / 1000000.0) AS p90_sec,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY elapsed_time / 1000000.0) AS p95_sec,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY elapsed_time / 1000000.0) AS p99_sec,
    COUNT(*) AS total_queries
FROM SYS_QUERY_HISTORY
WHERE start_time >= DATEADD(day, -1, GETDATE())
  AND query_type = 'SELECT'
  AND status = 'success';
```

## Streaming Ingestion Diagnostics

### 101. Streaming Ingestion Status

```sql
SELECT
    mv_name,
    schema_name,
    state,
    autorefresh,
    is_stale
FROM STV_MV_INFO
WHERE autorefresh = 1
ORDER BY mv_name;
```

### 102. Streaming MV Refresh Latency

```sql
SELECT
    query_id,
    start_time,
    end_time,
    elapsed_time / 1000000.0 AS refresh_sec,
    LEFT(query_text, 200) AS mv_query
FROM SYS_QUERY_HISTORY
WHERE query_type = 'REFRESH'
  AND query_text LIKE '%kinesis%' OR query_text LIKE '%kafka%'
  AND start_time >= DATEADD(day, -1, GETDATE())
ORDER BY start_time DESC
LIMIT 30;
```

## VACUUM and Maintenance Diagnostics

### 103. VACUUM History

```sql
SELECT
    query_id,
    table_name,
    start_time,
    end_time,
    elapsed_time / 1000000.0 AS duration_sec,
    status,
    LEFT(query_text, 200) AS vacuum_type
FROM SYS_QUERY_HISTORY
WHERE query_type = 'VACUUM'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY start_time DESC
LIMIT 30;
```

### 104. Tables Needing VACUUM

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    unsorted,
    stats_off,
    CASE
        WHEN unsorted > 20 THEN 'VACUUM SORT needed'
        WHEN stats_off > 10 THEN 'ANALYZE needed'
        ELSE 'OK'
    END AS recommendation
FROM SVV_TABLE_INFO
WHERE unsorted > 5 OR stats_off > 5
ORDER BY unsorted DESC, stats_off DESC;
```

### 105. Auto VACUUM Progress

```sql
SELECT
    query_id,
    start_time,
    elapsed_time / 1000000.0 AS running_sec,
    status,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE query_type = 'VACUUM'
  AND status = 'running'
ORDER BY start_time;
```

## Cost and Billing Analysis

### 106. Storage Usage Trend

```sql
SELECT
    TRUNC(GETDATE()) AS snapshot_date,
    SUM(size) AS total_mb,
    ROUND(SUM(size) / 1024.0, 2) AS total_gb,
    ROUND(SUM(size) / 1024.0 / 1024.0, 4) AS total_tb,
    COUNT(DISTINCT "table") AS table_count,
    SUM(tbl_rows) AS total_rows
FROM SVV_TABLE_INFO;
```

### 107. Top Storage Consumers

```sql
SELECT
    "schema",
    "table",
    tbl_rows,
    size AS size_mb,
    ROUND(size / 1024.0, 2) AS size_gb,
    ROUND(size * 100.0 / (SELECT SUM(size) FROM SVV_TABLE_INFO), 2) AS pct_of_total,
    diststyle,
    sortkey1,
    encoded
FROM SVV_TABLE_INFO
ORDER BY size DESC
LIMIT 30;
```

### 108. Estimated Compression Savings

```sql
-- Run on each large table to estimate potential savings
ANALYZE COMPRESSION public.orders;
-- Compare current size with recommended encodings
```

### 109. Serverless Usage Trend (30 Days)

```sql
SELECT
    TRUNC(start_time) AS usage_date,
    SUM(compute_seconds) AS compute_sec,
    ROUND(SUM(compute_seconds) / 3600.0, 2) AS compute_hours,
    COUNT(*) AS usage_intervals
FROM SYS_SERVERLESS_USAGE
WHERE start_time >= DATEADD(day, -30, GETDATE())
GROUP BY TRUNC(start_time)
ORDER BY usage_date DESC;
```

### 110. Concurrency Scaling Cost Estimation

```sql
SELECT
    TRUNC(starttime) AS usage_date,
    COUNT(*) AS scaling_events,
    SUM(DATEDIFF(second, starttime, endtime)) AS total_seconds,
    ROUND(SUM(DATEDIFF(second, starttime, endtime)) / 3600.0, 2) AS total_hours
FROM STL_CONCURRENCY_SCALING_USAGE
WHERE starttime >= DATEADD(day, -30, GETDATE())
GROUP BY TRUNC(starttime)
ORDER BY usage_date DESC;
```

## UNLOAD Diagnostics

### 111. UNLOAD History

```sql
SELECT
    query_id,
    user_id,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    returned_rows,
    returned_bytes / 1024.0 / 1024.0 AS returned_mb,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE query_type = 'UNLOAD'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY start_time DESC
LIMIT 20;
```

### 112. UNLOAD Performance Analysis

```sql
SELECT
    query_id,
    returned_rows,
    returned_bytes / 1024.0 / 1024.0 AS unloaded_mb,
    elapsed_time / 1000000.0 AS duration_sec,
    ROUND(returned_rows / NULLIF(elapsed_time / 1000000.0, 0), 0) AS rows_per_sec,
    ROUND((returned_bytes / 1024.0 / 1024.0) / NULLIF(elapsed_time / 1000000.0, 0), 2) AS mb_per_sec
FROM SYS_QUERY_HISTORY
WHERE query_type = 'UNLOAD'
  AND status = 'success'
  AND start_time >= DATEADD(day, -30, GETDATE())
ORDER BY unloaded_mb DESC
LIMIT 20;
```

## External Schema and Catalog Diagnostics

### 113. External Schemas

```sql
SELECT
    schemaname,
    databasename,
    esoptions
FROM SVV_EXTERNAL_SCHEMAS
ORDER BY schemaname;
```

### 114. External Tables

```sql
SELECT
    schemaname,
    tablename,
    location,
    input_format,
    output_format,
    serialization_lib
FROM SVV_EXTERNAL_TABLES
ORDER BY schemaname, tablename;
```

### 115. External Table Columns

```sql
SELECT
    schemaname,
    tablename,
    columnname,
    external_type,
    part_key
FROM SVV_EXTERNAL_COLUMNS
WHERE schemaname = '<schema_name>'
ORDER BY tablename, columnnum;
```

### 116. External Table Partitions

```sql
SELECT
    schemaname,
    tablename,
    values,
    location
FROM SVV_EXTERNAL_PARTITIONS
WHERE schemaname = '<schema_name>'
  AND tablename = '<table_name>'
ORDER BY values
LIMIT 100;
```

## Redshift ML Diagnostics

### 117. ML Model Status

```sql
SELECT
    schema_name,
    model_name,
    model_state,
    model_type,
    creation_time,
    training_data,
    target_column,
    function_name
FROM STLL_MODELINFO
ORDER BY creation_time DESC;
```

### 118. ML Model Prediction Performance

```sql
SELECT
    query_id,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    returned_rows,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE query_text LIKE '%fn_predict%'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY start_time DESC
LIMIT 20;
```

## Advanced Performance Analysis

### 119. Query Frequency Analysis (Top Repeated Queries)

```sql
SELECT
    MD5(REGEXP_REPLACE(query_text, '''[^'']*''', '?')) AS query_template_hash,
    COUNT(*) AS execution_count,
    AVG(elapsed_time / 1000000.0) AS avg_duration_sec,
    MAX(elapsed_time / 1000000.0) AS max_duration_sec,
    SUM(elapsed_time / 1000000.0) AS total_duration_sec,
    LEFT(MIN(query_text), 200) AS sample_query
FROM SYS_QUERY_HISTORY
WHERE start_time >= DATEADD(day, -1, GETDATE())
  AND query_type = 'SELECT'
  AND status = 'success'
GROUP BY 1
ORDER BY total_duration_sec DESC
LIMIT 30;
```

### 120. Peak Concurrency Analysis

```sql
SELECT
    DATE_TRUNC('minute', start_time) AS minute,
    COUNT(*) AS queries_started,
    MAX(elapsed_time / 1000000.0) AS max_duration_sec
FROM SYS_QUERY_HISTORY
WHERE start_time >= DATEADD(hour, -6, GETDATE())
  AND query_type IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE')
GROUP BY 1
ORDER BY queries_started DESC
LIMIT 30;
```

### 121. Join Type Distribution

```sql
SELECT
    label,
    COUNT(DISTINCT query) AS query_count,
    SUM(rows) AS total_rows,
    AVG(maxtime) AS avg_time_us
FROM SVL_QUERY_SUMMARY
WHERE label LIKE '%join%'
  AND query IN (
      SELECT query FROM STL_QUERY
      WHERE starttime >= DATEADD(day, -1, GETDATE())
      AND userid > 1
  )
GROUP BY label
ORDER BY query_count DESC;
```

### 122. Data Distribution Effectiveness (DS_DIST Analysis)

```sql
SELECT
    label,
    COUNT(DISTINCT query) AS query_count,
    SUM(rows) AS total_rows_moved,
    SUM(bytes) AS total_bytes_moved
FROM SVL_QUERY_SUMMARY
WHERE label LIKE 'DS_DIST%'
  AND query IN (
      SELECT query FROM STL_QUERY
      WHERE starttime >= DATEADD(day, -1, GETDATE())
      AND userid > 1
  )
GROUP BY label
ORDER BY total_bytes_moved DESC;
```

### 123. Commit Queue Wait Analysis

```sql
SELECT
    query,
    startqueue,
    startwork,
    DATEDIFF(microsecond, startqueue, startwork) / 1000.0 AS queue_wait_ms
FROM STL_COMMIT_STATS
WHERE startqueue >= DATEADD(hour, -24, GETDATE())
ORDER BY queue_wait_ms DESC
LIMIT 30;
```

### 124. Short Query Acceleration (SQA) Effectiveness

```sql
SELECT
    service_class,
    final_state,
    COUNT(*) AS query_count,
    AVG(total_exec_time / 1000000.0) AS avg_exec_sec
FROM STL_WLM_QUERY
WHERE service_class = 14  -- SQA queue
  AND queue_start_time >= DATEADD(day, -1, GETDATE())
GROUP BY service_class, final_state
ORDER BY query_count DESC;
```

### 125. Table Growth Estimation

```sql
-- Compare current size with recent COPY loads
SELECT
    lh.table_name,
    COUNT(*) AS loads_7d,
    SUM(lh.loaded_rows) AS rows_loaded_7d,
    SUM(lh.loaded_bytes) / 1024.0 / 1024.0 AS mb_loaded_7d,
    ti.size AS current_size_mb,
    ti.tbl_rows AS current_rows
FROM SYS_LOAD_HISTORY lh
JOIN SVV_TABLE_INFO ti ON LOWER(lh.table_name) = LOWER(ti."table")
WHERE lh.start_time >= DATEADD(day, -7, GETDATE())
  AND lh.status = 'success'
GROUP BY lh.table_name, ti.size, ti.tbl_rows
ORDER BY mb_loaded_7d DESC
LIMIT 20;
```

## Troubleshooting Playbook Queries

### 126. Emergency: Identify What Is Using All Disk Space

```sql
-- Top 20 tables by disk usage
SELECT "table", "schema", size AS size_mb, tbl_rows, diststyle
FROM SVV_TABLE_INFO
ORDER BY size DESC
LIMIT 20;

-- Check temp table usage
SELECT
    query,
    slot_count,
    start_time,
    is_diskbased,
    workmem
FROM STV_WLM_QUERY_STATE
WHERE is_diskbased = 't';
```

### 127. Emergency: Cluster Unresponsive -- Identify Culprit

```sql
-- Find running queries consuming most resources
SELECT
    pid,
    usename,
    starttime,
    DATEDIFF(second, starttime, GETDATE()) AS running_sec,
    LEFT(query, 200) AS query_preview
FROM STV_RECENTS
WHERE status = 'Running'
ORDER BY starttime;
```

### 128. Diagnose Slow COPY Performance

```sql
-- Check file count and sizes
SELECT
    query,
    filename,
    lines_scanned,
    bytes_scanned,
    DATEDIFF(microsecond, starttime, endtime) / 1000.0 AS load_ms
FROM STL_LOAD_COMMITS
WHERE query = <query_id>
ORDER BY load_ms DESC;

-- Check if files are split evenly across slices
SELECT
    slice,
    COUNT(*) AS files_loaded,
    SUM(lines_scanned) AS total_lines,
    SUM(bytes_scanned) AS total_bytes
FROM STL_LOAD_COMMITS
WHERE query = <query_id>
GROUP BY slice
ORDER BY slice;
```

### 129. Diagnose Why a Query Is Slow

```sql
-- Step 1: Get query duration and basic info
SELECT query_id, elapsed_time / 1000000.0 AS sec, queue_time / 1000000.0 AS queue_sec, status
FROM SYS_QUERY_HISTORY WHERE query_id = <query_id>;

-- Step 2: Check for alerts
SELECT event, solution FROM STL_ALERT_EVENT_LOG WHERE query = <query_id>;

-- Step 3: Check for disk-based operations (memory spilling)
SELECT step, label, rows, bytes, is_diskbased, workmem
FROM SVL_QUERY_SUMMARY WHERE query = <query_id> AND is_diskbased = 't';

-- Step 4: Check for heavy redistribution
SELECT step, label, rows, bytes
FROM SVL_QUERY_SUMMARY WHERE query = <query_id> AND label LIKE 'DS_DIST%';

-- Step 5: Check slice-level skew
SELECT seg, step, label, MIN(rows) AS min_rows, MAX(rows) AS max_rows,
       ROUND(MAX(rows)::FLOAT / NULLIF(AVG(rows), 0), 2) AS skew_ratio
FROM SVL_QUERY_REPORT WHERE query = <query_id>
GROUP BY seg, step, label HAVING MAX(rows) > 0
ORDER BY skew_ratio DESC LIMIT 10;

-- Step 6: Check compilation overhead
SELECT segment, compile, DATEDIFF(microsecond, starttime, endtime) / 1000.0 AS compile_ms
FROM SVL_COMPILE WHERE query = <query_id>;
```

### 130. Find Queries Causing Lock Contention

```sql
SELECT
    b.pid AS blocker_pid,
    b.user_name AS blocker_user,
    a.pid AS blocked_pid,
    a.usename AS blocked_user,
    l.table_id,
    TRIM(nsp.nspname || '.' || cls.relname) AS locked_table,
    l.lock_mode,
    LEFT(blocker.query, 200) AS blocker_query,
    LEFT(a.query, 200) AS blocked_query
FROM STV_BLOCKERS b
JOIN pg_stat_activity a ON a.pid != b.pid
JOIN STV_LOCKS l ON l.lock_owner_pid = b.pid
LEFT JOIN pg_class cls ON l.table_id = cls.oid
LEFT JOIN pg_namespace nsp ON cls.relnamespace = nsp.oid
LEFT JOIN pg_stat_activity blocker ON b.pid = blocker.pid;
```

### 131. Zero-ETL Integration Status

```sql
-- Check integration-replicated tables
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname LIKE '%integration%'
ORDER BY tablename;
```

### 132. Identify Queries Not Using Sort Keys Effectively

```sql
SELECT
    a.query,
    a.event,
    LEFT(q.querytxt, 200) AS query_preview,
    DATEDIFF(second, q.starttime, q.endtime) AS duration_sec
FROM STL_ALERT_EVENT_LOG a
JOIN STL_QUERY q ON a.query = q.query
WHERE a.event LIKE '%sort key%'
   OR a.event LIKE '%zone map%'
   OR a.event LIKE '%unsorted%'
ORDER BY q.starttime DESC
LIMIT 20;
```

### 133. Schema-Level Object Inventory

```sql
SELECT
    nspname AS schema_name,
    CASE c.relkind
        WHEN 'r' THEN 'table'
        WHEN 'v' THEN 'view'
        WHEN 'm' THEN 'materialized view'
        WHEN 'S' THEN 'sequence'
    END AS object_type,
    COUNT(*) AS object_count
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_internal')
  AND c.relkind IN ('r', 'v', 'm', 'S')
GROUP BY nspname, c.relkind
ORDER BY nspname, object_type;
```

### 134. Query Queue Wait Time Trends

```sql
SELECT
    DATE_TRUNC('hour', start_time) AS hour,
    COUNT(*) AS total_queries,
    AVG(queue_time / 1000000.0) AS avg_queue_sec,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY queue_time / 1000000.0) AS p95_queue_sec,
    MAX(queue_time / 1000000.0) AS max_queue_sec,
    SUM(CASE WHEN queue_time > 5000000 THEN 1 ELSE 0 END) AS queries_queued_over_5s
FROM SYS_QUERY_HISTORY
WHERE start_time >= DATEADD(day, -3, GETDATE())
  AND query_type = 'SELECT'
GROUP BY 1
ORDER BY 1 DESC;
```

### 135. SUPER Data Type Query Performance

```sql
SELECT
    query_id,
    start_time,
    elapsed_time / 1000000.0 AS duration_sec,
    returned_rows,
    LEFT(query_text, 200) AS query_preview
FROM SYS_QUERY_HISTORY
WHERE query_text LIKE '%SUPER%'
   OR query_text LIKE '%JSON_PARSE%'
   OR query_text LIKE '%json_extract%'
  AND start_time >= DATEADD(day, -7, GETDATE())
ORDER BY elapsed_time DESC
LIMIT 20;
```
