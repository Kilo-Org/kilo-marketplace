# Amazon Redshift Architecture Reference

## Cluster Architecture

### Leader Node

The leader node is the single entry point for all client connections and SQL operations:

- **SQL parsing and semantic analysis** -- Validates syntax, resolves object references, checks permissions.
- **Query optimization** -- Cost-based optimizer generates an optimal distributed execution plan. Considers table statistics (collected by ANALYZE), distribution styles, sort keys, zone maps, and materialized views.
- **Query plan distribution** -- Compiles the plan into C++ code (first execution), then distributes compiled segments to compute nodes.
- **Result aggregation** -- Collects partial results from compute nodes, performs final merge/sort/limit, and returns to the client.
- **Metadata storage** -- System catalog (pg_catalog), user credentials, and cluster metadata reside on the leader node.
- **No user data** -- The leader node does not store any user table data. It exclusively coordinates.

The leader node is always present (even in single-node clusters, the node acts as both leader and compute).

### Compute Nodes

Compute nodes store data and execute query plan segments in parallel:

- **Local storage (DC2)** -- Dense compute nodes with NVMe SSD storage. Data is stored locally. Capacity is fixed to node count.
- **Managed storage (RA3)** -- Nodes use local NVMe SSD as a high-performance cache, backed by Amazon S3 for durable storage (Redshift Managed Storage / RMS). Hot data is cached locally; cold data is transparently fetched from S3. Storage scales to virtually unlimited capacity independent of compute nodes.
- **DS2 nodes** -- Legacy dense storage nodes with HDD. No longer recommended for new clusters.

### Node Types (Current Generation)

| Node Type | vCPU | Memory | Storage | Slices | Use Case |
|---|---|---|---|---|---|
| RA3.xlplus | 4 | 32 GB | 32 TB RMS | 2 | Small workloads, dev/test |
| RA3.4xlarge | 12 | 96 GB | 128 TB RMS | 4 | Production workloads |
| RA3.16xlarge | 48 | 384 GB | 128 TB RMS | 16 | Large-scale production |
| DC2.large | 2 | 15 GB | 160 GB SSD | 2 | Small datasets, low latency |
| DC2.8xlarge | 32 | 244 GB | 2.56 TB SSD | 16 | Compute-intensive, <2.56TB/node |

**Elastic resize** allows adding/removing nodes (changes slice count). **Classic resize** changes node type. RA3 clusters can also use **concurrency scaling** to add transient compute for burst demand.

### Slices

Each compute node is divided into slices. A slice:

- Has its own allocation of memory, CPU, and disk (or cache for RA3).
- Processes its portion of the data independently and in parallel.
- Receives a subset of table rows based on the table's distribution style.
- Executes query plan steps (scan, join, aggregate) on its local data.

The total parallelism of a cluster = total number of slices across all compute nodes. For example, a 4-node RA3.4xlarge cluster has 4 * 4 = 16 slices.

## Columnar Storage Engine

### 1 MB Block Architecture

Redshift stores each column in a sequence of immutable 1 MB blocks:

- Each block contains compressed values for a single column from a contiguous range of rows.
- Blocks are the unit of I/O: Redshift reads or skips entire 1 MB blocks.
- Column blocks for the same row range form a **superblock** (logical grouping, not a physical unit).
- Block headers contain compression metadata, row count, and zone map information.

### Zone Maps

Zone maps are automatically maintained per-block min/max metadata:

- Every 1 MB block stores the minimum and maximum values of the data it contains.
- During a scan, the query executor checks the zone map before reading the block.
- If the query predicate does not overlap the block's [min, max] range, the block is skipped entirely.
- Zone maps make sort keys critical: a well-sorted column has narrow min/max ranges per block, enabling aggressive block skipping.
- Zone maps are maintained automatically on all columns -- no user action needed.

**Zone map effectiveness depends on data order:**
```
-- Table sorted by order_date
-- Block 1: order_date min=2026-01-01, max=2026-01-15  --> Zone map tight
-- Block 2: order_date min=2026-01-16, max=2026-01-31  --> Zone map tight
-- WHERE order_date = '2026-01-20' skips Block 1 entirely

-- Table NOT sorted by order_date
-- Block 1: order_date min=2020-01-01, max=2026-12-31  --> Zone map useless
-- Block 2: order_date min=2020-03-01, max=2026-11-15  --> Zone map useless
-- WHERE order_date = '2026-01-20' must read ALL blocks
```

