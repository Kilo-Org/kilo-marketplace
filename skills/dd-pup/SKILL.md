---
name: dd-pup
description: Datadog CLI (Rust). OAuth2 auth with token refresh.
metadata:
  version: 1.0.1
  author: datadog-labs
  repository: 'https://github.com/datadog-labs/agent-skills'
  tags: 'datadog,cli,dd-pup,pup'
  alwaysApply: 'false'
  category: observability
  source:
    repository: 'https://github.com/datadog-labs/agent-skills'
    path: dd-pup
    license_path: LICENSE
    commit: 9dbf79d0dccc53ac040fc151009d2179363bf34f
---

# pup (Datadog CLI)

Pup CLI for Datadog API operations. Supports OAuth2 and API key auth.

## Quick Reference

| Task | Command |
|------|---------|
| Search error logs | `pup logs search --query "status:error" --from 1h` |
| List monitors | `pup monitors list` |
| Schedule monitor downtime | `pup downtime create --file downtime.json` |
| Find recent slow traces for a service (last 1h) | `pup traces search --query "service:<service-name> @duration:>500ms" --from 1h` |
| List incidents | `pup incidents list --limit 50` |
| Import incident payload | `pup incidents import --file incident.json` |
| Query metrics | `pup metrics query --query "avg:system.cpu.user{*}"` |
| List hosts | `pup infrastructure hosts list --count 50` |
| Check SLOs | `pup slos list` |
| On-call teams | `pup on-call teams list` |
| Triage open critical security signals (last 1h) | `pup security signals list --query "status:open severity:critical" --from 1h --limit 100` |
| Search audit logs | `pup audit-logs search --query "@action:deleted" --from 24h` |
| Audit activity by user | `pup audit-logs search --query "@usr.email:user@example.com" --from 7d` |
| Investigate API key | `pup audit-logs search --query "@metadata.api_key.id:KEY_ID" --from 90d` |
| Check auth | `pup auth status` |
| Token expiry (time left) | `pup auth status` |
| Refresh token | `pup auth refresh` |

## Prerequisites

