---
name: dd-logs
description: 'Log management - search, archives, metrics, and cost control.'
metadata:
  version: 1.0.1
  author: datadog-labs
  repository: 'https://github.com/datadog-labs/agent-skills'
  tags: 'datadog,logs,logging,search,dd-logs'
  globs: '**/datadog*.yaml,**/*log*'
  alwaysApply: 'false'
  category: observability
  source:
    repository: 'https://github.com/datadog-labs/agent-skills'
    path: dd-logs
    license_path: LICENSE
    commit: 9dbf79d0dccc53ac040fc151009d2179363bf34f
---

# Datadog Logs

Search, process, and archive logs with cost awareness.

## Prerequisites

Datadog Pup should already be installed. See [Setup Pup](https://github.com/datadog-labs/agent-skills/tree/main?tab=readme-ov-file#setup-pup) if not.

## Command Execution Order (Token-Efficient)

For scoped commands, use this order:

1. Check context first (prior outputs, conversation, saved values).
2. If a required value is missing, run a discovery command first.
3. If still ambiguous, ask the user to confirm.
4. Then run the target command.
5. Avoid speculative commands likely to fail.

## Quick Start

```bash
pup auth login
```

## Search Logs

```bash
# Basic search
pup logs search --query="status:error" --from="1h"

# With filters
pup logs search --query="service:api status:error" --from="1h" --limit 100

# JSON output
pup logs search --query="@http.status_code:>=500" --from="1h"
```

### Search Syntax

| Query | Meaning |
|-------|---------|
| `error` | Full-text search |
| `status:error` | Tag equals |
| `@http.status_code:500` | Attribute equals |
| `@http.status_code:>=400` | Numeric range |
| `service:api AND env:prod` | Boolean |
| `@message:*timeout*` | Wildcard |

## Configuration APIs

Available log configuration commands in pup 0.42.0:

```bash
# List log archives
pup logs archives list

# List log restriction queries
pup logs restriction-queries list

# List custom log destinations
pup logs custom-destinations list
```

### Common Processors

```json
{
  "name": "API Logs",
  "filter": {"query": "service:api"},
  "processors": [
    {
      "type": "grok-parser",
      "name": "Parse nginx",
      "source": "message",
      "grok": {"match_rules": "%{IPORHOST:client_ip} %{DATA:method} %{DATA:path} %{NUMBER:status}"}
    },
    {
      "type": "status-remapper",
      "name": "Set severity",
      "sources": ["level", "severity"]
    },
    {
      "type": "attribute-remapper",
      "name": "Remap user_id",
      "sources": ["user_id"],
      "target": "usr.id"
    }
  ]
}
```

## Exclusion Filters (Cost Control)

**Index only what matters:**

```json
{
  "name": "Drop debug logs",
  "filter": {"query": "status:debug"},
  "is_enabled": true
}
```

### High-Volume Exclusions

```bash
# Find noisiest log sources
pup logs search --query="*" --from="1h" | jq 'group_by(.service) | map({service: .[0].service, count: length}) | sort_by(-.count)[:10]'
```

| Exclude | Query |
|---------|-------|
| Health checks | `@http.url:"/health" OR @http.url:"/ready"` |
| Debug logs | `status:debug` |
| Static assets | `@http.url:*.css OR @http.url:*.js` |
| Heartbeats | `@message:*heartbeat*` |

## Archives

Store logs cheaply for compliance:

```bash
# List archives
pup logs archives list

# Archive config (S3 example)
{
  "name": "compliance-archive",
  "query": "*",
  "destination": {
    "type": "s3",
    "bucket": "my-logs-archive",
    "path": "/datadog"
  },
  "rehydration_tags": ["team:platform"]
}
```

### Rehydrate (Restore)

```bash
# No `pup logs rehydrate` command in pup 0.42.0.
# Use Datadog UI/API for rehydration workflows.
```

## Log-Based Metrics

Create metrics from logs (cheaper than indexing):

```bash
# List log-based metrics
pup logs metrics list

# Get one metric by ID
pup logs metrics get api.errors.count
```

**Cardinality warning:** Group by bounded values only.

## Sensitive Data

### Scrubbing Rules

```json
{
  "type": "hash-remapper",
  "name": "Hash emails",
  "sources": ["email", "@user.email"]
}
```

### Never Log

```python
# In your app - sanitize before sending
import re

def sanitize_log(message: str) -> str:
    # Remove credit cards
    message = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED]', message)
    # Remove SSNs
    message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED]', message)
    return message
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Logs not appearing | Check agent, pipeline filters |
| High costs | Add exclusion filters |
| Search slow | Narrow time range, use indexes |
| Missing attributes | Check grok parser |

## References/Documentation

- [Log Search Syntax](https://docs.datadoghq.com/logs/explorer/search_syntax/)
- [Pipelines](https://docs.datadoghq.com/logs/log_configuration/pipelines/)
- [Exclusion Filters](https://docs.datadoghq.com/logs/indexes/#exclusion-filters)
- [Archives](https://docs.datadoghq.com/logs/archives/)
