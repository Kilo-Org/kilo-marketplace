# Change Data Capture (CDC) Patterns

This guide compares traditional CDC using Streams and Tasks with the modern Dynamic Tables approach. Learn when to use each pattern and how to migrate between them.

---

## What is Change Data Capture?

CDC is the process of:
1. **Detecting changes** in source data (inserts, updates, deletes)
2. **Capturing those changes** in a structured way
3. **Propagating changes** to downstream systems

Common use cases:
- Data warehouse updates
- Event-driven architectures
- Audit trails
- Real-time analytics

---

## Traditional Approach: Streams + Tasks

### Components

1. **Stream**: Captures changes (INSERT, UPDATE, DELETE) on a source table
2. **Task**: Scheduled job that processes the stream
3. **Target Table**: Receives the transformed changes
4. **MERGE Statement**: Handles insert/update/delete logic

### Architecture

```
Source Table → Stream (captures changes) → Task (scheduled) → Target Table
                                              ↓
                                         MERGE logic
                                         (INSERT/UPDATE/DELETE)
```

### Example Implementation

```sql
-- Step 1: Create a stream on the source table
CREATE OR REPLACE STREAM source_changes_stream
  ON TABLE source_table;

-- Step 2: Create the target table
CREATE OR REPLACE TABLE target_table (
  id NUMBER,
  name VARCHAR,
  amount NUMBER,
  updated_at TIMESTAMP_NTZ
);

-- Step 3: Create a task to process the stream
CREATE OR REPLACE TASK process_changes
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '1 HOUR'
WHEN
  SYSTEM$STREAM_HAS_DATA('source_changes_stream')
AS
  MERGE INTO target_table t
  USING (
    SELECT
      id,
      name,
      amount,
      METADATA$ACTION,
      METADATA$ISUPDATE
    FROM source_changes_stream
  ) s
  ON t.id = s.id
  WHEN MATCHED AND s.METADATA$ACTION = 'DELETE' THEN
    DELETE
  WHEN MATCHED THEN
    UPDATE SET
      t.name = s.name,
      t.amount = s.amount,
      t.updated_at = CURRENT_TIMESTAMP()
  WHEN NOT MATCHED AND s.METADATA$ACTION = 'INSERT' THEN
    INSERT (id, name, amount, updated_at)
    VALUES (s.id, s.name, s.amount, CURRENT_TIMESTAMP());

-- Step 4: Resume the task
ALTER TASK process_changes RESUME;
```

### Stream Metadata Columns

Streams provide special columns:
- `METADATA$ACTION`: 'INSERT' or 'DELETE'
- `METADATA$ISUPDATE`: TRUE if this is part of an UPDATE
- `METADATA$ROW_ID`: Unique identifier for the change

An UPDATE appears as DELETE + INSERT pair with `METADATA$ISUPDATE = TRUE`.

### Task Management

```sql
-- Check task status
SHOW TASKS LIKE 'process_changes';

-- Manually execute (for testing)
EXECUTE TASK process_changes;

-- Suspend task
ALTER TASK process_changes SUSPEND;

-- View task history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE name = 'PROCESS_CHANGES'
ORDER BY scheduled_time DESC
LIMIT 10;
```

---

## Modern Approach: Dynamic Tables

### Architecture

```
Source Table → Dynamic Table (automatic refresh)
```

That's it. No stream, no task, no MERGE logic.

### Example Implementation

```sql
-- Single statement replaces Stream + Task + MERGE
CREATE OR REPLACE DYNAMIC TABLE target_dt
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
AS
SELECT
  id,
  name,
  amount
FROM source_table;
```

### How It Works

Dynamic Tables automatically:
1. Track changes in source tables
2. Schedule refreshes based on TARGET_LAG
3. Perform incremental processing when possible
4. Handle insert/update/delete propagation

---

## Side-by-Side Comparison

### Code Complexity

**Streams + Tasks** (50+ lines):
```sql
CREATE STREAM ...;
CREATE TABLE ...;
CREATE TASK ... AS
  MERGE INTO ...
  USING (SELECT ... METADATA$ACTION ... FROM stream)
  ON ...
  WHEN MATCHED AND ... DELETE THEN DELETE
  WHEN MATCHED THEN UPDATE SET ...
  WHEN NOT MATCHED THEN INSERT ...;
ALTER TASK ... RESUME;
-- Plus initial data load
-- Plus error handling
-- Plus monitoring
```

**Dynamic Table** (5 lines):
```sql
CREATE DYNAMIC TABLE ...
  TARGET_LAG = '1 hour'
  WAREHOUSE = COMPUTE_WH
AS
SELECT ... FROM source;
```

### Objects to Manage

| Approach | Objects |
|----------|---------|
| Streams + Tasks | Stream, Task, Target Table (3) |
| Dynamic Table | Dynamic Table (1) |

### Scheduling

| Aspect | Streams + Tasks | Dynamic Table |
|--------|----------------|---------------|
| Schedule type | Explicit CRON/interval | Automatic (TARGET_LAG) |
| Control | Fine-grained | Coarse (freshness-based) |
| Dependency management | Manual | Automatic |

### Change Handling

| Aspect | Streams + Tasks | Dynamic Table |
|--------|----------------|---------------|
| DELETE handling | Manual (MERGE logic) | Automatic |
| UPDATE handling | Manual (MERGE logic) | Automatic |
| INSERT handling | Manual (MERGE logic) | Automatic |
| Out-of-order events | Manual handling needed | Handled automatically |

### Initialization

