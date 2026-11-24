# `GET /v2/logs`

Source: https://docs.aimlapi.com/api-references/service-endpoints/usage-logs.md

One row per request, failed ones included. Window: `period` (`24h`, `7d`) **or** `start` + `end`, at most 92 days. Filters: `model`, `status` (`succeeded`, `failed`; repeat the parameter, do not comma-separate), `key_prefix` (management key). Paging: `limit` (1 to 100, default 50) and `offset`. There is no filter by id: page through the window and match on your side. At most 200 requests per 60 s.

```json
{
  "data": [
    {
      "created": "2026-11-13T10:02:11Z",
      "status": "succeeded",
      "origin": "api",
      "model": "openai/gpt-4o-mini",
      "cost": { "usd": 0.00124, "credits": 2480 },
      "tokens": { "input": 14, "output": 761, "total": 775 },
      "request_id": "…",
      "inference_id": "V1StGXR8Z5jdHi6BmyT8k",
      "client_request_id": "order-8f21c4"
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 1, "has_more": false }
}
```

- `inference_id` is the `x-inference-id` header, the job id of an async generation, and `reference_id` in `GET /v2/billing/transactions`.
- `client_request_id` is your `X-Client-Request-Id`, or `null`.
- A failed row has `cost.usd` 0.
- `cost.credits` is exact; `cost.usd` is rounded up to $0.00001 per row, so many small rows summed in USD come out high. Sum credits, then convert once (currently 2,000,000 credits = $1: the example row above shows the ratio).
- A charge is recorded just after the response (after `completed` for async jobs): a lookup right after the call may not find it yet.
