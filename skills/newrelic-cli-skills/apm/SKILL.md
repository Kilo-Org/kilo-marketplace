---
name: "newrelic-cli-apm"
description: "This subskill should be used when triaging New Relic APM latency, throughput, database time, transaction errors, or performance regressions with the New Relic CLI and NRQL. Use the parent newrelic-cli-skills skill for setup and routing."
metadata:
  category: data
  source:
    repository: "https://github.com/vince-winkintel/newrelic-cli-skills"
    path: "apm"
    license_path: "LICENSE"
---

# APM Performance Triage

Use when investigating slow endpoints, high error rates, or performance regressions.

---

## Step 1: Identify the Problem App

```bash
# Get APM summary for all apps
newrelic entity search --name "" --type APPLICATION --domain APM | \
  jq '.[] | {name, alertSeverity, applicationId}'

# Get detailed APM summary for a specific app
newrelic apm application get --applicationId <APP_ID>
```

---

## Step 2: Slow Transaction Analysis

```bash
# Top 10 slowest transactions (last 1 hour)
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(duration), percentile(duration, 95), count(*)
  FROM Transaction
  WHERE appName = 'my-app'
  FACET name
  SINCE 1 hour ago
  LIMIT 10
  ORDER BY average(duration) DESC
"

# Transactions over SLA threshold (e.g. > 2 seconds)
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT count(*), average(duration)
  FROM Transaction
  WHERE appName = 'my-app' AND duration > 2
  FACET name
  SINCE 1 hour ago
"
```

---

## Step 3: Database Query Analysis

```bash
# Slowest DB operations
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(duration), count(*)
  FROM DatabaseTrace
  WHERE appName = 'my-app'
  FACET statement
  SINCE 1 hour ago
  LIMIT 10
  ORDER BY average(duration) DESC
"

# DB time as % of total transaction time
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(databaseDuration), average(duration),
         percentage(average(databaseDuration), average(duration)) AS 'DB %'
  FROM Transaction
  WHERE appName = 'my-app'
  SINCE 1 hour ago
"
```

---

## Step 4: Error Analysis

```bash
# Error rate by transaction
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT count(*), percentage(count(*), WHERE error IS true) AS 'Error Rate'
  FROM Transaction
  WHERE appName = 'my-app'
  FACET name
  SINCE 1 hour ago
"

# Recent errors with messages
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT message, count(*)
  FROM TransactionError
  WHERE appName = 'my-app'
  FACET message
  SINCE 1 hour ago
  LIMIT 20
"

# Full error details including stack trace fields
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT timestamp, name, message, error.class
  FROM TransactionError
  WHERE appName = 'my-app'
  SINCE 30 minutes ago
  LIMIT 10
"
```

---

## Step 5: Throughput & Apdex

```bash
# Requests per minute + Apdex trend
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT rate(count(*), 1 minute) AS 'RPM', apdex(duration, 0.5) AS 'Apdex'
  FROM Transaction
  WHERE appName = 'my-app'
  TIMESERIES 5 minutes
  SINCE 1 hour ago
"
```

---

## Step 6: Correlate with Deployments

```bash
# List recent deployments
newrelic apm deployment list --applicationId <APP_ID>

# Check if performance changed after a deploy
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(duration)
  FROM Transaction
  WHERE appName = 'my-app'
  TIMESERIES 10 minutes
  SINCE 3 hours ago
"
# Look for inflection points that align with deployment timestamps
```

---

## Get Application IDs

```bash
newrelic entity search --name "my-app" --type APPLICATION --domain APM | \
  jq '.[] | {name, applicationId, guid}'
```
