---
name: "soda-cli"
description: "How to use the Soda CLI for data quality management — authentication, datasources, datasets, contracts, monitors, results, secrets, permissions, and CI/CD integration. Use when working with Soda, data quality, or the sodacli command."
metadata:
  category: data
  source:
    repository: "https://github.com/sodadata/soda-cli"
    path: "skills/soda-cli"
    license_path: "LICENSE"
---

# Soda CLI Guide

The Soda CLI (`sodacli`) manages data quality from the command line. All commands follow `sodacli <resource> <action>`.

## Important: always use `--output json` when running commands

When calling `sodacli` from an agent, **always pass `--output json`** to get structured, parseable output. Without it, the CLI outputs human-readable tables that are harder to parse.

## Quick Reference — What Works

**Fully working (tested against live API):**
- `auth` — login, logout, status, switch profiles
- `datasource` — list, get, create, update, delete, onboard (full wizard), test-connection, diagnostics
- `dataset` — list (with filters), get, update, profiling, diagnostics, permissions, onboard
- `contract` — list, push, pull, diff, lint (JSON schema validation), create (skeleton/copilot), verify (cloud or local via soda-core)
- `monitor` — list, config, add (column/custom), update, delete
- `results` — list (with all filters, sorting, date ranges)
- `job` — status, logs
- `runner` — list, get, create (returns API keys for Kubernetes deployment), delete
- `iam` — user list, user invite, group CRUD, role list
- `secret` — list, get, create, update, delete (client-side encrypted with AES-256-GCM + RSA-OAEP)

**Not yet available (API blocked):**
- `incident` — list, get, update (documented in OpenAPI spec but still returns HTML on dev)
- `dataset attributes` — (documented in OpenAPI spec but still returns HTML on dev)
- `notification` — rules and integrations
- `job list`, `job cancel`
- `contract proposal` — list, pull, push, close
- `monitor add --type dataset` (dataset monitors exist by default, no write endpoint)

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success / all checks passed |
| `1` | One or more checks failed |
| `2` | Execution error |
| `3` | Authentication error — run `sodacli auth login` |

## Authentication

```bash
# Interactive login uses masked prompts for the API key ID and secret.
# Do not pass --api-key-secret on a command line; process listings and shell
# history can expose it.
sodacli auth login --host cloud.soda.io

# Check connection
sodacli auth status

# Named profile (credentials are still entered through masked prompts)
sodacli auth login --profile prod --host cloud.soda.io
sodacli auth switch prod
sodacli dataset list --profile prod    # any command accepts --profile
```

Credentials are stored in `~/.soda/credentials`; keep that file mode `0600`. For CI/CD, inject a pre-provisioned credentials file from the CI secret store rather than passing the API secret as an argument:

```bash
install -d -m 0700 "$HOME/.soda"
install -m 0600 "$SODA_CREDENTIALS_FILE" "$HOME/.soda/credentials"
sodacli auth status --output json
```

Generate API keys at https://docs.soda.io/reference/generate-api-keys and rotate any key exposed through history, logs, or a process list.

## Core Workflows

### Discover what's there

```bash
# List datasources
sodacli datasource list --output json

# Get datasource details
sodacli datasource get <id> --output json

# List datasets (default limit: 10)
sodacli dataset list --output json
sodacli dataset list --datasource <name> --status onboarded --limit 50 --output json

# Filter datasets by name, date range, tag
sodacli dataset list --filter "orders" --from 2026-01-01 --until 2026-12-31 --output json

# Get dataset details
sodacli dataset get <dataset-id> --output json

# View profiling data (column stats, row count, missing %)
sodacli dataset profiling <dataset-id> --output json
```

### Onboard a datasource (end-to-end)

```bash
# Full onboard: create datasource + discover + monitoring + profiling + contracts + verify
sodacli datasource onboard warehouse.yml --monitoring --profiling --contracts skeleton

# Or step by step:
sodacli datasource create warehouse.yml
# ⚠ Discovery is async — datasets won't appear immediately.
# Use `sodacli job logs <scan-id>` (printed by create) to confirm completion,
# or wait ~10-15 seconds before listing datasets.
sodacli datasource onboard <datasource-id> --monitoring --profiling --contracts none
```

**Onboarding a single dataset from a new datasource:**
`dataset onboard` only works after `datasource onboard` has run at least once. If you only need one table, you must still run `datasource onboard` first (which onboards all discovered datasets), then manage individual datasets afterwards.

```bash
# This will NOT work right after `datasource create`, even if the dataset appears in `dataset list`:
# sodacli dataset onboard <dataset-id>   ← returns "dataset not found"

# Instead, onboard the datasource first, then work with individual datasets:
sodacli datasource onboard <datasource-id> --monitoring --profiling --contracts copilot
# Now `dataset onboard`, `dataset profiling`, `monitor add`, etc. work on individual datasets.
```

