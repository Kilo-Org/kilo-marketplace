# Soda CLI Command Reference

Status key: **Working** = tested against live API. **Blocked** = API endpoint missing or returning errors.

## Global Flags (all commands)

| Flag | Short | Description |
|------|-------|-------------|
| `--output table\|json\|csv` | `-o` | Output format (auto-detects TTY vs pipe) |
| `--profile <name>` | | Override active auth profile |
| `--no-color` | | Disable color output |
| `--quiet` | `-q` | Suppress non-essential output |
| `--verbose` | `-v` | Show detailed output |
| `--no-interactive` | | Never prompt; fail if input missing |

---

## auth — Working

### `sodacli auth login`
Authenticate with Soda Cloud. Stores credentials in `~/.soda/credentials`.

| Flag | Description |
|------|-------------|
| `--host <host>` | Soda Cloud host (default: cloud.soda.io; US: cloud.us.soda.io) |
| `--api-key-id <id>` | API key ID |
| `--api-key-secret <secret>` | API key secret |
| `--profile <name>` | Save to named profile |

Without flags: interactive wizard. With `--no-interactive`: requires `--api-key-id` and `--api-key-secret`.

### `sodacli auth status`
Show active profile, host, API key ID, and connection health (tests the API).

### `sodacli auth logout`
Remove stored credentials for the active profile. Use `--profile <name>` to target a specific profile.

### `sodacli auth switch <profile>`
Switch the active auth profile.

---

## datasource (alias: ds) — Working

### `sodacli datasource list`
List all datasources. Returns: id, name, label, type, created, updated.

### `sodacli datasource get <id>`
Show datasource details by ID.

### `sodacli datasource create <config-file>`
Register a datasource from a YAML connection config. Requires a self-hosted Soda Runner. Triggers an async discovery scan — datasets won't appear in `dataset list` until the scan completes (~10-15 seconds). The scan ID is printed in the output; use `sodacli job logs <scan-id>` to confirm completion.

| Flag | Description |
|------|-------------|
| `--runner <id>` | Soda Runner ID (auto-detects if only one) |

### `sodacli datasource onboard <config-file-or-datasource-id>`
Guided setup: create datasource + discover datasets + onboard + verify contracts.

| Flag | Description |
|------|-------------|
| `--runner <id>` | Soda Runner ID (only for new datasources) |
| `--monitoring` / `--no-monitoring` | Toggle default metric monitors |
| `--profiling` / `--no-profiling` | Toggle dataset profiling |
| `--contracts copilot\|skeleton\|none` | Generate contracts for all datasets |

When all action flags provided, runs fully non-interactively (no prompts). When `--contracts skeleton` or `--contracts copilot` is used, automatically verifies generated contracts against your data after creation.

### `sodacli datasource delete <id>`
Schedule a datasource for deletion.

### `sodacli datasource update <id>` — Working
Update a datasource's label, runner, or connection config.

| Flag | Description |
|------|-------------|
| `--label <text>` | New label |
| `--runner <id>` | New runner ID |
| `--config <file>` | Updated YAML connection config |

### `sodacli datasource test-connection <config-file>` — Working
Test a datasource connection via Soda Runner. Async: polls until completed/failed (2 minute timeout).

| Flag | Description |
|------|-------------|
| `--runner <id>` | Soda Runner ID (auto-detects if only one) |

### `sodacli datasource diagnostics <id>` — Working
View or configure the diagnostics warehouse. No flags = view current config. Uses read-modify-write (changing one flag preserves all others).

| Flag | Description |
|------|-------------|
| `--enable` / `--disable` | Toggle diagnostics warehouse |
| `--warehouse same\|<config-file>` | Warehouse connection |
| `--table-template <tpl>` | Table name template (e.g. `{dataset_name}`) |
| `--collect-results` / `--no-collect-results` | Store check results |
| `--collect-failed-rows` / `--no-collect-failed-rows` | Store failed rows |
| `--expose-failed-rows-query` / `--no-expose-failed-rows-query` | Expose SQL queries in Cloud |
| `--max-failed-rows <n>` | Maximum failed rows to store |
| `--failed-rows-location <text>` | Message about where to find failed rows |
| `--failed-rows-cta` / `--no-failed-rows-cta` | Toggle CTA button in Cloud |
| `--failed-rows-cta-title <text>` | CTA button title |
| `--failed-rows-cta-url <url>` | CTA button URL |
| `--failed-rows-strategy <type>` | `useDefaultMaxRowCount\|absolute\|percentage` |
| `--failed-rows-threshold <n>` | Threshold (required for absolute/percentage, >= 1) |
| `--failed-rows-threshold-condition` | `greaterThan\|lessThan` (default: greaterThan) |

