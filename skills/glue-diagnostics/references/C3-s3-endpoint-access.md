---
title: "C3 — S3 Endpoint Access"
description: "Diagnose S3 access issues from Glue jobs running in VPCs"
status: active
severity: MEDIUM
triggers:
  - "S3 access denied from Glue"
  - "cannot read S3"
  - "S3 timeout from VPC"
  - "S3 endpoint"
  - "S3 gateway endpoint"
owner: devops-agent
objective: "Resolve S3 access issues for Glue jobs running in VPC-connected configurations"
context: "Glue jobs using connections run in a VPC and need explicit routes to S3. S3 gateway VPC endpoints are free and provide private connectivity. Without a gateway endpoint or NAT gateway, Glue jobs in private subnets cannot reach S3. S3 bucket policies may also restrict access based on VPC endpoint or source IP conditions."
---

## Phase 1 — Triage

MUST:
- Check if the job uses a connection (VPC-bound): `aws glue get-job --name <name>`
- Verify S3 VPC endpoint exists: `aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id> Name=service-name,Values=com.amazonaws.<region>.s3`
- Check the endpoint is associated with the correct route table
- Verify S3 bucket policy does not restrict VPC endpoint access

SHOULD:
- Check IAM role S3 permissions: `aws iam get-role-policy --role-name <role> --policy-name <policy>`
- Verify S3 bucket exists and is in the expected region
- Check for S3 bucket policy conditions on aws:sourceVpce or aws:sourceVpc
- Verify KMS permissions if the bucket uses SSE-KMS encryption

MAY:
- Check S3 access logs for denied requests
- Verify cross-account S3 access if bucket is in a different account
- Check for S3 Object Lock or Glacier restrictions

## Phase 2 — Remediate

MUST:
- Create S3 gateway VPC endpoint if missing (free, no hourly charge)
- Associate the endpoint with the subnet's route table
- Fix S3 bucket policy to allow access from the VPC endpoint

SHOULD:
- Use S3 gateway endpoints instead of NAT gateways for S3 traffic (cost savings)
- Add VPC endpoint policy to restrict S3 access to specific buckets
- Ensure KMS key policy allows the Glue IAM role

MAY:
- Implement S3 access logging for audit trail
- Use S3 bucket policy conditions to enforce VPC endpoint usage

## Common Issues

- symptoms: "Glue job timeout reading from S3 in VPC"
  diagnosis: "No S3 VPC endpoint and no NAT gateway route for S3 traffic."
  resolution: "Create S3 gateway VPC endpoint: aws ec2 create-vpc-endpoint --vpc-id <vpc> --service-name com.amazonaws.<region>.s3 --route-table-ids <rtb-id>"

- symptoms: "Access Denied on S3 despite IAM permissions"
  diagnosis: "S3 bucket policy has a Deny condition on aws:sourceVpce that doesn't include the Glue VPC endpoint."
  resolution: "Update bucket policy to allow the Glue VPC endpoint ID in the aws:sourceVpce condition."

- symptoms: "KMS decrypt error reading encrypted S3 objects"
  diagnosis: "Glue IAM role not authorized in the KMS key policy."
  resolution: "Add the Glue IAM role ARN to the KMS key policy with kms:Decrypt permission."

## Output Format

```yaml
root_cause: "s3_endpoint_access — <specific_cause>"
evidence:
  - type: vpc_endpoint_config
    content: "<endpoint existence and route table association>"
  - type: bucket_policy
    content: "<relevant bucket policy conditions>"
severity: MEDIUM
mitigation:
  immediate: "Create S3 VPC endpoint or fix bucket policy"
  long_term: "Use gateway endpoints, implement endpoint policies"
```


## Safety Ratings
```
safety_ratings:
  - "Check VPC endpoint and route tables: GREEN — read-only API calls"
  - "Check S3 bucket policy: GREEN — read-only inspection"
  - "Create S3 gateway VPC endpoint: YELLOW — changes VPC routing (free, no hourly charge)"
  - "Fix S3 bucket policy: YELLOW — changes bucket access controls"
  - "Fix KMS key policy: YELLOW — changes encryption key access"
```

## Escalation Conditions
- Job processes production data pipeline
- S3 access failure blocking data pipeline
- Bucket policy changes affecting other services
- KMS key policy changes requiring security review
- Cross-account S3 access requiring bucket policy updates

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "S3 bucket names and paths: data storage locations"
    - "Bucket policies: access control configuration"
    - "KMS key IDs: encryption key identifiers"
    - "VPC endpoint IDs: network configuration"
  handling: "Do not expose S3 bucket names, paths, or KMS key IDs externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER grant s3:* permissions — use specific actions
- NEVER modify S3 bucket policies without understanding impact on all consumers

## Phase 3 — Rollback
- If S3 VPC endpoint was created: delete the endpoint and remove route table association
- If bucket policy was modified: restore previous bucket policy
- If KMS key policy was changed: restore previous key policy
- If VPC endpoint policy was added: remove the policy to restore default (full S3 access)

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