**Contract generation modes:**
- `skeleton` — schema structure + not-null checks only (fast, deterministic)
- `copilot` — AI analyzes your data and generates format, range, uniqueness, and business-logic checks (takes longer, may need manual fixes — see Troubleshooting below)

When `--contracts skeleton` or `--contracts copilot` is used, the onboard flow automatically verifies the generated contracts against your data and displays pass/fail results.

Datasource config file format:
```yaml
type: snowflake           # snowflake, postgres, bigquery, mysql, redshift, etc.
name: my_warehouse
connection:
  host: account.snowflakecomputing.com
  database: ANALYTICS
  schema: PUBLIC
  user: soda_user
  password: ${secret.DB_PASSWORD}  # Create through Soda's masked secret prompt
  role: SODA_ROLE
  warehouse: COMPUTE_WH
```

### Contracts (data quality checks)

```bash
# List contracts
sodacli contract list --output json

# Generate a contract from live schema
sodacli contract create --dataset datasource/db/schema/table --mode skeleton --output my_table.yml

# Pull existing contract from cloud
sodacli contract pull datasource/db/schema/table

# Edit locally, then push back
sodacli contract push my_table.yml

# Compare local vs cloud
sodacli contract diff my_table.yml

# Validate syntax (offline, no auth needed)
sodacli contract lint my_table.yml
sodacli contract lint contracts/*.yml               # glob support

# Run checks via cloud Runner (local file)
sodacli contract verify my_table.yml --output json

# Run checks via cloud Runner using dataset DQN — no local file needed
sodacli contract verify datasource/db/schema/table --output json

# Run checks locally via soda-core (no cloud auth needed)
sodacli contract verify my_table.yml --local --datasource datasource.yml

# Fire and forget (returns immediately, cloud mode only)
sodacli contract verify my_table.yml --no-wait
```

### Monitors (ML anomaly detection)

```bash
# List monitors on a dataset (--dataset is required)
sodacli monitor list --dataset <dataset-id> --output json

# View monitoring config
sodacli monitor config <dataset-id> --output json

# Enable monitoring with schedule
sodacli monitor config <dataset-id> --enable --schedule "0 6 * * *" --timezone "UTC"

# Add column monitor
sodacli monitor add --dataset <id> --type column --column revenue --metric avg
sodacli monitor add --dataset <id> --type column --column order_id --metric count --group-by region

# Group-by with excluded values (skip specific partitions)
sodacli monitor add --dataset <id> --type column --column amount --metric avg \
  --group-by region --exclude-values region=EU,APAC

# Add custom SQL monitor
sodacli monitor add --dataset <id> --type custom \
  --name "dup check" \
  --sql "SELECT count(*) as c FROM t GROUP BY id HAVING count(*) > 1" \
  --result-metric c

# Update a monitor (enable/disable, change SQL)
sodacli monitor update <monitor-id> --dataset <id> --disable
sodacli monitor update <monitor-id> --dataset <id> --name "renamed" --sql "SELECT 1 as c"

# Delete
sodacli monitor delete <monitor-id> --dataset <id>
```

Column metric types: `count`, `missing-pct`, `duplicate-pct`, `distinct-count`, `min`, `max`, `avg`, `sum`, `std-dev`, `variance`, `q1`, `median`, `q3`, `min-length`, `max-length`, `avg-length`, `freshness`

### Results (check outcomes)

```bash
# Recent results
sodacli results list --output json

# Filter by dataset, status, date
sodacli results list --dataset <id> --status failing --output json
sodacli results list --dataset-name "orders" --from 2026-03-01 --until 2026-03-31 --output json

# Sort and paginate
sodacli results list --limit 50 --sort name --order asc --output json
```

### Permissions

```bash
# List roles and users (to find IDs)
sodacli iam role list --output json
sodacli iam user list --output json

# List dataset permissions
sodacli dataset permissions list <dataset-id> --output json

# Grant / revoke
sodacli dataset permissions assign <dataset-id> --role <role-id> --user <user-id>
sodacli dataset permissions revoke <dataset-id> --role <role-id> --user <user-id>
```

### Groups

```bash
sodacli iam group list --output json
sodacli iam group create --name "Data Engineers" --member alice@co.com --member bob@co.com
sodacli iam group update <id> --add-member carol@co.com
sodacli iam group update <id> --remove-member bob@co.com
sodacli iam group delete <id>
```

### Jobs (scan status & logs)

```bash
# Check scan/job status (shows state, timing, check summary)
sodacli job status <scan-id> --output json

# View logs
sodacli job logs <scan-id>
sodacli job logs <scan-id> --follow    # stream live
```

### Secrets (encrypted credentials)

