# Dynamic Tables Deep Dive

This document provides comprehensive coverage of Snowflake Dynamic Tables - what they are, how they work, and when to use them.

---

## What Are Dynamic Tables?

Dynamic Tables are a declarative way to define data transformations in Snowflake. Unlike traditional ETL pipelines where you write code to:
1. Detect changes in source data
2. Transform the data
3. Load it into a target table
4. Schedule and monitor the process

Dynamic Tables let you simply declare: **"I want this query's results, kept fresh within X time."**

Snowflake handles all the complexity automatically:
- Change detection
- Incremental processing (when possible)
- Scheduling refreshes
- Managing dependencies between tables

### The Core Concept

Think of a Dynamic Table as a **materialized query result that stays fresh**. You define:
1. **What data you want** (the SELECT query)
2. **How fresh it should be** (TARGET_LAG)
3. **What compute to use** (WAREHOUSE)

Snowflake handles everything else.

---

## How Dynamic Tables Work Internally

### The Automated Refresh Process

When you create a Dynamic Table, Snowflake:

1. **Analyzes your query** to understand dependencies and determine if incremental refresh is possible
2. **Creates an initial snapshot** by running the full query
3. **Monitors source tables** for changes
4. **Schedules refreshes** based on TARGET_LAG to maintain freshness
5. **Executes refreshes** using the specified warehouse, preferring incremental when possible

### The Refresh Cycle

```
Source Data Changes → Change Detection → Refresh Scheduled → Refresh Executed → DT Updated
```

The refresh doesn't happen instantly when source data changes. Instead, Snowflake batches changes and refreshes periodically to stay within TARGET_LAG.

### Snapshot Isolation

Dynamic Tables guarantee **snapshot isolation**. When a refresh runs:
- All source tables are read at the **same point in time**
- Even if source tables are updating during the refresh, the DT sees a consistent snapshot
- This prevents data inconsistencies in complex pipelines

For example, if DT_C reads from DT_A and DT_B:
```
DT_A ──┐
       ├──► DT_C (sees consistent snapshot of A and B)
DT_B ──┘
```

---

## Key Properties of Dynamic Tables

### TARGET_LAG

Controls how fresh the data should be. Options:
- **Time-based**: `'1 minute'`, `'5 minutes'`, `'1 hour'`, `'24 hours'`
- **DOWNSTREAM**: Refresh only when downstream tables need it

See `TARGET_LAG_GUIDE.md` for detailed guidance.

### WAREHOUSE

The virtual warehouse that performs refresh operations. Considerations:
- Must have USAGE privilege on the warehouse
- Warehouse size affects refresh speed
- Consider dedicated warehouses for large pipelines

### REFRESH_MODE

How the table is refreshed:
- **AUTO** (default): Snowflake chooses the best approach
- **INCREMENTAL**: Only process changed data
- **FULL**: Recompute the entire table

See `REFRESH_MODES.md` for detailed guidance.

### INITIALIZE

When the initial data population occurs:
- **ON_CREATE** (default): Populate immediately when created
- **ON_SCHEDULE**: Populate during the first scheduled refresh

---

## When to Use Dynamic Tables

### Ideal Use Cases

1. **Data Transformation Pipelines**
   - ETL/ELT workflows
   - Data warehouse dimensional modeling
   - Feature engineering for ML

2. **Aggregation and Summarization**
   - Dashboard backing tables
   - Report pre-computation
   - KPI materialization

3. **Slowly Changing Dimensions (SCDs)**
   - Type 1 SCDs (overwrite)
   - Type 2 SCDs (historical tracking)

4. **Change Data Capture (CDC)**
   - Simpler alternative to Streams + Tasks
   - Automatic change propagation

5. **Data Freshness Requirements**
   - When data needs to be "near real-time" but not instant
   - When you need control over how stale data can be

### When NOT to Use Dynamic Tables

1. **Real-time requirements** (sub-second freshness)
   - Use Streams + Tasks or Snowpipe Streaming instead

2. **Simple one-off queries**
   - Just use a regular VIEW

3. **Exact schedule requirements**
   - If you need refreshes at exact times (e.g., "every day at 2 AM")
   - Use Tasks with CRON schedules instead

4. **Complex procedural logic**
   - If transformation requires loops, conditionals, or multi-step logic
   - Use Stored Procedures + Tasks instead

---

## Dynamic Tables vs Other Objects

### vs Regular Tables

| Aspect | Regular Table | Dynamic Table |
|--------|--------------|---------------|
| Data population | Manual INSERT/UPDATE | Automatic from query |
| Freshness | Point-in-time snapshot | Continuously refreshed |
| Maintenance | Manual | Automatic |

### vs Views

| Aspect | View | Dynamic Table |
|--------|------|---------------|
| Storage | No data stored | Data materialized |
| Query cost | Full query each time | Pre-computed |
| Freshness | Always current | Within TARGET_LAG |
| Complex queries | Can be slow | Pre-computed, fast |

### vs Materialized Views

