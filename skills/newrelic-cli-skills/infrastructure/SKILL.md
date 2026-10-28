---
name: "newrelic-cli-infrastructure"
description: "This subskill should be used when investigating New Relic Infrastructure host CPU, memory, disk, network, process, or capacity metrics with the New Relic CLI and NRQL. Use the parent newrelic-cli-skills skill for setup and routing."
metadata:
  category: observability
  source:
    repository: "https://github.com/vince-winkintel/newrelic-cli-skills"
    path: "infrastructure"
    license_path: "LICENSE"
---

# Infrastructure Monitoring

Monitor host metrics (CPU, memory, disk, processes) via New Relic Infrastructure.

---

## List Hosts

```bash
newrelic entity search --name "" --type HOST | \
  jq '.[] | {name, alertSeverity, guid}'
```

---

## CPU Usage

```bash
# Average CPU per host (last hour)
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(cpuPercent)
  FROM SystemSample
  FACET hostname
  TIMESERIES 5 minutes
  SINCE 1 hour ago
"

# CPU spikes > 80%
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT percentage(count(*), WHERE cpuPercent > 80) AS 'Time > 80% CPU'
  FROM SystemSample
  FACET hostname
  SINCE 1 hour ago
"
```

---

## Memory Usage

```bash
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(memoryUsedPercent), average(memoryFreeBytes / 1e9) AS 'Free GB'
  FROM SystemSample
  FACET hostname
  TIMESERIES 5 minutes
  SINCE 1 hour ago
"
```

---

## Disk Usage

```bash
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT latest(diskUsedPercent)
  FROM StorageSample
  FACET hostname, mountPoint
  SINCE 10 minutes ago
"
```

---

## Network I/O

```bash
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(receiveBytesPerSecond), average(transmitBytesPerSecond)
  FROM NetworkSample
  FACET hostname
  TIMESERIES 5 minutes
  SINCE 1 hour ago
"
```

---

## Top Processes by CPU

```bash
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(cpuPercent)
  FROM ProcessSample
  WHERE hostname = 'my-host'
  FACET processDisplayName
  SINCE 30 minutes ago
  LIMIT 10
  ORDER BY average(cpuPercent) DESC
"
```

---

## Top Processes by Memory

```bash
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(memoryResidentSizeBytes) / 1e6 AS 'RSS MB'
  FROM ProcessSample
  WHERE hostname = 'my-host'
  FACET processDisplayName
  SINCE 30 minutes ago
  LIMIT 10
  ORDER BY average(memoryResidentSizeBytes) DESC
"
```

---

## Correlate Host Load with App Performance

```bash
# Side-by-side: host CPU vs app response time
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(cpuPercent) AS 'CPU %'
  FROM SystemSample
  WHERE hostname = 'my-host'
  TIMESERIES 5 minutes
  SINCE 1 hour ago
"

newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT average(duration) AS 'Avg Response (s)'
  FROM Transaction
  WHERE appName = 'my-app'
  TIMESERIES 5 minutes
  SINCE 1 hour ago
"
# Compare the two time series to see if CPU pressure correlates with slowdowns
```

---

## Host Reporting Status

```bash
newrelic entity search --name "" --type HOST | \
  jq '.[] | {name, reporting}'
```
