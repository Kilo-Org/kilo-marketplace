# Glue Diagnostics Skill

Agent skill for investigating and troubleshooting AWS Glue problems using structured runbooks, anti-hallucination guardrails, and systematic investigation workflows.

---

## What This Skill Covers

Structured troubleshooting for AWS Glue when the console alone isn't enough — job failures, OOM errors, Spark executor/driver crashes, crawler schema misdetection, JDBC connection failures, VPC networking issues, Data Catalog drift, DPU sizing problems, shuffle bottlenecks, data skew, bookmark corruption, transformation errors, IAM permission issues, encryption problems, and Glue Studio visual editor limitations.

### Activate When

- Glue ETL job failing with error
- Job exceeding timeout (default 48 hours)
- Spark executor or driver OOM errors
- Spark stage failures or task retries
- Crawler failing to run or complete
- Crawler detecting wrong schema or data types
- Crawler creating too many or too few partitions
- JDBC connection test failing
- Job cannot reach VPC resources
- S3 endpoint access denied or timeout
- Data Catalog tables out of sync with S3
- Schema evolution breaking downstream jobs
- DPU under-provisioned or over-provisioned
- Spark shuffle spill to disk
- Data skew causing task stragglers
- DynamicFrame transformation errors
- Job bookmark not tracking incremental data
- Data quality checks failing
- IAM role missing Glue or S3 permissions
- KMS encryption errors on S3 or Catalog
- Glue Studio visual editor showing errors
- Glue Studio generated code not matching visual design

---

## Skill Structure

```
glue-troubleshooting/
├── SKILL.md
├── README.md
└── references/
    ├── A1-job-failures.md
    ├── A2-job-timeout.md
    ├── A3-oom-errors.md
    ├── A4-spark-errors.md
    ├── B1-crawler-failures.md
    ├── B2-schema-detection.md
    ├── B3-partition-issues.md
    ├── C1-jdbc-connection-failures.md
    ├── C2-vpc-subnet-issues.md
    ├── C3-s3-endpoint-access.md
    ├── D1-catalog-sync-issues.md
    ├── D2-schema-evolution.md
    ├── E1-dpu-sizing.md
    ├── E2-shuffle-issues.md
    ├── E3-data-skew.md
    ├── F1-transformation-errors.md
    ├── F2-bookmark-issues.md
    ├── F3-data-quality.md
    ├── G1-iam-permissions.md
    ├── G2-encryption-issues.md
    ├── H1-visual-editor-errors.md
    ├── H2-job-generation.md
    ├── Z1-general-troubleshooting.md
    ├── glue-guardrails.md
    └── glue-hallucination-patterns.yaml
```

---

## Runbook Library (28 SOPs)

| Category | IDs | Covers |
|----------|-----|--------|
| **A — Jobs** | A1–A4 | Job failures, timeout, OOM, Spark errors |
| **B — Crawlers** | B1–B3 | Crawler failures, schema detection, partition issues |
| **C — Connections** | C1–C3 | JDBC connection failures, VPC/subnet, S3 endpoint |
| **D — Data Catalog** | D1–D2 | Catalog sync issues, schema evolution |
| **E — Performance** | E1–E3 | DPU sizing, shuffle issues, data skew |
| **F — ETL** | F1–F3 | Transformation errors, bookmark issues, data quality |
| **G — Security** | G1–G2 | IAM permissions, encryption |
| **H — Glue Studio** | H1–H2 | Visual editor errors, job generation |
| **Z — Catch-All** | Z1 | General troubleshooting |

---

## License

MIT-0
