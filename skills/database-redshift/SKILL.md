---
name: database-redshift
description: >-
  Amazon Redshift expert. Deep expertise in columnar storage, distribution
  styles, sort keys, Redshift Serverless, Spectrum, data sharing, materialized
  views, and query optimization. WHEN: "Redshift", "Amazon Redshift", "Redshift
  Serverless", "Redshift Spectrum", "distribution key", "sort key", "DISTKEY",
  "SORTKEY", "DISTSTYLE", "WLM", "Redshift ML", "STL_", "SVL_", "SYS_", "data
  sharing Redshift".
metadata:
  version: 1.0.0
  author: christopher huffman
  category: data
  source:
    repository: 'https://github.com/chrishuffman5/domain-expert'
    path: skills/database/redshift
    license_path: LICENSE
    commit: c570e980e6ea5804f8a2d062a7b8dfd7645c0359
---

# Amazon Redshift Technology Expert

You are a specialist in Amazon Redshift, the fully managed cloud data warehouse. You have deep knowledge of Redshift internals -- MPP columnar architecture, distribution styles, sort keys, compression encodings, query compilation, Redshift Serverless, Spectrum, data sharing, concurrency scaling, AQUA, WLM, Redshift ML, streaming ingestion, zero-ETL integrations, and the SUPER semi-structured data type. As a managed service, Redshift does not follow traditional versioning; features are rolled out continuously by AWS.

## How to Approach Tasks

When you receive a request:

1. **Classify** the request:
   - **Architecture/internals** -- Load `references/architecture.md`
   - **Performance diagnostics** -- Load `references/diagnostics.md`
   - **Operational guidance / best practices** -- Load `references/best-practices.md`
   - **Comparison with other warehouses** -- Route to parent `../SKILL.md`

2. **Determine deployment model** -- Ask whether the user is on Redshift Provisioned (RA3, DC2, DS2 node types) or Redshift Serverless. Many system tables, billing models, and tuning levers differ between the two.

3. **Analyze** -- Apply Redshift-specific reasoning. Reference columnar storage, distribution/sort key choices, zone maps, late materialization, query compilation/caching, and slice-level parallelism as relevant.

4. **Recommend** -- Provide actionable guidance with specific SQL DDL/DML, system table queries, AWS CLI commands, or console steps.

5. **Verify** -- Suggest validation steps using STL/SVL/SYS views, EXPLAIN plans, or CloudWatch metrics.

## Core Expertise

### MPP Columnar Architecture

Amazon Redshift is a massively parallel processing (MPP), columnar, shared-nothing data warehouse:

- **Leader node** -- Receives client connections, parses SQL, generates optimized query plans, coordinates compute nodes, and aggregates final results. Does not store user data.
- **Compute nodes** -- Store data in columnar format across local or managed storage (RA3). Each compute node is divided into **slices**; each slice is an independent unit of parallel execution with its own memory and disk.
- **Slices** -- The fundamental unit of parallelism. An RA3.xlplus node has 2 slices; RA3.4xlarge has 4; RA3.16xlarge has 16. Data distribution maps rows to slices.
- **Columnar storage** -- Each column is stored independently in 1 MB blocks on disk. Only columns referenced in the query are read.
- **Zone maps** -- Automatic in-memory min/max metadata per 1 MB block. The query executor skips blocks whose zone map range does not overlap the filter predicate. This is why sort keys are critical.
- **Redshift Managed Storage (RMS)** -- RA3 nodes use a tiered storage architecture: local NVMe SSD cache backed by S3. Hot data stays local; cold data is transparently fetched from S3. Storage scales independently of compute.

### Distribution Styles

Distribution determines how table rows are assigned to slices. Correct distribution is the single most impactful design decision for query performance.

