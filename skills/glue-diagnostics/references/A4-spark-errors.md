---
title: "A4 — Spark Errors"
description: "Diagnose Spark-level errors in Glue ETL jobs"
status: active
severity: HIGH
triggers:
  - "Spark error"
  - "stage failed"
  - "task failed"
  - "SparkException"
  - "AnalysisException"
  - "Py4JJavaError"
  - "serialization error"
owner: devops-agent
objective: "Identify and resolve Spark framework errors occurring within Glue ETL jobs"
context: "Spark errors in Glue jobs include AnalysisException (schema/column issues), Py4JJavaError (Python-Java bridge failures), serialization errors (non-serializable objects in closures), task failures from corrupt data, and stage retries from lost executors. The Glue version determines the Spark version: 2.0→Spark 2.4, 3.0→Spark 3.1, 4.0→Spark 3.3."
---

## Phase 1 — Triage

MUST:
- Get the error details: `aws glue get-job-run --job-name <name> --run-id <run-id>`
- Search CloudWatch logs for the Spark exception: `aws logs filter-log-events --log-group-name /aws-glue/jobs/logs-v2 --log-stream-name-prefix <run-id> --filter-pattern "Exception"`
- Check the Glue version to determine Spark version: `aws glue get-job --name <name>`
- Identify the failing stage and transformation from the stack trace

SHOULD:
- Review Spark UI for DAG visualization and stage details
- Check for schema mismatches between source and expected schema
- Verify all referenced columns exist in the DataFrame/DynamicFrame
- Check for Python library version conflicts

MAY:
- Test the failing transformation in isolation with sample data
- Check Spark configuration parameters for version-specific settings

## Phase 2 — Remediate

MUST:
- Fix the identified Spark error (schema mismatch, missing column, serialization)
- Verify the Glue version supports the Spark APIs used in the script
- Test the fix with a job run

SHOULD:
- Add schema validation before transformations
- Use DynamicFrame resolveChoice() for ambiguous column types
- Wrap transformations in try-except blocks for graceful error handling

MAY:
- Enable Spark event logging for detailed post-mortem analysis
- Add data quality checks between transformation stages

## Common Issues

- symptoms: "AnalysisException: cannot resolve column name"
  diagnosis: "Column referenced in transformation does not exist in the DataFrame. Common after schema changes in source data."
  resolution: "Verify column names with printSchema(). Use DynamicFrame apply_mapping() for explicit column mapping."

- symptoms: "Py4JJavaError: An error occurred while calling o123.parquet"
  diagnosis: "File format error, corrupt Parquet file, or incompatible Parquet version."
  resolution: "Validate source files. Use format option mergeSchema=true for schema evolution. Check for corrupt files."

- symptoms: "Task serialization error: object not serializable"
  diagnosis: "Non-serializable object (database connection, file handle) referenced inside a Spark transformation closure."
  resolution: "Move non-serializable objects outside the closure. Use mapPartitions() to create connections per partition."

## Output Format

```yaml
root_cause: "spark_error — <specific_exception>"
evidence:
  - type: spark_exception
    content: "<exception class and message>"
  - type: cloudwatch_logs
    content: "<relevant stack trace>"
severity: HIGH
mitigation:
  immediate: "Fix the Spark error in the job script"
  long_term: "Add schema validation, error handling, and Spark UI monitoring"
```


## Safety Ratings
```
safety_ratings:
  - "Check error details and logs: GREEN — read-only diagnostics"
  - "Check Glue version: GREEN — read-only API call"
  - "Fix script errors: GREEN — code change, no infrastructure impact"
  - "Add schema validation: GREEN — defensive code addition"
  - "Change Glue version: YELLOW — may affect Spark API compatibility"
```

## Escalation Conditions
- Job processes production data pipeline
- Spark errors from source data schema changes
- Fix requires Glue version upgrade
- Serialization errors requiring script architecture changes
- Recurring errors from corrupt source data

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Stack traces: may contain data values and schema details"
    - "CloudWatch logs: may contain sensitive error context"
    - "Job script: ETL transformation logic"
  handling: "Stack traces may contain sensitive data. Restrict log access."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER change Glue version without testing compatibility with existing scripts
- NEVER ignore AnalysisException errors — they indicate schema problems that will persist

## Phase 3 — Rollback
- If script was modified: revert to previous script version
- If Glue version was changed: revert to previous version
- If Spark configuration was changed: restore previous --conf parameters
- If schema validation was added: remove if it causes false rejections

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
