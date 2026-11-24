# aimlapi-webhooks

Receive results by signed webhook.

## Install

```bash
gh skill install aimlapi/skills aimlapi-webhooks
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- `webhook_url` on async requests, signing secret, event types
- Standard Webhooks signature verification in Python and Node, tested against the published test vector
- Retries, deduplication, rotation, re-sends

The agent reads [SKILL.md](SKILL.md).

## Requirements

`AIMLAPI_API_KEY` and a public HTTPS endpoint.
