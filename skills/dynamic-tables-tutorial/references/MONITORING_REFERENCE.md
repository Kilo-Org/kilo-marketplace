# Dynamic Tables Monitoring Reference

This guide covers how to monitor Dynamic Tables using Snowflake's built-in functions and views.

---

## Key Monitoring Functions

### DYNAMIC_TABLE_REFRESH_HISTORY

The primary function for monitoring refreshes.

```sql
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
ORDER BY refresh_start_time DESC
LIMIT 100;
```

**Key columns**:

| Column | Description |
|--------|-------------|
| `NAME` | Dynamic table name |
| `SCHEMA_NAME` | Schema name |
| `DATABASE_NAME` | Database name |
| `STATE` | SCHEDULED, EXECUTING, SUCCEEDED, FAILED, CANCELLED, UPSTREAM_FAILED |
| `STATE_CODE` | Numeric code for the state |
| `STATE_MESSAGE` | Detailed message about the state |
| `QUERY_ID` | Query ID for the refresh (useful for Query Profile) |
| `DATA_TIMESTAMP` | Point-in-time when source data was captured |
| `REFRESH_START_TIME` | When refresh started |
| `REFRESH_END_TIME` | When refresh completed |
| `COMPLETION_TARGET` | Time by which refresh should complete |
| `REFRESH_ACTION` | INCREMENTAL, FULL, REINITIALIZE, NO_DATA |
| `REFRESH_TRIGGER` | SCHEDULED, MANUAL, CREATION |
| `TARGET_LAG_SEC` | Configured target lag in seconds |
| `STATISTICS` | JSON with row counts and partition changes |

### Function Parameters

```sql
-- Filter by time range
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  DATA_TIMESTAMP_START => '2024-01-01 00:00:00'::TIMESTAMP_LTZ,
  DATA_TIMESTAMP_END => '2024-01-31 23:59:59'::TIMESTAMP_LTZ
));

-- Filter by table name
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME => 'MY_DYNAMIC_TABLE'
));

-- Filter by name prefix (for all tables in a schema)
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME_PREFIX => 'MY_DB.MY_SCHEMA.'
));

-- Only show errors
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  ERROR_ONLY => TRUE
));

-- Increase result limit (default is 100, max is 10000)
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  RESULT_LIMIT => 1000
));
```

---

## DYNAMIC_TABLE_GRAPH_HISTORY

Shows the dependency graph and configuration history for Dynamic Tables.

```sql
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_GRAPH_HISTORY())
WHERE name = 'MY_DYNAMIC_TABLE'
ORDER BY valid_from DESC;
```

**Key columns**:

| Column | Description |
|--------|-------------|
| `QUALIFIED_NAME` | Fully qualified table name |
| `VALID_FROM` | When this configuration became active |
| `SCHEDULING_STATE` | RUNNING, SUSPENDED, UPSTREAM_SUSPENDED, etc. |
| `TARGET_LAG` | Configured target lag |
| `WAREHOUSE` | Assigned warehouse |
| `REFRESH_MODE` | AUTO, INCREMENTAL, or FULL |
| `DIRECT_DEPENDENCIES` | Array of upstream objects |

---

## Common Monitoring Queries

### Refresh Success Rate

```sql
SELECT
  name,
  COUNT(*) AS total_refreshes,
  SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS succeeded,
  SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) AS failed,
  ROUND(100.0 * SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
GROUP BY name
ORDER BY success_rate_pct ASC;
```

### Average Refresh Duration

```sql
SELECT
  name,
  refresh_action,
  COUNT(*) AS refresh_count,
  ROUND(AVG(DATEDIFF('second', refresh_start_time, refresh_end_time)), 1) AS avg_duration_sec,
  ROUND(MAX(DATEDIFF('second', refresh_start_time, refresh_end_time)), 1) AS max_duration_sec,
  ROUND(MIN(DATEDIFF('second', refresh_start_time, refresh_end_time)), 1) AS min_duration_sec
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
WHERE state = 'SUCCEEDED'
GROUP BY name, refresh_action
ORDER BY avg_duration_sec DESC;
```

### Lag Violations

Find refreshes that completed after their target:

```sql
SELECT
  name,
  data_timestamp,
  refresh_end_time,
  completion_target,
  DATEDIFF('second', completion_target, refresh_end_time) AS seconds_late
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
WHERE refresh_end_time > completion_target
  AND state = 'SUCCEEDED'
ORDER BY seconds_late DESC;
```

### Recent Failures

```sql
SELECT
  name,
  state,
  state_code,
  state_message,
  query_id,
  refresh_start_time
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  ERROR_ONLY => TRUE,
  DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
ORDER BY refresh_start_time DESC
LIMIT 20;
```

### Refresh Statistics (Row Changes)

```sql
SELECT
  name,
  refresh_start_time,
  refresh_action,
  statistics:numInsertedRows::INT AS rows_inserted,
  statistics:numDeletedRows::INT AS rows_deleted,
  statistics:numCopiedRows::INT AS rows_copied,
  statistics:numAddedPartitions::INT AS partitions_added,
  statistics:numRemovedPartitions::INT AS partitions_removed
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name = 'MY_DYNAMIC_TABLE'
  AND state = 'SUCCEEDED'
ORDER BY refresh_start_time DESC
LIMIT 10;
```

