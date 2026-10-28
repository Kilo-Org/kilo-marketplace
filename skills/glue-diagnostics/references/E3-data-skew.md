---
title: "E3 — Data Skew"
description: "Diagnose data skew causing uneven task distribution and straggler tasks"
status: active
severity: MEDIUM
triggers:
  - "data skew"
  - "straggler tasks"
  - "uneven partitions"
  - "one task much slower"
  - "hot key"
  - "skewed join"
owner: devops-agent
objective: "Identify and resolve data skew that causes uneven processing and straggler tasks"
context: "Data skew occurs when some partition keys have disproportionately more data than others. This causes a few tasks to process much more data while others finish quickly. Common in joins on skewed keys (e.g., null values, popular categories), groupBy on low-cardinality columns, and time-based partitions with uneven event distribution. Spark UI shows skew as large variance in task duration within a stage."
---

## Phase 1 — Triage

MUST:
- Check Spark UI for task duration variance within stages (if enabled)
- Identify the skewed key by examining data distribution
- Check CloudWatch metrics for uneven executor utilization
- Review the transformation causing skew (join key, groupBy key, partition key)

SHOULD:
- Sample the data to identify hot keys: count records per key value
- Check for null values in join keys (nulls all hash to the same partition)
- Verify partition count and size distribution
- Check if the skew is in the source data or introduced by transformations

MAY:
- Profile key distribution with a separate analysis job
- Check historical data for skew pattern changes over time

## Phase 2 — Remediate

MUST:
- Address the specific skew pattern (null keys, hot keys, uneven partitions)
- Verify the fix reduces task duration variance

SHOULD:
- Use salting for skewed join keys: add a random prefix to the hot key, replicate the other table
- Filter null values before joins and handle them separately
- Use Spark AQE skew join optimization (Glue 3.0+): `--conf spark.sql.adaptive.skewJoin.enabled=true`
- Repartition with a more evenly distributed key

MAY:
- Implement custom partitioning logic for known skew patterns
- Pre-aggregate data to reduce skew before joins
- Use two-phase aggregation: partial aggregate per partition, then final aggregate

## Common Issues

- symptoms: "One task takes 10x longer than others in a join stage"
  diagnosis: "Join key has a hot value (e.g., 'unknown', null, or a popular category) with millions of records."
  resolution: "Salt the hot key: add random suffix (key + '_' + rand(0,10)), replicate the small table 10x with matching suffixes."

- symptoms: "GroupBy operation has straggler tasks"
  diagnosis: "Low-cardinality groupBy key with uneven distribution."
  resolution: "Use two-phase aggregation: partial aggregate with salted key, then final aggregate on original key."

- symptoms: "Null values causing skew in join"
  diagnosis: "Null join keys all hash to the same partition, creating a massive skewed partition."
  resolution: "Filter nulls before join: df.filter(col('key').isNotNull()). Process null records separately."

## Output Format

```yaml
root_cause: "data_skew — <specific_cause>"
evidence:
  - type: task_metrics
    content: "<task duration variance, partition sizes>"
  - type: key_distribution
    content: "<hot keys and their record counts>"
severity: MEDIUM
mitigation:
  immediate: "Apply salting, null filtering, or AQE skew join"
  long_term: "Redesign partition keys, implement pre-aggregation"
```


## Safety Ratings
```
safety_ratings:
  - "Check Spark UI for task variance: GREEN — read-only diagnostics"
  - "Identify hot keys: GREEN — read-only data analysis"
  - "Add salting to join keys: GREEN — code change"
  - "Filter null values: GREEN — code change"
  - "Enable AQE skew join: GREEN — Spark configuration change"
```

## Escalation Conditions
- Job processes production data pipeline
- Straggler tasks causing job timeout
- Fix requires data pipeline redesign
- Hot keys from business data patterns
- Skew worsening over time with data growth

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Key distribution data: business data patterns"
    - "Hot key values: may reveal business entities"
  handling: "Hot key analysis may reveal business data patterns. Do not expose key values externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER ignore null values in join keys (they cause massive skew)
- NEVER apply salting without replicating the other table to match

## Phase 3 — Rollback
- If salting was added: remove salting logic and restore original join
- If null filtering was added: remove filter if nulls need to be preserved
- If AQE skew join was enabled: disable if it causes unexpected behavior
- If repartitioning was added: remove if it causes excessive shuffle

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