### Late Materialization

Redshift uses late materialization to minimize data movement:

1. Predicates are evaluated on individual compressed columns.
2. Only row positions that pass all predicates are collected.
3. Remaining projected columns are materialized (decompressed and assembled) only for qualifying rows.

This means a query like `SELECT name FROM users WHERE age > 30 AND country = 'US'` only decompresses the `name` column for rows that pass both filters on `age` and `country`.

### Compression Architecture

Compression is applied per column at the block level:

- **Encoding** is set per column at CREATE TABLE time (or automatically by ENCODE AUTO / ATO).
- **ANALYZE COMPRESSION** examines sample data and recommends optimal encodings.
- Compressed data stays compressed during I/O and in the buffer cache; decompression occurs during query execution.
- Compression ratios of 3:1 to 10:1 are typical for well-encoded analytical data.

**Encoding selection algorithm (ENCODE AUTO):**
1. For new tables with ENCODE AUTO, Redshift initially uses RAW encoding.
2. After sufficient data is loaded, background ATO processes analyze data patterns.
3. Redshift selects the encoding that minimizes storage while maintaining acceptable CPU overhead.
4. The sort key leading column can use any encoding (Redshift removed the historical RAW-only restriction for sort key columns).

## Query Execution Pipeline

### 1. Parse and Analyze

- SQL text arrives at the leader node.
- Parser validates syntax and generates an AST.
- Analyzer resolves table/column references, checks permissions, and binds data types.

### 2. Optimize

The cost-based optimizer:

- Generates candidate query plans considering join order, join type (hash join, merge join, nested loop), scan type (sequential, zone-map-accelerated), and data distribution.
- Uses table statistics (row count, distinct values, null fraction, histogram) collected by ANALYZE or auto-analyze.
- Considers sort key order (to enable merge joins on sorted data and zone map pruning).
- Considers distribution style (to identify co-located joins vs. redistribution needed).
- Evaluates materialized view rewriting opportunities.
- Selects the plan with the lowest estimated cost.

### 3. Compile

- The optimized plan is compiled into C++ code.
- Compiled code is cached (keyed by query template / parameterized plan).
- **Compilation cache** persists across sessions. First execution of a new query template incurs compilation overhead (1-10 seconds); subsequent executions with the same template reuse the compiled code.
- Monitor compilation via SVL_COMPILE. High compile times indicate many unique query shapes.

### 4. Distribute and Execute

- Compiled plan segments are distributed to compute nodes.
- Each slice executes its segment on its local data in parallel.
- Data movement between slices occurs for:
  - **Redistribution** (DS_DIST_BOTH, DS_DIST_INNER, DS_DIST_ALL_INNER) -- Data is redistributed across slices for joins when tables are not co-located.
  - **Broadcast** (DS_BCAST_INNER) -- Small table is broadcast to all slices for a join.
  - **Sort merge** -- Data is sorted and merged across slices for ORDER BY or merge joins.

### 5. Return Results

- Compute nodes return partial results to the leader node.
- Leader node performs final aggregation, sorting (if needed), and LIMIT.
- Results are streamed back to the client.

### Data Movement in Joins (EXPLAIN Plan Labels)

| Label | Meaning | Performance Impact |
|---|---|---|
| `DS_DIST_NONE` | Both tables are co-located on the join key (same DISTKEY) | Best -- no data movement |
| `DS_DIST_ALL_NONE` | Inner table is DISTSTYLE ALL (replicated on every node) | Good -- no data movement |
| `DS_DIST_INNER` | Inner table is redistributed to match outer table's distribution | Moderate -- moves inner table data |
| `DS_DIST_BOTH` | Both tables are redistributed on the join key | Expensive -- moves data from both tables |
| `DS_BCAST_INNER` | Inner table is broadcast to all nodes | Acceptable for small inner tables; costly if inner is large |
| `DS_DIST_ALL_INNER` | Inner table (ALL distribution) is redistributed | Unusual; indicates mismatched distribution |

### Result Caching

Redshift caches query results on the leader node:

