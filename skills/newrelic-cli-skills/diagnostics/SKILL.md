---
name: "newrelic-cli-diagnostics"
description: "This subskill should be used when diagnosing New Relic agent configuration, API connectivity, profile authentication, or missing telemetry with the New Relic CLI. Use the parent newrelic-cli-skills skill for setup and routing."
metadata:
  category: observability
  source:
    repository: "https://github.com/vince-winkintel/newrelic-cli-skills"
    path: "diagnostics"
    license_path: "LICENSE"
---

# Agent Diagnostics

Validate New Relic agent configuration, connectivity, and reporting status.

---

## Run Full Diagnostics

```bash
newrelic diagnose run
```

Checks: API key validity, account connectivity, agent config files, log paths, proxy settings.

---

## Validate Config File

```bash
# For .NET agent on Windows
newrelic diagnose validate \
  --config "C:\ProgramData\New Relic\.NET Agent\newrelic.config"

# For Linux
newrelic diagnose validate --config /etc/newrelic/newrelic.yml
```

---

## Check Agent is Reporting

```bash
# Verify an app is actively sending data
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID --query "
  SELECT count(*)
  FROM Transaction
  WHERE appName = 'my-app'
  SINCE 10 minutes ago
"
# count = 0 means agent is not reporting

# Check entity reporting status
newrelic entity search --name "my-app" --type APPLICATION --domain APM | \
  jq '.[] | {name, reporting}'
```

---

## Check Agent Version

```bash
newrelic entity search --name "my-app" --type APPLICATION --domain APM | \
  jq '.[] | {name, tags: (.tags[] | select(.key == "agentVersion"))}'
```

---

## Connectivity Test

```bash
# Test API key and account access
newrelic profile list
newrelic nrql query --accountId $NEW_RELIC_ACCOUNT_ID \
  --query "SELECT count(*) FROM NrIntegrationError SINCE 1 hour ago"
```

If `NrIntegrationError` count > 0, data ingestion has issues.

---

## Common Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| App shows `reporting: false` | Agent stopped or config missing | Restart app pool / check agent logs |
| Transaction count = 0 | IIS app pool recycled without agent init | Ensure agent auto-instruments on startup |
| High `NrIntegrationError` | Data too large or malformed | Check agent logs for serialization errors |
| `alertSeverity: NOT_CONFIGURED` | No alert conditions on the entity | Add NRQL or APM metric conditions |

---

## .NET Agent Specific (Windows/IIS)

```bash
# Check which apps are instrumented on a host
newrelic entity search --name "my-host" --type HOST | \
  jq '.[] | .tags[] | select(.key == "apmApplicationNames")'

# Agent logs location (Windows)
# C:\ProgramData\New Relic\.NET Agent\Logs\
```

---

## Profile Management

```bash
# List all profiles
newrelic profile list

# Switch profile
newrelic profile default --profile production

# Add a new profile
newrelic profile add \
  --profile staging \
  --apiKey $NEW_RELIC_API_KEY \
  --accountId $NEW_RELIC_ACCOUNT_ID \
  --region US
```
