---
name: "glue-diagnostics"
description: "Use this skill to investigate and troubleshoot AWS Glue problems by analyzing ETL jobs, crawlers, connections, Data Catalog, DPU utilization, Spark execution, and job bookmarks following structured runbooks. Activate when: job failures, job timeouts, OOM errors, Spark executor or driver crashes, crawler failures, schema detection issues, partition problems, JDBC connection failures, VPC/subnet connectivity, S3 endpoint access, Data Catalog sync issues, schema evolution conflicts, DPU sizing problems, shuffle bottlenecks, data skew, transformation errors, bookmark issues, data quality failures, IAM permission errors, encryption problems, Glue Studio visual editor errors, job generation failures, or the user says something is wrong with Glue without naming specific symptoms."
metadata:
  category: data
  source:
    repository: "https://github.com/aws-samples/sample-ai-agent-skills"
    path: "glue-troubleshooting"
    license_path: "LICENSE"
---

# Glue Diagnostics

## When to use

Any AWS Glue investigation where the console alone is insufficient — job failures, OOM errors, Spark crashes, crawler schema misdetection, connection timeouts, Data Catalog drift, DPU under/over-provisioning, data skew, bookmark corruption, or Glue Studio generation errors.

## Investigation workflow

### Step 1 — Collect and triage

```
aws glue get-job --name <job-name>
aws glue get-job-run --job-name <job-name> --run-id <run-id>
aws glue batch-get-jobs --job-names <job1> <job2>
aws glue get-crawler --name <crawler-name>
aws glue get-connection --name <connection-name>
aws logs filter-log-events --log-group-name /aws-glue/jobs/logs-v2 --log-stream-name-prefix <run-id>
```

### Step 2 — Domain deep dive

```
aws glue get-job-runs --job-name <job-name> --max-results 10
aws glue get-crawler-metrics --crawler-name-list <crawler-name>
aws glue get-databases
aws glue get-tables --database-name <db-name>
aws glue get-partitions --database-name <db-name> --table-name <table-name>
aws glue get-job-bookmark --job-name <job-name>
aws cloudwatch get-metric-statistics --namespace Glue --metric-name glue.driver.aggregate.bytesRead --dimensions Name=JobName,Value=<job-name> --start-time <iso> --end-time <iso> --period 300 --statistics Sum
```

Read `references/glue-guardrails.md` before concluding on any Glue issue.

## Tool quick reference

| Tool / API | When to use |
|------------|-------------|
| `glue get-job` | Job configuration, Glue version, DPU, worker type |
| `glue get-job-run` | Specific run status, error message, execution time |
| `glue batch-get-jobs` | Retrieve multiple job configs at once |
| `glue get-job-runs` | Job run history, failure patterns |
| `glue get-crawler` | Crawler config, targets, schedule, schema change policy |
| `glue get-crawler-metrics` | Crawler runtime stats, tables created/updated |
| `glue get-connection` | JDBC/network connection config, VPC, subnet |
| `glue get-databases` / `get-tables` | Data Catalog metadata, schema definitions |
| `glue get-partitions` | Partition metadata, partition keys, storage location |
| `glue get-job-bookmark` | Bookmark state for incremental processing |
| `logs filter-log-events` | Glue job CloudWatch logs for Spark errors |
| `cloudwatch get-metric-statistics` | Glue job metrics (bytes read/written, DPU usage) |

## Gotchas: AWS Glue

