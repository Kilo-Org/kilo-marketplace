# aimlapi-errors

Read errors and retry the right ones.

## Install

```bash
gh skill install aimlapi/skills aimlapi-errors
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- The error body formats and what each status means
- Which errors to retry, with `Retry-After` and backoff
- How not to pay twice after a timeout
- Content-policy refusals and `safety_identifier`

The agent reads [SKILL.md](SKILL.md).

## Requirements

Nothing.