---

## dataset — Working

### `sodacli dataset list`
List datasets (onboarded + discovered-not-yet-onboarded).

| Flag | Default | Description |
|------|---------|-------------|
| `--filter <query>` | | Fuzzy search on dataset name |
| `--datasource <name>` | | Filter by datasource name |
| `--id <substring>` | | Filter by dataset ID |
| `--status onboarded\|not-onboarded` | all | Filter by onboard status |
| `--limit <n>` | 10 | Max rows |
| `--from <date>` | | Updated on or after (YYYY-MM-DD) |
| `--until <date>` | | Updated on or before (YYYY-MM-DD) |
| `--tag <tag>` | | Filter by tag |

### `sodacli dataset get <id>` — Working
Show dataset details: name, qualified name, datasource, DQ status, checks, incidents, partition column, tags, cloud URL.

### `sodacli dataset update <id>`

| Flag | Description |
|------|-------------|
| `--owner <user-id>` | Set dataset owner (user ID from `sodacli iam user list`) |
| `--tag <tag>` | Set tags (repeatable; replaces all existing) |

At least one flag required.

### `sodacli dataset delete <id>`
Delete a dataset from Soda Cloud.

### `sodacli dataset onboard <id>`
Guided setup for an existing dataset: monitoring, profiling, contracts, and verification.

**Important:** `dataset onboard` only works after `datasource onboard` has been run at least once for the parent datasource. Running it right after `datasource create` will return "dataset not found" even if the dataset appears in `dataset list`.

| Flag | Description |
|------|-------------|
| `--monitoring` / `--no-monitoring` | Toggle monitoring |
| `--profiling` / `--no-profiling` | Toggle profiling |
| `--contracts copilot\|skeleton\|none` | Contract generation |

Contract modes:
- `skeleton` — schema structure + not-null checks only (fast, deterministic)
- `copilot` — AI-generated checks including format, range, uniqueness, and business logic (slower, may need manual fixes for edge cases like UUID columns on Postgres)

When all flags provided, runs non-interactively. When contracts are generated, they are automatically verified against your data.

### `sodacli dataset time-partition <id>`

| Flag | Description |
|------|-------------|
| `--column <col>` | Set partition column (omit to view current) |

### `sodacli dataset profiling <id>`
No flags = view current profiling data and column stats.

| Flag | Description |
|------|-------------|
| `--enable` / `--disable` | Toggle profiling |
| `--schedule <cron>` | Cron expression (e.g. `0 6 * * *`) |
| `--timezone <tz>` | Timezone (default: UTC) |
| `--sampling-rows <n>` | Number of rows to sample |

### `sodacli dataset diagnostics <id>`
No flags = view current settings. Requires diagnostics enabled on the datasource first.

| Flag | Description |
|------|-------------|
| `--collect-results` / `--no-collect-results` | Store check results |
| `--collect-failed-rows` / `--no-collect-failed-rows` | Store failed rows |

### `sodacli dataset permissions list <id>`
List permissions (principal, type, role).

### `sodacli dataset permissions assign <id>`

| Flag | Description |
|------|-------------|
| `--role <role-id>` | Role ID (required) |
| `--user <email>` | User email |
| `--group <group-id>` | Group ID |

One of `--user` or `--group` required.

### `sodacli dataset permissions revoke <id>`
Same flags as assign. Removes matching permission.

---

## contract — Working

### `sodacli contract list`
List all contracts in Soda Cloud. Returns: id, dataset, updated.

### `sodacli contract create`
Generate a contract YAML from a live dataset schema.

| Flag | Description |
|------|-------------|
| `--dataset <fqn>` | Dataset FQN: `datasource/db/schema/table` (required) |
| `--mode skeleton\|copilot` | Generation mode (default: skeleton) |
| `--output <file>` | Output file path |
| `--no-wait` | Return immediately (copilot mode only) |

### `sodacli contract push [file]`
Push a local contract YAML to Soda Cloud (upsert). Reads `dataset:` field from the file to find/create the contract.

### `sodacli contract pull <identifier>`
Pull a contract by dataset qualified name (`datasource/db/schema/table`). Saves to `<table>.yml`.