- If the same query is resubmitted and underlying data has not changed, results are returned from cache immediately.
- Result cache is per-cluster, persists across sessions, and is invalidated on data changes.
- Controlled by `enable_result_cache_for_session` (default ON).
- Result cache hits show `source_query` in SYS_QUERY_HISTORY pointing to the original execution.

## Redshift Managed Storage (RMS) Architecture

RA3 nodes use a tiered storage architecture:

1. **Local NVMe SSD cache** -- Multi-TB local cache on each compute node. Stores hot blocks (recently and frequently accessed).
2. **Amazon S3 durable storage** -- All data is durably stored in S3. This is the system of record.
3. **Automatic tiering** -- Redshift's intelligent caching algorithm tracks block access patterns and keeps hot data local. Cold data is evicted to S3 and fetched on demand.
4. **Prefetching** -- The query executor prefetches blocks from S3 ahead of sequential scans.
5. **Cross-AZ durability** -- S3 provides 99.999999999% (11 nines) durability.

### Snapshots and Recovery

- **Automated snapshots** -- Taken every 8 hours or after 5 GB of data changes. Retained for 1-35 days. Incremental (only changed blocks are stored).
- **Manual snapshots** -- User-initiated, retained until explicitly deleted. Can be copied cross-region.
- **Restore** -- Creates a new cluster from a snapshot. Can restore to a different node type or count.
- **Table-level restore** -- Restore individual tables from a snapshot without restoring the entire cluster.
- **Point-in-time recovery** -- Restore to any second within the retention period (continuous backup).

## Redshift Serverless Architecture

Redshift Serverless separates compute from storage entirely:

### Workgroups and Namespaces

- **Namespace** -- Logical container for databases, schemas, tables, users, and datashares. A namespace has one underlying Redshift Managed Storage. Multiple workgroups can share a single namespace for data sharing.
- **Workgroup** -- A compute endpoint. Defined by base RPU capacity (8-512 RPUs in increments of 8). Scales automatically up from the base during demand spikes.
- **RPU (Redshift Processing Unit)** -- Abstract unit of compute capacity. 1 RPU provides approximately the compute of one RA3 slice. Billed per RPU-second of actual usage.

### Auto-Scaling Behavior

1. Query arrives at the workgroup endpoint.
2. If current RPU allocation is insufficient, Redshift Serverless automatically scales up (within seconds).
3. After queries complete and demand drops, RPUs scale back down.
4. You are billed only for RPU-seconds consumed, with a minimum of 60 seconds per query.
5. The base RPU setting establishes the minimum compute that is always warm (zero cold-start for queries within base capacity).

### Cost Controls

- **Usage limits** -- Set maximum RPU-hours per period (daily, weekly, monthly).
- **Actions on limit breach** -- Log only, send alert (SNS), or turn off the workgroup.
- **Cross-workgroup isolation** -- Different teams/workloads can use separate workgroups against the same namespace, each with their own cost controls and RPU settings.

## AQUA (Advanced Query Accelerator)

AQUA is a hardware-accelerated distributed cache layer available on RA3 nodes:

### Architecture

- AQUA nodes sit between compute nodes and Redshift Managed Storage (S3).
- Each AQUA node has custom AWS-designed hardware (Nitro-based) with FPGA-accelerated processing.
- AQUA pushes scan filtering and aggregation operations down to the storage/cache layer.
- This reduces the volume of data transferred to compute nodes by orders of magnitude for selective queries.

### Operations Accelerated by AQUA

- Predicate evaluation (WHERE clause filtering) -- especially LIKE, string comparisons, numeric comparisons.
- Aggregation (SUM, COUNT, MIN, MAX, AVG) on filtered data.
- Scan-intensive queries on large tables.

### AQUA Behavior

- Automatically enabled on RA3 node types (no user configuration needed).
- The query optimizer decides whether to route scan/filter operations to AQUA based on cost estimation.
- Benefits are most visible for queries that scan large amounts of data but return small result sets.
- AQUA status can be monitored via SYS_QUERY_DETAIL (shows whether AQUA was used for scan steps).

## Concurrency Scaling

Concurrency scaling provides burst compute capacity:

