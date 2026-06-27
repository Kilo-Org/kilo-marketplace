# Dynamic Tables Performance Optimization

This guide covers best practices for optimizing Dynamic Table performance, reducing costs, and ensuring reliable refresh operations.

---

## Performance Fundamentals

### What Affects Refresh Performance?

1. **Query complexity** - Joins, aggregations, functions used
2. **Data volume** - Source table size and change rate
3. **Refresh mode** - INCREMENTAL vs FULL
4. **Warehouse size** - Compute resources available
5. **Data organization** - Clustering and micro-partition structure

### The Performance Equation

```
Refresh Time = Data Scanned / Warehouse Throughput + Processing Overhead
```

To optimize, you either:
- Reduce data scanned (incremental refresh, filtering, clustering)
- Increase throughput (larger warehouse)
- Reduce overhead (simpler queries)

---

## Query Optimization

### Keep Queries Simple

**Avoid over-engineering**. The simplest query that produces correct results is usually the best.

```sql
-- Overly complex (harder to optimize)
CREATE DYNAMIC TABLE my_dt AS
SELECT
  COALESCE(NULLIF(TRIM(name), ''), 'Unknown') AS name,
  CASE WHEN amount > 0 THEN amount ELSE 0 END AS amount,
  ...
FROM source;

-- Simpler (easier to optimize)
CREATE DYNAMIC TABLE my_dt AS
SELECT name, amount FROM source WHERE amount > 0;
```

### Optimize Joins

Joins are expensive. Optimize them:

1. **Filter early** - Apply WHERE before JOIN
   ```sql
   -- Better: Filter before join
   SELECT a.*, b.name
   FROM (SELECT * FROM table_a WHERE active = TRUE) a
   JOIN table_b b ON a.id = b.id;
   ```

2. **Use appropriate join type** - Don't use OUTER when INNER works
   ```sql
   -- Only use LEFT JOIN if you need unmatched rows
   SELECT a.*, b.name
   FROM a
   INNER JOIN b ON a.id = b.id;  -- Not LEFT if you don't need nulls
   ```

3. **Join on clustered columns** - If possible, join on columns that are clustered

### Optimize Aggregations

1. **Pre-filter before aggregating**
   ```sql
   -- Good: Filter first
   SELECT category, SUM(amount)
   FROM source
   WHERE date >= '2024-01-01'  -- Reduces data before aggregation
   GROUP BY category;
   ```

2. **Avoid unnecessary precision**
   ```sql
   -- Excessive precision
   SELECT AVG(amount) AS avg_amt  -- Returns many decimal places

   -- Better
   SELECT ROUND(AVG(amount), 2) AS avg_amt
   ```

### Use Supported Constructs for Incremental

If you want incremental refresh, avoid:
- `UNION` (use `UNION ALL` instead)
- Non-deterministic functions (`RANDOM()`, `UUID_STRING()`)
- Complex recursive CTEs
- Certain window function patterns

See `REFRESH_MODES.md` for the full list.

---

## Warehouse Sizing

### Choosing the Right Size

| Source Data Size | Recommended Start | Notes |
|------------------|-------------------|-------|
| < 1 GB | X-Small | Minimal data, simple queries |
| 1 - 10 GB | Small | Moderate data |
| 10 - 100 GB | Medium | Larger datasets |
| 100 GB - 1 TB | Large | Significant data |
| > 1 TB | X-Large+ | Very large datasets |

**Start small and scale up** based on actual refresh duration.

### Monitoring Warehouse Utilization

```sql
-- Check warehouse load during refreshes
SELECT
  query_id,
  warehouse_name,
  warehouse_size,
  execution_time / 1000 AS seconds,
  bytes_scanned / 1e9 AS gb_scanned,
  rows_produced
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_tag LIKE 'DYNAMIC_TABLE_REFRESH%'
  AND start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY execution_time DESC
LIMIT 20;
```

### Dedicated Refresh Warehouse

For critical pipelines, use a dedicated warehouse:

```sql
-- Create dedicated warehouse
CREATE WAREHOUSE dt_refresh_wh
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- Use for dynamic tables
CREATE DYNAMIC TABLE my_dt
  WAREHOUSE = dt_refresh_wh
  ...;
```

Benefits:
- Isolated from user queries
- Predictable performance
- Easier cost attribution

---

## Clustering

### When to Use Clustering

Clustering improves performance when:
- Source tables are large (> 1 TB)
- Queries filter on specific columns
- Data is naturally time-series or categorical

### Adding Clustering to Dynamic Tables

```sql
CREATE OR REPLACE DYNAMIC TABLE my_dt
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
  CLUSTER BY (date_column, category)  -- Cluster by frequently filtered columns
AS
SELECT ...;
```

### Clustering Best Practices

1. **Cluster by filter columns** - Columns in WHERE clauses
2. **Limit to 3-4 columns** - More isn't better
3. **Order by cardinality** - Lower cardinality first
4. **Monitor automatic clustering**:
   ```sql
   SELECT *
   FROM TABLE(INFORMATION_SCHEMA.AUTOMATIC_CLUSTERING_HISTORY(
     TABLE_NAME => 'MY_DT'
   ));
   ```

---

## Immutability Constraints

For tables with historical data that never changes, use immutability constraints:

