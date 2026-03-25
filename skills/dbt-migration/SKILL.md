---
name: dbt-migration
description: "Migrates dbt projects from dbt Core to the Fusion engine or across data platforms (e.g., Snowflake to Databricks), triaging errors into actionable categories and fixing SQL dialect differences. Use when migrating dbt projects between platforms or upgrading to dbt Fusion."
license: Apache-2.0
metadata:
  category: development
  author: dbt-labs
  source:
    repository: https://github.com/dbt-labs/dbt-agent-skills
    path: skills/dbt-migration
---

## Quick Start: dbt Core to Fusion

Run the migration and triage errors in four steps:

```bash
# 1. Install dbt Fusion CLI
curl -sSf https://install.dbt.com | bash

# 2. Compile the project with Fusion to surface errors
cd /path/to/dbt-project
dbt-fusion compile

# 3. Capture errors to a file for triage
dbt-fusion compile 2>&1 | tee migration-errors.log

# 4. Count errors by type
grep -c "ERROR" migration-errors.log
```

## Workflow

1. **Compile with Fusion** — Run `dbt-fusion compile` on the existing project. Collect all errors.
2. **Triage errors** — Classify each error using the categories below. Prioritize auto-fixable and guided-fix items first.
3. **Apply fixes** — Resolve errors by category, starting with auto-fixable. For guided fixes, follow the sub-skill instructions.
4. **Validate** — Re-run `dbt-fusion compile` after each batch of fixes. Repeat until zero errors remain.
5. **Test** — Run `dbt-fusion test` to confirm model outputs match expectations.

## Error Triage Categories

Classify each compilation error into one of these categories to determine the correct action:

| Category | Action | Example Error |
|---|---|---|
| **Auto-fixable** | Applied automatically by Fusion | `WARN: Implicit cast converted automatically` |
| **Guided fix** | Follow step-by-step resolution | `ERROR: QUALIFY clause not supported` — rewrite as subquery |
| **Needs input** | Requires user decision on intent | `ERROR: Ambiguous column reference` — user must clarify which source |
| **Blocked** | Awaiting Fusion engine update | `ERROR: Unsupported macro` — track in Fusion issue tracker |

See `skills/migrating-dbt-core-to-fusion/references/` for the full error pattern catalog and classification rules.

## Cross-Platform Migration (e.g., Snowflake to Databricks)

When moving between data platforms, SQL dialect differences cause most errors. Common patterns:

| Snowflake SQL | Databricks SQL | Fix |
|---|---|---|
| `FLATTEN(input => ...)` | `EXPLODE(...)` | Rewrite lateral flatten to explode |
| `QUALIFY ROW_NUMBER() ...` | Wrap in subquery with `WHERE rn = 1` | Add CTE or subquery |
| `TRY_TO_NUMBER(...)` | `TRY_CAST(... AS DECIMAL)` | Replace function call |
| `OBJECT_CONSTRUCT(...)` | `NAMED_STRUCT(...)` | Replace function call |

Use `dbt-fusion compile` with the new target profile to surface all dialect differences at once. See `skills/migrating-dbt-project-across-platforms/references/` for platform-specific guidance, unit test generation, and Fusion installation.