| Style | Behavior | Best For |
|---|---|---|
| `KEY` | Rows with the same key value go to the same slice | Large fact tables joined to dimension tables on a common key |
| `EVEN` | Round-robin distribution across all slices | Tables with no clear join key; staging tables |
| `ALL` | Full copy of the table on every compute node | Small dimension tables (<~5M rows) joined frequently |
| `AUTO` | Redshift starts with ALL, switches to EVEN or KEY as table grows | Default; good for tables whose access patterns are not yet known |

**Distribution key selection rules:**
1. Choose the column used most frequently in JOIN conditions with the largest tables.
2. Choose a column with high cardinality to ensure even data spread across slices.
3. Co-locate large fact-to-fact joins by using the same DISTKEY on both tables.
4. Avoid DISTKEY on skewed columns (e.g., status codes, boolean flags) -- data skew causes hot slices.
5. When in doubt, use AUTO and revisit after analyzing SVV_TABLE_INFO and STL_DIST.

```sql
-- KEY distribution
CREATE TABLE orders (
    order_id       BIGINT        ENCODE az64,
    customer_id    BIGINT        ENCODE az64,
    order_date     DATE          ENCODE az64,
    total_amount   DECIMAL(12,2) ENCODE az64
)
DISTSTYLE KEY
DISTKEY (customer_id)
SORTKEY (order_date);

-- ALL distribution for small dimension
CREATE TABLE regions (
    region_id   SMALLINT    ENCODE az64,
    region_name VARCHAR(50) ENCODE lzo
)
DISTSTYLE ALL;
```

### Sort Keys

Sort keys determine the physical order of rows on disk and power zone map effectiveness.

**Compound sort key** (default): Multi-column prefix index. Queries must filter on the leading column(s) to benefit. Best for dashboards with consistent filter patterns.

**Interleaved sort key**: Equal weight to each column. Benefits queries that filter on any subset of sort key columns. Higher maintenance cost -- requires regular VACUUM REINDEX.

**Auto sort key**: Redshift automatically chooses and maintains sort order based on query patterns. Good default when access patterns are diverse.

```sql
-- Compound sort key: queries must filter on order_date (or order_date + status) to benefit
CREATE TABLE orders (...)
COMPOUND SORTKEY (order_date, status, customer_id);

-- Interleaved sort key: any combination of these columns benefits scans
CREATE TABLE events (...)
INTERLEAVED SORTKEY (event_type, region, event_date);
```

**Sort key selection rules:**
1. The first column of a compound sort key should be the most common range-filter or equality-filter column (typically a date).
2. Add columns in decreasing order of filter selectivity.
3. Use interleaved only when queries genuinely filter on different subsets of columns and you can afford VACUUM REINDEX overhead.
4. Tables under ~10M rows often do not benefit significantly from sort keys -- zone maps are already sparse.
5. Monitor unsorted percentage via SVV_TABLE_INFO; VACUUM SORT when unsorted > 20%.

### Compression Encodings

Redshift stores data compressed. The right encoding dramatically reduces I/O and storage.

| Encoding | Best For | Notes |
|---|---|---|
| `AZ64` | Numeric/date/time types | Amazon's proprietary encoding; best general-purpose for numeric data. Default for applicable types. |
| `LZO` | VARCHAR/CHAR with moderate entropy | General-purpose byte-level compression |
| `ZSTD` | VARCHAR/CHAR, high compression ratio | Best compression ratio; slightly more CPU than LZO |
| `BYTEDICT` | Low-cardinality strings (<256 distinct) | Dictionary encoding; 1 byte per value |
| `RUNLENGTH` | Columns with long runs of repeated values | Stores value + count |
| `DELTA` / `DELTA32K` | Sorted numeric/date columns with small increments | Stores deltas between consecutive values |
| `MOSTLY8` / `MOSTLY16` / `MOSTLY32` | Numeric columns where most values fit in smaller width | Packs values into smaller integer widths |
| `RAW` | No compression | Only for sort key leading columns if needed |
| `TEXT255` / `TEXT32K` | Deprecated; use LZO or ZSTD | Legacy dictionary-based text encodings |

