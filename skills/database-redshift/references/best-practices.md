# Amazon Redshift Best Practices Reference

## Table Design

### Distribution Style Selection

Distribution style is the most impactful design decision for join performance.

**Decision tree:**

1. **Is the table small (<~2M rows) and frequently joined?** --> DISTSTYLE ALL
2. **Is there a single column used in most JOINs with other large tables?** --> DISTSTYLE KEY on that column
3. **Are there multiple large fact tables that join to each other?** --> DISTKEY both on the shared join column
4. **Is the table rarely joined or used only for scans/aggregations?** --> DISTSTYLE EVEN
5. **Unsure about access patterns?** --> DISTSTYLE AUTO (let ATO decide)

**Common mistakes:**
- DISTKEY on a low-cardinality column (e.g., `status`, `country_code`) causing extreme data skew.
- DISTKEY on a column not used in JOINs -- pays the cost of key distribution without the co-location benefit.
- Using DISTSTYLE ALL on a large table -- wastes storage (full copy on every node) and slows COPY/INSERT (must write to every node).
- Not aligning DISTKEY between fact tables that are frequently joined together.

**Validating distribution:**
```sql
-- Check current distribution style and skew
SELECT "table", diststyle, skew_rows, skew_sortkey1
FROM SVV_TABLE_INFO
WHERE schema = 'public'
ORDER BY skew_rows DESC;

-- Check redistribution in query plans
EXPLAIN <your_query>;
-- Look for DS_DIST_BOTH or DS_DIST_INNER -- these indicate data movement
```

### Sort Key Selection

**Decision tree:**

1. **Most queries filter on a date/timestamp range?** --> COMPOUND SORTKEY with date column first.
2. **Queries consistently filter on the same 2-3 columns in order?** --> COMPOUND SORTKEY in filter-frequency order.
3. **Queries filter on unpredictable subsets of columns?** --> INTERLEAVED SORTKEY (accept higher maintenance).
4. **Unsure?** --> AUTO SORTKEY (let ATO decide).

**Compound sort key column ordering:**
```sql
-- Most dashboards filter by date, then by region, then by product
CREATE TABLE sales (...)
COMPOUND SORTKEY (sale_date, region, product_id);
-- Queries filtering on sale_date benefit fully
-- Queries filtering on sale_date + region benefit fully
-- Queries filtering on region alone get NO sort key benefit (must include leading columns)
```

**Maintenance:**
- VACUUM SORT restores sort order after INSERT/UPDATE/DELETE operations.
- VACUUM REINDEX rebuilds interleaved sort key indexes (required periodically for interleaved keys).
- Monitor unsorted percentage: `SELECT "table", unsorted FROM SVV_TABLE_INFO WHERE unsorted > 5;`

### Compression Encoding

**Recommendations by data type:**

| Data Type | Recommended Encoding | Notes |
|---|---|---|
| BIGINT, INT, SMALLINT | AZ64 | Default; best for numeric types |
| DECIMAL/NUMERIC | AZ64 | Default for RA3 |
| DATE, TIMESTAMP | AZ64 | Excellent for date/time |
| BOOLEAN | ZSTD or RAW | Small columns; compression overhead may exceed benefit |
| VARCHAR (low cardinality) | BYTEDICT | <256 distinct values; 1-byte dictionary lookup |
| VARCHAR (moderate cardinality) | LZO | Good balance of compression and CPU |
| VARCHAR (high cardinality, large) | ZSTD | Best compression ratio for text |
| CHAR | LZO or ZSTD | Depends on string length and cardinality |
| FLOAT/DOUBLE | AZ64 or ZSTD | AZ64 for numeric patterns; ZSTD for random |
| SUPER | LZO | Semi-structured data |

**Best practice:** Use `ENCODE AUTO` on CREATE TABLE and let Redshift/ATO choose. Override only when ANALYZE COMPRESSION shows a clear improvement.

### Column Data Types