### `sodacli contract diff [file]`
Show unified diff between local contract and Soda Cloud version.

### `sodacli contract lint [file...]` (alias: `validate`)
Validate contract YAML files against the Soda data contract JSON schema. No network or auth required.

Supports multiple files and glob patterns. Defaults to `contracts/*.yml` if no arguments given.

Exit codes: 0=valid, 2=validation errors found.

```bash
sodacli contract lint orders.yml                    # single file
sodacli contract lint contracts/*.yml               # glob pattern
sodacli contract lint orders.yml users.yml          # multiple files
sodacli contract lint --output json                 # structured output
```

### `sodacli contract verify <file>`
Run data quality checks defined in a contract file. By default, pushes the contract to Soda Cloud and verifies via a Runner.

With `--local`, runs verification locally via soda-core (must be installed on PATH). In local mode, `--datasource` is required and no Soda Cloud auth is needed (unless `--push` is also set).

| Flag | Description |
|------|-------------|
| `--local` | Run locally via soda-core (requires soda-core on PATH) |
| `--datasource <file>` | Datasource config file (required with `--local`) |
| `--push` | Push results to Soda Cloud (useful with `--local`) |
| `--no-wait` | Start verification and return immediately (cloud mode only) |
| `--set key=value` | Runtime variable overrides (repeatable) |

Exit codes: 0=pass, 1=checks failed, 2=error, 3=auth error.

```bash
# Cloud mode (default)
sodacli contract verify orders.yml
sodacli contract verify orders.yml --no-wait

# Local mode (via soda-core)
sodacli contract verify orders.yml --local --datasource datasource.yml
sodacli contract verify orders.yml --local --datasource datasource.yml --push
```

**Debugging exit code 2 (cloud mode):** The output may only show "0 checks passed" without details. Use `sodacli job logs <scan-id>` (scan ID is printed in the verify output) to see the actual SQL or runtime error. Common cause: copilot-generated regex checks on Postgres UUID columns — remove `invalid`/`valid_format` checks on UUID columns since the data type already enforces format.

### `sodacli contract copilot` — Blocked
Not yet available.

### `sodacli contract proposal` — Blocked
Subcommands: list, pull, push, close. All return "not yet available".

---

## monitor — Working

### `sodacli monitor list`

| Flag | Description |
|------|-------------|
| `--dataset <id>` | Dataset ID (**required** — no global monitor list) |
| `--type column\|custom\|dataset` | Filter by monitor type |

### `sodacli monitor config <dataset-id>`
No flags = view current config. Shows enabled/disabled, schedule, monitor count.

| Flag | Description |
|------|-------------|
| `--enable` / `--disable` | Toggle monitoring |
| `--schedule <cron>` | Cron expression |
| `--timezone <tz>` | Timezone (default: UTC) |

### `sodacli monitor add`

| Flag | Description |
|------|-------------|
| `--dataset <id>` | Dataset ID (required) |
| `--type column\|custom` | Monitor type (required) |

**Column monitors** (`--type column`):

| Flag | Description |
|------|-------------|
| `--column <col>` | Column name (required) |
| `--metric <type>` | Metric (required) — see list below |
| `--group-by <col>` | Partition by column values (repeatable) |
| `--exclude-values <col=v1,v2>` | Exclude values from a `--group-by` column (repeatable) |

Metrics: `count`, `missing-pct`, `duplicate-pct`, `distinct-count`, `min`, `max`, `avg`, `sum`, `std-dev`, `variance`, `q1`, `median`, `q3`, `min-length`, `max-length`, `avg-length`, `freshness`

**Custom SQL monitors** (`--type custom`):

| Flag | Description |
|------|-------------|
| `--name <name>` | Monitor name (required) |
| `--sql <query>` | SQL query (required) |
| `--result-metric <col>` | Result metric column (required) |
| `--column <col>` | Associated column (optional) |

**Dataset monitors** (`--type dataset`): Not yet available via API. These exist by default — enable from Soda Cloud UI.

### `sodacli monitor update <monitor-id>`

| Flag | Description |
|------|-------------|
| `--dataset <id>` | Dataset ID (required) |
| `--enable` / `--disable` | Toggle monitor |
| `--sql <query>` | Update SQL (custom only) |
| `--name <name>` | Update name (custom only) |
| `--result-metric <col>` | Update result metric (custom only) |

### `sodacli monitor delete <monitor-id>`

