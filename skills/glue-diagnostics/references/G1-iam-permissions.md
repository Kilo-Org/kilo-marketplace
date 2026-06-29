---
title: "G1 — IAM Permissions"
description: "Diagnose IAM permission issues affecting Glue jobs, crawlers, and connections"
status: active
severity: HIGH
triggers:
  - "access denied"
  - "not authorized"
  - "IAM permission"
  - "role permission"
  - "insufficient permissions"
  - "AssumeRole failed"
owner: devops-agent
objective: "Identify and resolve IAM permission issues preventing Glue operations"
context: "Glue requires IAM roles for jobs, crawlers, and dev endpoints. The role needs permissions for Glue service actions, S3 data access, CloudWatch logging, KMS decryption (if encrypted), and any target service (RDS, Redshift, DynamoDB). The AWSGlueServiceRole managed policy covers basic Glue operations but not S3 data bucket access. Cross-account access requires trust policies and resource policies."
---

## Phase 1 — Triage

MUST:
- Check the IAM role attached to the job/crawler: `aws glue get-job --name <name>` or `aws glue get-crawler --name <name>`
- Review role policies: `aws iam list-attached-role-policies --role-name <role>` and `aws iam list-role-policies --role-name <role>`
- Check the specific error message for the denied action
- Verify the role trust policy allows Glue to assume it: `aws iam get-role --role-name <role>`

SHOULD:
- Check for S3 bucket policies that may deny access
- Verify KMS key policies if accessing encrypted data
- Check for SCP (Service Control Policies) that may restrict Glue actions
- Review CloudTrail for the specific AccessDenied event

MAY:
- Use IAM Policy Simulator to test permissions
- Check for resource-based policies on target services
- Verify cross-account role assumptions if applicable

## Phase 2 — Remediate

MUST:
- Add the missing IAM permissions to the role
- Ensure the trust policy includes `glue.amazonaws.com` as a trusted principal
- Verify the fix resolves the access denied error

SHOULD:
- Use AWSGlueServiceRole managed policy as a baseline
- Add specific S3 bucket permissions for data access (not S3 full access)
- Add CloudWatch Logs permissions for job logging
- Follow least-privilege principle for production roles

MAY:
- Implement IAM Access Analyzer to identify unused permissions
- Create separate roles for different job types (ETL, crawlers, dev endpoints)
- Use permission boundaries to limit maximum permissions

## Common Issues

- symptoms: "Job fails with 'Access Denied' on S3 GetObject"
  diagnosis: "IAM role has AWSGlueServiceRole but missing S3 data bucket permissions."
  resolution: "Add s3:GetObject, s3:ListBucket for the specific data bucket to the role policy."

- symptoms: "Crawler fails with 'not authorized to perform glue:CreateTable'"
  diagnosis: "IAM role missing Glue Data Catalog write permissions."
  resolution: "Add glue:CreateTable, glue:UpdateTable, glue:CreatePartition to the role policy."

- symptoms: "Job fails with 'AssumeRole' error for cross-account access"
  diagnosis: "Target account role trust policy does not allow the Glue role to assume it."
  resolution: "Update target role trust policy to allow the Glue role ARN. Add sts:AssumeRole to the Glue role."

## Output Format

```yaml
root_cause: "iam_permissions — <specific_denied_action>"
evidence:
  - type: iam_role
    content: "<role ARN and attached policies>"
  - type: error_message
    content: "<specific access denied error>"
severity: HIGH
mitigation:
  immediate: "Add missing IAM permissions"
  long_term: "Implement least-privilege roles, use IAM Access Analyzer"
```


## Safety Ratings
```
safety_ratings:
  - "Check IAM role and policies: GREEN — read-only IAM inspection"
  - "Check CloudTrail for denied events: GREEN — read-only audit log query"
  - "Add missing IAM permissions: YELLOW — changes access scope"
  - "Update trust policy: YELLOW — changes who can assume the role"
  - "Attach AWSGlueServiceRole: YELLOW — grants broad Glue permissions"
```

## Escalation Conditions
- Job processes production data pipeline
- IAM permission issues blocking multiple Glue components
- Fix requires cross-account role trust policy changes
- SCP restrictions blocking Glue operations
- Permission changes affecting other services using the same role

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "IAM role ARNs and policies: permission configuration"
    - "Trust policies: cross-service and cross-account access"
    - "CloudTrail events: API call history with parameters"
  handling: "IAM policies reveal access patterns. Do not expose role ARNs or policies externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER grant AdministratorAccess or s3:* to Glue roles
- NEVER modify IAM roles shared by multiple services without understanding the blast radius

## Phase 3 — Rollback
- If IAM permissions were added: remove the added policy statements
- If trust policy was updated: restore previous trust policy
- If managed policy was attached: detach the policy
- If cross-account role was modified: revert changes in both accounts

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