- **Use the smallest data type that fits.** SMALLINT instead of BIGINT; DATE instead of TIMESTAMP if time is not needed; VARCHAR(100) instead of VARCHAR(65535).
- **Avoid VARCHAR(MAX) / VARCHAR(65535)** unless necessary. Large VARCHAR allocations consume more memory for intermediate results.
- **Use DECIMAL for financial data.** Never use FLOAT/DOUBLE for currency.
- **Use SUPER for semi-structured JSON.** Avoid storing JSON as VARCHAR -- SUPER enables PartiQL queries and pushdown optimization.
- **Use TIMESTAMPTZ for time-zone-aware timestamps.** Redshift stores TIMESTAMPTZ in UTC internally.
- **Use BIGINT for surrogate keys.** INT (4 bytes) limits to ~2.1 billion; BIGINT (8 bytes) scales to petabyte warehouses.

### Primary Keys and Foreign Keys

Redshift does not enforce primary key or foreign key constraints, but defining them provides critical query optimizer hints:

```sql
CREATE TABLE orders (
    order_id BIGINT NOT NULL PRIMARY KEY ENCODE az64,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id) ENCODE az64,
    order_date DATE NOT NULL ENCODE az64
)
DISTSTYLE KEY DISTKEY (customer_id)
SORTKEY (order_date);
```

- **NOT NULL** -- Enforced. Use on all columns that should never be null.
- **PRIMARY KEY** -- Not enforced but used by the optimizer to eliminate redundant joins and enable certain optimizations.
- **FOREIGN KEY** -- Not enforced but used by the optimizer for join elimination.
- **UNIQUE** -- Not enforced. Define for optimizer hints only.
- **It is your responsibility** to ensure uniqueness and referential integrity in your ETL process.

## Data Loading

### COPY Command Best Practices

COPY is the fastest way to load data into Redshift. It leverages parallel loading across all slices.

```sql
COPY orders
FROM 's3://my-bucket/orders/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftCopyRole'
FORMAT AS PARQUET;
```

**Performance optimization:**
1. **Split input files to match slice count.** For a 16-slice cluster, provide 16 (or a multiple of 16) equally-sized files. Each slice loads one file in parallel. A single large file forces sequential loading on one slice.
2. **Use columnar formats.** Parquet and ORC are 2-10x faster to load than CSV because Redshift can skip unused columns and leverage predicate pushdown.
3. **Compress input files.** GZIP, LZO, BZIP2, or ZSTD for text formats. Parquet/ORC have built-in compression.
4. **Use a manifest file** for exact control over which files to load:
   ```json
   {
     "entries": [
       {"url": "s3://bucket/orders/part-001.parquet", "mandatory": true},
       {"url": "s3://bucket/orders/part-002.parquet", "mandatory": true}
     ]
   }
   ```
   ```sql
   COPY orders FROM 's3://bucket/orders/manifest.json'
   IAM_ROLE '...' MANIFEST FORMAT AS PARQUET;
   ```
5. **MAXERROR** -- Set to a small number (e.g., 10) to abort loads with unexpected errors rather than silently skipping rows.
6. **COMPUPDATE OFF** -- If table already has optimal encodings, skip the analyze-and-update step.
7. **STATUPDATE OFF** -- Skip automatic statistics update after COPY if you manage ANALYZE separately.

**File sizing guidelines:**
| Cluster Size | Ideal File Size | Ideal File Count |
|---|---|---|
| 2-node RA3.xlplus (4 slices) | 64-128 MB each | 4-8 files |
| 4-node RA3.4xlarge (16 slices) | 64-128 MB each | 16-32 files |
| 8-node RA3.16xlarge (128 slices) | 64-128 MB each | 128-256 files |

### COPY Error Handling

```sql
-- After a failed COPY, check errors
SELECT * FROM STL_LOAD_ERRORS ORDER BY starttime DESC LIMIT 20;

-- Detailed error information
SELECT
    le.starttime, le.filename, le.line_number, le.colname,
    le.type, le.raw_field_value, le.err_reason,
    d.raw_line
FROM STL_LOAD_ERRORS le
LEFT JOIN STL_LOADERROR_DETAIL d ON le.query = d.query AND le.line_number = d.line_number
ORDER BY le.starttime DESC
LIMIT 20;
```

