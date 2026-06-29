---
title: "A3 — Out of Memory (OOM) Errors"
description: "Diagnose and resolve Glue job OOM errors on executors or driver"
status: active
severity: CRITICAL
triggers:
  - "OutOfMemoryError"
  - "OOM"
  - "heap space"
  - "Container killed by YARN for exceeding memory limits"
  - "executor lost"
  - "driver out of memory"
owner: devops-agent
objective: "Identify whether OOM is on executor or driver side and apply the correct fix"
context: "OOM errors in Glue jobs are either executor-side (data partitions too large for worker memory) or driver-side (too much data collected to the driver node). The fix is fundamentally different for each. Executor OOM requires repartitioning or larger worker types. Driver OOM requires eliminating collect() calls and reducing broadcast join sizes. Never apply the same fix to both."
---

## Phase 1 — Triage

MUST:
- Get the error message: `aws glue get-job-run --job-name <name> --run-id <run-id>`
- Check CloudWatch logs for the full stack trace: `aws logs filter-log-events --log-group-name /aws-glue/jobs/logs-v2 --log-stream-name-prefix <run-id> --filter-pattern "OutOfMemoryError"`
- Determine if OOM is on executor or driver from the stack trace
- Check current worker type and count: `aws glue get-job --name <name>`

SHOULD:
- Review Spark UI for task memory usage and GC time
- Check input data size and partition count
- Identify the specific stage/transformation causing OOM
- Check for broadcast join thresholds in job parameters

MAY:
- Profile memory usage with smaller data samples
- Check for memory leaks in UDFs or custom transformations

## Phase 2 — Remediate

MUST:
- For executor OOM: repartition data to smaller partitions or upgrade worker type (G.1X → G.2X → G.4X)
- For driver OOM: remove collect(), toPandas(), or countByKey() calls; reduce broadcast join threshold
- Verify fix with a test run

SHOULD:
- Set spark.sql.autoBroadcastJoinThreshold to -1 to disable broadcast joins for large tables
- Use coalesce() instead of repartition() when reducing partition count (avoids full shuffle)
- Add --conf spark.executor.memoryOverhead for off-heap memory issues

MAY:
- Enable adaptive query execution (Glue 3.0+) for automatic partition coalescing
- Implement incremental processing to reduce per-run data volume

## Common Issues

- symptoms: "java.lang.OutOfMemoryError: Java heap space on executor"
  diagnosis: "Data partitions exceed executor memory. Common with large joins, groupBy, or reading large files."
  resolution: "Repartition data: df.repartition(200). Or upgrade from G.1X (16 GB) to G.2X (32 GB) workers."

- symptoms: "java.lang.OutOfMemoryError: Java heap space on driver"
  diagnosis: "Driver collecting too much data via collect(), toPandas(), or large broadcast join."
  resolution: "Remove collect() calls. Set spark.sql.autoBroadcastJoinThreshold=-1. Use take(N) instead of collect()."

- symptoms: "Container killed by YARN for exceeding memory limits"
  diagnosis: "Off-heap memory usage (native memory, serialization buffers) exceeding container limits."
  resolution: "Increase spark.executor.memoryOverhead via --conf parameter. Upgrade worker type for more total memory."

## Output Format

```yaml
root_cause: "oom_error — <executor|driver> — <specific_cause>"
evidence:
  - type: error_stack_trace
    content: "<OOM error and stack trace>"
  - type: job_config
    content: "<worker type, count, and memory settings>"
severity: CRITICAL
mitigation:
  immediate: "Apply executor or driver-specific OOM fix"
  long_term: "Right-size workers, optimize partitioning, add memory monitoring"
```


## Safety Ratings
```
safety_ratings:
  - "Check error message and logs: GREEN — read-only diagnostics"
  - "Check worker type and count: GREEN — read-only API call"
  - "Upgrade worker type: YELLOW — increases cost per DPU-hour"
  - "Repartition data in script: GREEN — code change, no infrastructure impact"
  - "Disable broadcast joins: GREEN — Spark configuration change"
```

## Escalation Conditions
- Job processes production data pipeline
- OOM errors on largest available worker type (G.8X)
- Fix requires data pipeline redesign
- Driver OOM requiring script architecture changes
- Recurring OOM due to growing data volumes

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Stack traces: may reveal data processing logic"
    - "Job configuration: worker type and memory settings"
    - "Data volumes: business activity indicators"
  handling: "Stack traces may contain sensitive data references. Do not expose externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER apply the same fix for executor OOM and driver OOM (they require different solutions)
- NEVER use collect() on large datasets in production jobs

## Phase 3 — Rollback
- If worker type was upgraded: downgrade back to previous type if OOM is resolved by code changes
- If repartition was added: remove if it causes excessive shuffle overhead
- If broadcast join threshold was changed: restore previous value
- If memoryOverhead was increased: restore default if not needed

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
