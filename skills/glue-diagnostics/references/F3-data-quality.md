---
title: "F3 — Data Quality"
description: "Diagnose data quality issues in Glue ETL pipelines"
status: active
severity: MEDIUM
triggers:
  - "data quality"
  - "data validation"
  - "null values"
  - "duplicate records"
  - "data integrity"
  - "quality check failed"
owner: devops-agent
objective: "Identify and resolve data quality issues in Glue ETL processing"
context: "Data quality issues in Glue include unexpected nulls, duplicate records, type mismatches, out-of-range values, referential integrity violations, and encoding problems. Glue Data Quality (DQDL) provides rule-based validation. Common causes: source data changes, missing validation, schema drift, and ETL logic errors. Quality issues often propagate silently until downstream consumers report problems."
---

## Phase 1 — Triage

MUST:
- Identify the specific quality issue (nulls, duplicates, type errors, range violations)
- Check source data for the quality problem: verify if it originates in source or ETL
- Review the ETL script for missing validation or incorrect transformations
- Check Glue Data Quality results if rules are configured: review CloudWatch logs

SHOULD:
- Sample output data to quantify the quality issue
- Compare current output with previous successful runs
- Check for schema changes in source data that may cause quality degradation
- Verify encoding settings for text data (UTF-8, Latin-1)

MAY:
- Profile source data distribution to establish quality baselines
- Check for upstream pipeline changes that may affect data quality
- Review Glue Data Quality rule definitions for completeness

## Phase 2 — Remediate

MUST:
- Add data validation for the identified quality issue
- Fix the ETL logic causing quality degradation
- Verify output data quality after the fix

SHOULD:
- Implement Glue Data Quality rules (DQDL) for automated validation
- Add null handling (dropnulls, fillna) for critical columns
- Implement deduplication logic (dropDuplicates on key columns)
- Add data type validation before writes

MAY:
- Set up Glue Data Quality alerts via EventBridge for rule failures
- Implement data quarantine for records failing quality checks
- Create data quality dashboards for ongoing monitoring

## Common Issues

- symptoms: "Unexpected null values in output columns"
  diagnosis: "Source data contains nulls not handled by the ETL script, or join producing nulls for non-matching records."
  resolution: "Add null filtering or default values. Use inner join instead of outer join if nulls are not expected. Add DQDL rule: Completeness 'column' > 0.99"

- symptoms: "Duplicate records in target table"
  diagnosis: "Source data has duplicates, or job bookmark issue causing reprocessing."
  resolution: "Add dropDuplicates() on key columns. Check bookmark state. Implement upsert logic for the target."

- symptoms: "Data type errors in downstream queries"
  diagnosis: "ETL output has mixed types in a column (string and int) due to source data inconsistency."
  resolution: "Use resolveChoice() to enforce consistent types. Add explicit type casting. Add DQDL rule: ColumnDataType 'column' = 'int'"

## Output Format

```yaml
root_cause: "data_quality — <specific_cause>"
evidence:
  - type: quality_metrics
    content: "<null counts, duplicate counts, type distribution>"
  - type: sample_data
    content: "<sample records showing quality issue>"
severity: MEDIUM
mitigation:
  immediate: "Add validation and fix ETL logic"
  long_term: "Implement DQDL rules, monitoring, and data quarantine"
```


## Safety Ratings
```
safety_ratings:
  - "Check data quality metrics: GREEN — read-only analysis"
  - "Sample output data: GREEN — read-only inspection"
  - "Add DQDL rules: GREEN — adds validation without changing data"
  - "Add null handling: GREEN — defensive code addition"
  - "Add deduplication: YELLOW — changes output data, may affect downstream"
```

## Escalation Conditions
- Job processes production data pipeline
- Data quality issues affecting downstream analytics
- Duplicate records causing incorrect business metrics
- Null values breaking downstream transformations
- Source data quality degradation requiring upstream fixes

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Data samples: business data content"
    - "Quality metrics: data integrity indicators"
    - "DQDL rules: data validation logic"
  handling: "Data samples contain business data. Do not expose externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER silently drop records without logging them to a quarantine location
- NEVER disable data quality checks in production without approval

## Phase 3 — Rollback
- If DQDL rules were added: remove rules if they cause false rejections
- If deduplication was added: remove if it incorrectly removes valid records
- If null handling was added: remove if it masks data quality issues
- If data quarantine was implemented: disable quarantine routing if not needed

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