### INSERT Performance

- **Avoid single-row INSERTs in loops.** Each INSERT is a separate transaction with commit overhead.
- **Use INSERT INTO ... SELECT for transformations** within Redshift.
- **Use COPY for bulk loading** from S3 -- always prefer COPY over multi-row INSERT for external data.
- **CREATE TABLE AS (CTAS)** is often faster than INSERT INTO ... SELECT because it creates optimally encoded, sorted, distributed data in one pass.
- **Deep copy pattern** for table restructuring:
  ```sql
  -- Create new table with desired structure
  CREATE TABLE orders_new (LIKE orders) DISTSTYLE KEY DISTKEY(customer_id) SORTKEY(order_date);
  -- Copy data
  INSERT INTO orders_new SELECT * FROM orders;
  -- Swap
  ALTER TABLE orders RENAME TO orders_old;
  ALTER TABLE orders_new RENAME TO orders;
  DROP TABLE orders_old;
  ```

### UNLOAD Best Practices

```sql
UNLOAD ('SELECT * FROM orders WHERE order_date >= ''2026-01-01''')
TO 's3://my-bucket/unload/orders_'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftUnloadRole'
FORMAT AS PARQUET
PARTITION BY (order_date)
MAXFILESIZE 256 MB
ALLOWOVERWRITE;
```

- **FORMAT AS PARQUET** -- Columnar output, much smaller than CSV, and faster to reload.
- **PARTITION BY** -- Creates Hive-style partitioned directory structure in S3.
- **MAXFILESIZE** -- Controls output file size. 256 MB - 1 GB per file is optimal for downstream consumption.
- **PARALLEL ON** (default) -- Each slice writes its own file(s) in parallel.

## VACUUM and ANALYZE

### VACUUM

Redshift tables require VACUUM to reclaim space from deleted rows and restore sort order.

```sql
-- Full vacuum: reclaims space AND re-sorts
VACUUM FULL orders;

-- Delete-only vacuum: reclaims space but does not re-sort
VACUUM DELETE ONLY orders;

-- Sort-only vacuum: re-sorts but does not reclaim space
VACUUM SORT ONLY orders;

-- Reindex: rebuilds interleaved sort key indexes
VACUUM REINDEX orders;

-- Vacuum to a threshold (only vacuum if >threshold% unsorted or >threshold% deleted)
VACUUM FULL orders TO 80 PERCENT;
```

**Automated vacuum:** Redshift runs automatic VACUUM DELETE in the background during low-activity periods. Manual VACUUM is still needed for SORT and REINDEX operations.

**VACUUM best practices:**
- Schedule VACUUM SORT during maintenance windows after large batch loads.
- Monitor `unsorted` and `tbl_rows` vs `size` in SVV_TABLE_INFO.
- For large tables, VACUUM can take hours. Use `VACUUM ... TO <threshold> PERCENT` to limit work.
- VACUUM acquires a table-level lock that blocks DDL (but not DML reads/writes).

### ANALYZE

ANALYZE updates table statistics used by the query optimizer.

```sql
-- Analyze a specific table
ANALYZE orders;

-- Analyze specific columns
ANALYZE orders (order_date, customer_id);

-- Analyze predicate columns (columns used in WHERE, JOIN, GROUP BY, ORDER BY)
ANALYZE PREDICATE COLUMNS orders;
```

**Auto-analyze:** Redshift automatically runs ANALYZE on tables that have changed significantly (>10% of rows). This handles most cases.

**When to run manual ANALYZE:**
- After initial bulk load of a new table.
- After loading a large batch that changes data distribution significantly.
- After DDL changes that affect statistics (ADD COLUMN, etc.).
- When query plans show unexpected full table scans.

## Query Performance Optimization

### EXPLAIN Plan Analysis

```sql
EXPLAIN SELECT o.order_id, c.name, o.total_amount
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date BETWEEN '2026-01-01' AND '2026-03-31';
```

**Key things to look for in EXPLAIN output:**