Install pup using the [setup instructions](https://github.com/datadog-labs/agent-skills/tree/main?tab=readme-ov-file#setup-pup).

## Required Input Resolution

For commands that need specific scope values (`<env>`, `<service-name>`, `<team-id>`, resource IDs), use this order:

1. Check context first (conversation history, prior command output, saved variables).
2. If missing, run a discovery command first (list/search) to get valid values.
3. If still missing or ambiguous, ask the user to confirm the exact value.
4. Then run the target command.
5. Never run commands with unresolved placeholders like `<env>` or `<monitor-id>`.

## Auth

```bash
pup auth login          # OAuth2 browser flow (recommended)
pup auth status         # Check token validity
pup auth refresh        # Refresh expired token (no browser)
pup auth logout         # Clear credentials
```

**Tokens expire (~1 hour)**. If a command fails with 401/403 mid-conversation:

```bash
pup auth refresh        # Try refresh first
pup auth login          # If refresh fails, full re-auth
```

If Chrome opens the wrong profile/window, use the one-time OAuth URL printed by `pup auth login`
(`If the browser doesn't open, visit: ...`) and open that link manually in the correct account session.

### Headless/CI (no browser)

```bash
# Use env vars or:
export DD_API_KEY=your-api-key
export DD_APP_KEY=your-app-key
export DD_SITE=datadoghq.com    # or datadoghq.eu, etc.
```

## Command Reference

### Monitors
```bash
pup monitors list --limit 10
pup monitors list --tags "env:<env>"
pup monitors get <monitor-id>
pup monitors search --query "<monitor-name>"
pup monitors create --file monitor.json
pup monitors update <monitor-id> --file monitor.json
pup monitors delete <monitor-id>
# No pup monitors mute/unmute commands; use downtime payloads instead.
pup downtime create --file downtime.json
```

### Logs
```bash
pup logs search --query "status:error" --from 1h
pup logs search --query "service:<service-name>" --from 1h --limit 100
pup logs search --query "@http.status_code:5*" --from 24h
pup logs search --query "env:<env> level:error" --from 1h
pup logs aggregate --query "service:<service-name>" --compute count --from 1h
```

### Metrics
```bash
pup metrics query --query "avg:system.cpu.user{*}" --from 1h --to now
pup metrics query --query "sum:trace.express.request.hits{service:<service-name>}" --from 1h --to now
pup metrics list --filter "system.*"
```

### APM / Traces
```bash
# Confirm env tag with the user first (do not assume production/prod/prd).
pup apm services list --env <env> --from 1h --to now
pup traces search --query "service:<service-name>" --from 1h
pup traces search --query "service:<service-name> @duration:>500ms" --from 1h
pup traces search --query "service:<service-name> status:error" --from 1h
```

### Incidents
```bash
pup incidents list --limit 50
pup incidents get <incident-id>
pup incidents import --file incident.json
```

### Dashboards
```bash
pup dashboards list
pup dashboards get <dashboard-id>
pup dashboards create --file dashboard.json
pup dashboards update <dashboard-id> --file dashboard.json
pup dashboards delete <dashboard-id>
```

### SLOs
```bash
pup slos list
pup slos get <slo-id>
pup slos status <slo-id> --from 30d --to now
pup slos create --file slo.json
```

### Synthetics
```bash
pup synthetics tests list
pup synthetics tests get <test-id>
pup synthetics tests search --text "login"
pup synthetics locations list
```

### On-Call
```bash
pup on-call teams list
# Pick a real team id from `pup on-call teams list` output.
pup on-call teams get <team-id>
pup on-call teams memberships list <team-id>
```

### Hosts / Infrastructure
```bash
pup infrastructure hosts list --count 50
pup infrastructure hosts list --filter "env:<env>"
pup infrastructure hosts get <host-name>
```

### Events
```bash
pup events list --from 24h
pup events list --tags "source:deploy"
pup events search --query "deploy" --from 24h --limit 50
pup events get <event-id>
```

### Downtimes
```bash
pup downtime list
pup downtime create --file downtime.json
pup downtime cancel <downtime-id>
```

### Users / Teams
```bash
pup users list
pup users get <user-id>
```

### Security
```bash
pup security signals list --query "*" --from 1h --limit 100
pup security signals list --query "status:open severity:critical" --from 1h --limit 100
# Broader lookback for historical triage
pup security signals list --query "severity:critical" --from 24h --limit 100
```

### Audit Logs
```bash
# List recent events
pup audit-logs list --from 1h --limit 100

# Search with query (Lucene syntax, same as Log Explorer)
pup audit-logs search --query "@action:deleted" --from 24h
pup audit-logs search --query "@usr.email:user@example.com" --from 7d
pup audit-logs search --query "@evt.name:Authentication @action:login" --from 7d
pup audit-logs search --query "@metadata.api_key.id:KEY_ID" --from 90d --limit 200

# JSON output for piping to jq
pup audit-logs search --query "@action:deleted" --from 24h -o json | jq '.data[].attributes'

# audit-logs is the long form (both work)
pup audit-logs search --query "@evt.name:Monitor @action:modified" --from 7d
```

### Service Catalog
```bash
pup service-catalog list
pup service-catalog get <service-name>
```

### Notebooks
```bash
pup notebooks list
pup notebooks get <notebook-id>
```

### Workflows
```bash
pup workflows get <workflow-id>
pup workflows run <workflow-id> --payload '{"key":"value"}'
pup workflows instances list <workflow-id>
```

### Observability Pipelines
```bash
pup obs-pipelines list --limit 50
pup obs-pipelines get <pipeline-id>
pup obs-pipelines create --file pipeline.json
pup obs-pipelines update <pipeline-id> --file pipeline.json
pup obs-pipelines delete <pipeline-id>
pup obs-pipelines validate --file pipeline.json
```

### LLM Observability
```bash
pup llm-obs projects list
pup llm-obs projects create --file project.json
pup llm-obs experiments list
pup llm-obs experiments list --filter-project-id <project-id>
pup llm-obs experiments list --filter-dataset-id <dataset-id>
pup llm-obs experiments create --file experiment.json
pup llm-obs experiments update <experiment-id> --file experiment.json
pup llm-obs experiments delete --file delete-request.json
pup llm-obs datasets list --project-id <project-id>
pup llm-obs datasets create --project-id <project-id> --file dataset.json
pup llm-obs spans search --ml-app <ml-app-name> --from 1h --limit 20
```

### Reference Tables
```bash
pup reference-tables list --limit 50
pup reference-tables get <table-id>
pup reference-tables create --file table.json
pup reference-tables batch-query --file query.json
```

### Cost Cloud Configs
```bash
# AWS CUR configs
pup cost aws-config list
pup cost aws-config get <account-id>
pup cost aws-config create --file config.json
pup cost aws-config delete <account-id>

# Azure UC configs
pup cost azure-config list
pup cost azure-config get <account-id>
pup cost azure-config create --file config.json
pup cost azure-config delete <account-id>

# GCP usage cost configs
pup cost gcp-config list
pup cost gcp-config get <account-id>
pup cost gcp-config create --file config.json
pup cost gcp-config delete <account-id>
```

## Subcommand Discovery

```bash
pup --help              # List all commands
pup <command> --help    # Command-specific help
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Token expired | `pup auth refresh` |
| 403 Forbidden | Missing scope | Check app key permissions |
| 404 Not Found | Wrong ID/resource | Verify resource exists |
| Rate limited | Too many requests | Add delays between calls |

## Install

See [Setup Pup](https://github.com/datadog-labs/agent-skills/tree/main?tab=readme-ov-file#setup-pup) for installation instructions.

### Verify Installation

```bash
which pup
pup --version
```

## Sites

| Site | `DD_SITE` value |
|------|-----------------|
| US1 (default) | `datadoghq.com` |
| US3 | `us3.datadoghq.com` |
| US5 | `us5.datadoghq.com` |
| EU1 | `datadoghq.eu` |
| AP1 | `ap1.datadoghq.com` |
| AP2 | `ap2.datadoghq.com` |
| US1-FED | `ddog-gov.com` |
