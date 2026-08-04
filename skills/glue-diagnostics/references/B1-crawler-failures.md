---
title: "B1 — Crawler Failures"
description: "Diagnose why a Glue crawler is failing to run or complete"
status: active
severity: HIGH
triggers:
  - "crawler failed"
  - "crawler error"
  - "crawler not running"
  - "crawler stuck"
  - "crawler timeout"
owner: devops-agent
objective: "Identify the root cause of a Glue crawler failure and restore successful crawling"
context: "Crawler failures are caused by IAM permission issues, S3 access denied, JDBC connection failures, too many S3 objects to crawl, network connectivity issues, or service quota limits. Crawlers have a default timeout and can fail silently if the IAM role lacks required permissions."
---

## Phase 1 — Triage

MUST:
- Check crawler status and last run: `aws glue get-crawler --name <crawler-name>`
- Get crawler metrics: `aws glue get-crawler-metrics --crawler-name-list <crawler-name>`
- Verify the IAM role has S3 and Glue permissions
- Check CloudWatch logs: `aws logs filter-log-events --log-group-name /aws-glue/crawlers --log-stream-name-prefix <crawler-name>`

SHOULD:
- Verify S3 paths in crawler targets are accessible
- Check for JDBC connection issues if crawling a database
- Review the number of S3 objects in the target path (very large counts slow crawlers)

MAY:
- Check Glue service quotas for crawler limits
- Verify no other crawler is running on the same targets

## Phase 2 — Remediate

MUST:
- Fix IAM permissions or S3 access issues
- Resolve JDBC connection problems if applicable
- Verify the crawler completes successfully after the fix

SHOULD:
- Scope crawler targets to specific prefixes to reduce crawl time
- Set crawler schedule to avoid peak data ingestion times
- Configure recrawl policy to only crawl new folders

MAY:
- Split large crawl targets across multiple crawlers
- Use S3 event notifications with Lambda to trigger targeted crawls

## Common Issues

- symptoms: "Crawler fails with 'Access Denied' on S3"
  diagnosis: "IAM role missing s3:GetObject or s3:ListBucket on the target bucket/prefix."
  resolution: "Add S3 read permissions to the crawler's IAM role for the specific bucket and prefix."

- symptoms: "Crawler runs for hours and times out"
  diagnosis: "Too many S3 objects or deeply nested folder structure."
  resolution: "Narrow the crawler target to specific prefixes. Use exclude patterns to skip irrelevant paths. Enable recrawl policy for new folders only."

- symptoms: "Crawler fails with JDBC connection error"
  diagnosis: "Database unreachable due to VPC/security group misconfiguration or credentials expired."
  resolution: "Test the Glue connection separately. Verify VPC, subnet, security group, and database credentials."

## Output Format

```yaml
root_cause: "crawler_failure — <specific_cause>"
evidence:
  - type: crawler_status
    content: "<crawler state and last crawl info>"
  - type: crawler_metrics
    content: "<tables created/updated, time elapsed>"
severity: HIGH
mitigation:
  immediate: "Fix the identified access or connectivity issue"
  long_term: "Scope crawler targets, set recrawl policy, add monitoring"
```


## Safety Ratings
```
safety_ratings:
  - "Check crawler status and metrics: GREEN — read-only API calls"
  - "Check IAM role and logs: GREEN — read-only diagnostics"
  - "Fix IAM permissions: YELLOW — changes access scope"
  - "Narrow crawler targets: GREEN — reduces crawl scope"
  - "Run crawler: YELLOW — updates Data Catalog metadata"
```

## Escalation Conditions
- Job processes production data pipeline
- Crawler failure blocking Data Catalog updates
- Fix requires IAM role changes affecting multiple crawlers
- JDBC connection issues requiring database team coordination
- Crawler timeout due to massive S3 object count

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Crawler targets: S3 paths and JDBC connection details"
    - "Data Catalog metadata: table schemas and partition information"
    - "Connection credentials: database access information"
  handling: "Do not expose crawler targets or connection details externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER run crawlers with overly broad S3 targets in production
- NEVER store database credentials in plaintext in connection properties

## Phase 3 — Rollback
- If IAM permissions were changed: revert to previous policy
- If crawler targets were modified: restore previous target configuration
- If crawler updated catalog incorrectly: manually revert table definitions
- If recrawl policy was changed: restore previous policy setting

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