```sql
CREATE DYNAMIC TABLE sales_analysis
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
  IMMUTABLE WHERE (sale_date < CURRENT_DATE - 90)
AS
SELECT * FROM sales;
```

### Benefits

- Rows matching the IMMUTABLE condition are **never re-scanned**
- Significantly reduces refresh time for large historical tables
- Ideal for time-series data with append-only historical portions

### When to Use

- Time-series data where history doesn't change
- Tables with a clear "frozen" vs "active" partition
- Large tables where most data is historical

---

## Pipeline Architecture

### Break Down Complex Pipelines

Instead of one massive Dynamic Table, use multiple stages:

```sql
-- BAD: One huge DT with everything
CREATE DYNAMIC TABLE final_output AS
SELECT /* complex transformations */ FROM raw_data;

-- BETTER: Multiple stages
CREATE DYNAMIC TABLE stage1_clean TARGET_LAG = DOWNSTREAM AS
SELECT * FROM raw_data WHERE is_valid = TRUE;

CREATE DYNAMIC TABLE stage2_transform TARGET_LAG = DOWNSTREAM AS
SELECT /* transformations */ FROM stage1_clean;

CREATE DYNAMIC TABLE stage3_aggregate TARGET_LAG = '15 minutes' AS
SELECT /* aggregations */ FROM stage2_transform;
```

### Benefits of Staged Pipelines

1. **Easier debugging** - Identify which stage fails
2. **Better incremental refresh** - Each stage optimized separately
3. **Reusability** - Intermediate stages can serve multiple outputs
4. **Isolation** - Problems in one stage don't affect others

### Use DOWNSTREAM for Intermediate Tables

Only the final consumer needs a time-based TARGET_LAG:

```sql
-- Intermediate stages
CREATE DYNAMIC TABLE stage1 TARGET_LAG = DOWNSTREAM ...;
CREATE DYNAMIC TABLE stage2 TARGET_LAG = DOWNSTREAM ...;

-- Final stage controls the schedule
CREATE DYNAMIC TABLE final TARGET_LAG = '15 minutes' ...;
```

---

## Monitoring and Tuning

### Regular Performance Reviews

Run weekly:

```sql
-- Top 10 slowest refreshes
SELECT
  name,
  refresh_action,
  DATEDIFF('second', refresh_start_time, refresh_end_time) AS duration_sec,
  refresh_start_time
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE state = 'SUCCEEDED'
  AND refresh_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY duration_sec DESC
LIMIT 10;
```

### Identify Full Refreshes That Should Be Incremental

```sql
-- Find DTs doing FULL refresh
SELECT name, refresh_action, COUNT(*) as count
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE refresh_start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY name, refresh_action
HAVING refresh_action = 'FULL'
ORDER BY count DESC;
```

If a table is doing FULL when you expect INCREMENTAL, check `refresh_mode_reason` in SHOW DYNAMIC TABLES.

### Cost Tracking

```sql
-- Estimate refresh costs by DT
SELECT
  name,
  COUNT(*) AS refresh_count,
  SUM(DATEDIFF('second', refresh_start_time, refresh_end_time)) / 3600.0 AS total_hours
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE state = 'SUCCEEDED'
  AND refresh_start_time > DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY name
ORDER BY total_hours DESC
LIMIT 20;
```

---

## Common Performance Antipatterns

### Antipattern 1: SELECT *

```sql
-- Bad
CREATE DYNAMIC TABLE dt AS SELECT * FROM source;

-- Good: Only select needed columns
CREATE DYNAMIC TABLE dt AS SELECT id, name, amount FROM source;
```

### Antipattern 2: Unnecessary Sorting

```sql
-- Bad: ORDER BY in DT definition (sorted during refresh, not query)
CREATE DYNAMIC TABLE dt AS
SELECT * FROM source ORDER BY date DESC;

-- Good: Sort at query time if needed
CREATE DYNAMIC TABLE dt AS SELECT * FROM source;
-- Then: SELECT * FROM dt ORDER BY date DESC;
```

### Antipattern 3: Over-Aggressive TARGET_LAG

```sql
-- Bad: 1-minute lag for data used weekly
CREATE DYNAMIC TABLE weekly_report
  TARGET_LAG = '1 minute'
AS SELECT ...;

-- Good: Match lag to actual requirements
CREATE DYNAMIC TABLE weekly_report
  TARGET_LAG = '4 hours'
AS SELECT ...;
```

### Antipattern 4: Missing Filters

```sql
-- Bad: Processing all historical data every refresh
CREATE DYNAMIC TABLE dt AS SELECT * FROM events;

-- Good: Filter to relevant window
CREATE DYNAMIC TABLE dt AS
SELECT * FROM events WHERE event_time >= DATEADD('day', -30, CURRENT_DATE);
```

---

## Quick Wins Checklist

- [ ] Use INCREMENTAL refresh mode where possible
- [ ] Set appropriate TARGET_LAG (not too aggressive)
- [ ] Use DOWNSTREAM for intermediate tables
- [ ] Only SELECT columns you need
- [ ] Add WHERE clauses to filter early
- [ ] Consider clustering for large tables
- [ ] Use immutability constraints for historical data
- [ ] Break complex queries into stages
- [ ] Use appropriately sized warehouses
- [ ] Monitor refresh duration regularly