### Pipeline Dependency View

```sql
-- See all DTs and their upstream dependencies
SELECT
  qualified_name,
  target_lag,
  scheduling_state,
  ARRAY_TO_STRING(direct_dependencies, ', ') AS upstream_tables
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_GRAPH_HISTORY())
WHERE valid_to IS NULL  -- Current configuration only
ORDER BY qualified_name;
```

---

## Dashboard Queries

### Executive Summary

```sql
WITH stats AS (
  SELECT
    COUNT(DISTINCT name) AS total_dynamic_tables,
    COUNT(*) AS total_refreshes_7d,
    SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS successful_refreshes,
    SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) AS failed_refreshes,
    SUM(DATEDIFF('second', refresh_start_time, refresh_end_time)) / 3600.0 AS total_compute_hours
  FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
    DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
  ))
  WHERE state IN ('SUCCEEDED', 'FAILED')
)
SELECT
  total_dynamic_tables,
  total_refreshes_7d,
  successful_refreshes,
  failed_refreshes,
  ROUND(100.0 * successful_refreshes / NULLIF(successful_refreshes + failed_refreshes, 0), 2) AS success_rate_pct,
  ROUND(total_compute_hours, 2) AS compute_hours_7d
FROM stats;
```

### Hourly Refresh Activity

```sql
SELECT
  DATE_TRUNC('hour', refresh_start_time) AS hour,
  COUNT(*) AS refresh_count,
  SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS succeeded,
  SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) AS failed
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  DATA_TIMESTAMP_START => DATEADD('day', -1, CURRENT_TIMESTAMP())
))
GROUP BY 1
ORDER BY 1;
```

### Top Resource Consumers

```sql
SELECT
  name,
  COUNT(*) AS refresh_count,
  SUM(DATEDIFF('second', refresh_start_time, refresh_end_time)) AS total_seconds,
  ROUND(SUM(DATEDIFF('second', refresh_start_time, refresh_end_time)) / 3600.0, 2) AS total_hours
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  DATA_TIMESTAMP_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
WHERE state = 'SUCCEEDED'
GROUP BY name
ORDER BY total_seconds DESC
LIMIT 10;
```

---

## Alerting Queries

### Alert: Failed Refreshes

Set up an alert for any failed refresh:

```sql
-- Use with Snowflake Alerts or external monitoring
SELECT
  name,
  state_message,
  query_id,
  refresh_start_time
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  ERROR_ONLY => TRUE,
  DATA_TIMESTAMP_START => DATEADD('hour', -1, CURRENT_TIMESTAMP())
));
```

### Alert: Long-Running Refreshes

```sql
-- Find refreshes taking longer than expected
SELECT
  name,
  refresh_start_time,
  DATEDIFF('minute', refresh_start_time, CURRENT_TIMESTAMP()) AS running_minutes
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE state = 'EXECUTING'
  AND DATEDIFF('minute', refresh_start_time, CURRENT_TIMESTAMP()) > 30;  -- Threshold
```

### Alert: Suspended Dynamic Tables

```sql
SELECT
  qualified_name,
  scheduling_state,
  target_lag
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_GRAPH_HISTORY())
WHERE valid_to IS NULL
  AND scheduling_state != 'RUNNING';
```

---

## Using Query Profile for Refresh Analysis

When you have a `query_id` from refresh history, use Query Profile for deep analysis:

1. **In Snowsight**: Go to Activity → Query History → Search by query_id
2. **Click on the query** to view the Query Profile
3. **Look for**:
   - Most expensive operators
   - Data spilling to disk
   - Inefficient joins
   - Full table scans

### Programmatic Query History Access

```sql
-- Get query details for a specific refresh
SELECT
  query_id,
  query_text,
  execution_status,
  execution_time / 1000 AS seconds,
  bytes_scanned / 1e9 AS gb_scanned,
  rows_produced,
  warehouse_size
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_id = 'YOUR_QUERY_ID_HERE';
```

---

## SHOW DYNAMIC TABLES

Quick overview of all Dynamic Tables:

```sql
SHOW DYNAMIC TABLES;
SHOW DYNAMIC TABLES LIKE 'MENU%';
SHOW DYNAMIC TABLES IN SCHEMA my_db.my_schema;
```

**Key columns**:

| Column | Description |
|--------|-------------|
| `name` | Table name |
| `database_name` | Database |
| `schema_name` | Schema |
| `target_lag` | Configured lag |
| `refresh_mode` | AUTO, INCREMENTAL, FULL |
| `refresh_mode_reason` | Why this mode was chosen |
| `warehouse` | Assigned warehouse |
| `scheduling_state` | RUNNING, SUSPENDED, etc. |
| `owner` | Owning role |

---

## Best Practices

1. **Set up regular monitoring** - Run health checks daily or weekly
2. **Track failure trends** - Investigate any increase in failures
3. **Monitor duration trends** - Catch performance degradation early
4. **Alert on critical failures** - Don't wait for users to report issues
5. **Review compute costs** - Ensure refresh costs align with value delivered
6. **Check lag compliance** - Verify data freshness meets requirements
