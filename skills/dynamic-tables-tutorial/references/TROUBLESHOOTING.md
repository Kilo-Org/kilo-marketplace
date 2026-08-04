# Dynamic Tables Troubleshooting Guide

This guide helps diagnose and resolve common issues with Dynamic Tables.

---

## Refresh Failures

### Symptom: Refresh State is FAILED

**How to identify**:
```sql
SELECT name, state, state_code, state_message, query_id
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE state = 'FAILED'
ORDER BY refresh_start_time DESC
LIMIT 10;
```

**Common causes and solutions**:

#### Cause 1: Warehouse Suspended or Doesn't Exist

```
Error: Warehouse 'COMPUTE_WH' does not exist or not authorized
```

**Solution**:
```sql
-- Check warehouse exists
SHOW WAREHOUSES LIKE 'COMPUTE_WH';

-- If suspended, resume it
ALTER WAREHOUSE COMPUTE_WH RESUME;

-- Or change the DT to use a different warehouse
ALTER DYNAMIC TABLE my_dt SET WAREHOUSE = ANOTHER_WH;
```

#### Cause 2: Insufficient Privileges

```
Error: SQL access control error: Insufficient privileges
```

**Solution**:
```sql
-- Grant necessary privileges
GRANT USAGE ON WAREHOUSE compute_wh TO ROLE my_role;
GRANT SELECT ON TABLE source_table TO ROLE my_role;

-- Check ownership
SHOW DYNAMIC TABLES LIKE 'MY_DT';
-- The owner role needs privileges on all source objects
```

#### Cause 3: Source Object Modified or Dropped

```
Error: Object 'SOURCE_TABLE' does not exist or not authorized
```

**Solution**:
```sql
-- Check if source table exists
SHOW TABLES LIKE 'SOURCE_TABLE';

-- If table was recreated, you may need to recreate the DT
CREATE OR REPLACE DYNAMIC TABLE my_dt ...;
```

#### Cause 4: Query Timeout

```
Error: Statement reached its statement or warehouse timeout
```

**Solution**:
```sql
-- Increase warehouse timeout
ALTER WAREHOUSE compute_wh SET STATEMENT_TIMEOUT_IN_SECONDS = 7200;

-- Or use a larger warehouse
ALTER DYNAMIC TABLE my_dt SET WAREHOUSE = LARGER_WH;

-- Or optimize the query (see Performance guide)
```

---

## Refresh State: UPSTREAM_FAILED

### What It Means

Your Dynamic Table's refresh was skipped because an upstream Dynamic Table failed to refresh.

**How to identify**:
```sql
SELECT name, state, state_message
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE state = 'UPSTREAM_FAILED'
ORDER BY refresh_start_time DESC;
```

**Solution**:
1. Identify the failed upstream table from `state_message`
2. Investigate why that table failed
3. Fix the upstream issue
4. Manually refresh if needed:
   ```sql
   ALTER DYNAMIC TABLE failed_upstream_dt REFRESH;
   ```

---

## Refresh State: CANCELLED

### Common Causes

1. **Manual cancellation** - Someone cancelled the query
2. **Warehouse suspension** - Warehouse suspended during refresh
3. **System maintenance** - Rare, but possible

**How to investigate**:
```sql
SELECT name, state, state_code, state_message, query_id
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE state = 'CANCELLED'
ORDER BY refresh_start_time DESC;
```

Use the `query_id` to check query history for more details.

---

## Dynamic Table Suspended

### Symptom: No Refreshes Occurring

**Check if DT is suspended**:
```sql
SHOW DYNAMIC TABLES LIKE 'MY_DT';
-- Look at the 'scheduling_state' column
```

**Common scheduling states**:
- `RUNNING` - Normal operation
- `SUSPENDED` - Manually suspended
- `UPSTREAM_SUSPENDED` - Upstream DT is suspended

### Causes of Automatic Suspension

Dynamic Tables can be auto-suspended when:
1. Multiple consecutive refresh failures
2. Upstream table changes invalidate the DT
3. Cloning (cloned DTs start suspended)

### Solution: Resume the Dynamic Table

```sql
-- Resume a manually suspended DT
ALTER DYNAMIC TABLE my_dt RESUME;

-- If upstream is suspended, resume that first
ALTER DYNAMIC TABLE upstream_dt RESUME;
```

---

## Data Issues

### Issue: Dynamic Table Has No Data

**Check**:
```sql
SELECT COUNT(*) FROM my_dynamic_table;
-- Returns 0
```

**Possible causes**:

1. **Source table is empty**:
   ```sql
   SELECT COUNT(*) FROM source_table;
   ```

2. **WHERE clause filters everything**:
   ```sql
   -- Check if filter is too restrictive
   SELECT COUNT(*) FROM source_table WHERE <your_filter>;
   ```

3. **Initial refresh hasn't completed**:
   ```sql
   -- Check refresh history
   SELECT state, refresh_start_time
   FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
   WHERE name = 'MY_DYNAMIC_TABLE'
   ORDER BY refresh_start_time DESC
   LIMIT 5;
   ```

### Issue: Data Doesn't Match Expected Results

**Debugging steps**:

1. **Check refresh mode and lag**:
   ```sql
   SHOW DYNAMIC TABLES LIKE 'MY_DT';
   ```