1. **DS_DIST labels** -- DS_DIST_NONE (best) vs DS_DIST_BOTH (worst). Indicates data movement needed for joins.
2. **Scan types** -- Sequential Scan is expected (columnar). Look at `rows=` estimate vs actual.
3. **Hash Join vs Merge Join** -- Merge join is possible when both inputs are sorted on the join key. Hash join builds a hash table (memory intensive).
4. **Sort steps** -- Sorts are expensive. If ORDER BY aligns with the sort key, no runtime sort is needed.
5. **Cost** -- Relative units. Higher cost means more I/O and CPU.
6. **Width** -- Bytes per row in the output. SELECT fewer columns to reduce width.
7. **Broadcast** -- DS_BCAST_INNER means inner table is broadcast. Acceptable for small tables; alarm for large ones.

### Query Anti-Patterns

**1. SELECT * -- Never use in production queries.**
```sql
-- BAD: reads all columns
SELECT * FROM orders WHERE order_date = '2026-04-07';

-- GOOD: reads only needed columns
SELECT order_id, customer_id, total_amount FROM orders WHERE order_date = '2026-04-07';
```

**2. Cross-joins and Cartesian products.**
```sql
-- Check for accidental cross-joins by reviewing EXPLAIN for "Nested Loop" with no join predicate.
```

**3. Large DISTINCT or GROUP BY on high-cardinality columns.**
```sql
-- Consider approximate functions for large-scale distinct counts
SELECT approximate_count_distinct(user_id) FROM events;
```

**4. Functions on sort key columns in WHERE clauses.**
```sql
-- BAD: function on sort key prevents zone map pruning
SELECT * FROM orders WHERE DATE_TRUNC('month', order_date) = '2026-01-01';

-- GOOD: range predicate preserves zone map pruning
SELECT * FROM orders WHERE order_date >= '2026-01-01' AND order_date < '2026-02-01';
```

**5. NOT IN with NULLs (use NOT EXISTS instead).**
```sql
-- BAD: NOT IN returns no rows if subquery contains any NULL
SELECT * FROM orders WHERE customer_id NOT IN (SELECT customer_id FROM blacklist);

-- GOOD: NOT EXISTS handles NULLs correctly
SELECT * FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM blacklist b WHERE b.customer_id = o.customer_id);
```

**6. Excessive use of ORDER BY without LIMIT.**

**7. LIKE with leading wildcard ('%%pattern') -- cannot use sort key optimization.**

### Join Optimization

- **Co-locate large-to-large joins** by using the same DISTKEY on both tables' join column.
- **Use DISTSTYLE ALL** for small dimension tables that are joined by many large tables on different keys.
- **Avoid joining on expressions** (e.g., `ON UPPER(a.name) = UPPER(b.name)`) -- this prevents co-located joins.
- **Pre-filter** large tables in subqueries/CTEs before joining to reduce data movement.
- **Materialized views** can pre-compute expensive joins.

### Window Functions

Redshift has excellent window function support. Use them instead of self-joins:

```sql
-- Running total using window function (efficient)
SELECT
    order_date,
    total_amount,
    SUM(total_amount) OVER (ORDER BY order_date ROWS UNBOUNDED PRECEDING) AS running_total
FROM orders;

-- Instead of a correlated subquery (inefficient)
SELECT o1.order_date, o1.total_amount,
    (SELECT SUM(o2.total_amount) FROM orders o2 WHERE o2.order_date <= o1.order_date) AS running_total
FROM orders o1;
```

## Workload Management (WLM) Configuration

### Automatic WLM (Recommended)

```sql
-- Check current WLM configuration
SELECT * FROM STV_WLM_SERVICE_CLASS_CONFIG;

-- View query priorities
SELECT service_class, condition, action, action_value
FROM STV_WLM_CLASSIFICATION_CONFIG;
```

**Priority setup via console or CLI:**
- Create queues for different workload classes (e.g., ETL, BI, ad-hoc).
- Assign priority per queue: HIGHEST, HIGH, NORMAL, LOW, LOWEST.
- Map queries to queues using user groups or query groups.

