---
name: "newrelic-cli-alerts"
description: "This subskill should be used when managing New Relic alert policies, APM or NRQL conditions, notification channels, or open incidents with the New Relic CLI. Use the parent newrelic-cli-skills skill for setup and routing."
metadata:
  category: data
  source:
    repository: "https://github.com/vince-winkintel/newrelic-cli-skills"
    path: "alerts"
    license_path: "LICENSE"
---

# Alert Management

Manage alert policies, conditions, and notification channels via CLI.

---

## List Alert Policies

```bash
newrelic alerts policy list
```

## Get a Policy

```bash
newrelic alerts policy get --policyId <ID>
```

## Create a Policy

```bash
newrelic alerts policy create \
  --name "My App - Performance" \
  --incidentPreference "PER_CONDITION_AND_TARGET"
```

Incident preference options:
- `PER_POLICY` — one incident per policy breach
- `PER_CONDITION` — one incident per condition
- `PER_CONDITION_AND_TARGET` — most granular, one per condition+entity

---

## Alert Conditions

### List Conditions for a Policy

```bash
newrelic alerts conditions list --policyId <POLICY_ID>
```

### Create an APM Metric Condition

```bash
newrelic alerts apmCondition create \
  --policyId <POLICY_ID> \
  --name "High Response Time" \
  --type "apm_app_metric" \
  --metric "response_time_web" \
  --conditionScope "application" \
  --violationCloseTimer 24 \
  --threshold 2.0 \
  --thresholdDuration 5 \
  --thresholdOccurrences "ALL"
```

### Delete a Condition

```bash
newrelic alerts conditions delete --conditionId <ID>
```

---

## NRQL Alert Conditions

```bash
newrelic alerts nrqlCondition static create \
  --policyId <POLICY_ID> \
  --name "Error Rate > 5%" \
  --query "SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName='my-app'" \
  --threshold 5 \
  --thresholdDuration 5 \
  --thresholdOccurrences "ALL" \
  --violationTimeLimitSeconds 86400
```

---

## Notification Channels

```bash
# List channels
newrelic alerts channel list

# Create email channel
newrelic alerts channel create \
  --name "On-Call Email" \
  --type email \
  --configuration '{"recipients": "team@example.com", "include_json_attachment": false}'
```

---

## View Open Incidents

```bash
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT *
  FROM NrAiIncident
  WHERE event = 'open'
  SINCE 24 hours ago
  LIMIT 20
"
```

---

## Check Entity Alert Severity

```bash
newrelic entity search --name "my-app" --type APPLICATION --domain APM | \
  jq '.[] | {name, alertSeverity}'
```

Severity values: `NOT_CONFIGURED`, `NOT_ALERTING`, `WARNING`, `CRITICAL`
