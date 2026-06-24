# Step A: Data Exploration

**Identity**: You are a senior data engineer. Your goal is to understand the data landscape so the dashboard can be planned effectively.

## Data Source Detection

Before executing any queries, check for local data files:

## Entry Requirements

Before Step A begins, verify:
- the user has either `sample-data/*.csv` files or a populated `QUERIES.md`
- `.env` exists if the database path will be used
- if both local CSVs and DB inputs exist, you explicitly tell the user which source you are choosing and why

Prefer the local CSV path only when the project looks like a demo or CSV-first workflow. If `QUERIES.md` contains real queries or `.env` is present, do not silently fall back to `sample-data/`.

### Priority 1: Local Files (`sample-data/` directory)

If the user's project root contains a `sample-data/` directory with data files:

1. **Scan the directory** for supported file types: `.csv`
2. **Load each file** using pandas:
   - CSV: `pd.read_csv(path)`
3. **Analyze** each file as if it were a query result (see Analysis section below)
4. **Skip database queries entirely** — do not require `.env` or `QUERIES.md`

When using local files, note in DS-ARCHITECTURE.md that the datasource is a local file (with filename) rather than a database query.

### Priority 2: Database Queries (`QUERIES.md`)

If no `sample-data/` directory exists (or it is empty), or the user has clearly chosen the DB path, read `QUERIES.md` and execute queries:

1. **Parse QUERIES.md** — queries are grouped under headings that indicate the database type:
   - `## PostgreSQL` → use the installed skill's `scripts/query_postgresql.py`
   - Other database types → add a matching `query_<dbtype>.py` script to the installed skill's `scripts/` directory following the PostgreSQL pattern
   - Within a database heading, treat each fenced SQL block as a separate query artifact
   - Name query outputs deterministically in execution order, such as `query_01_orders.csv`, `query_02_targets.csv`

2. **Execute each query** using the matching script:

```bash
# PostgreSQL example from the installed skill path
python "<SKILL_PATH>/scripts/query_postgresql.py" "SELECT * FROM public.table" --output "<project-root>/step-a-query-results/query_01"
```

The PostgreSQL helper accepts one read-only `SELECT`, `WITH`, or plain `EXPLAIN` query, uses a read-only database session, and enforces a hard 500-row outer limit even when the query already contains a larger or nested `LIMIT`. It rejects multi-statement SQL, DDL/DML, `COPY`, `CALL`, `DO`, `EXPLAIN ANALYZE`, `SELECT INTO`, and row-locking clauses.

## Analysis

For each datasource (whether from local files or query results), analyze:

- Column names, data types, and cardinality
- Sample values and value distributions
- Null rates and data quality observations
- Identify date/time columns, dimensions, and measures
- Spot relationships between datasources (shared keys)

## Create DS-ARCHITECTURE.md

Use the template below:

```markdown
# Data Source Architecture

## Overview
[Brief summary of the datasources and how they relate to the dashboard request]

---

## Datasource 1: [Table/View Name or File Name]

**Source**: `[SQL query used]` or `[sample-data/filename.csv]`
**Rows sampled**: [N]
**Description**: [What this datasource represents]

### Fields

| Field | Type | Description | Sample Values | Notes |
|-------|------|-------------|---------------|-------|
| field_name | STRING | [What this field represents] | val1, val2, val3 | [Nullable/unique/FK] |
| ... | ... | ... | ... | ... |

### Observations
- [Key patterns noticed in the data]
- [Data quality notes]
- [Potential join keys or relationships]

---

## Datasource 2: [Table/View Name or File Name]
[Same structure as above]

---

## Data Model: Joins vs Relationships

Tableau distinguishes between **Joins** and **Relationships** at the data-model level:

| Approach | When to Use | Example |
|----------|-------------|---------|
| **Join** | Tables share the same granularity (e.g., both are at User ID level) | `orders` JOIN `order_details` on `order_id` |
| **Relationship** | Tables have different granularity (e.g., opportunities vs account-level targets) | `opportunities` related to `ae_targets` via `account_executive_id` |

**Why it matters**: Joins at mismatched granularity cause row duplication (the "table explosion" problem — e.g., joining 100 opportunities to 5 AE targets produces 500 rows). Relationships let Tableau query each table independently and combine results only when needed, preserving correct aggregation.

### Connections
[For each pair of related datasources, specify:]
- **Tables**: [Table A] ↔ [Table B]
- **Type**: Join / Relationship
- **Key**: [shared field(s)]
- **Granularity**: [Table A granularity] vs [Table B granularity]
- **Rationale**: [Why join vs relationship was chosen]

## Data Quality Notes
[Any concerns: nulls, duplicates, unexpected values, type mismatches]
```

## Guidelines

- Write field descriptions that a data analyst (not an engineer) can understand
- Flag fields that look like they could serve as dimensions vs. measures
- If a query fails, document the error and suggest fixes
- If data looks sparse or suspicious, note it in observations
- When using local files, note CSV parsing considerations (encoding, delimiters, quoting)
- Choose **Join** when tables share the same granularity; use **Relationship** when granularity differs to avoid row duplication
- Never imply that the user should run query scripts manually; the agent runs the installed skill's scripts
- If both CSV and DB inputs exist, add a one-line source selection note near the top of `DS-ARCHITECTURE.md`
- Preserve each SQL query result as a separate artifact so later steps can trace datasource lineage clearly
- If you ignore `sample-data/` because DB intent is clear, say so explicitly
- If you use fallback sample files instead of a partially configured DB path, say so explicitly
- Approval criteria:
  - every datasource has a clear source and description
  - field descriptions are analyst-friendly
  - likely join keys or relationships are identified
  - source-selection reasoning is visible when both CSV and DB inputs are present
- Present DS-ARCHITECTURE.md to the user and **wait for approval** before proceeding to Step B