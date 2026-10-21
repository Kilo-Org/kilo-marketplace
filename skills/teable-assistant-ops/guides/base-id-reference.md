# --base-id Reference

`--base-id` selects a Teable Project (API resource `base`, ID prefix `bse`) and can be pre-configured via `teable config`. When the user explicitly provides a project ID, pass it with `-b` / `--base-id` to the commands below.

Commands that accept it show `-b, --base-id <baseId>` in their options. The tables below list all commands.

## Commands that accept --base-id

<a id="base-management"></a>

### Project Management

| Command | Also requires |
|---------|---------------|
| `base get/update/delete` | — |

`base list/create` are space-scoped or unscoped and do not use project context. Before `base delete`, verify the ID; deletion moves the project to trash.

### Data Query

| Command | Also requires |
|---------|---------------|
| `table get` | — |
| `field get`, `record get`, `view get` | `--table-id` |
| `sql-query` | `--sql` |
| `get-ai-config`, `get-collaborators` | — |

### CRUD

| Command | Also requires |
|---------|---------------|
| `table create` | — |
| `table update/delete` | `--table-id` |
| `field create` | `--table-id` |
| `field update/delete` | `--table-id`, `--field-id` |
| `record create/update/delete` | `--table-id` |
| `view create` | `--table-id` |
| `view update/delete` | `--view-id` |

### Node & Folder

| Command | Also requires |
|---------|---------------|
| `get-node-tree` | — |
| `folder create` | `--name` |
| `folder update` | `--folder-id`, `--name` |
| `folder delete` | `--folder-id` |
| `folder move` | `--node-id` |

### AI / App

| Command | Also requires |
|---------|---------------|
| `trigger-ai-fill` | `--table-id`, `--field-id` |
| `app list/create/update` | — |
| `app get-code/delete/publish/status/unpublish` | `--app-id` |
| `app login-config/ai-enable` | `--app-id` |
| `app ai-docs` | — |

### Artifacts

| Command | Also requires |
|---------|---------------|
| `artifact list` | — |
| `artifact create` | `--file`, `--name` |

`artifact list` accepts optional project context; omit it to search across all projects. `artifact update/get` target an artifact ID directly and do not accept `--base-id`.

### Media

| Command | Also requires |
|---------|---------------|
| `media generate` | `--prompt` or `--input` |
| `media get/cancel` | `--id` |

### Authority

| Command | Also requires |
|---------|---------------|
| `authority get/export/enable/disable/role-list` | — |
| `authority diff/apply` | `--file` |
| `authority role-get/role-delete/role-duplicate` | `--role-id` |

### Automation

| Command | Also requires |
|---------|---------------|
| `automation list` | — |
| `automation get/get-runs/get-run` | `--workflow-id` |
| `automation setup-trigger` | `--trigger-type` |
| `automation activate/test-node/delete-node` | `--workflow-id`, `--node-id` (except activate) |
| `automation generate-script/generate-flowchart/get-script-input` | `--workflow-id`, `--action-id` |

### Routines

| Command | Also requires |
|---------|---------------|
| `routine create/list` | — |
| `routine get/update/activate/deactivate/delete/run-now/get-runs` | `--routine-id` |
| `routine get-run` | `--routine-id`, `--run-id` |

### Advanced

| Command | Also requires |
|---------|---------------|
| `search-api` | `--query` |
| `call-api` | `--method`, `--url` |
| `import` | `--file` or `--attachment-token` + mode flag |
| `scrape search` | `--query` |
| `scrape run` | `--dataset-id`, `--inputs` |
| `scrape status` | `--snapshot-id` |
| `send-email` | `--subject`, `--body`, `--to`/`--bcc` |
| `import-airtable` | `--airtable-base-id` + `--space-id`/`--base-name` (new project) — note: `--base-id` here is an **optional import target** (no `-b` short flag), not the usual configured Teable project |
| `import-google-sheet` | `--spreadsheet-id` + `--space-id`/`--base-name` (new project) — `--base-id` is an optional existing import target, not project context |
| `tools list`, `get-doc` | `--topic` (get-doc only) |

## Commands that do NOT need --base-id

`auth` / `auth status`, `config`, `base list/create`, `artifact update/get`, `upload-attachment`, `import-status`, `integration list/connect/get-token`, `env list/set/update/delete`, `secret list/set/grant/revoke/delete`
