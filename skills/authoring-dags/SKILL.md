---
name: "authoring-dags"
description: "Workflow and best practices for writing Apache Airflow DAGs. Use when the user wants to create a new DAG, write pipeline code, or asks about DAG patterns and conventions. Includes validation and a minimal test-debug-fix loop using af CLI commands."
metadata:
  category: data
  source:
    repository: "https://github.com/astronomer/agents"
    path: "skills/authoring-dags"
    license_path: "LICENSE"
---

# DAG Authoring Skill

This skill guides you through creating and validating Airflow DAGs using best practices and `af` CLI commands.

> For testing and debugging DAGs, use the Phase 5 test-debug-fix loop in this skill.

---

## Running the CLI

These commands assume `af` is on PATH. Run via `astro otto` to get it automatically, or install standalone with `uv tool install astro-airflow-mcp`.

---

## Workflow Overview

```
+-----------------------------------------+
| 1. DISCOVER                             |
|    Understand codebase & environment    |
+-----------------------------------------+
                 |
+-----------------------------------------+
| 2. PLAN                                 |
|    Propose structure, get approval      |
+-----------------------------------------+
                 |
+-----------------------------------------+
| 3. IMPLEMENT                            |
|    Write DAG following patterns         |
+-----------------------------------------+
                 |
+-----------------------------------------+
| 4. VALIDATE                             |
|    Check import errors, warnings        |
+-----------------------------------------+
                 |
+-----------------------------------------+
| 5. TEST (with user consent)             |
|    Trigger, monitor, check logs         |
+-----------------------------------------+
                 |
+-----------------------------------------+
| 6. ITERATE                              |
|    Fix issues, re-validate              |
+-----------------------------------------+
```

---

## Phase 1: Discover

Before writing code, understand the context.

### Explore the Codebase

Use file tools to find existing patterns:
- `Glob` for `**/dags/**/*.py` to find existing DAGs
- `Read` similar DAGs to understand conventions
- Check `requirements.txt` for available packages

### Query the Airflow Environment

Use `af` CLI commands to understand what's available:

| Command | Purpose |
|---------|---------|
| `af config connections` | What external systems are configured |
| `af config variables` | What configuration values exist |
| `af config providers` | What operator packages are installed |
| `af config version` | Version constraints and features |
| `af dags list` | Existing DAGs and naming conventions |
| `af config pools` | Resource pools for concurrency |

**Example discovery questions:**
- "Is there a Snowflake connection?" -> `af config connections`
- "What Airflow version?" -> `af config version`
- "Are S3 operators available?" -> `af config providers`

---

## Phase 2: Plan

Based on discovery, propose:

1. **DAG structure** - Tasks, dependencies, schedule
2. **Operators to use** - Based on available providers
3. **Connections needed** - Existing or to be created
4. **Variables needed** - Existing or to be created
5. **Packages needed** - Additions to requirements.txt

**Get user approval before implementing.**

---

## Phase 3: Implement

Write the DAG following best practices (see below). Key steps:

1. Create DAG file in appropriate location
2. Update `requirements.txt` if needed
3. Save the file

---

## Phase 4: Validate

**Use `af` CLI as a feedback loop to validate your DAG.**

### Step 1: Check Import Errors

After saving, check for parse errors (Airflow will have already parsed the file):

```bash
af dags errors
```

- If your file appears -> **fix and retry**
- If no errors -> **continue**

Common causes: missing imports, syntax errors, missing packages.

### Step 2: Verify DAG Exists

```bash
af dags get <dag_id>
```

Check: DAG exists, schedule correct, tags set, paused status.

### Step 3: Check Warnings

```bash
af dags warnings
```

Look for deprecation warnings or configuration issues.

### Step 4: Explore DAG Structure

```bash
af dags explore <dag_id>
```

Returns in one call: metadata, tasks, dependencies, source code.

### On Astro

If you're running on Astro, you can also validate locally before deploying:

- **Parse check**: Run `astro dev parse` to catch import errors and DAG-level issues without starting a full Airflow environment
- **DAG-only deploy**: Once validated, use `astro deploy --dags` for fast DAG-only deploys that skip the Docker image build — ideal for iterating on DAG code

---

## Phase 5: Test

Once validation passes, test the DAG with this workflow:

1. **Get user consent** -- Always ask before triggering
2. **Trigger and wait** -- `af runs trigger-wait <dag_id> --timeout 300`
3. **Analyze results** -- Check success/failure status
4. **Debug if needed** -- `af runs diagnose <dag_id> <run_id>` and `af tasks logs <dag_id> <run_id> <task_id>`

### Quick Test (Minimal)

```bash
# Ask user first, then:
af runs trigger-wait <dag_id> --timeout 300
```

Repeat this trigger -> diagnose -> fix -> retest loop until the DAG succeeds or the user chooses to stop.

---

## Phase 6: Iterate

If issues found:
1. Fix the code
2. Check for import errors: `af dags errors`
3. Re-validate (Phase 4)
4. Re-test using the Phase 5 workflow

---

## CLI Quick Reference

| Phase | Command | Purpose |
|-------|---------|---------|
| Discover | `af config connections` | Available connections |
| Discover | `af config variables` | Configuration values |
| Discover | `af config providers` | Installed operators |
| Discover | `af config version` | Version info |
| Validate | `af dags errors` | Parse errors (check first!) |
| Validate | `af dags get <dag_id>` | Verify DAG config |
| Validate | `af dags warnings` | Configuration warnings |
| Validate | `af dags explore <dag_id>` | Full DAG inspection |

> **Testing commands** -- Use `af runs trigger-wait`, `af runs diagnose`, `af tasks logs`, and related `af` commands from the table above.

---

## Best Practices & Anti-Patterns

For code patterns and anti-patterns, see **[reference/best-practices.md](reference/best-practices.md)**.

**Read this reference when writing new DAGs or reviewing existing ones.** It covers what patterns are correct (including Airflow 3-specific behavior) and what to avoid.

---

## Related Skills

- **deploying-airflow**: For deploying DAGs to production (Astro or open-source)

Use the Phase 5 workflow in this skill for DAG testing and debugging.
