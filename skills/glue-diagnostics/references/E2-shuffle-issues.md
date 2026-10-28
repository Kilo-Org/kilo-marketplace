---
title: "E2 — Shuffle Issues"
description: "Diagnose Spark shuffle bottlenecks causing slow Glue job performance"
status: active
severity: MEDIUM
triggers:
  - "shuffle"
  - "spill to disk"
  - "shuffle read"
  - "shuffle write"
  - "slow join"
  - "slow groupBy"
owner: devops-agent
objective: "Identify and resolve Spark shuffle bottlenecks in Glue ETL jobs"
context: "Shuffle occurs during joins, groupBy, repartition, and sort operations. Data is redistributed across executors via network and disk. Excessive shuffle causes disk spill, network saturation, and slow execution. Glue 3.0+ has optimized shuffle with push-based shuffle. Key indicators: high shuffle read/write bytes, shuffle spill metrics, and long stage durations in Spark UI."
---

## Phase 1 — Triage

MUST:
- Check job run duration and identify slow stages via Spark UI (if enabled)
- Review CloudWatch metrics for shuffle: `glue.ALL.system.cpuSystemLoad`, `glue.ALL.jvm.heap.usage`
- Check CloudWatch logs for shuffle-related errors or warnings
- Identify which transformations trigger shuffle (joins, groupBy, distinct, repartition)

SHOULD:
- Check Spark UI for shuffle read/write bytes per stage
- Look for shuffle spill (memory) and shuffle spill (disk) metrics
- Verify partition count before and after shuffle operations
- Check if broadcast joins could replace shuffle joins for small tables

MAY:
- Profile the job with Spark event logs for detailed shuffle analysis
- Check network throughput between executors

## Phase 2 — Remediate

MUST:
- Reduce shuffle data volume by filtering early in the pipeline
- Use broadcast joins for small dimension tables (< 100 MB)
- Optimize partition count: too few = large shuffles, too many = scheduling overhead

SHOULD:
- Set spark.sql.shuffle.partitions appropriately (default 200, adjust based on data volume)
- Use Glue 3.0+ for optimized push-based shuffle
- Pre-sort or pre-partition data to reduce shuffle in recurring jobs
- Use coalesce() instead of repartition() when reducing partitions

MAY:
- Enable adaptive query execution (AQE) in Glue 3.0+ for automatic shuffle optimization
- Implement bucketing for frequently joined tables
- Use map-side aggregation (reduceByKey instead of groupByKey) for aggregations

## Common Issues

- symptoms: "Join operation takes 90% of total job time"
  diagnosis: "Large shuffle join between two big tables without partition alignment."
  resolution: "Use broadcast join if one table is small. Pre-partition both tables on the join key. Filter data before joining."

- symptoms: "Shuffle spill to disk causing slow performance"
  diagnosis: "Shuffle data exceeds executor memory, spilling to local disk."
  resolution: "Increase worker type (G.1X → G.2X) for more memory. Reduce partition size. Filter data earlier in the pipeline."

- symptoms: "Job slow after repartition() call"
  diagnosis: "Repartition triggers a full shuffle of all data across the cluster."
  resolution: "Use coalesce() to reduce partitions without full shuffle. Only use repartition() when increasing partitions or changing partition key."

## Output Format

```yaml
root_cause: "shuffle_issue — <specific_cause>"
evidence:
  - type: spark_ui_metrics
    content: "<shuffle read/write bytes, spill metrics>"
  - type: stage_duration
    content: "<slow stage identification>"
severity: MEDIUM
mitigation:
  immediate: "Optimize shuffle-heavy transformations"
  long_term: "Use broadcast joins, AQE, pre-partitioning"
```


## Safety Ratings
```
safety_ratings:
  - "Check Spark UI and metrics: GREEN — read-only diagnostics"
  - "Optimize shuffle partitions: GREEN — Spark configuration change"
  - "Use broadcast joins: GREEN — code change, no infrastructure impact"
  - "Upgrade worker type: YELLOW — increases cost"
  - "Enable AQE: GREEN — Spark configuration change"
```

## Escalation Conditions
- Job processes production data pipeline
- Shuffle bottleneck causing job timeout
- Fix requires data pipeline redesign
- Shuffle spill to disk degrading performance
- Large join operations requiring architecture changes

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Spark UI metrics: execution details"
    - "Shuffle data volumes: data flow patterns"
  handling: "Do not expose Spark execution details externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER set shuffle partitions to 1 (creates a single massive partition)
- NEVER use broadcast join for tables larger than 100 MB

## Phase 3 — Rollback
- If shuffle partitions were changed: restore previous value
- If broadcast join was added: remove if it causes driver OOM
- If AQE was enabled: disable if it causes unexpected behavior
- If worker type was upgraded: downgrade after optimization

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
