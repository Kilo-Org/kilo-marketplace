# aimlapi-decisions

Typed answers with calibrated probabilities from decision models, and routers that pick a model per request.

## Install

```bash
gh skill install aimlapi/skills aimlapi-decisions
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- `POST /v1/decisions`: yes/no, choice, score and extraction questions, in both request shapes the endpoint takes
- Reading probabilities, confidence and `found`, and setting thresholds on them
- Routers (`aimlapi/dynamic-router` and the presets): buckets, empty buckets that end a request, ladders, `meta.router`
- What a decision and a routed request cost, and testing both in sandbox mode

The agent reads [SKILL.md](SKILL.md).

## Requirements

`AIMLAPI_API_KEY` for requests; `python3` for the script, which needs no key.
