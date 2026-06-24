---
name: "newrelic-cli-deployments"
description: "This subskill should be used when recording, listing, or automating New Relic APM deployment markers and correlating releases with performance changes. Use the parent newrelic-cli-skills skill for setup and routing."
metadata:
  category: data
  source:
    repository: "https://github.com/vince-winkintel/newrelic-cli-skills"
    path: "deployments"
    license_path: "LICENSE"
---

# Deployment Markers

Record deployment events in New Relic so you can correlate releases with performance changes.

---

## Record a Deployment

```bash
newrelic apm deployment create \
  --applicationId <APP_ID> \
  --revision "v1.2.3" \
  --description "Brief description of what changed" \
  --user "deploy-bot"
```

### Required
- `--applicationId` — numeric APM application ID
- `--revision` — version string (e.g. git SHA, semver, MR number)

### Optional
- `--description` — what changed (show in NR UI on charts)
- `--user` — who/what deployed
- `--changelog` — detailed change notes

---

## Get Application ID

```bash
newrelic entity search --name "my-app" --type APPLICATION --domain APM | \
  jq '.[] | {name, applicationId}'
```

---

## List Recent Deployments

```bash
newrelic apm deployment list --applicationId <APP_ID>
```

---

## GitLab/GitHub CI Integration

Add to your CI pipeline after a successful deploy:

```bash
#!/bin/bash
# deploy-marker.sh
APP_ID="${NEW_RELIC_APP_ID}"
REVISION="${CI_COMMIT_SHORT_SHA:-$(git rev-parse --short HEAD)}"
DESCRIPTION="${CI_COMMIT_TITLE:-Deployment}"
USER="${GITLAB_USER_LOGIN:-ci-bot}"

newrelic apm deployment create \
  --applicationId "$APP_ID" \
  --revision "$REVISION" \
  --description "$DESCRIPTION" \
  --user "$USER"
```

---

## Why Deployment Markers Matter

After recording a deployment, the New Relic UI places a vertical line on all APM charts at that timestamp. This makes it immediately obvious if:
- Response times increased after a deploy
- Error rates spiked post-release
- Throughput dropped unexpectedly

You can also query them via NRQL:

```nrql
SELECT *
FROM Deployment
WHERE appId = <APP_ID>
SINCE 1 week ago
```

---

## Automation: Mark on Every Merge

Script to call from a post-merge webhook or CI step:

```bash
#!/bin/bash
# Usage: ./deployment-marker.sh <app_id> <revision> <description>
set -euo pipefail

APP_ID="${1:?app_id required}"
REVISION="${2:?revision required}"
DESCRIPTION="${3:-Automated deployment}"

newrelic apm deployment create \
  --applicationId "$APP_ID" \
  --revision "$REVISION" \
  --description "$DESCRIPTION" \
  --user "ci-bot"

echo "Deployment marker recorded: $REVISION → app $APP_ID"
```
