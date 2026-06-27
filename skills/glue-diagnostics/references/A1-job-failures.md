---
title: "A1 — Job Failures"
description: "Diagnose why an AWS Glue ETL job is failing"
status: active
severity: HIGH
triggers:
  - "job failed"
  - "glue job error"
  - "job run failed"
  - "ETL job failure"
  - "job status FAILED"
owner: devops-agent
objective: "Identify the root cause of a Glue ETL job failure and restore successful execution"
context: "Glue job failures can be caused by script errors, missing dependencies, IAM permission issues, data format mismatches, connection failures, resource exhaustion, or Glue service issues. The error message in the job run details is the primary diagnostic starting point. CloudWatch logs under /aws-glue/jobs/logs-v2 provide detailed Spark-level error information."
---

## Phase 1 — Triage

MUST:
- Get the job run details and error message: `aws glue get-job-run --job-name <name> --run-id <run-id>`
- Check the job configuration: `aws glue get-job --name <name>`
- Review CloudWatch logs: `aws logs filter-log-events --log-group-name /aws-glue/jobs/logs-v2 --log-stream-name-prefix <run-id>`
- Verify the IAM role has required permissions: `aws iam get-role --role-name <glue-role>`

SHOULD:
- Check recent job run history for patterns: `aws glue get-job-runs --job-name <name> --max-results 10`
- Verify S3 paths in the script are accessible
- Check if the Glue version and worker type are appropriate for the workload

MAY:
- Compare with a previous successful run configuration
- Check for concurrent job runs that may cause resource contention
- Review Glue service quotas: `aws service-quotas get-service-quota --service-code glue --quota-code L-5E3AF21B`

## Phase 2 — Remediate

MUST:
- Fix the identified error (script bug, IAM permissions, data path, connection)
- Verify the fix by running the job again
- Set an explicit timeout if using the 48-hour default

SHOULD:
- Add error handling and retry logic to the script
- Enable CloudWatch metrics for monitoring
- Configure job notifications via CloudWatch alarms or EventBridge

MAY:
- Enable Spark UI for detailed execution analysis
- Add data quality checks before critical transformations

## Common Issues

- symptoms: "Job fails immediately with 'Access Denied' error"
  diagnosis: "IAM role missing required S3, Glue, or KMS permissions."
  resolution: "Attach AWSGlueServiceRole managed policy and add S3 bucket permissions to the role."

- symptoms: "Job fails with 'No such file or directory' on S3 path"
  diagnosis: "S3 source path does not exist or has incorrect prefix."
  resolution: "Verify S3 path exists. Check for trailing slashes and case sensitivity in bucket/key names."

- symptoms: "Job fails with 'Unable to parse file' error"
  diagnosis: "Data format mismatch between actual file format and configured format."
  resolution: "Verify the data format (CSV, JSON, Parquet, ORC) matches the source configuration. Check for corrupt files."

## Output Format

```yaml
root_cause: "job_failure — <specific_cause>"
evidence:
  - type: job_run_error
    content: "<error message from get-job-run>"
  - type: cloudwatch_logs
    content: "<relevant log entries>"
severity: HIGH
mitigation:
  immediate: "Fix the identified error and re-run the job"
  long_term: "Add error handling, monitoring, and explicit timeout"
```


## Safety Ratings
```
safety_ratings:
  - "Get job run details and logs: GREEN — read-only API calls"
  - "Check IAM role permissions: GREEN — read-only IAM inspection"
  - "Fix script errors and re-run: GREEN — corrects code, no infrastructure change"
  - "Fix IAM role permissions: YELLOW — changes access scope"
  - "Set explicit timeout: GREEN — adds cost protection"
```

## Escalation Conditions
- Job processes production data pipeline
- Job failure blocking downstream data consumers
- Fix requires IAM role changes affecting multiple jobs
- Data format issues requiring source system changes
- Repeated failures suggesting systemic issue

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "CloudWatch logs: may contain data values and error details"
    - "Job script: ETL logic and data transformation rules"
    - "Connection credentials: database access information"
    - "S3 paths: data source and target locations"
  handling: "CloudWatch logs may contain sensitive data values. Restrict log access. Do not expose S3 paths externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER run a failed job repeatedly without fixing the root cause
- NEVER use overly permissive IAM roles (e.g., AdministratorAccess) for Glue jobs

## Phase 3 — Rollback
- If job script was modified: revert to previous script version
- If IAM permissions were changed: revert to previous IAM policy version
- If job parameters were changed: restore previous job configuration
- If job produced incorrect output: delete incorrect output data and re-run with fixed script

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
