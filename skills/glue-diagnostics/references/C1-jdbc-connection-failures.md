---
title: "C1 — JDBC Connection Failures"
description: "Diagnose Glue JDBC connection test failures and job connection errors"
status: active
severity: HIGH
triggers:
  - "JDBC connection failed"
  - "connection test failed"
  - "cannot connect to database"
  - "connection timeout"
  - "connection refused"
owner: devops-agent
objective: "Identify and resolve JDBC connection failures between Glue and target databases"
context: "Glue JDBC connections require VPC, subnet, security group, and proper networking. The connection test creates an ENI in the specified subnet. Common failures: wrong JDBC URL, invalid credentials, security group blocking traffic, no route to database, DNS resolution failure, or SSL/TLS mismatch. The security group must allow self-referencing inbound rules for Glue ENIs."
---

## Phase 1 — Triage

MUST:
- Check connection configuration: `aws glue get-connection --name <connection-name>`
- Verify the JDBC URL format and port number
- Check security group rules allow traffic to the database port: `aws ec2 describe-security-groups --group-ids <sg-id>`
- Verify the subnet has a route to the database (same VPC or peering/transit gateway)

SHOULD:
- Test database connectivity from an EC2 instance in the same subnet
- Verify database credentials are correct and not expired
- Check if the database requires SSL/TLS and the connection is configured for it
- Verify DNS resolution for the database hostname

MAY:
- Check VPC flow logs for rejected traffic
- Verify the database is accepting connections (not at max connections limit)
- Check for RDS/Aurora security group allowing the Glue security group

## Phase 2 — Remediate

MUST:
- Fix the JDBC URL, credentials, or security group rules
- Ensure the Glue security group has a self-referencing inbound rule (all TCP from itself)
- Add an inbound rule on the database security group allowing the Glue security group

SHOULD:
- Use Secrets Manager for credential management instead of plaintext in connection properties
- Configure SSL/TLS for encrypted database connections
- Document the required networking setup for the team

MAY:
- Set up VPC endpoints to avoid NAT gateway dependency
- Implement connection pooling in the Glue script for better performance

## Common Issues

- symptoms: "Connection test fails with timeout"
  diagnosis: "No network route between Glue ENI subnet and database. Security group blocking traffic."
  resolution: "Verify subnet route table, security group inbound rules, and NACLs. Add self-referencing rule to Glue security group."

- symptoms: "Connection test fails with 'Authentication failed'"
  diagnosis: "Wrong username/password or database user lacks required privileges."
  resolution: "Verify credentials. Check database user permissions. Update connection properties."

- symptoms: "Connection works in test but fails in job"
  diagnosis: "Job using a different connection name, or concurrent connections exceeding database limit."
  resolution: "Verify the job references the correct connection. Check database max_connections setting."

## Output Format

```yaml
root_cause: "jdbc_connection_failure — <specific_cause>"
evidence:
  - type: connection_config
    content: "<JDBC URL, VPC, subnet, security group>"
  - type: security_group_rules
    content: "<inbound/outbound rules>"
severity: HIGH
mitigation:
  immediate: "Fix networking, credentials, or security group rules"
  long_term: "Use Secrets Manager, document networking requirements"
```


## Safety Ratings
```
safety_ratings:
  - "Check connection configuration: GREEN — read-only API call"
  - "Check security group rules: GREEN — read-only network inspection"
  - "Add security group rules: YELLOW — changes network access"
  - "Update connection credentials: YELLOW — changes database access"
  - "Add self-referencing security group rule: YELLOW — required for Glue ENI communication"
```

## Escalation Conditions
- Job processes production data pipeline
- JDBC connection failure blocking ETL pipeline
- Security group changes affecting other services
- Database credentials expired requiring rotation
- VPC networking changes requiring cross-team coordination

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "JDBC URL: database endpoint and port"
    - "Connection credentials: database username and password"
    - "Security group rules: network access configuration"
    - "VPC configuration: network topology"
  handling: "NEVER expose database credentials. Use Secrets Manager for credential management."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER store database credentials in plaintext — use Secrets Manager
- NEVER open database ports to 0.0.0.0/0 in security groups

## Phase 3 — Rollback
- If security group rules were added: remove the added rules
- If connection credentials were updated: restore previous credentials if the update was incorrect
- If JDBC URL was changed: restore previous URL
- If self-referencing rule was added: keep it (required for Glue) unless the connection is being decommissioned

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
