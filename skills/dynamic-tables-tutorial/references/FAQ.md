# Dynamic Tables FAQ

Frequently asked questions about Snowflake Dynamic Tables.

---

## General Questions

### What is a Dynamic Table?

A Dynamic Table is a table whose contents are defined by a query and automatically refreshed based on a target freshness (TARGET_LAG). Unlike regular tables that require manual INSERT/UPDATE statements, Dynamic Tables stay synchronized with their source data automatically.

### How is a Dynamic Table different from a View?

| View | Dynamic Table |
|------|---------------|
| No data stored | Data is materialized |
| Query runs every access | Query ran at refresh time |
| Always current | Fresh within TARGET_LAG |
| Can be slow for complex queries | Pre-computed, fast queries |

### How is a Dynamic Table different from a Materialized View?

| Materialized View | Dynamic Table |
|-------------------|---------------|
| Background refresh (no control) | TARGET_LAG controls freshness |
| No incremental refresh | Incremental refresh when possible |
| Cannot chain (MV can't read MV) | Can chain (DT can read DT) |
| More query restrictions | Fewer query restrictions |

### Can I query a Dynamic Table while it's refreshing?

Yes! Queries see the last successful refresh. The new refresh happens in the background and becomes visible only after it completes successfully.

---

## TARGET_LAG Questions

### What's the minimum TARGET_LAG I can set?

60 seconds (1 minute) is the minimum.

### Does TARGET_LAG guarantee exact refresh times?

No. TARGET_LAG is a maximum staleness guarantee. If you set `TARGET_LAG = '5 minutes'`, the data will never be more than 5 minutes stale, but it might be fresher. Snowflake schedules refreshes intelligently to stay within the target.

### What does TARGET_LAG = DOWNSTREAM mean?

It means "only refresh when a downstream Dynamic Table needs me to." Use this for intermediate tables in a pipeline where only the final output needs time-based freshness.

### Can I have different TARGET_LAGs for different tables in a pipeline?

Yes, but downstream tables must have a TARGET_LAG >= their upstream tables. If TableA has `TARGET_LAG = '30 minutes'`, any table reading from TableA must have at least 30 minutes lag.

---

## Refresh Questions

### What's the difference between INCREMENTAL and FULL refresh?

**INCREMENTAL**: Only processes rows that changed since the last refresh. Much faster for large tables with few changes.

**FULL**: Recomputes the entire table from scratch. Required when incremental isn't possible or efficient.

### How do I know which refresh mode my table uses?

```sql
SHOW DYNAMIC TABLES LIKE 'MY_TABLE';
-- Look at refresh_mode and refresh_mode_reason columns
```

### Can I force a manual refresh?

Yes:
```sql
ALTER DYNAMIC TABLE my_table REFRESH;
```

### What happens if a refresh fails?

The Dynamic Table continues serving the last successful refresh. The failed refresh is logged in DYNAMIC_TABLE_REFRESH_HISTORY. Depending on the failure type, Snowflake may retry or suspend the table.

### Why is my table doing FULL refresh when I expected INCREMENTAL?

Check `refresh_mode_reason` in SHOW DYNAMIC TABLES. Common reasons:
- Query uses non-incrementalizable constructs
- Upstream table changed in an incompatible way
- Snowflake determined FULL is more efficient for your data size

---

## Creation and Management

### How do I create a Dynamic Table?

```sql
CREATE DYNAMIC TABLE my_dt
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
AS
SELECT ... FROM source_table;
```

### How do I change the TARGET_LAG after creation?

```sql
ALTER DYNAMIC TABLE my_dt SET TARGET_LAG = '30 minutes';
```

### How do I change the REFRESH_MODE after creation?

You cannot change REFRESH_MODE with ALTER. You must recreate the table:
```sql
CREATE OR REPLACE DYNAMIC TABLE my_dt
  REFRESH_MODE = FULL
  ...;
```

### How do I suspend/resume a Dynamic Table?

```sql
-- Suspend (stop automatic refreshes)
ALTER DYNAMIC TABLE my_dt SUSPEND;

-- Resume (restart automatic refreshes)
ALTER DYNAMIC TABLE my_dt RESUME;
```

### How do I drop a Dynamic Table?

```sql
DROP DYNAMIC TABLE my_dt;
```

---

## Pipeline Questions

### Can a Dynamic Table read from another Dynamic Table?

Yes! This is a key advantage over Materialized Views. You can chain Dynamic Tables to create multi-stage pipelines.

### What happens to downstream tables if an upstream table fails?

Downstream tables will have state `UPSTREAM_FAILED` and won't refresh until the upstream is fixed.

### How do I see the dependencies between Dynamic Tables?

```sql
SELECT
  qualified_name,
  ARRAY_TO_STRING(direct_dependencies, ', ') AS upstream_tables
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_GRAPH_HISTORY())
WHERE valid_to IS NULL;
```

---

## Performance Questions

### How do I make my Dynamic Table refresh faster?

1. Use a larger warehouse
2. Ensure queries are optimized for incremental refresh
3. Add clustering on frequently filtered columns
4. Use IMMUTABLE WHERE for historical data
5. Filter early in the query to reduce data scanned

### Does TARGET_LAG affect cost?

Yes. Shorter TARGET_LAG = more frequent refreshes = higher compute cost. Choose the longest lag that meets your requirements.

### How do I see how long refreshes take?

```sql
SELECT
  name,
  DATEDIFF('second', refresh_start_time, refresh_end_time) AS duration_sec,
  refresh_start_time
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name = 'MY_TABLE'
ORDER BY refresh_start_time DESC;
```

---

## Permissions Questions

### What privileges do I need to create a Dynamic Table?

- CREATE DYNAMIC TABLE on the schema
- USAGE on the warehouse
- SELECT on all source tables/views

### Who runs the refresh queries?

The role that owns the Dynamic Table. The owner's privileges are used during refresh.

### How do I transfer ownership of a Dynamic Table?

```sql
GRANT OWNERSHIP ON DYNAMIC TABLE my_dt TO ROLE new_owner;
```

---

## Troubleshooting Questions

### My Dynamic Table has no data. Why?

1. Source table might be empty
2. WHERE clause might filter all rows
3. Initial refresh might not have completed
4. Check DYNAMIC_TABLE_REFRESH_HISTORY for failures

### Why am I getting "Object does not exist" errors?

The source table was dropped or you lost SELECT privileges. Check that all source objects exist and you have access.

### My Dynamic Table is suspended. How do I fix it?

```sql
-- Check why it's suspended
SHOW DYNAMIC TABLES LIKE 'MY_TABLE';

-- Resume it
ALTER DYNAMIC TABLE my_table RESUME;
```

If there's an underlying issue (failed refreshes, upstream problems), fix that first.

### How do I debug a failing refresh?

1. Check the error in DYNAMIC_TABLE_REFRESH_HISTORY
2. Get the query_id from the failed refresh
3. Look at the query in Query History
4. Use Query Profile to identify the issue

---

## Comparison Questions

### When should I use Streams + Tasks instead of Dynamic Tables?

Use Streams + Tasks when:
- You need exact schedule control (CRON)
- You need complex procedural logic
- You need multiple consumers of changes
- You need to preserve change history

### When should I use a regular View instead?

Use a View when:
- Data must always be 100% current
- Query is simple and fast
- Storage cost is a concern
- You don't need materialized results

### Can I use Dynamic Tables with external tables?

Yes, Dynamic Tables can read from external tables. The refresh will re-scan the external storage based on TARGET_LAG.

---

## Quick Reference

### Essential Commands

```sql
-- Create
CREATE DYNAMIC TABLE dt TARGET_LAG='1h' WAREHOUSE=wh AS SELECT...;

-- View
SHOW DYNAMIC TABLES;

-- Modify lag
ALTER DYNAMIC TABLE dt SET TARGET_LAG = '30m';

-- Manual refresh
ALTER DYNAMIC TABLE dt REFRESH;

-- Suspend/Resume
ALTER DYNAMIC TABLE dt SUSPEND;
ALTER DYNAMIC TABLE dt RESUME;

-- Drop
DROP DYNAMIC TABLE dt;

-- Check history
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY());
```

---

## Getting the Latest Documentation

### Official Snowflake Documentation

The most up-to-date information is always in the official Snowflake docs:

| Topic | URL |
|-------|-----|
| Dynamic Tables Overview | https://docs.snowflake.com/en/user-guide/dynamic-tables-about |
| CREATE DYNAMIC TABLE | https://docs.snowflake.com/en/sql-reference/sql/create-dynamic-table |
| ALTER DYNAMIC TABLE | https://docs.snowflake.com/en/sql-reference/sql/alter-dynamic-table |
| Dynamic Table Refresh | https://docs.snowflake.com/en/user-guide/dynamic-tables-refresh |
| Monitoring Dynamic Tables | https://docs.snowflake.com/en/user-guide/dynamic-tables-monitor |
| Dynamic Table Tasks & Graphs | https://docs.snowflake.com/en/user-guide/dynamic-tables-tasks-graphs |

### How to Fetch Latest Docs in Cortex Code

Ask the agent to fetch the latest documentation:

```
"Fetch the latest docs for Dynamic Tables from Snowflake"
"What's new with Dynamic Tables?"
"Get the current documentation for TARGET_LAG"
```

The agent can use `web_fetch` to retrieve the most current information directly from Snowflake's documentation site.

### Release Notes

Check for new features and changes:

| Resource | URL |
|----------|-----|
| Snowflake Release Notes | https://docs.snowflake.com/en/release-notes |
| Data Engineering Features | https://docs.snowflake.com/en/release-notes/new-features#data-engineering |
| BCR (Behavior Change) Bundles | https://docs.snowflake.com/en/release-notes/bcr-bundles |

### SNOWFLAKE_LEARNING Environment

For the learning environment used in this tutorial:

| Resource | URL |
|----------|-----|
| Learning Environment (BCR-1992) | https://docs.snowflake.com/en/release-notes/bcr-bundles/un-bundled/bcr-1992 |
| Snowsight Templates | https://docs.snowflake.com/en/user-guide/ui-snowsight/snowsight-templates |

### Related Documentation

| Topic | URL |
|-------|-----|
| Streams | https://docs.snowflake.com/en/user-guide/streams |
| Tasks | https://docs.snowflake.com/en/user-guide/tasks |
| Materialized Views | https://docs.snowflake.com/en/user-guide/views-materialized |
| Data Pipelines | https://docs.snowflake.com/en/user-guide/data-pipelines |

### Staying Current

1. **Bookmark the docs**: Save the Dynamic Tables overview page for quick reference
2. **Check release notes**: Review monthly for new features
3. **Ask in Cortex Code**: The agent can fetch latest docs on demand
4. **Snowflake Community**: https://community.snowflake.com for discussions and tips
