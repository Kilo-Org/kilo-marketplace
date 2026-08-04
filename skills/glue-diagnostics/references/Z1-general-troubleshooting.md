---
title: "Z1 — General Troubleshooting"
description: "General Glue troubleshooting when symptoms do not match a specific runbook"
status: active
severity: MEDIUM
triggers:
  - "Glue problem"
  - "Glue issue"
  - "something wrong with Glue"
  - "Glue not working"
  - "help with Glue"
owner: devops-agent
objective: "Systematically investigate Glue issues that do not match a specific runbook category"
context: "This catch-all runbook provides a systematic approach when the user reports a Glue problem without clear symptoms. It covers initial triage across all Glue components: jobs, crawlers, connections, Data Catalog, and security. The goal is to narrow down the issue to a specific runbook category."
---

## Phase 1 — Triage

MUST:
- Identify the Glue component involved (job, crawler, connection, catalog, studio)
- Get the current state of the component:
  - Jobs: `aws glue get-job-runs --job-name <name> --max-results 5`
  - Crawlers: `aws glue get-crawler --name <name>`
  - Connections: `aws glue get-connection --name <name>`
  - Catalog: `aws glue get-tables --database-name <db>`
- Check for recent error messages in CloudWatch logs
- Verify IAM role permissions for the affected component

SHOULD:
- Check AWS Health Dashboard for Glue service issues
- Review recent changes to the Glue configuration (job parameters, crawler targets, connections)
- Check CloudTrail for recent Glue API calls that may have caused the issue
- Verify Glue service quotas are not exceeded

MAY:
- Check for regional Glue service availability
- Review AWS re:Post or documentation for known issues
- Check if the issue correlates with a recent AWS service update

## Phase 2 — Route to Specific Runbook

Based on triage findings, route to the appropriate runbook:

| Symptom | Route To |
|---------|----------|
| Job failed with error | A1 — Job Failures |
| Job running too long | A2 — Job Timeout |
| OOM error in job | A3 — OOM Errors |
| Spark exception in job | A4 — Spark Errors |
| Crawler not completing | B1 — Crawler Failures |
| Wrong schema detected | B2 — Schema Detection |
| Partition problems | B3 — Partition Issues |
| JDBC connection failing | C1 — JDBC Connection Failures |
| VPC networking issue | C2 — VPC/Subnet Issues |
| S3 access from VPC | C3 — S3 Endpoint Access |
| Catalog metadata stale | D1 — Catalog Sync Issues |
| Schema changes breaking jobs | D2 — Schema Evolution |
| Performance/cost concerns | E1 — DPU Sizing |
| Slow joins or shuffles | E2 — Shuffle Issues |
| Uneven task processing | E3 — Data Skew |
| Transform errors | F1 — Transformation Errors |
| Bookmark not working | F2 — Bookmark Issues |
| Data quality problems | F3 — Data Quality |
| Permission denied | G1 — IAM Permissions |
| Encryption errors | G2 — Encryption Issues |
| Glue Studio problems | H1 — Visual Editor Errors |
| Generated code issues | H2 — Job Generation |

## Phase 3 — Remediate

MUST:
- Follow the specific runbook identified in Phase 2
- Document the root cause and resolution

SHOULD:
- Set up monitoring to detect the issue earlier next time
- Review related components for similar issues

MAY:
- Create a custom CloudWatch dashboard for Glue monitoring
- Implement EventBridge rules for Glue job state change notifications

## Output Format

```yaml
root_cause: "general — <identified_category>"
evidence:
  - type: triage_findings
    content: "<initial investigation results>"
  - type: routed_runbook
    content: "<specific runbook for detailed investigation>"
severity: MEDIUM
mitigation:
  immediate: "Follow the identified specific runbook"
  long_term: "Implement monitoring and alerting for Glue components"
```


## Safety Ratings
```
safety_ratings:
  - "Check component status and logs: GREEN — read-only API calls"
  - "Check IAM permissions: GREEN — read-only IAM inspection"
  - "Check CloudTrail events: GREEN — read-only audit log query"
  - "Route to specific runbook: GREEN — diagnostic classification, no state change"
```

## Escalation Conditions
- Job processes production data pipeline
- Issue cannot be classified into a specific failure domain
- Multiple Glue components affected simultaneously
- AWS service health issue suspected
- Issue requires cross-team coordination

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Job run details: processing status and error messages"
    - "Crawler status: metadata update state"
    - "Connection details: database access configuration"
    - "CloudTrail events: API call history"
  handling: "Diagnostic data may contain sensitive error details. Mask connection credentials in shared reports."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER make configuration changes without first classifying the failure domain
- NEVER apply fixes from multiple runbooks simultaneously

## Phase 3 — Rollback
- For general investigation: no rollback needed — all triage steps are read-only
- If routed to a specific runbook: follow that runbook's Phase 3 rollback procedures
- If configuration changes were made during investigation: revert each change individually

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
