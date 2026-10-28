---
title: "G2 — Encryption Issues"
description: "Diagnose encryption-related errors in Glue jobs, Data Catalog, and connections"
status: active
severity: HIGH
triggers:
  - "KMS error"
  - "encryption error"
  - "decrypt failed"
  - "SSE-KMS"
  - "encryption at rest"
  - "security configuration"
owner: devops-agent
objective: "Resolve encryption configuration issues affecting Glue operations"
context: "Glue supports encryption at rest for the Data Catalog, job bookmarks, S3 targets, and CloudWatch logs via KMS. Glue security configurations define encryption settings. Common issues: KMS key policy not granting Glue role access, wrong KMS key specified, cross-account KMS access, security configuration mismatch, and SSE-KMS on S3 buckets requiring explicit decrypt permissions."
---

## Phase 1 — Triage

MUST:
- Check the Glue security configuration: `aws glue get-security-configuration --name <config-name>`
- Verify KMS key policy allows the Glue IAM role: `aws kms describe-key --key-id <key-id>` and `aws kms get-key-policy --key-id <key-id> --policy-name default`
- Check the job's security configuration setting: `aws glue get-job --name <name>`
- Review the error message for the specific KMS or encryption error

SHOULD:
- Verify the KMS key is in the same region as the Glue job
- Check if the KMS key is enabled and not pending deletion
- Verify S3 bucket encryption settings match the Glue security configuration
- Check for cross-account KMS key access requirements

MAY:
- Review CloudTrail for KMS Decrypt/Encrypt failures
- Check Data Catalog encryption settings: `aws glue get-data-catalog-encryption-settings`
- Verify connection password encryption settings

## Phase 2 — Remediate

MUST:
- Add the Glue IAM role to the KMS key policy with kms:Decrypt and kms:GenerateDataKey permissions
- Ensure the security configuration matches the S3 bucket encryption type
- Verify the KMS key ARN is correct in the security configuration

SHOULD:
- Use AWS managed keys (aws/glue, aws/s3) for simpler permission management
- Create a dedicated KMS key for Glue with appropriate key policy
- Enable Data Catalog encryption for sensitive metadata

MAY:
- Implement KMS key rotation
- Use separate KMS keys for different data classification levels
- Enable CloudTrail logging for KMS key usage monitoring

## Common Issues

- symptoms: "Job fails with 'AccessDeniedException' on KMS Decrypt"
  diagnosis: "Glue IAM role not listed as a key user in the KMS key policy."
  resolution: "Add the Glue role ARN to the KMS key policy with kms:Decrypt, kms:DescribeKey, kms:GenerateDataKey permissions."

- symptoms: "Job fails writing to SSE-KMS encrypted S3 bucket"
  diagnosis: "Glue role missing kms:GenerateDataKey permission for the bucket's KMS key."
  resolution: "Add kms:GenerateDataKey to the role policy for the specific KMS key ARN."

- symptoms: "Data Catalog encryption error when creating tables"
  diagnosis: "Data Catalog encryption enabled but crawler role lacks KMS permissions."
  resolution: "Add KMS permissions to the crawler role. Ensure the KMS key policy allows the crawler role."

## Output Format

```yaml
root_cause: "encryption_issue — <specific_cause>"
evidence:
  - type: security_config
    content: "<Glue security configuration>"
  - type: kms_key_policy
    content: "<KMS key policy and Glue role access>"
severity: HIGH
mitigation:
  immediate: "Fix KMS key policy or security configuration"
  long_term: "Use managed keys, enable catalog encryption, implement key rotation"
```


## Safety Ratings
```
safety_ratings:
  - "Check security configuration and KMS key: GREEN — read-only API calls"
  - "Check KMS key policy: GREEN — read-only inspection"
  - "Fix KMS key policy: YELLOW — changes encryption key access"
  - "Create security configuration: GREEN — creates new configuration"
  - "Enable Data Catalog encryption: YELLOW — encrypts catalog metadata"
```

## Escalation Conditions
- Job processes production data pipeline
- KMS key access issues blocking data pipeline
- Encryption configuration changes affecting multiple jobs
- Cross-account KMS key access required
- Data Catalog encryption enabling requiring coordination

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "KMS key IDs and policies: encryption configuration"
    - "Security configuration: encryption settings"
    - "Connection credentials: encrypted database access"
    - "Data Catalog metadata: encrypted table definitions"
  handling: "KMS key IDs and policies are highly sensitive. Never expose key policies externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER disable or delete KMS keys used by active Glue jobs
- NEVER share KMS key policies or key IDs externally

## Phase 3 — Rollback
- If KMS key policy was changed: restore previous key policy
- If security configuration was created: delete if not needed
- If Data Catalog encryption was enabled: cannot be easily disabled — plan carefully
- If job security configuration was changed: restore previous configuration

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
