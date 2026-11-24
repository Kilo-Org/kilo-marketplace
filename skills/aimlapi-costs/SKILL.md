---
name: aimlapi-costs
description: >-
  Use when someone asks what an AI/ML API (aimlapi) request cost, needs cost per
  request, customer or feature, wants usage, spend, balance or request logs, or
  must reconcile AI/ML API charges with their own records.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/capabilities/request-tracing-and-cost.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-costs
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Track cost and usage

Every inference response says what it cost and carries an id that finds it in the logs and the ledger. Use that, not token counts times a price table.

## When to use

- "How much did this call cost", "log the cost per request / per customer"
- "Spend this week by model", "my balance", reconciling spend with your own records

## Steps

### 1. Read the cost of a call

| Response | Where the cost is |
| -------- | ----------------- |
| Non-streaming JSON | headers `x-aimlapi-usd-spent` (USD) and `x-aimlapi-credits-used` (integer credits); also `meta.usage` in the body on most endpoints |
| Chat Completions stream (SSE) | the last chunk: `meta.usage.usd_spent`, `meta.usage.credits_used`. Headers are sent before the cost is known |
| Messages stream (`/v1/messages`, Anthropic SDK) | not in the events: keep the `x-inference-id` response header (`stream.response.headers` in the Anthropic SDK) and read `cost.credits` from `GET /v2/logs` once the call has ended |
| Async job (video, music, STT) | the final poll's `meta.usage`; the charge lands after `completed` |
| Binary audio (`wav`) | not in the response; read it from `GET /v2/logs` |

`meta.usage.usd_spent` is a JSON number; the `x-aimlapi-usd-spent` header is a decimal string. In `/v2/logs`, `cost.usd` is rounded up per row to $0.00001: sum `cost.credits` (exact) and convert the total once. The `/v2/logs` row shape and paging: [references/logs.md](references/logs.md).

```python
import os
import requests

resp = requests.post(
    "https://api.aimlapi.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}",
        "X-Client-Request-Id": "order-8f21c4",
    },
    json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 50},
    timeout=300,
)
print(resp.headers.get("x-inference-id"), resp.headers.get("x-aimlapi-usd-spent"))
```

With the OpenAI Python SDK, read headers through `client.chat.completions.with_raw_response.create(...)` (`raw.headers`, then `raw.parse()`); in the TypeScript SDK, `.withResponse()`. In a stream, the SDK keeps the unknown `meta` field of the last chunk in `chunk.model_extra["meta"]` (Python) or `chunk.meta` (TypeScript).

### 2. Tag requests with your own id

Send `X-Client-Request-Id` (1 to 128 characters from `A-Z a-z 0-9 . _ : -`). It is echoed back and stored as `client_request_id` in the logs. A value outside that alphabet or too long is **silently dropped**: the request still runs and is billed, you just lose the correlation. Sanitize ids you build from user input.

The response carries `x-inference-id` (our id; for an async job, the job id) and `x-client-request-id` (yours, when valid).

### 3. Report spend

All need the key; windows are `period=24h|7d|…` **or** `start` + `end` (ISO-8601, UTC unless an offset is given), at most 92 days.

| Question | Call |
| -------- | ---- |
| Total spend of this key | `GET /v2/usage?period=7d` |
| Spend by day and model | `GET /v2/usage/detail?period=30d&group_by=day,model&tz=Europe/Berlin` |
| One row per request, failed ones included (cost `0`) | `GET /v2/logs?period=24h&limit=100` (filters `model`, `status`: repeat the parameter, do not comma-separate) |
| Balance | `GET /v2/billing` |
| Every money movement (top-ups and charges) | `GET /v2/billing/transactions` (page with `cursor` from `pagination.next_cursor`, never an offset) |

A charge is recorded just after the response is delivered (after `completed` for async jobs). A ledger lookup the instant a call returns may not see it yet; that is expected.

### 4. Follow one request end to end

1. Send `X-Client-Request-Id`.
2. Keep `x-inference-id` next to your record.
3. Find its row in `GET /v2/logs`: list a window and match `client_request_id` or `inference_id` (no filter exists for them).
4. Find the money in `GET /v2/billing/transactions`, where the same id is `reference_id`.

## Rules

- [ ] Use the cost the API reports. Do not compute bills from token counts and copied prices; prices change, and cached tokens, tools and media are priced differently.
- [ ] To estimate **before** a call, read the current price with `include=pricing` (`aimlapi-models`), from the band for the request size, and say it is an estimate.
- [ ] `x-aimlapi-usd-spent` is a decimal string; parse it as a decimal, not a float, if you sum many of them.
- [ ] `/v2/usage` totals count charged requests only; `/v2/logs` lists failed ones too. Do not expect the counts to match.
- [ ] Management keys can report on other keys with `key_prefix`; a regular key reports on itself.

## Errors

| Response | Meaning | Do |
| -------- | ------- | -- |
| `400` on `/v2/usage` or `/v2/logs` | both `period` and `start`/`end`, or neither; window over 92 days; `group_by` on `/v2/usage` | fix the query |
| `403` with `key_prefix` | a regular key asking about another key | use a management key or drop `key_prefix` |
| `429` on `/v2/logs` | more than 200 requests per 60 s | slow down |
| no cost headers | streamed or binary response, or a JSON answer that took over 60 s | read `meta.usage` in the body or last chunk, or the logs |

## Check before done

- [ ] In sandbox mode your code reads a zero cost without errors.
- [ ] Your `X-Client-Request-Id` values match `^[A-Za-z0-9._:-]{1,128}$`.

## Reference

- https://docs.aimlapi.com/capabilities/request-tracing-and-cost.md
- https://docs.aimlapi.com/api-references/service-endpoints/api-key-usage.md
- https://docs.aimlapi.com/api-references/service-endpoints/usage-logs.md
- https://docs.aimlapi.com/api-references/service-endpoints/account-balance.md
