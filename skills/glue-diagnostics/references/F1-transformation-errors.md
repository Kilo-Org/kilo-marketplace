---
title: "F1 — Transformation Errors"
description: "Diagnose DynamicFrame and DataFrame transformation errors in Glue ETL jobs"
status: active
severity: HIGH
triggers:
  - "transformation error"
  - "ApplyMapping error"
  - "resolveChoice"
  - "DynamicFrame error"
  - "type mismatch"
  - "cast error"
owner: devops-agent
objective: "Identify and resolve data transformation errors in Glue ETL scripts"
context: "Glue uses DynamicFrames (Glue-native) and DataFrames (Spark-native) for transformations. DynamicFrames handle schema flexibility with resolveChoice() for ambiguous types. Common errors: ApplyMapping with wrong column names, type casting failures, null handling issues, nested struct flattening problems, and incompatible transformations between DynamicFrame and DataFrame APIs."
---

## Phase 1 — Triage

MUST:
- Get the error message from job run: `aws glue get-job-run --job-name <name> --run-id <run-id>`
- Check CloudWatch logs for the transformation error: `aws logs filter-log-events --log-group-name /aws-glue/jobs/logs-v2 --log-stream-name-prefix <run-id> --filter-pattern "Error"`
- Identify the failing transformation (ApplyMapping, Filter, Join, resolveChoice)
- Verify input schema matches expected schema for the transformation

SHOULD:
- Add printSchema() before the failing transformation to inspect actual schema
- Check for null values in columns used by the transformation
- Verify column name case sensitivity (DynamicFrame is case-sensitive)
- Check for nested structs or arrays that need flattening

MAY:
- Test the transformation with a small data sample
- Compare DynamicFrame vs DataFrame behavior for the specific operation

## Phase 2 — Remediate

MUST:
- Fix the transformation to match actual input schema
- Handle type ambiguities with resolveChoice() before transformations
- Verify the fix produces correct output

SHOULD:
- Use apply_mapping() for explicit column name and type mapping
- Add null handling (coalesce, fillna) before operations that fail on nulls
- Use Relationalize for flattening nested structures
- Add schema validation between transformation stages

MAY:
- Implement custom error handling with try-except around transformations
- Use Glue's stageThreshold and totalThreshold for error tolerance
- Log transformation metrics for monitoring

## Common Issues

- symptoms: "ApplyMapping fails with 'column not found'"
  diagnosis: "Column name in mapping does not match actual schema. Case sensitivity or schema change in source data."
  resolution: "Print schema before mapping. Use exact column names including case. Update mapping for schema changes."

- symptoms: "resolveChoice fails with 'no choice to resolve'"
  diagnosis: "Column does not have ambiguous types. resolveChoice is unnecessary for this column."
  resolution: "Only apply resolveChoice to columns with ChoiceType. Check schema for actual choice columns."

- symptoms: "Type cast error converting string to int"
  diagnosis: "Source data contains non-numeric values in a column being cast to integer."
  resolution: "Use resolveChoice with cast:int to handle type conversion. Filter or clean invalid values before casting."

## Output Format

```yaml
root_cause: "transformation_error — <specific_cause>"
evidence:
  - type: error_message
    content: "<transformation error details>"
  - type: input_schema
    content: "<actual vs expected schema>"
severity: HIGH
mitigation:
  immediate: "Fix transformation to match actual schema and data"
  long_term: "Add schema validation, null handling, and error tolerance"
```


## Safety Ratings
```
safety_ratings:
  - "Check error message and logs: GREEN — read-only diagnostics"
  - "Add printSchema for debugging: GREEN — read-only inspection"
  - "Fix transformation logic: GREEN — code change"
  - "Add resolveChoice: GREEN — handles type ambiguity"
  - "Add null handling: GREEN — defensive code addition"
```

## Escalation Conditions
- Job processes production data pipeline
- Transformation errors blocking data pipeline
- Schema changes in source data causing failures
- Fix requires understanding of DynamicFrame vs DataFrame APIs
- Nested data structures requiring complex flattening

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Error messages: may contain data values"
    - "Schema details: data structure information"
    - "Transformation logic: ETL business rules"
  handling: "Error messages may contain sensitive data values. Do not expose externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER ignore type mismatch errors — they indicate data quality issues
- NEVER use stageThreshold=0 (disables all error tolerance)

## Phase 3 — Rollback
- If transformation logic was changed: revert to previous script version
- If resolveChoice was added: remove if it causes incorrect type casting
- If null handling was added: remove if it masks data quality issues
- If schema validation was added: adjust thresholds if too strict

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