| Aspect | Materialized View | Dynamic Table |
|--------|------------------|---------------|
| Refresh control | Background, no control | TARGET_LAG control |
| Incremental refresh | No | Yes (when possible) |
| Can chain | No (MV can't read MV) | Yes (DT can read DT) |
| Query restrictions | Many | Fewer |

### vs Streams + Tasks

| Aspect | Streams + Tasks | Dynamic Table |
|--------|----------------|---------------|
| Code complexity | High (MERGE logic) | Low (just SELECT) |
| Objects to manage | 3+ (stream, task, table) | 1 (dynamic table) |
| Scheduling | Explicit (CRON) | Automatic (TARGET_LAG) |
| Fine-grained control | More | Less |

---

## Chaining Dynamic Tables

One of the most powerful features is the ability to chain Dynamic Tables. Unlike Materialized Views, a Dynamic Table can read from other Dynamic Tables.

### Example: Multi-Stage Pipeline

```sql
-- Stage 1: Clean raw data
CREATE DYNAMIC TABLE cleaned_data
  TARGET_LAG = DOWNSTREAM
  WAREHOUSE = ETL_WH
AS
SELECT * FROM raw_data WHERE is_valid = TRUE;

-- Stage 2: Aggregate
CREATE DYNAMIC TABLE daily_summary
  TARGET_LAG = DOWNSTREAM
  WAREHOUSE = ETL_WH
AS
SELECT date, SUM(amount) as total
FROM cleaned_data
GROUP BY date;

-- Stage 3: Final output (controls the pipeline)
CREATE DYNAMIC TABLE dashboard_data
  TARGET_LAG = '15 minutes'
  WAREHOUSE = ETL_WH
AS
SELECT * FROM daily_summary WHERE date >= CURRENT_DATE - 30;
```

In this pattern:
- `cleaned_data` and `daily_summary` use `DOWNSTREAM` - they only refresh when needed
- `dashboard_data` has a 15-minute lag - it controls the refresh timing for the whole pipeline
- When `dashboard_data` refreshes, it automatically triggers upstream refreshes if needed

### Dependency Management

Snowflake automatically:
- Tracks dependencies between Dynamic Tables
- Refreshes upstream tables before downstream tables
- Maintains snapshot isolation across the pipeline

---

## Immutability Constraints

For large tables where historical data never changes, you can use **immutability constraints** to improve performance:

```sql
CREATE DYNAMIC TABLE sales_history
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
  IMMUTABLE WHERE (sale_date < CURRENT_DATE - 90)
AS
SELECT * FROM raw_sales;
```

The `IMMUTABLE WHERE` clause tells Snowflake that rows matching the condition will never change. This allows:
- Skip scanning those rows during incremental refresh
- Significant performance improvement for large historical datasets

---

## Common Patterns

### Pattern 1: Bronze-Silver-Gold Pipeline

```
Raw Data → Bronze (cleaned) → Silver (transformed) → Gold (aggregated)
```

Each stage is a Dynamic Table, with only the Gold layer having a time-based TARGET_LAG.

### Pattern 2: Type 2 SCD

```sql
CREATE DYNAMIC TABLE customer_history
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
AS
SELECT
  customer_id,
  name,
  email,
  updated_at AS valid_from,
  LEAD(updated_at) OVER (PARTITION BY customer_id ORDER BY updated_at) AS valid_to,
  CASE WHEN LEAD(updated_at) OVER (PARTITION BY customer_id ORDER BY updated_at) IS NULL
       THEN TRUE ELSE FALSE END AS is_current
FROM customer_changes;
```

### Pattern 3: Dashboard Backing Table

```sql
CREATE DYNAMIC TABLE dashboard_metrics
  TARGET_LAG = '5 minutes'
  WAREHOUSE = BI_WH
AS
SELECT
  DATE_TRUNC('hour', event_time) AS hour,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_id) AS unique_users,
  SUM(revenue) AS total_revenue
FROM events
WHERE event_time >= CURRENT_DATE - 7
GROUP BY 1;
```

---

## Limitations and Considerations

### Query Restrictions

Some SQL constructs don't support incremental refresh:
- Certain window functions
- Non-deterministic functions (RANDOM, UUID)
- External functions
- Recursive CTEs

When these are present, Snowflake uses FULL refresh mode.

### Cost Considerations

Dynamic Tables incur costs for:
- **Warehouse compute**: Refresh operations
- **Storage**: Materialized data
- **Serverless compute**: Change tracking

Balance TARGET_LAG against cost - shorter lag means more frequent refreshes.

### Ownership

- The role that creates the DT owns it
- The owner's privileges are used during refresh
- Use GRANT OWNERSHIP to transfer if needed

---

## Further Reading

- `TARGET_LAG_GUIDE.md` - Detailed guidance on TARGET_LAG
- `REFRESH_MODES.md` - Understanding refresh modes
- `PERFORMANCE_OPTIMIZATION.md` - Optimization techniques
- `MONITORING_REFERENCE.md` - Monitoring and troubleshooting