2. **Verify source data**:
   ```sql
   -- Run the DT's query manually against source
   SELECT ... FROM source_table ...;
   -- Compare with DT contents
   ```

3. **Check data timestamp**:
   ```sql
   -- See when the data was captured
   SELECT data_timestamp
   FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
   WHERE name = 'MY_DT'
   ORDER BY refresh_start_time DESC
   LIMIT 1;
   ```

4. **Force a manual refresh**:
   ```sql
   ALTER DYNAMIC TABLE my_dt REFRESH;
   ```

---

## Performance Issues

### Issue: Refreshes Taking Too Long

**Diagnose**:
```sql
-- Check refresh duration
SELECT
  name,
  refresh_action,
  DATEDIFF('minute', refresh_start_time, refresh_end_time) AS duration_minutes
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name = 'MY_DT'
ORDER BY refresh_start_time DESC
LIMIT 10;
```

**Solutions**:
1. Use a larger warehouse
2. Optimize the query (see Performance guide)
3. Check if FULL refresh is happening when INCREMENTAL expected
4. Add clustering if data is poorly organized

### Issue: Unexpected FULL Refresh Instead of INCREMENTAL

**Check why**:
```sql
SHOW DYNAMIC TABLES LIKE 'MY_DT';
-- Look at refresh_mode_reason column
```

**Common reasons**:
- Upstream view definition changed
- Query uses non-incrementalizable constructs
- Snowflake determined FULL is more efficient

---

## Error: "Dynamic table can no longer be refreshed incrementally"

### What It Means

The Dynamic Table was created with incremental refresh support, but something changed that makes incremental refresh impossible now.

### Common Causes

1. **Upstream view definition changed**
2. **Source table was recreated**
3. **Permissions changed on source objects**

### Solution

Recreate the Dynamic Table:
```sql
CREATE OR REPLACE DYNAMIC TABLE my_dt
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
AS
SELECT ... ;  -- Same query
```

---

## Error: "Target lag must be greater than or equal to upstream"

### What It Means

You're trying to create a Dynamic Table with a shorter lag than its upstream dependencies.

### Example

```sql
-- Upstream has 30-minute lag
CREATE DYNAMIC TABLE upstream TARGET_LAG = '30 minutes' ...;

-- This will FAIL
CREATE DYNAMIC TABLE downstream TARGET_LAG = '10 minutes'
AS SELECT * FROM upstream;
-- Error: Target lag must be >= 30 minutes
```

### Solution

Either:
1. Increase the downstream TARGET_LAG
2. Decrease the upstream TARGET_LAG
3. Use DOWNSTREAM for the upstream table

```sql
-- Option 1: Increase downstream lag
CREATE DYNAMIC TABLE downstream TARGET_LAG = '30 minutes' ...;

-- Option 2: Make upstream DOWNSTREAM and control from final table
ALTER DYNAMIC TABLE upstream SET TARGET_LAG = DOWNSTREAM;
CREATE DYNAMIC TABLE downstream TARGET_LAG = '10 minutes' ...;
```

---

## Error: "Object does not exist or not authorized"

### During Creation

The source table or view doesn't exist, or you don't have SELECT privileges.

```sql
-- Check object exists
SHOW TABLES LIKE 'SOURCE_TABLE';

-- Grant privileges if needed
GRANT SELECT ON TABLE source_table TO ROLE my_role;
```

### During Refresh

The source object existed at creation but was dropped or you lost access.

```sql
-- Recreate the DT after restoring the source
CREATE OR REPLACE DYNAMIC TABLE my_dt ...;
```

---

## Checking DT Health

### Comprehensive Health Check Query

```sql
WITH dt_info AS (
  SELECT
    database_name || '.' || schema_name || '.' || name AS full_name,
    name,
    scheduling_state,
    target_lag,
    refresh_mode,
    warehouse
  FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
),
refresh_stats AS (
  SELECT
    name,
    COUNT(*) AS total_refreshes,
    SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS successful,
    SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) AS failed,
    AVG(DATEDIFF('second', refresh_start_time, refresh_end_time)) AS avg_duration_seconds
  FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
  WHERE refresh_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
  GROUP BY name
)
SELECT
  dt.full_name,
  dt.scheduling_state,
  dt.target_lag,
  dt.refresh_mode,
  COALESCE(rs.total_refreshes, 0) AS refreshes_7d,
  COALESCE(rs.successful, 0) AS successful_7d,
  COALESCE(rs.failed, 0) AS failed_7d,
  ROUND(rs.avg_duration_seconds, 1) AS avg_duration_sec
FROM dt_info dt
LEFT JOIN refresh_stats rs ON dt.name = rs.name
ORDER BY dt.full_name;
```

First run: `SHOW DYNAMIC TABLES;`

---

## Getting Help

If you can't resolve an issue:

1. **Gather diagnostics**:
   - SHOW DYNAMIC TABLES output
   - DYNAMIC_TABLE_REFRESH_HISTORY for the failing DT
   - Query ID of the failed refresh
   - Error messages

2. **Check Query Profile**:
   - Use the query_id from refresh history
   - Look for bottlenecks in the Query Profile

3. **Contact Support**:
   - Provide all gathered diagnostics
   - Include the DT definition (CREATE statement)