- DPU sizing matters: G.1X (1 DPU per worker, 16 GB memory), G.2X (2 DPU, 32 GB), G.4X (4 DPU, 64 GB), G.8X (8 DPU, 128 GB). Under-provisioning causes OOM; over-provisioning wastes cost.
- Spark executor OOM vs driver OOM: executor OOM means data partitions are too large (repartition or increase worker type). Driver OOM means too much data collected to the driver (avoid collect(), reduce broadcast join size).
- Job bookmarks track processed data for incremental loads. Bookmarks only work with S3 sources using job.init()/job.commit(). Resetting bookmarks reprocesses all data.
- Crawler schema evolution: crawlers can add new columns but may not handle type changes gracefully. Schema change policy (UPDATE_IN_DATABASE vs LOG) controls behavior.
- Glue connections for JDBC require VPC, subnet, and security group configuration. The subnet must have a NAT gateway or VPC endpoints for Glue service access.
- Glue Data Catalog vs Hive metastore: Glue Data Catalog is the default metastore for Glue jobs. External Hive metastore requires explicit configuration and network connectivity.
- Glue Studio visual editor has limitations: complex transformations may require custom code nodes. Not all PySpark/Scala operations are available as visual transforms.
- Spark UI is available for Glue 2.0+ jobs via the Glue console. It provides DAG visualization, stage details, and executor metrics for debugging performance issues.
- Job timeout defaults to 48 hours (2880 minutes). Long-running jobs may silently consume DPUs. Always set an explicit timeout.
- Glue version compatibility: Glue 2.0 (Spark 2.4), Glue 3.0 (Spark 3.1), Glue 4.0 (Spark 3.3). Library availability and behavior differ across versions.
- Partition management: too many small partitions cause excessive S3 LIST calls. Too few large partitions cause OOM. Aim for 128 MB–512 MB per partition.
- S3 eventual consistency impact: S3 provides strong read-after-write consistency since December 2020, but Glue Data Catalog partition metadata updates may still lag behind S3 changes.

### Worker type comparison

| Worker Type | DPU | Memory | vCPU | Use Case |
|-------------|-----|--------|------|----------|
| G.1X | 1 | 16 GB | 4 | Standard ETL, small-medium datasets |
| G.2X | 2 | 32 GB | 8 | Memory-intensive transforms, large joins |
| G.4X | 4 | 64 GB | 16 | ML transforms, very large datasets |
| G.8X | 8 | 128 GB | 32 | Massive datasets, complex aggregations |
| G.025X | 0.25 | 2 GB | 2 | Python shell jobs only |
| Z.2X | 2 | 32 GB | 8 | Ray jobs (Glue 4.0+) |

### Glue version comparison

| Version | Spark | Python | Key Features |
|---------|-------|--------|-------------|
| Glue 2.0 | 2.4 | 3.7 | Spark UI, no startup overhead |
| Glue 3.0 | 3.1 | 3.7 | Optimized shuffle, auto-scaling |
| Glue 4.0 | 3.3 | 3.10 | Ray support, Python 3.10, improved performance |

## Anti-hallucination rules

1. Always cite specific job run error messages, crawler metrics, or CloudWatch log entries as evidence.
2. Never assume OOM is always executor-side. Check whether the error is on the driver or executor — the fix is different.
3. Job bookmarks only work with supported sources (S3, JDBC) and require job.init()/job.commit() calls. Never claim bookmarks work automatically with all sources.
4. Crawler schema changes depend on the SchemaChangePolicy. Never assume crawlers automatically update table schemas.
5. Glue connections require VPC networking. Never suggest JDBC connections work without proper VPC, subnet, and security group configuration.
6. Spend no more than 2 minutes on any single hypothesis. Pivot if inconclusive.

## 28 runbooks

| Category | IDs | Covers |
|----------|-----|--------|
| A — Jobs | A1–A4 | Job failures, timeout, OOM, Spark errors |
| B — Crawlers | B1–B3 | Crawler failures, schema detection, partition issues |
| C — Connections | C1–C3 | JDBC connection failures, VPC/subnet, S3 endpoint |
| D — Data Catalog | D1–D2 | Catalog sync issues, schema evolution |
| E — Performance | E1–E3 | DPU sizing, shuffle issues, data skew |
| F — ETL | F1–F3 | Transformation errors, bookmark issues, data quality |
| G — Security | G1–G2 | IAM permissions, encryption |
| H — Glue Studio | H1–H2 | Visual editor errors, job generation |
| Z — Catch-All | Z1 | General troubleshooting |
