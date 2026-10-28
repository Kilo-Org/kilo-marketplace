---
title: "B2 — Schema Detection Issues"
description: "Diagnose crawler schema detection problems including wrong data types and missing columns"
status: active
severity: MEDIUM
triggers:
  - "wrong schema"
  - "wrong data type"
  - "crawler detected wrong type"
  - "schema mismatch"
  - "columns missing from table"
  - "crawler classification"
owner: devops-agent
objective: "Identify why a crawler is detecting incorrect schemas and fix table definitions"
context: "Crawlers infer schema by sampling data files. They can misdetect types (string vs int), miss columns in sparse data, or create incorrect table definitions when files have mixed formats. The SchemaChangePolicy controls whether changes are applied or logged. Classifiers (built-in or custom) determine how files are parsed."
---

## Phase 1 — Triage

MUST:
- Check the table schema in Data Catalog: `aws glue get-table --database-name <db> --table-name <table>`
- Review crawler configuration and classifiers: `aws glue get-crawler --name <crawler-name>`
- Verify the actual data format and schema in source files
- Check SchemaChangePolicy settings (UpdateBehavior, DeleteBehavior)

SHOULD:
- Compare detected schema with expected schema
- Check if custom classifiers are configured and matching correctly
- Review crawler logs for classification decisions
- Verify data files have consistent format across the crawl target

MAY:
- Test with a subset of files to isolate the problematic data
- Check if mixed file formats exist in the same S3 prefix

## Phase 2 — Remediate

MUST:
- Manually update the table schema if the crawler detected incorrectly: `aws glue update-table --database-name <db> --table-input <table-definition>`
- Fix source data format inconsistencies if possible

SHOULD:
- Create custom classifiers for non-standard data formats
- Set SchemaChangePolicy to LOG to prevent automatic overwrites
- Use exclude patterns to skip files that confuse the classifier

MAY:
- Define tables manually instead of using crawlers for critical schemas
- Use Glue Schema Registry for schema enforcement

## Common Issues

- symptoms: "Crawler detects all columns as string type"
  diagnosis: "CSV files without headers or with inconsistent quoting cause the crawler to default to string."
  resolution: "Add a custom CSV classifier with explicit column definitions. Or define the table manually with correct types."

- symptoms: "Crawler creates multiple tables for the same dataset"
  diagnosis: "Mixed file formats (CSV and Parquet) or inconsistent schemas in the same prefix."
  resolution: "Separate different formats into distinct S3 prefixes. Use exclude patterns in crawler targets."

- symptoms: "Columns disappear after crawler re-run"
  diagnosis: "SchemaChangePolicy DeleteBehavior set to DELETE_FROM_DATABASE and source files changed."
  resolution: "Set DeleteBehavior to LOG or DEPRECATE_IN_DATABASE to prevent column deletion."

## Output Format

```yaml
root_cause: "schema_detection — <specific_cause>"
evidence:
  - type: table_schema
    content: "<detected vs expected schema>"
  - type: crawler_config
    content: "<classifier and schema change policy>"
severity: MEDIUM
mitigation:
  immediate: "Manually correct the table schema"
  long_term: "Add custom classifiers, set schema change policy to LOG"
```


## Safety Ratings
```
safety_ratings:
  - "Check table schema and crawler config: GREEN — read-only API calls"
  - "Manually update table schema: YELLOW — changes catalog metadata used by all consumers"
  - "Create custom classifiers: GREEN — adds classification rules"
  - "Set SchemaChangePolicy to LOG: GREEN — prevents automatic overwrites"
```

## Escalation Conditions
- Job processes production data pipeline
- Wrong schema detection breaking downstream queries
- Schema changes affecting multiple consumers (Athena, Redshift Spectrum, EMR)
- Custom classifier needed for non-standard data formats

## Data Sensitivity
```
data_sensitivity:
  classification: HIGH
  sensitive_fields:
    - "Table schemas: data structure and column names"
    - "Data samples: source data content"
    - "Classifier configurations: data parsing rules"
  handling: "Table schemas reveal data structure. Do not expose column names or data samples externally."
```

## Prohibited Actions
- NEVER suggest resetting job bookmarks without understanding reprocessing impact
- NEVER suggest deleting Data Catalog tables
- NEVER set SchemaChangePolicy to UPDATE_IN_DATABASE for critical production tables
- NEVER let crawlers auto-detect schemas for tables with strict schema requirements

## Phase 3 — Rollback
- If table schema was manually updated: restore previous schema definition
- If custom classifier was added: remove the classifier if it causes incorrect detection
- If SchemaChangePolicy was changed: restore previous policy setting
- If crawler created wrong tables: delete incorrect tables and restore from backup

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