| Aspect | Streams + Tasks | Dynamic Table |
|--------|----------------|---------------|
| Existing data | Manual initial load | Automatic |
| Stream starts at | Creation time | N/A |
| Backfill | Must be coded | Automatic |

---

## When to Use Each Approach

### Use Dynamic Tables When:

1. **Simplicity is priority** - One object vs three
2. **Standard CDC patterns** - INSERT/UPDATE/DELETE propagation
3. **Freshness-based requirements** - "Data within X time"
4. **Pipeline chaining** - Multiple transformation stages
5. **Automatic dependency management** - Let Snowflake handle it

### Use Streams + Tasks When:

1. **Exact scheduling required** - "Run at 2 AM daily"
2. **Complex procedural logic** - Loops, conditionals, multi-step
3. **Multiple target systems** - One stream, multiple consumers
4. **Audit trail requirements** - Need to preserve change history
5. **Fine-grained control** - Custom error handling, retries

### Decision Matrix

| Requirement | Dynamic Table | Streams + Tasks |
|-------------|--------------|-----------------|
| Simple transformation | ✓ Best | Works |
| Complex logic | Limited | ✓ Best |
| Exact schedule (CRON) | ✗ | ✓ |
| Multiple consumers | ✗ | ✓ |
| Minimum code | ✓ | ✗ |
| Incremental by default | ✓ | Manual |
| Automatic backfill | ✓ | Manual |

---

## Migration: Streams + Tasks to Dynamic Tables

### Step 1: Identify Candidate Pipelines

Good candidates:
- Simple MERGE patterns
- No complex procedural logic
- No exact schedule requirements
- Single consumer

### Step 2: Create Equivalent Dynamic Table

```sql
-- Original: Stream + Task with MERGE
-- New: Dynamic Table

CREATE DYNAMIC TABLE target_dt
  TARGET_LAG = '1 hour'  -- Match original task schedule
  WAREHOUSE = COMPUTE_WH
AS
SELECT
  id,
  name,
  amount
  -- Add any transformations from the original MERGE
FROM source_table;
```

### Step 3: Validate Data

```sql
-- Compare row counts
SELECT 'TASK_TARGET' as source, COUNT(*) FROM target_table
UNION ALL
SELECT 'DT_TARGET', COUNT(*) FROM target_dt;

-- Compare sample data
SELECT * FROM target_table ORDER BY id LIMIT 10;
SELECT * FROM target_dt ORDER BY id LIMIT 10;
```

### Step 4: Cutover

```sql
-- Suspend the task
ALTER TASK process_changes SUSPEND;

-- Update downstream consumers to use the Dynamic Table
-- ...

-- Drop old objects (after validation period)
DROP TASK process_changes;
DROP STREAM source_changes_stream;
DROP TABLE target_table;
```

---

## Advanced: Combining Both Approaches

Sometimes you need both patterns:

### Pattern: Stream for Audit + DT for Analytics

```sql
-- Stream captures all changes for audit trail
CREATE STREAM audit_stream ON TABLE source_table;

-- Task writes to audit log (preserves all changes)
CREATE TASK write_audit
  SCHEDULE = '5 MINUTES'
AS
INSERT INTO audit_log
SELECT *, CURRENT_TIMESTAMP() as captured_at
FROM audit_stream;

-- Dynamic Table for current-state analytics
CREATE DYNAMIC TABLE analytics_view
  TARGET_LAG = '15 minutes'
AS
SELECT * FROM source_table WHERE is_active = TRUE;
```

### Pattern: DT Pipeline + Task for Notifications

```sql
-- DT pipeline for transformations
CREATE DYNAMIC TABLE processed_orders
  TARGET_LAG = '5 minutes'
AS
SELECT * FROM raw_orders WHERE status = 'COMPLETE';

-- Stream on the DT for notifications
CREATE STREAM new_completed_orders
  ON DYNAMIC TABLE processed_orders;

-- Task sends notifications
CREATE TASK send_notifications
  SCHEDULE = '1 MINUTE'
WHEN SYSTEM$STREAM_HAS_DATA('new_completed_orders')
AS
CALL send_order_notification_procedure();
```

---

## Performance Comparison

### Streams + Tasks

- **Predictable scheduling**: Runs exactly when scheduled
- **Control over batch size**: Process N records at a time
- **Resource isolation**: Dedicated task execution

### Dynamic Tables

- **Automatic optimization**: Snowflake chooses best refresh strategy
- **Incremental by default**: When query supports it
- **No scheduling overhead**: No task management needed

### Benchmark Guidance

For a table with 1M rows and 10K daily changes:

| Metric | Streams + Tasks | Dynamic Table |
|--------|----------------|---------------|
| Code complexity | High | Low |
| Initial setup time | Hours | Minutes |
| Daily compute cost | Similar | Similar |
| Maintenance effort | Higher | Lower |

---

## Common Mistakes

### Mistake 1: Forgetting Initial Load with Streams

```sql
-- Stream only captures FUTURE changes!
CREATE STREAM my_stream ON TABLE source;

-- You must manually load existing data
INSERT INTO target SELECT * FROM source;
```

Dynamic Tables handle this automatically.

### Mistake 2: Not Suspending Tasks

```sql
-- IMPORTANT: Suspend tasks when done testing
ALTER TASK my_task SUSPEND;

-- Running tasks consume credits!
```

### Mistake 3: Overly Complex MERGE Logic

If your MERGE has multiple WHEN clauses and complex conditions, Dynamic Tables might be simpler:

```sql
-- Instead of complex MERGE, just express the desired state
CREATE DYNAMIC TABLE target_dt AS
SELECT * FROM source WHERE <conditions>;
```
