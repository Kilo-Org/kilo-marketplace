---
title: dg api run get-logs
triggers:
  - "fetching stdout stderr compute logs for a run; downloading step output logs"
---

```bash
dg api run get-logs <RUN_ID>
```

- `--step-key` — filter to a specific step.
- `--link-only` — return download URLs instead of log content.
- `--max-bytes` — maximum bytes of log content per step.
- `--cursor` — cursor for paginating log content.
- `--json` — output in JSON format.
