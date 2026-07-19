# TARGET_LAG Complete Guide

TARGET_LAG is the most important parameter for Dynamic Tables. It controls data freshness, refresh frequency, and ultimately cost. This guide covers everything you need to know.

---

## What is TARGET_LAG?

TARGET_LAG specifies the **maximum acceptable staleness** of your Dynamic Table's data compared to its source tables.

If you set `TARGET_LAG = '5 minutes'`:
- The data in your Dynamic Table will never be more than 5 minutes behind the source
- Snowflake will schedule refreshes to maintain this freshness
- The actual lag might be less than 5 minutes, but never more

---

## TARGET_LAG Options

### Time-Based Lag

Specify how fresh the data must be:

```sql
TARGET_LAG = '60 seconds'    -- Minimum allowed
TARGET_LAG = '5 minutes'     -- Near real-time dashboards
TARGET_LAG = '1 hour'        -- Hourly reporting
TARGET_LAG = '24 hours'      -- Daily batch processing
TARGET_LAG = '7 days'        -- Weekly summaries
```

**Valid units**: `seconds`, `minutes`, `hours`, `days`

**Minimum value**: 60 seconds (1 minute)

### DOWNSTREAM Lag

```sql
TARGET_LAG = DOWNSTREAM
```

This special value means: "Only refresh this table when a downstream Dynamic Table needs it."

Use DOWNSTREAM for intermediate tables in a pipeline where only the final output needs time-based freshness.

---

## How TARGET_LAG Affects Refresh Scheduling

Snowflake doesn't refresh exactly at TARGET_LAG intervals. Instead, it uses a **smart scheduling algorithm**:

### Example: 4-hour TARGET_LAG

If you set `TARGET_LAG = '4 hours'`, Snowflake might:
- Refresh every 3.5 hours
- Or every 2 hours if there's heavy activity
- Or less frequently if there are no source changes

The goal is to **guarantee** the lag never exceeds 4 hours, not to refresh exactly every 4 hours.

### Factors Affecting Schedule

1. **Source data changes**: More changes may trigger more frequent refreshes
2. **Refresh duration**: If refresh takes 30 minutes, scheduling accounts for this
3. **Downstream dependencies**: Coordinated with dependent tables
4. **System load**: May adjust slightly for cluster efficiency

---

## Choosing the Right TARGET_LAG

### Decision Framework

| Use Case | Recommended Lag | Rationale |
|----------|-----------------|-----------|
| Real-time dashboards | 1-5 minutes | Users expect current data |
| Operational reporting | 15-30 minutes | Good balance of freshness and cost |
| Business analytics | 1-4 hours | Hourly freshness usually sufficient |
| Historical analysis | 12-24 hours | Data doesn't need to be real-time |
| Archival/compliance | 24+ hours | Infrequent updates acceptable |

### Cost vs. Freshness Tradeoff

```
Shorter Lag = More Refreshes = Higher Cost = Fresher Data
Longer Lag = Fewer Refreshes = Lower Cost = Staler Data
```

**Rule of thumb**: Start with a longer lag and decrease only if business requirements demand fresher data.

### Questions to Ask

1. **How fresh does this data actually need to be?**
   - Don't assume "real-time" - many use cases work fine with hourly data

2. **What's the cost of stale data?**
   - Financial impact? User frustration? Incorrect decisions?

3. **How large is the source data?**
   - Larger tables = longer refresh = need more buffer

4. **How expensive are the transformations?**
   - Complex queries need more compute time

---

## DOWNSTREAM Deep Dive

### When to Use DOWNSTREAM

Use `TARGET_LAG = DOWNSTREAM` when:
- The table is an **intermediate step** in a pipeline
- Only **downstream tables** actually consume the data
- You want to **minimize unnecessary refreshes**

### How DOWNSTREAM Works

```sql
-- This table refreshes ONLY when dashboard_metrics needs it
CREATE DYNAMIC TABLE cleaned_events
  TARGET_LAG = DOWNSTREAM
  WAREHOUSE = ETL_WH
AS SELECT * FROM raw_events WHERE is_valid = TRUE;

-- This table controls the pipeline's refresh schedule
CREATE DYNAMIC TABLE dashboard_metrics
  TARGET_LAG = '15 minutes'
  WAREHOUSE = ETL_WH
AS SELECT COUNT(*) FROM cleaned_events;
```

When `dashboard_metrics` refreshes:
1. Snowflake checks if `cleaned_events` needs to be updated
2. If yes, `cleaned_events` refreshes first
3. Then `dashboard_metrics` refreshes using the fresh data

### DOWNSTREAM Chains

In a pipeline with all DOWNSTREAM tables:

```sql
A (DOWNSTREAM) → B (DOWNSTREAM) → C (DOWNSTREAM) → D ('1 hour')
```

Only D has a time-based lag. When D needs to refresh:
- Snowflake traces back through C, B, A
- Refreshes any that need updating
- Maintains snapshot isolation throughout

**Important**: If ALL tables in a DAG have `TARGET_LAG = DOWNSTREAM`, no automatic refreshes occur. At least one table needs a time-based lag.