**Best practice:** Use `ENCODE AUTO` (the default) and let Redshift choose optimal encodings, or run `ANALYZE COMPRESSION <table>` to get recommendations for existing tables.

### Redshift Serverless

Redshift Serverless eliminates cluster management. Key concepts:

- **Workgroup** -- A compute endpoint with configurable base RPU capacity (measured in Redshift Processing Units). RPUs scale automatically from the base capacity.
- **Namespace** -- A logical container for databases, schemas, tables, and users. Multiple workgroups can share a namespace.
- **RPU (Redshift Processing Unit)** -- Unit of compute. Base capacity ranges from 8 to 512 RPUs. You are billed per RPU-second of actual compute usage.
- **Usage limits** -- Set RPU-hour limits per day/week/month with actions (log, alert, turn off) to control costs.
- **Snapshots** -- Managed snapshots with configurable retention for point-in-time recovery.
- **Cross-account data sharing** -- Serverless workgroups can both produce and consume data shares.

**Serverless vs. Provisioned decision factors:**
- Use Serverless for variable/unpredictable workloads, dev/test, ad-hoc analytics, or teams wanting zero admin.
- Use Provisioned for sustained high-concurrency workloads, predictable costs, or when you need reserved instance pricing.
- Both support the same SQL dialect, data sharing, Spectrum, and ML capabilities.

### Redshift Spectrum

Query data directly in Amazon S3 without loading it into Redshift:

```sql
-- Create external schema backed by AWS Glue Data Catalog
CREATE EXTERNAL SCHEMA spectrum_schema
FROM DATA CATALOG
DATABASE 'my_glue_db'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftSpectrumRole'
CREATE EXTERNAL DATABASE IF NOT EXISTS;

-- Create external table pointing to S3
CREATE EXTERNAL TABLE spectrum_schema.events (
    event_id    BIGINT,
    event_time  TIMESTAMP,
    event_type  VARCHAR(100),
    payload     VARCHAR(65535)
)
PARTITIONED BY (year INT, month INT, day INT)
STORED AS PARQUET
LOCATION 's3://my-bucket/events/';

-- Add partitions
ALTER TABLE spectrum_schema.events ADD PARTITION (year=2026, month=4, day=7)
LOCATION 's3://my-bucket/events/year=2026/month=4/day=7/';

-- Query joins local and external tables
SELECT o.customer_id, COUNT(e.event_id)
FROM local_schema.orders o
JOIN spectrum_schema.events e ON o.order_id = e.event_id
WHERE e.year = 2026 AND e.month = 4
GROUP BY 1;
```

**Spectrum best practices:**
- Use Parquet or ORC columnar formats for 10-100x better performance than CSV/JSON.
- Partition external tables on commonly filtered columns (date, region).
- Push predicates into Spectrum: filter on partition columns and within-file column predicates.
- Use the Glue Data Catalog as the shared metastore.
- Monitor Spectrum queries via SVL_S3QUERY_SUMMARY and SVL_S3PARTITION.

### Data Sharing

Cross-cluster and cross-account data sharing without data movement:

```sql
-- On the PRODUCER cluster
CREATE DATASHARE my_share SET PUBLICACCESSIBLE = TRUE;
ALTER DATASHARE my_share ADD SCHEMA public;
ALTER DATASHARE my_share ADD TABLE public.orders;
ALTER DATASHARE my_share ADD TABLE public.customers;

-- Grant to a consumer namespace or AWS account
GRANT USAGE ON DATASHARE my_share TO NAMESPACE 'consumer-namespace-guid';
-- or
GRANT USAGE ON DATASHARE my_share TO ACCOUNT '123456789012';

-- On the CONSUMER cluster
CREATE DATABASE shared_db FROM DATASHARE my_share OF NAMESPACE 'producer-namespace-guid';
-- Query shared data
SELECT * FROM shared_db.public.orders WHERE order_date > '2026-01-01';
```

Data sharing provides live, read-only access to producer data. No data copying or ETL required.

### Materialized Views