1. When queues back up (queries wait in WLM queues), Redshift launches transient concurrency scaling clusters.
2. These clusters are functionally identical to the main cluster with full access to the same data (via RMS/S3).
3. Queries are routed to scaling clusters transparently.
4. Scaling clusters are terminated when demand subsides.
5. **Free credit:** Each cluster earns up to 1 hour of free concurrency scaling credits per day for every 24 hours the cluster is active.
6. **Beyond free credits:** Billed per-second at the same rate as on-demand cluster pricing.

### Concurrency Scaling Modes

- `auto` (default) -- Redshift automatically uses concurrency scaling when queues back up.
- `off` -- Disabled; queries wait in WLM queues.

Enable per-queue via WLM configuration: set `concurrency_scaling` to `auto` on the target WLM queue.

## Data Sharing Architecture

Data sharing uses the Redshift Managed Storage layer for zero-copy access:

- **Producer** -- The cluster/serverless namespace that owns the data and creates the datashare.
- **Consumer** -- The cluster/serverless workgroup that reads shared data.
- **No data movement** -- Consumers query producer data directly via RMS. Data stays in the producer's S3 storage.
- **Live access** -- Consumers always see the producer's current data (no snapshots or lag).
- **Isolation** -- Consumer queries execute on consumer compute resources; they do not impact producer performance.
- **Cross-region** -- Data sharing works across AWS regions (cross-region incurs data transfer costs).
- **Cross-account** -- Share data with different AWS accounts.
- **Granularity** -- Share at schema, table, view (including materialized views), or UDF level.

## Streaming Ingestion Architecture

Streaming ingestion provides low-latency data ingestion from streaming sources:

1. Redshift connects directly to Kinesis Data Streams or Amazon MSK (Kafka) topics.
2. Data is ingested via a materialized view defined over an external schema FROM KINESIS or FROM MSK.
3. The materialized view is auto-refreshed (typically every 10 seconds to a few minutes depending on configuration).
4. Incoming records are parsed (JSON, Avro, etc.) and landed into Redshift columnar storage.
5. No intermediate staging in S3 or Kinesis Firehose needed.

## Zero-ETL Integration Architecture

Zero-ETL replicates data from transactional databases to Redshift:

1. **Change data capture (CDC)** -- Aurora/RDS writes are captured via the database engine's transaction log.
2. **Continuous replication** -- Changes are streamed to Redshift with seconds-to-minutes latency.
3. **Schema mapping** -- Source tables are mapped to Redshift tables in a target database.
4. **Automatic schema evolution** -- DDL changes (add column, etc.) are replicated.
5. **Integration management** -- Managed via AWS Console, CLI, or CloudFormation. Each integration links one source database to one Redshift target.

Supported sources: Amazon Aurora MySQL, Amazon Aurora PostgreSQL, Amazon RDS MySQL, Amazon RDS PostgreSQL, Amazon DynamoDB.

## Network and Security Architecture

### VPC and Network

- Redshift clusters run within a VPC.
- **Enhanced VPC Routing** -- Forces all COPY/UNLOAD traffic through the VPC (instead of public internet routes), enabling VPC flow logs, VPC endpoints, and network ACLs.
- **VPC endpoints** -- Use interface VPC endpoints (PrivateLink) for private connectivity from other VPCs.
- **Publicly accessible** -- Optional; assigns a public IP for external tool connectivity. Not recommended for production.

### Encryption

- **At rest** -- AES-256 encryption using AWS KMS (default) or CloudHSM. Encrypts data blocks, system metadata, and snapshots.
- **In transit** -- SSL/TLS encryption for client connections (enforced via `require_ssl` parameter).
- **Key rotation** -- Automated key rotation supported for KMS-managed keys.

### Authentication and Authorization

- **IAM authentication** -- Temporary credentials via GetClusterCredentials API or IAM identity federation.
- **Native database users** -- CREATE USER with password.
- **Federated identity** -- SAML 2.0 or OIDC integration for SSO.
- **Role-based access control (RBAC)** -- CREATE ROLE, GRANT ROLE, system-defined roles (sys:operator, sys:dba, sys:superuser, sys:secadmin, sys:monitor).
- **Row-level security (RLS)** -- CREATE RLS POLICY to restrict row visibility per user/role.
- **Column-level access control** -- GRANT SELECT on specific columns.
- **Dynamic data masking** -- CREATE MASKING POLICY to mask sensitive column values based on user/role.
