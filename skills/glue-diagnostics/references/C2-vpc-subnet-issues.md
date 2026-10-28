---
title: "C2 — VPC and Subnet Issues"
description: "Diagnose VPC and subnet configuration problems affecting Glue jobs and connections"
status: active
severity: HIGH
triggers:
  - "VPC configuration"
  - "subnet issue"
  - "ENI creation failed"
  - "no route to host"
  - "network unreachable"
  - "NAT gateway"
owner: devops-agent
objective: "Resolve VPC and subnet networking issues that prevent Glue jobs from accessing resources"
context: "Glue jobs using connections create ENIs in the specified subnet. The subnet must have routes to target resources and to AWS service endpoints (Glue, S3, CloudWatch). Private subnets need NAT gateways or VPC endpoints. The security group must allow self-referencing inbound traffic for Glue ENI-to-ENI communication. Insufficient IP addresses in the subnet cause ENI creation failures."
---

## Phase 1 — Triage

MUST:
- Check the connection's VPC and subnet: `aws glue get-connection --name <connection-name>`
- Verify subnet has available IP addresses: `aws ec2 describe-subnets --subnet-ids <subnet-id>`
- Check route table for the subnet: `aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=<subnet-id>`
- Verify security group allows self-referencing inbound: `aws ec2 describe-security-groups --group-ids <sg-id>`

SHOULD:
- Check for NAT gateway in the route table (for internet-routed services)
- Verify VPC endpoints exist for S3 and Glue: `aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id>`
- Check NACLs for the subnet are not blocking traffic
- Verify DNS resolution is enabled for the VPC

MAY:
- Check VPC flow logs for rejected packets
- Verify VPC peering or transit gateway routes if accessing cross-VPC resources
- Check for overlapping CIDR ranges in peered VPCs

## Phase 2 — Remediate

MUST:
- Add self-referencing inbound rule to the Glue security group (all TCP, source: same security group)
- Ensure subnet has available IP addresses (Glue needs IPs for ENIs)
- Add routes to target resources (NAT gateway, VPC peering, transit gateway)

SHOULD:
- Create VPC endpoints for S3 (gateway endpoint, free) and Glue (interface endpoint)
- Use private subnets with VPC endpoints instead of NAT gateways to reduce cost
- Ensure the subnet is in an AZ supported by Glue

MAY:
- Create dedicated subnets for Glue with sufficient IP address space
- Implement VPC flow log monitoring for Glue ENI traffic

## Common Issues

- symptoms: "ENI creation failed: insufficient IP addresses"
  diagnosis: "Subnet CIDR too small or too many ENIs already allocated."
  resolution: "Use a larger subnet or clean up unused ENIs. Glue needs one ENI per worker."

- symptoms: "Job fails with 'Unable to reach Glue service'"
  diagnosis: "Private subnet without NAT gateway or Glue VPC endpoint."
  resolution: "Add a NAT gateway route or create a VPC endpoint for Glue (com.amazonaws.<region>.glue)."

- symptoms: "Job can reach database but not S3"
  diagnosis: "Missing S3 VPC endpoint or NAT gateway route for S3 traffic."
  resolution: "Create an S3 gateway VPC endpoint (free) and associate it with the subnet's route table."

## Output Format

```yaml
root_cause: "vpc_subnet_issue — <specific_cause>"
evidence:
  - type: subnet_config
    content: "<subnet CIDR, available IPs, route table>"
  - type: security_group
    content: "<inbound/outbound rules>"
severity: HIGH
mitigation:
  immediate: "Fix routing, security groups, or VPC endpoints"
  long_term: "Create dedicated Glue subnets with VPC endpoints"
```


## Safety Ratings
```
safety_ratings:
  - "Check VPC, subnet, and route tables: GREEN — read-only API calls"
  - "Check security group rules: GREEN — read-only inspection"
  - "Add self-referencing security group rule: YELLOW — changes network access"
  - "Create VPC endpoints: YELLOW — changes VPC routing"
  - "Add NAT gateway route: YELLOW — changes network routing with cost implications"
```

## Escalation Conditions
- Job processes production data pipeline
- VPC networking issues blocking multiple Glue jobs
- Insufficient IP addresses in subnet
- VPC endpoint creation requiring networking team coordination
- Cross-VPC access requiring peering or Transit Gateway

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "VPC configuration: network topology"
    - "Subnet details: CIDR ranges and IP availability"
    - "Route tables: network routing configuration"
    - "Security group rules: access control configuration"
  handling: "Do not expose VPC topology or CIDR ranges externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER remove the self-referencing security group rule (required for Glue ENI communication)
- NEVER modify route tables without understanding impact on other services in the VPC

## Phase 3 — Rollback
- If security group rules were added: remove the added rules (except self-referencing)
- If VPC endpoints were created: delete endpoints if not needed
- If NAT gateway route was added: remove the route
- If dedicated subnets were created: delete subnets if not needed (must be empty)

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
