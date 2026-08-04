---
title: "D1 — Catalog Sync Issues"
description: "Diagnose Data Catalog metadata being out of sync with actual data in S3 or databases"
status: active
severity: MEDIUM
triggers:
  - "catalog out of sync"
  - "table not found"
  - "stale metadata"
  - "partition not registered"
  - "catalog does not match S3"
owner: devops-agent
objective: "Identify and resolve synchronization gaps between the Glue Data Catalog and underlying data stores"
context: "The Glue Data Catalog is a metadata store, not a real-time view of S3 or databases. New files, partitions, or schema changes in S3 are not reflected until a crawler runs or metadata is manually updated. Concurrent jobs writing to S3 and updating the catalog can create race conditions. The catalog supports up to 10 million partitions per table and 1 million tables per database."
---

## Phase 1 — Triage

MUST:
- Check table metadata: `aws glue get-table --database-name <db> --table-name <table>`
- Compare catalog partitions with S3 folders: `aws glue get-partitions --database-name <db> --table-name <table>`
- Verify the table location matches the actual S3 path
- Check when the crawler last ran: `aws glue get-crawler --name <crawler-name>`

SHOULD:
- List S3 objects to compare with catalog metadata: verify S3 prefix matches table location
- Check for recently added S3 folders not yet registered as partitions
- Verify table schema matches actual file schema
- Check for concurrent jobs that may be modifying the catalog

MAY:
- Review CloudTrail for recent Glue API calls modifying the table
- Check for catalog resource policies restricting access
- Verify cross-account catalog access if applicable

## Phase 2 — Remediate

MUST:
- Run a crawler to update metadata, or manually update: `aws glue update-table --database-name <db> --table-input <definition>`
- Register missing partitions: `aws glue batch-create-partition`
- Fix table location if pointing to wrong S3 path

SHOULD:
- Implement automated partition registration (Lambda + S3 events) for near-real-time sync
- Schedule crawlers to run after data pipeline completion
- Use batch-create-partition in ETL jobs that create new partitions

MAY:
- Implement catalog change notifications via EventBridge
- Create a reconciliation job that compares S3 and catalog state

## Common Issues

- symptoms: "Athena query returns no results but data exists in S3"
  diagnosis: "Table location or partition metadata does not match S3 path."
  resolution: "Verify table location. Run MSCK REPAIR TABLE or batch-create-partition for missing partitions."

- symptoms: "Job reads stale data despite new files in S3"
  diagnosis: "Catalog table still points to old schema or partitions."
  resolution: "Run crawler or manually update table metadata. Check if job is using catalog table vs direct S3 path."

- symptoms: "Duplicate tables in catalog after crawler run"
  diagnosis: "Crawler target overlaps with another crawler or manual table definitions."
  resolution: "Review crawler targets for overlap. Use exclude patterns. Delete duplicate tables."

## Output Format

```yaml
root_cause: "catalog_sync — <specific_cause>"
evidence:
  - type: table_metadata
    content: "<catalog table definition>"
  - type: s3_state
    content: "<actual S3 folder/file structure>"
severity: MEDIUM
mitigation:
  immediate: "Update catalog metadata to match actual data"
  long_term: "Automate catalog sync with event-driven partition registration"
```


## Safety Ratings
```
safety_ratings:
  - "Check table metadata and partitions: GREEN — read-only API calls"
  - "Compare catalog with S3: GREEN — read-only inspection"
  - "Run crawler to update metadata: YELLOW — may change table schemas"
  - "Manually update table: YELLOW — changes metadata for all consumers"
  - "Register missing partitions: GREEN — adds metadata, no data change"
```

## Escalation Conditions
- Job processes production data pipeline
- Stale catalog causing incorrect query results
- Catalog updates affecting multiple downstream consumers
- Concurrent jobs creating race conditions on catalog updates
- Catalog limits approaching (10M partitions per table)

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Data Catalog metadata: table schemas, partition info, locations"
    - "S3 paths: data storage locations"
    - "Table definitions: data structure information"
  handling: "Catalog metadata reveals data structure and storage locations. Restrict access appropriately."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER run crawlers with UPDATE_IN_DATABASE on production tables without review
- NEVER delete catalog tables without confirming no downstream consumers depend on them

## Phase 3 — Rollback
- If table metadata was updated: restore previous table definition
- If partitions were registered: delete incorrect partitions
- If crawler updated schema incorrectly: manually revert table schema
- If duplicate tables were created: delete the duplicates

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
