---
title: dg api run list
triggers:
  - "listing or filtering runs"
---

```bash
dg api run list
```

- `--status` — filter by run status: QUEUED, STARTING, STARTED, SUCCESS, FAILURE, CANCELING, CANCELED. Repeatable (e.g. `--status FAILURE --status CANCELED`).
- `--job` — filter by job name
