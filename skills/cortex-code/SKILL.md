---
name: "cortex-code"
description: "Routes Snowflake-specific operations to the Cortex Code CLI while keeping local and non-Snowflake work in Kilo. Use for Snowflake SQL, warehouses, Snowpark, Cortex AI, dynamic tables, governance, and Snowflake security."
metadata:
  category: data
  source:
    repository: "https://github.com/snowflake-labs/subagent-cortex-code"
    path: "skills/cortex-code"
    license_path: "LICENSE"
---

# Cortex Code Integration

Use Cortex Code only for Snowflake-specific work. Keep local files, Git, general programming, non-Snowflake databases, and unrelated infrastructure work in Kilo.

## Prerequisite

Install and configure the Cortex Code CLI using the official documentation: <https://docs.snowflake.com/en/user-guide/cortex-code>.

```bash
command -v cortex
cortex connections list
```

This skill already contains its routing and security scripts. Run script commands from the installed `cortex-code` skill directory so relative paths resolve.

## Security Defaults

Without a local `config.yaml`, the scripts use these defaults:

- `approval_mode: prompt`
- `allowed_envelopes: RO, RW, RESEARCH`
- prompt sanitization enabled
- capability cache and audit output under `~/.cache/cortex-skill/`
- prompts containing credential-file paths are blocked

To customize settings, copy `config.yaml.example` to `config.yaml` in this skill directory and pass it explicitly with `--config config.yaml`. An organization policy can be passed with `--org-policy <path>`. Do not search for agent-specific configuration directories.

Use the least-permissive envelope:

- `RO`: Snowflake reads and analysis
- `RW`: intended Snowflake writes
- `RESEARCH`: read-oriented work that also needs web research
- `DEPLOY`: deployment operations; enable only through policy and explicit confirmation

Never include credentials, private keys, `.env` paths, or credential-file contents in a Cortex prompt.

## First Snowflake Request in a Session

### 1. Discover capabilities

```bash
python scripts/discover_cortex.py
```

This runs `cortex skill list` and caches the discovered capabilities. Run it once per session or after Cortex skills change.

### 2. Route the request

```bash
python scripts/route_request.py --prompt "<user request>"
```

Route to Cortex only when the request is specifically about Snowflake or Cortex. A generic SQL, local-code, or repository task stays in Kilo.

### 3. Build a minimal prompt

Include only:

- the user's Snowflake task
- necessary database, schema, table, or warehouse names
- relevant constraints from the current conversation
- desired output and whether writes are allowed

Do not send unrelated conversation history. If recent Cortex context is essential, load a small sanitized sample:

```bash
python scripts/read_cortex_sessions.py --limit 3
```

### 4. Preview security and approval

```bash
python scripts/security_wrapper.py \
  --prompt "<enriched prompt>" \
  --envelope '{"mode":"RO"}' \
  --dry-run
```

For the default `prompt` mode, run the wrapper without `--dry-run` to obtain the predicted tools and approval text:

```bash
python scripts/security_wrapper.py \
  --prompt "<enriched prompt>" \
  --envelope '{"mode":"RO"}'
```

Present that scope to the user. Do not execute until the user explicitly approves it.

### 5. Execute after approval

Use the approved envelope and only the approved tools returned by the security preview:

```bash
python scripts/execute_cortex.py \
  --prompt-file "/path/to/chmod-600-enriched-prompt.txt" \
  --connection "<connection-name>" \
  --envelope RO \
  --approval-mode prompt \
  --allowed-tools <approved-tool-1> <approved-tool-2>
```

The execution wrapper also accepts the prompt on stdin when `--prompt-file` is omitted. It copies the prompt to a mode-0600 temporary file and uses Cortex's documented `--file` batch mode, preserving stream JSON while keeping prompt text out of process arguments.

For policy-authorized `auto` or `envelope_only` operation, the security wrapper can execute directly and write an audit event. Do not switch away from `prompt` mode merely to bypass approval.

## Follow-up Requests

Reuse the discovered capability cache and active connection for the current session. Re-run routing only when the request is ambiguous or crosses the Snowflake/local boundary. Always repeat approval for a broader envelope, new write target, or destructive operation.

## Routing Rules

Route to Cortex for:

- Snowflake databases, schemas, tables, stages, streams, tasks, and warehouses
- Snowflake-specific SQL and query tuning
- Snowpark, dynamic tables, and governance
- Cortex Search, Cortex Analyst, ML functions, and other Cortex AI features
- Snowflake permissions, masking, row access, and data quality

Keep in Kilo:

- local file reads or edits
- Git and repository operations
- general Python, JavaScript, frontend, or backend work
- PostgreSQL, MySQL, MongoDB, Redis, and other non-Snowflake systems
- infrastructure that is not part of the Snowflake task

When a task mixes both, split it: use Kilo for local artifacts and Cortex only for the Snowflake operation.

## Result Handling

Return the useful result rather than the raw event stream:

- summarize SQL and tool actions
- format query results clearly
- identify changed Snowflake objects
- report the envelope and approval scope used
- redact tokens, credentials, and sensitive values
- surface partial failures and unexecuted steps

## Troubleshooting

- **Cortex CLI missing**: verify `command -v cortex` and follow the official installation guide.
- **Connection refused or missing**: run `cortex connections list` and select a configured connection.
- **Capabilities not cached**: run `python scripts/discover_cortex.py`.
- **Prompt blocked**: remove credential paths or sensitive content; do not weaken the allowlist to send secrets.
- **Envelope blocked**: choose an allowed, narrower envelope or use an approved organization policy.
- **Audit log missing**: verify that `~/.cache/cortex-skill/` is writable or set `audit_log_path` in the explicit local config.
- **Tool denied**: request a new approval scope rather than silently broadening `--allowed-tools`.

This file, the script `--help` output, `config.yaml.example`, and the official Cortex Code documentation are the available guidance; there are no additional bundled reference documents.