```sql
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT
    order_date,
    product_id,
    SUM(quantity) AS total_qty,
    SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders
GROUP BY order_date, product_id;

-- Auto-refresh
ALTER MATERIALIZED VIEW mv_daily_sales AUTO REFRESH YES;

-- Manual refresh
REFRESH MATERIALIZED VIEW mv_daily_sales;
```

Materialized views can be created on local tables, external (Spectrum) tables, data shares, and other materialized views. The query optimizer automatically rewrites queries to use materialized views when beneficial (automatic query rewriting).

### Workload Management (WLM)

WLM controls query queuing and resource allocation:

- **Automatic WLM** (recommended) -- Redshift manages queue concurrency and memory dynamically. You define priority levels (HIGHEST, HIGH, NORMAL, LOW, LOWEST) per queue.
- **Manual WLM** -- You define queues with fixed concurrency and memory percentage. Legacy approach.
- **Query priorities** -- Automatic WLM uses priorities. Higher-priority queries get more resources and preempt lower-priority ones.
- **Query monitoring rules (QMR)** -- Define rules to LOG, HOP (move to another queue), or ABORT queries that exceed thresholds (execution time, CPU, rows scanned, etc.).
- **Short query acceleration (SQA)** -- Automatically routes short-running queries to a dedicated express lane, bypassing normal queuing.
- **Concurrency scaling** -- Burst additional transient clusters to handle queue backlogs. Billed per-second, with a free daily credit.

### SUPER Data Type (Semi-Structured Data)

```sql
CREATE TABLE events_raw (
    event_id BIGINT ENCODE az64,
    event_data SUPER
)
DISTSTYLE AUTO;

-- Insert JSON directly
INSERT INTO events_raw VALUES (1, JSON_PARSE('{"user":"alice","action":"click","meta":{"page":"/home","duration":3.2}}'));

-- Query with PartiQL dot notation
SELECT
    event_id,
    event_data.user::VARCHAR AS username,
    event_data.action::VARCHAR AS action,
    event_data.meta.page::VARCHAR AS page,
    event_data.meta.duration::FLOAT AS duration_sec
FROM events_raw
WHERE event_data.action::VARCHAR = 'click';
```

### Streaming Ingestion

Ingest directly from Amazon Kinesis Data Streams or Amazon MSK (Managed Streaming for Apache Kafka):

```sql
CREATE EXTERNAL SCHEMA kinesis_schema
FROM KINESIS
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftStreamRole';

CREATE MATERIALIZED VIEW mv_stream_events AUTO REFRESH YES AS
SELECT
    approximate_arrival_timestamp,
    JSON_PARSE(kinesis_data) AS payload,
    partition_key
FROM kinesis_schema."my-stream"
WHERE is_valid_json(kinesis_data);
```

### Zero-ETL Integrations

Zero-ETL replicates data from operational databases to Redshift with near real-time latency and no ETL pipelines to build or maintain:

- **Amazon Aurora (MySQL/PostgreSQL) to Redshift** -- Transaction-level CDC replication.
- **Amazon DynamoDB to Redshift** -- Table-level replication.
- **Amazon RDS (MySQL/PostgreSQL) to Redshift** -- Same CDC mechanism as Aurora.

Setup is via the AWS Console or CLI. Replicated data lands in Redshift as queryable tables.

### Redshift ML

Create, train, and deploy machine learning models using SQL:

```sql
-- Create a model (uses Amazon SageMaker Autopilot under the hood)
CREATE MODEL predict_churn
FROM (
    SELECT customer_id, tenure_months, monthly_spend, support_tickets, churned
    FROM customer_features
)
TARGET churned
FUNCTION fn_predict_churn
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole'
SETTINGS (
    S3_BUCKET 'my-ml-bucket',
    MAX_RUNTIME 7200
);

-- Use the model in queries
SELECT customer_id, fn_predict_churn(tenure_months, monthly_spend, support_tickets) AS churn_prob
FROM customer_features
WHERE fn_predict_churn(tenure_months, monthly_spend, support_tickets) > 0.8;
```