---

## TARGET_LAG in Dependencies

### Lag Inheritance Rules

A Dynamic Table's TARGET_LAG must be **greater than or equal to** the lag of any Dynamic Tables it reads from.

```sql
-- This is VALID
CREATE DYNAMIC TABLE upstream TARGET_LAG = '5 minutes' ...;
CREATE DYNAMIC TABLE downstream TARGET_LAG = '10 minutes'
  AS SELECT * FROM upstream;  -- ✓ 10 min >= 5 min

-- This is INVALID
CREATE DYNAMIC TABLE upstream TARGET_LAG = '30 minutes' ...;
CREATE DYNAMIC TABLE downstream TARGET_LAG = '5 minutes'
  AS SELECT * FROM upstream;  -- ✗ 5 min < 30 min
```

**Why?** If upstream data is only guaranteed fresh within 30 minutes, downstream can't promise better than 30 minutes.

### Mixed Lag Pipelines

```sql
-- Upstream with different lags
CREATE DYNAMIC TABLE fast_source TARGET_LAG = '1 minute' ...;
CREATE DYNAMIC TABLE slow_source TARGET_LAG = '1 hour' ...;

-- Downstream must respect the SLOWEST upstream
CREATE DYNAMIC TABLE combined TARGET_LAG = '1 hour'  -- Must be >= 1 hour
  AS SELECT * FROM fast_source JOIN slow_source ON ...;
```

---

## Changing TARGET_LAG

You can change TARGET_LAG without recreating the table:

```sql
-- Increase freshness (more frequent refresh)
ALTER DYNAMIC TABLE my_dt SET TARGET_LAG = '5 minutes';

-- Decrease freshness (less frequent refresh)
ALTER DYNAMIC TABLE my_dt SET TARGET_LAG = '4 hours';

-- Switch to DOWNSTREAM
ALTER DYNAMIC TABLE my_dt SET TARGET_LAG = DOWNSTREAM;
```

Changes take effect on the next refresh cycle.

---

## Monitoring Lag

### Check Current Lag

```sql
-- See the actual vs target lag
SELECT
  name,
  target_lag_seconds,
  DATEDIFF('second', data_timestamp, CURRENT_TIMESTAMP()) AS actual_lag_seconds
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name = 'MY_DYNAMIC_TABLE'
ORDER BY refresh_start_time DESC
LIMIT 1;
```

### Check if Lag is Being Met

```sql
-- Find refreshes that took longer than expected
SELECT
  name,
  data_timestamp,
  refresh_start_time,
  completion_target,
  CASE
    WHEN refresh_end_time > completion_target THEN 'MISSED'
    ELSE 'MET'
  END AS lag_status
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name = 'MY_DYNAMIC_TABLE'
ORDER BY refresh_start_time DESC
LIMIT 10;
```

---

## Common Mistakes

### Mistake 1: Lag Too Short for Query Complexity

```sql
-- BAD: Complex aggregation with 1 minute lag
CREATE DYNAMIC TABLE complex_agg
  TARGET_LAG = '1 minute'  -- Refresh might take 5 minutes!
AS
SELECT ... (very complex query over huge data) ...;
```

**Fix**: Ensure TARGET_LAG is longer than worst-case refresh duration.

### Mistake 2: All Tables Set to DOWNSTREAM

```sql
-- BAD: No table controls the schedule
CREATE DYNAMIC TABLE a TARGET_LAG = DOWNSTREAM ...;
CREATE DYNAMIC TABLE b TARGET_LAG = DOWNSTREAM AS SELECT * FROM a;
CREATE DYNAMIC TABLE c TARGET_LAG = DOWNSTREAM AS SELECT * FROM b;
-- Nothing ever refreshes automatically!
```

**Fix**: At least one table (usually the final consumer) needs a time-based lag.

### Mistake 3: Unnecessary Short Lag

```sql
-- BAD: 1-minute lag for monthly reporting
CREATE DYNAMIC TABLE monthly_report
  TARGET_LAG = '1 minute'  -- Wasteful!
AS
SELECT MONTH(date), SUM(sales) FROM ... GROUP BY 1;
```

**Fix**: Match TARGET_LAG to actual business requirements.

---

## Best Practices

1. **Start Long, Shorten If Needed**
   - Begin with `'1 hour'` or `'4 hours'`
   - Only shorten if users complain about staleness

2. **Use DOWNSTREAM for Intermediate Tables**
   - Only final consumer tables need time-based lag
   - Reduces unnecessary refresh operations

3. **Consider Refresh Duration**
   - TARGET_LAG should be at least 2x expected refresh time
   - Monitor refresh duration and adjust

4. **Align with Business Cycles**
   - Daily reports: `'24 hours'`
   - Shift changes: `'8 hours'`
   - Meeting prep: `'1 hour'`

5. **Monitor and Adjust**
   - Review DYNAMIC_TABLE_REFRESH_HISTORY regularly
   - Adjust lag based on actual usage patterns