```sql
-- Route a session to a specific queue
SET query_group TO 'etl_queue';

-- Route by user group (configured in WLM)
-- Users in the 'analysts' group automatically go to the BI queue
```

### Query Monitoring Rules (QMR)

Define rules to abort, log, or hop (re-route) queries that exceed thresholds:

| Rule | Metric | Recommended Threshold | Action |
|---|---|---|---|
| Long-running queries | `query_execution_time` | 3600 seconds | HOP or ABORT |
| Memory hogs | `query_mem_peak_usage_percentage` | 80% | LOG + ABORT |
| Runaway scans | `scan_row_count` | 10 billion rows | LOG + ABORT |
| CPU hogs | `query_cpu_time` | 600 seconds | LOG |
| Nested loops | `nested_loop_join_row_count` | 1 billion rows | ABORT |
| Return too many rows | `return_row_count` | 10 million rows | LOG |

### Short Query Acceleration (SQA)

SQA routes short-running queries to a fast-path execution lane:

- Enabled by default in Automatic WLM.
- Redshift predicts whether a query will complete within the SQA maximum runtime (configurable, default dynamically determined).
- Short queries bypass the main WLM queue and execute immediately.
- If prediction is wrong and the query exceeds the threshold, it is re-routed to a regular queue.

### Concurrency Scaling

```sql
-- Enable concurrency scaling on a WLM queue (via console/CLI configuration)
-- Check concurrency scaling usage
SELECT * FROM STL_CONCURRENCY_SCALING_USAGE ORDER BY starttime DESC LIMIT 20;
```

Best practice: Enable concurrency scaling on queues serving interactive/BI queries. Disable for ETL queues (where queuing is acceptable).

## ETL and Data Pipeline Best Practices

### Incremental Loading Pattern

```sql
-- Stage new/changed data
CREATE TEMP TABLE stg_orders AS
SELECT * FROM spectrum_schema.raw_orders
WHERE load_timestamp > (SELECT MAX(load_timestamp) FROM public.orders);

-- Delete existing rows that will be replaced (merge/upsert pattern)
BEGIN TRANSACTION;

DELETE FROM public.orders
USING stg_orders
WHERE orders.order_id = stg_orders.order_id;

INSERT INTO public.orders
SELECT * FROM stg_orders;

COMMIT;

ANALYZE public.orders;
```

### Large Table Maintenance

For tables that are heavily updated/deleted:

1. **Deep copy** instead of VACUUM for severely fragmented tables (>50% deleted rows):
   ```sql
   CREATE TABLE orders_clean (LIKE orders INCLUDING DEFAULTS);
   INSERT INTO orders_clean SELECT * FROM orders;
   DROP TABLE orders;
   ALTER TABLE orders_clean RENAME TO orders;
   ```

2. **Time-partitioned tables** -- Use separate tables per time period (e.g., `orders_2026_q1`, `orders_2026_q2`) and a UNION ALL view or late-binding view.

3. **Staging tables** -- Use temporary or staging tables for ETL transforms. Drop them after use to reclaim space.

### Transaction Best Practices

- **Redshift uses serializable isolation** by default (the strictest level).
- **Keep transactions short.** Long-running transactions hold locks and prevent VACUUM from reclaiming space.
- **Avoid explicit BEGIN/COMMIT around single statements** -- each statement is auto-committed.
- **Use COMMIT frequency** for multi-statement ETL: batch into groups of a few hundred statements per transaction.
- **Monitor long transactions:** `SELECT * FROM SVV_TRANSACTIONS WHERE lockable_object_type = 'relation' ORDER BY txn_start;`

## Monitoring and Alerting

### Key CloudWatch Metrics