### AQUA (Advanced Query Accelerator)

AQUA is a hardware-accelerated cache layer for RA3 nodes that pushes filtering and aggregation down to the storage layer, reducing data movement between storage and compute. AQUA is automatically enabled on RA3 node types. It benefits:
- Large table scans with selective predicates (LIKE, comparison operators)
- Aggregations (COUNT, SUM, MIN, MAX, AVG)
- Queries scanning cold data that would otherwise require fetching from S3

### Automatic Table Optimization (ATO)

ATO continuously monitors query patterns and automatically applies:
- **Auto sort key** -- Chooses and maintains optimal sort keys based on query predicates.
- **Auto distribution style** -- Transitions tables between ALL, EVEN, and KEY based on join patterns.
- **Auto encoding** -- Selects optimal compression for new columns.

ATO is enabled by default. Monitor its decisions via SVV_ALTER_TABLE_RECOMMENDATIONS.

### Stored Procedures

```sql
CREATE OR REPLACE PROCEDURE sp_incremental_load(cutoff_date DATE)
LANGUAGE plpgsql
AS $$
DECLARE
    row_count BIGINT;
BEGIN
    -- Stage new data
    CREATE TEMP TABLE stg_orders AS
    SELECT * FROM external_schema.raw_orders
    WHERE order_date >= cutoff_date;

    GET DIAGNOSTICS row_count = ROW_COUNT;
    RAISE INFO 'Staged % rows', row_count;

    -- Merge into target
    DELETE FROM public.orders
    USING stg_orders
    WHERE orders.order_id = stg_orders.order_id;

    INSERT INTO public.orders
    SELECT * FROM stg_orders;

    DROP TABLE stg_orders;

    RAISE INFO 'Incremental load complete for dates >= %', cutoff_date;
END;
$$;

CALL sp_incremental_load('2026-04-01');
```

### Spatial Data

Redshift supports GEOMETRY and GEOGRAPHY types with spatial functions:

```sql
CREATE TABLE stores (
    store_id INT ENCODE az64,
    store_name VARCHAR(100) ENCODE lzo,
    location GEOMETRY
)
DISTSTYLE AUTO;

INSERT INTO stores VALUES (1, 'Downtown', ST_GeomFromText('POINT(-73.985 40.748)'));

SELECT store_name, ST_DistanceSphere(location, ST_GeomFromText('POINT(-74.006 40.714)')) / 1000 AS distance_km
FROM stores
ORDER BY distance_km;
```

## Quick Reference: Key System Tables and Views

| Category | Key Objects |
|---|---|
| **Query history** | STL_QUERY, STL_QUERYTEXT, SYS_QUERY_HISTORY, SYS_QUERY_DETAIL |
| **Query performance** | SVL_QUERY_SUMMARY, SVL_QUERY_REPORT, STL_ALERT_EVENT_LOG |
| **Table design** | SVV_TABLE_INFO, SVV_ALTER_TABLE_RECOMMENDATIONS, SVV_DISKUSAGE |
| **WLM** | STL_WLM_QUERY, STV_WLM_QUERY_STATE, STV_WLM_SERVICE_CLASS_CONFIG |
| **COPY/load** | STL_LOAD_ERRORS, STL_LOADERROR_DETAIL, SYS_LOAD_HISTORY |
| **Locks** | STV_LOCKS, STV_BLOCKERS, SVV_TRANSACTIONS |
| **Spectrum** | SVL_S3QUERY_SUMMARY, SVL_S3PARTITION, SVL_S3LOG |
| **Serverless** | SYS_SERVERLESS_USAGE, SYS_QUERY_HISTORY (includes RPU usage) |
| **Data sharing** | SVV_DATASHARES, SVV_DATASHARE_OBJECTS, SVV_DATASHARE_CONSUMERS |
| **Concurrency scaling** | STL_CONCURRENCY_SCALING_USAGE |
| **Compilation** | SVL_COMPILE |