| Flag | Description |
|------|-------------|
| `--dataset <id>` | Dataset ID (required) |

---

## results — Working

### `sodacli results list`
List check results across datasets.

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset <id>` | | Filter by dataset ID (server-side) |
| `--dataset-name <pattern>` | | Substring match on qualified name (client-side) |
| `--status passing\|failing\|error` | all | Filter by status (client-side) |
| `--type check\|monitor\|all` | check | Filter by type |
| `--limit <n>` | 10 | Max results |
| `--sort dataset\|name\|column\|status\|date` | date | Sort column |
| `--order asc\|desc` | desc | Sort order |
| `--from <date>` | | On or after (YYYY-MM-DD) |
| `--until <date>` | | On or before (YYYY-MM-DD) |

---

## job (alias: scan) — Partially Working

### `sodacli job status <id>` — Working
Show scan/job status: state, timing, check summary (pass/fail counts), cloud URL.

### `sodacli job logs <id>` — Working
Show logs for a scan/job.

| Flag | Description |
|------|-------------|
| `--follow` | Stream logs as they arrive |

### `sodacli job list` — Blocked
No list endpoint in API.

### `sodacli job cancel <id>` — Blocked
API returns 404.

---

## runner — Working

### `sodacli runner list`
List registered Soda Runners. Returns: id, name, status, version, last seen.

### `sodacli runner get <runner-id>`
Show details for a specific runner.

### `sodacli runner create --name <name>`
Create runner credentials for Kubernetes deployment. Returns API key ID + secret (shown once). The runner appears in `runner list` only after the Helm chart is deployed and the agent connects to Soda Cloud.

### `sodacli runner delete <runner-id>`
Delete a runner.

---

## iam — Partially Working

### `sodacli iam user list`
List users in the organization. Working.

### `sodacli iam group list`
List groups with members. Working.

### `sodacli iam group create --name <name>`
Create a group. Working.

| Flag | Description |
|------|-------------|
| `--member <email>` | Initial member (repeatable) |

### `sodacli iam group update <id>`
Working.

| Flag | Description |
|------|-------------|
| `--name <name>` | New group name |
| `--add-member <email>` | Add member (repeatable) |
| `--remove-member <email>` | Remove member (repeatable) |

### `sodacli iam group delete <id>`
Working.

### `sodacli iam role list`
List roles. Working.

| Flag | Description |
|------|-------------|
| `--scope global\|dataset` | Filter by scope |

### `sodacli iam user invite` — Working
Invite users to the organization.

| Flag | Description |
|------|-------------|
| `--email <email>` | User email (repeatable, max 10 per call) |

Reports valid and failed invitations separately.

### Blocked IAM commands
- `sodacli iam role create/delete/show`
- `sodacli iam user remove/assign/revoke`
- `sodacli iam group assign/revoke` (role assignment)
- `sodacli iam service-account *`

---

## secret — Working

### `sodacli secret list`
List all secrets. Returns: id, name, created, updated.

### `sodacli secret get <id>`
Show secret details by ID.

### `sodacli secret create`
Create a new secret. Values are encrypted client-side using AES-256-GCM + RSA-OAEP before sending — Soda never sees plaintext. Decryption happens only during scan execution within the runner.

| Flag | Description |
|------|-------------|
| `--name <name>` | Secret name (required, no whitespace, unique per org) |
| `--value <value>` | Secret value (omit for masked prompt, or pipe via stdin) |

Three ways to provide the value:
1. `sodacli secret create --name X` — masked interactive prompt (default)
2. `sodacli secret create --name X --value "val"` — via flag (visible in shell history)
3. `echo "val" | sodacli secret create --name X` — via stdin pipe

Reference in datasource configs: `${secret.NAME}`

### `sodacli secret update <id>`
Update a secret's value. Same encryption and input methods as create.

| Flag | Description |
|------|-------------|
| `--value <value>` | New value (omit for masked prompt, or pipe via stdin) |

### `sodacli secret delete <id>`
Delete a secret.

---

## Blocked commands (no API endpoints)

| Command | Status |
|---------|--------|
| `sodacli incident *` | Documented in OpenAPI spec but returns HTML on dev |
| `sodacli dataset attributes <id>` | Documented in OpenAPI spec but returns HTML on dev |
| `sodacli notification *` | No API endpoint |
| `sodacli dashboard` | No API endpoint |
| `sodacli contract proposal *` | No API endpoint |