```bash
# List secrets
sodacli secret list --output json

# Create/update through the masked interactive prompt. Never use --value for a
# secret because command arguments and shell history can expose it.
sodacli secret create --name DB_PASSWORD --output json
sodacli secret update <SECRET_ID> --output json

# For controlled automation, use a mode-0600 temporary input file populated by
# the CI secret provider. The secret is read from stdin, not an argument.
umask 077
SECRET_INPUT=$(mktemp)
trap 'rm -f "$SECRET_INPUT"' EXIT
install -m 0600 "$CI_SECRET_FILE" "$SECRET_INPUT"
sodacli secret create --name DB_PASSWORD --output json < "$SECRET_INPUT"
rm -f "$SECRET_INPUT"
trap - EXIT

# DESTRUCTIVE: inspect the exact target and verify the source credential can be
# recreated or restored. Secret deletion may be permanent.
SECRET_ID="<SECRET_ID>"
# Review the list and verify the selected ID/name without retrieving a value.
sodacli secret list --output json
read -r -p "Type DELETE SODA SECRET ${SECRET_ID}: " CONFIRMATION
if [ "$CONFIRMATION" = "DELETE SODA SECRET ${SECRET_ID}" ]; then
  sodacli secret delete "$SECRET_ID" --output json
else
  printf '%s\n' "Aborted; target confirmation did not match."
fi

# Reference in datasource configs: ${secret.DB_PASSWORD}
```

### User invite

```bash
sodacli iam user invite --email alice@co.com --email bob@co.com   # up to 10 per call
```

### Datasource connection & diagnostics

```bash
# Test a datasource connection (async via Runner)
sodacli datasource test-connection config.yml

# Update datasource label, runner, or connection
sodacli datasource update <id> --label "Production DW"

# View diagnostics warehouse config
sodacli datasource diagnostics <id>

# Configure diagnostics warehouse
sodacli datasource diagnostics <id> --enable --warehouse same --collect-results --collect-failed-rows
sodacli datasource diagnostics <id> --max-failed-rows 5000 --expose-failed-rows-query
sodacli datasource diagnostics <id> --table-template "soda_{dataset_name}"
sodacli datasource diagnostics <id> --failed-rows-cta --failed-rows-cta-title "View in Snowflake" --failed-rows-cta-url "https://app.snowflake.com"
```

### Profiling and dataset diagnostics

```bash
# Enable profiling
sodacli dataset profiling <dataset-id> --enable --schedule "0 6 * * *" --sampling-rows 1000000

# View profiling data
sodacli dataset profiling <dataset-id> --output json

# Set time-partition column
sodacli dataset time-partition <dataset-id> --column created_at

# Configure dataset-level diagnostics overrides
sodacli dataset diagnostics <dataset-id> --collect-results --collect-failed-rows
```

## CI/CD Pattern

```bash
# Option 1: Cloud mode. The CI secret store provides a temporary credentials
# file; do not put the API key secret in command arguments.
install -d -m 0700 "$HOME/.soda"
install -m 0600 "$SODA_CREDENTIALS_FILE" "$HOME/.soda/credentials"
sodacli auth status --no-interactive --output json
sodacli contract lint contracts/*.yml                                        # validate syntax first
sodacli contract verify contracts/orders.yml --no-interactive --output json   # verify via cloud Runner

# Option 2: Local mode (needs soda-core on PATH, no cloud auth)
sodacli contract lint contracts/*.yml
sodacli contract verify contracts/orders.yml --local --datasource datasource.yml

# Exit codes drive pipeline:
# 0 = all checks passed
# 1 = checks failed  →  fail the pipeline
# 2 = execution error →  retry or alert
# 3 = auth error      →  check credentials
```

## Troubleshooting

### Contract verification fails with exit code 2
When `contract verify` returns exit code 2, the output may only show "0 checks passed" without details. Always check the scan logs for the actual error:
```bash
sodacli job logs <scan-id>
```
The scan ID is printed by the `contract verify` command.

### Copilot contracts: UUID regex checks fail on Postgres
Copilot may generate `valid_format` regex checks on UUID columns (e.g., `'^[0-9a-fA-F]{8}-...'`). On Postgres, the `~` regex operator doesn't work on `uuid` type columns, causing a SQL error. **Fix:** Remove `invalid` / `valid_format` checks on UUID columns — the database data type already enforces UUID format. Keep `missing` and `duplicate` checks, which work fine.

### Discovery scan not complete
After `datasource create`, the discovery scan runs asynchronously. If `dataset list` returns empty or `dataset onboard` returns "not found", the scan may still be running. Check with:
```bash
sodacli job logs <scan-id>   # scan-id is printed by datasource create
```

## Global Flags (all commands)

| Flag | Short | Description |
|------|-------|-------------|
| `--output table\|json\|csv` | `-o` | Output format (auto-detects TTY vs pipe) |
| `--profile <name>` | | Override active auth profile |
| `--no-color` | | Disable color output |
| `--quiet` | `-q` | Suppress non-essential output |
| `--verbose` | `-v` | Show detailed output |
| `--no-interactive` | | Never prompt; fail with clear error if input missing |

## Full Command Reference

For detailed flags and usage of every command, see [command-reference.md](command-reference.md).
