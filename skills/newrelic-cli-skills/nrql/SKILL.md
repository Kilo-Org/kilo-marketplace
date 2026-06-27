---
name: "newrelic-cli-nrql"
description: "This subskill should be used when composing or running ad hoc NRQL queries for New Relic telemetry, facets, time windows, rates, and comparisons. Use newrelic-nrql-debug-ladder instead for failing, empty, or schema-mismatched queries."
metadata:
  category: observability
  source:
    repository: "https://github.com/vince-winkintel/newrelic-cli-skills"
    path: "nrql"
    license_path: "LICENSE"
---

# NRQL Queries

Run ad-hoc NRQL queries against your New Relic account.

---

## Basic Syntax

```bash
newrelic nrql query \
  --accountId $NEW_RELIC_ACCOUNT_ID \
  --query "YOUR NRQL HERE"
```

---

## Key Event Types

| Event Type | What it tracks |
|---|---|
| `Transaction` | Web/non-web request timings |
| `TransactionError` | Exceptions and errors |
| `DatabaseTrace` | Individual DB query timings |
| `ExternalTrace` | Outbound HTTP calls |
| `SystemSample` | Host CPU, memory, disk |
| `ProcessSample` | Per-process metrics |
| `Log` | Log lines (if log forwarding enabled) |
| `PageView` | Browser page load events |
| `JavaScriptError` | Front-end JS errors |

---

## Common Patterns

### Response Time

```nrql
SELECT average(duration), percentile(duration, 95, 99)
FROM Transaction
WHERE appName = 'my-app'
TIMESERIES 5 minutes
SINCE 1 hour ago
```

### Error Rate

```nrql
SELECT percentage(count(*), WHERE error IS true) AS 'Error %'
FROM Transaction
WHERE appName = 'my-app'
TIMESERIES 5 minutes
SINCE 1 hour ago
```

### Throughput (RPM)

```nrql
SELECT rate(count(*), 1 minute) AS 'RPM'
FROM Transaction
WHERE appName = 'my-app'
TIMESERIES
SINCE 1 hour ago
```

### Slowest Endpoints

```nrql
SELECT average(duration)
FROM Transaction
WHERE appName = 'my-app'
FACET name
SINCE 1 hour ago
LIMIT 10
ORDER BY average(duration) DESC
```

### DB Bottlenecks

```nrql
SELECT average(duration), count(*)
FROM DatabaseTrace
WHERE appName = 'my-app'
FACET statement
SINCE 1 hour ago
LIMIT 10
ORDER BY average(duration) DESC
```

### Compare Two Time Windows

```nrql
SELECT average(duration)
FROM Transaction
WHERE appName = 'my-app'
SINCE 1 hour ago
COMPARE WITH 1 day ago
```

### Count Errors by Type

```nrql
SELECT count(*)
FROM TransactionError
WHERE appName = 'my-app'
FACET error.class
SINCE 1 hour ago
```

### Host CPU

```nrql
SELECT average(cpuPercent)
FROM SystemSample
FACET hostname
TIMESERIES 5 minutes
SINCE 1 hour ago
```

### Host Memory

```nrql
SELECT average(memoryUsedPercent)
FROM SystemSample
FACET hostname
TIMESERIES 5 minutes
SINCE 1 hour ago
```

---

## Time Range Shortcuts

```
SINCE 30 minutes ago
SINCE 1 hour ago
SINCE 3 hours ago
SINCE 1 day ago
SINCE 1 week ago
SINCE '2026-02-01 00:00:00' UNTIL '2026-02-02 00:00:00'
```

---

## Useful Clauses

```nrql
FACET name          -- group by field
TIMESERIES 5 min    -- time series chart
LIMIT 20            -- max results
ORDER BY count() DESC
COMPARE WITH 1 day ago
WHERE appName = 'x' AND duration > 1
```

---

## Output Formatting

```bash
# Raw JSON
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID \
  --query "SELECT count(*) FROM Transaction SINCE 1 hour ago" \
  --format json

# Pretty table (default)
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID \
  --query "SELECT count(*) FROM Transaction SINCE 1 hour ago"
```
