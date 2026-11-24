# aimlapi-batch

Bulk chat completions through the Batch API.

## Install

```bash
gh skill install aimlapi/skills aimlapi-batch
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- OpenAI-format JSONL, `/v1/files` and the parts flow of `/v1/uploads`
- Account limits: 3 batches and 100,000 lines in progress
- Create once with `Idempotency-Key`, poll or get a webhook, read output and error files
- Holds, charges and cancels

The agent reads [SKILL.md](SKILL.md).

## Requirements

`AIMLAPI_API_KEY`; `python3` for the script.