| Metric | Healthy Range | Alert Threshold |
|---|---|---|
| `CPUUtilization` | <80% sustained | >90% for >15 min |
| `PercentageDiskSpaceUsed` | <75% | >80% |
| `DatabaseConnections` | <400 | >450 (max 500) |
| `HealthStatus` | 1 (healthy) | 0 (unhealthy) |
| `MaintenanceMode` | 0 | 1 (maintenance in progress) |
| `ReadLatency` | <5 ms | >20 ms |
| `WriteLatency` | <10 ms | >50 ms |
| `QueriesCompletedPerSecond` | varies | sudden drop |
| `QueryDuration` | varies | p99 > 2x baseline |
| `WLMQueueLength` | 0-5 | >20 sustained |
| `ConcurrencyScalingActiveClusters` | 0-1 | >3 sustained |

### Serverless CloudWatch Metrics

| Metric | Description |
|---|---|
| `ComputeCapacity` | Current RPU allocation |
| `ComputeSeconds` | RPU-seconds consumed |
| `DataStorage` | Total storage in bytes |
| `QueriesRunning` | Active query count |
| `QueriesQueued` | Queued query count |
| `QueryDuration` | Average query duration |

### Recommended Alarms

1. Disk space > 80% -- Immediate action needed (VACUUM, drop old data, resize).
2. CPU > 90% sustained -- Review running queries, add nodes, or enable concurrency scaling.
3. WLM queue length > 20 for > 5 minutes -- Queue is backed up; consider concurrency scaling or priority tuning.
4. Health status = 0 -- Cluster unavailable; check AWS Health Dashboard.
5. Query duration p99 > threshold -- Performance regression; review recent schema/data changes.

## Security Best Practices

### Principle of Least Privilege

```sql
-- Create a read-only role
CREATE ROLE analyst_role;
GRANT USAGE ON SCHEMA public TO ROLE analyst_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ROLE analyst_role;

-- Create a user and assign the role
CREATE USER analyst_user PASSWORD 'ComplexP@ss123!';
GRANT ROLE analyst_role TO analyst_user;

-- Row-level security
CREATE RLS POLICY region_policy
WITH (region VARCHAR(50))
USING (region = current_setting('app.user_region'));

ATTACH RLS POLICY region_policy ON orders TO ROLE analyst_role;
ALTER TABLE orders ROW LEVEL SECURITY ON;

-- Dynamic data masking
CREATE MASKING POLICY mask_email
WITH (email VARCHAR(256))
USING (
    CASE
        WHEN current_user IN ('admin') THEN email
        ELSE '***@' || SPLIT_PART(email, '@', 2)
    END
);
ATTACH MASKING POLICY mask_email ON customers(email) TO PUBLIC;
```

### Network Security

- **Always enable Enhanced VPC Routing** for COPY/UNLOAD to keep data within the VPC.
- **Use VPC endpoints** for S3, Glue, STS, and other AWS service access.
- **Restrict security groups** to specific CIDR ranges and ports (5439).
- **Enable SSL** via parameter group: `require_ssl = true`.
- **Audit logging** -- Enable user activity logging via parameter group and ship to S3.

### Encryption

- **Enable encryption at rest** for all production clusters (cannot be changed after cluster creation for provisioned; serverless is always encrypted).
- **Use AWS KMS** for key management with automatic rotation.
- **Rotate credentials** regularly; use IAM-based authentication where possible.

## Cost Optimization

### Provisioned Cluster Cost Optimization

1. **Right-size:** Start with the smallest RA3 node type that meets your performance SLA. Use elastic resize to adjust.
2. **Reserved Instances:** Commit to 1 or 3-year reservations for 30-75% savings on stable workloads.
3. **Pause/Resume:** Pause clusters during off-hours (dev/test environments). You pay only for storage when paused.
4. **Concurrency scaling free credits:** 1 hour free per 24 hours. Schedule burst workloads to use free credits first.
5. **Spectrum offload:** Move cold/archival data to S3 and query via Spectrum. S3 storage is ~10x cheaper than Redshift RA3 storage.
6. **Data sharing:** Instead of replicating data across clusters, use data sharing for zero-copy access.

### Serverless Cost Optimization

