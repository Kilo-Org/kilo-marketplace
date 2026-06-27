---
title: "A2 — Job Timeout"
description: "Diagnose why a Glue job is exceeding its timeout or running longer than expected"
status: active
severity: HIGH
triggers:
  - "job timeout"
  - "job running too long"
  - "job exceeded timeout"
  - "job hung"
  - "job not finishing"
owner: devops-agent
objective: "Identify why a Glue job is timing out or running excessively long and optimize execution time"
context: "The default Glue job timeout is 2880 minutes (48 hours). Jobs can appear hung due to data skew, shuffle bottlenecks, JDBC source slowness, S3 throttling, or insufficient DPUs. A stuck job at 10 G.2X workers for 48 hours costs over $400 in DPU-hours. Always set explicit timeouts."
---

## Phase 1 — Triage

MUST:
- Check job run status and duration: `aws glue get-job-run --job-name <name> --run-id <run-id>`
- Verify the configured timeout: `aws glue get-job --name <name>` (check Timeout field)
- Check CloudWatch metrics for DPU utilization: `aws cloudwatch get-metric-statistics --namespace Glue --metric-name glue.ALL.system.cpuSystemLoad --dimensions Name=JobName,Value=<name>,Name=JobRunId,Value=<run-id> --start-time <iso> --end-time <iso> --period 300 --statistics Average`
- Review Spark UI (if enabled) for stage progress and task distribution

SHOULD:
- Check for data skew by examining task duration variance in Spark UI
- Verify JDBC source query performance if reading from databases
- Check S3 request metrics for throttling (503 SlowDown errors)
- Compare execution time with previous successful runs

MAY:
- Profile the job with smaller dataset to identify bottleneck stages
- Check for Spark speculative execution settings

## Phase 2 — Remediate

MUST:
- Set an explicit timeout appropriate for the workload (2-3x expected duration)
- Address the identified bottleneck (data skew, shuffle, source slowness)

SHOULD:
- Enable auto-scaling (Glue 3.0+) to dynamically adjust worker count
- Optimize partition sizes to 128 MB–512 MB
- Add pushdown predicates for JDBC sources to reduce data transfer

MAY:
- Split large jobs into smaller, focused jobs
- Implement checkpointing for long-running jobs
- Use Glue job metrics CloudWatch alarms for early warning

## Common Issues

- symptoms: "Job runs for hours with low CPU utilization"
  diagnosis: "Data skew causing most tasks to finish quickly while a few tasks process disproportionately large partitions."
  resolution: "Repartition data using a more evenly distributed key. Use salting for skewed join keys."

- symptoms: "Job timeout reading from JDBC source"
  diagnosis: "Database query returning too much data or running slowly."
  resolution: "Add pushdown predicates, partition the JDBC read using hashfield or hashpartitions, or pre-filter data in the source query."

- symptoms: "Job runs much longer than previous runs on same data"
  diagnosis: "Data volume growth without corresponding DPU increase, or S3 throttling due to high request rates."
  resolution: "Increase worker count, optimize S3 key prefixes for better request distribution, or enable S3 request metrics to confirm throttling."

## Output Format

```yaml
root_cause: "job_timeout — <specific_cause>"
evidence:
  - type: job_run_duration
    content: "<execution time and timeout setting>"
  - type: cloudwatch_metrics
    content: "<DPU utilization and CPU metrics>"
severity: HIGH
mitigation:
  immediate: "Set explicit timeout and address bottleneck"
  long_term: "Enable auto-scaling, optimize partitioning, add monitoring"
```


## Safety Ratings
```
safety_ratings:
  - "Check job run status and metrics: GREEN — read-only API calls"
  - "Review Spark UI: GREEN — read-only analysis"
  - "Set explicit timeout: GREEN — adds cost protection"
  - "Enable auto-scaling: YELLOW — may increase cost during peak"
  - "Increase worker count: YELLOW — increases cost"
  - "Stop a running job: YELLOW — terminates processing, partial output may exist"
```

## Escalation Conditions
- Job processes production data pipeline
- Job running for hours with no progress
- Timeout causing missed SLA for downstream consumers
- Fix requires data pipeline architecture changes
- Cost of stuck job exceeding budget

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Job metrics: processing patterns and data volumes"
    - "Spark UI data: execution details and data flow"
    - "JDBC source queries: database access patterns"
  handling: "Do not expose job metrics or JDBC queries externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER leave the default 48-hour timeout on production jobs
- NEVER stop a job without checking if partial output needs cleanup

## Phase 3 — Rollback
- If timeout was changed: restore previous timeout value
- If worker count was increased: reduce back to previous count after optimization
- If auto-scaling was enabled: disable if cost is too high
- If job was stopped: clean up partial output data before re-running

## Escalation Conditions

escalation_conditions:
  - "Remediation requires modifying IAM policies in a production account"
  - "Remediation requires disabling a security control even temporarily"
  - "Root cause cannot be identified after 3 hypothesis pivots"
  - "Blast radius affects more than one account or region"
  - "Issue involves potential data loss or exposure"

## Prohibited Actions

prohibited_actions:
  - "NEVER suggest disabling encryption for Glue jobs"
  - "NEVER suggest overly broad Glue service role"
  - "NEVER suggest public S3 access for data catalog"
