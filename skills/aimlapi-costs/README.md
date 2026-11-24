# aimlapi-costs

Cost per call, tracing, usage and spend reports.

## Install

```bash
gh skill install aimlapi/skills aimlapi-costs
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- Cost from headers and `meta.usage`, including streams and async jobs
- Correlation with `X-Client-Request-Id` and `x-inference-id`
- Usage, logs, balance and ledger endpoints

The agent reads [SKILL.md](SKILL.md).

## Requirements

`AIMLAPI_API_KEY`.