1. **Set appropriate base RPU capacity.** Start low (32-64 RPUs) and increase if queries are slow.
2. **Usage limits.** Set daily/weekly RPU-hour limits with alert actions.
3. **Workgroup separation.** Create separate workgroups for different teams with independent cost controls.
4. **Schedule workloads.** Batch ETL during off-peak when auto-scaling overhead is lower.
5. **Optimize queries.** Every RPU-second matters -- tune slow queries aggressively.

## Troubleshooting Playbooks

### Query Stuck in Queue (WLM)

1. Check queue state: `SELECT * FROM STV_WLM_QUERY_STATE WHERE state = 'Queued';`
2. Identify blocking queue: `SELECT * FROM STV_WLM_SERVICE_CLASS_STATE;`
3. Check if concurrency scaling is enabled for the queue.
4. Check for long-running queries consuming all slots: `SELECT * FROM STV_RECENTS WHERE status = 'Running' ORDER BY starttime;`
5. Resolution: Kill long-running queries, increase WLM concurrency (automatic WLM), or enable concurrency scaling.

### Disk Full (100% Disk Usage)

1. **Immediate:** Kill all running queries to free temp space: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename != 'rdsdb';`
2. **Check space:** `SELECT * FROM SVV_TABLE_INFO ORDER BY size DESC LIMIT 20;`
3. **Run VACUUM DELETE** on tables with high deleted row counts.
4. **Drop temp tables** and staging tables.
5. **Truncate or DROP** unnecessary tables.
6. **Elastic resize** to add nodes if storage is genuinely insufficient.
7. **Long-term:** Migrate to RA3 nodes for managed storage, or offload cold data to Spectrum.

### Data Skew (Hot Slices)

1. **Identify skewed tables:** `SELECT "table", skew_rows FROM SVV_TABLE_INFO WHERE skew_rows > 2.0 ORDER BY skew_rows DESC;`
2. **Analyze distribution:** Check the DISTKEY column's cardinality and value distribution.
3. **Resolution options:**
   - Change DISTKEY to a higher-cardinality column.
   - Switch to DISTSTYLE EVEN if no good DISTKEY exists.
   - Switch to DISTSTYLE AUTO.
4. **Apply change:** Use deep copy pattern (CREATE TABLE ... LIKE + INSERT INTO ... SELECT).

### COPY Failures

1. **Check errors:** `SELECT * FROM STL_LOAD_ERRORS ORDER BY starttime DESC LIMIT 20;`
2. **Check error detail:** `SELECT * FROM STL_LOADERROR_DETAIL WHERE query = <query_id>;`
3. **Common causes:**
   - Data type mismatch (string value for numeric column) -- fix source data or use explicit COPY options.
   - File not found -- check S3 path, IAM permissions, VPC routing.
   - Manifest errors -- validate manifest JSON syntax.
   - Permission denied -- verify IAM role trust policy and S3 bucket policy.
   - Encoding errors (UTF-8) -- use `ACCEPTINVCHARS` option.
   - Field delimiter in data -- use `ESCAPE` or switch to Parquet format.

### Lock Contention

1. **Identify locks:** `SELECT * FROM STV_LOCKS;`
2. **Find blockers:** `SELECT * FROM STV_BLOCKERS;`
3. **View transactions:** `SELECT * FROM SVV_TRANSACTIONS ORDER BY txn_start LIMIT 20;`
4. **Resolution:**
   - Terminate the blocking session: `SELECT pg_terminate_backend(<pid>);`
   - Avoid running DDL during active query periods.
   - Keep transactions short.
   - Schedule VACUUM and maintenance during low-activity windows.

### Slow Spectrum Queries

1. **Check Spectrum performance:** `SELECT * FROM SVL_S3QUERY_SUMMARY WHERE query = <query_id>;`
2. **Check partition pruning:** `SELECT * FROM SVL_S3PARTITION WHERE query = <query_id>;`
3. **Common causes:**
   - Not using columnar format (CSV/JSON instead of Parquet/ORC).
   - Too many small files (< 64 MB each).
   - Missing partition pruning (no WHERE on partition columns).
   - Scanning too many partitions.
4. **Resolution:** Convert to Parquet, compact small files, add partition predicates, add more partitions on frequently filtered columns.
