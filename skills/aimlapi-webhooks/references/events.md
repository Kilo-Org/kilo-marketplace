# Events, retries and the delivery log

Source: https://docs.aimlapi.com/capabilities/webhooks.md

## Request headers

| Header | Value |
| ------ | ----- |
| `content-type` | `application/json` |
| `user-agent` | `AIMLAPI-Webhooks/1.0` |
| `webhook-id` | event id `evt_…`, the same on every attempt and re-send |
| `webhook-timestamp` | Unix seconds when this attempt was sent |
| `webhook-signature` | `v1,<base64>`; two space-separated during a secret rotation |

The body is the same bytes on every attempt.

## Generation and response events

```json
{
  "object": "event",
  "id": "evt_3YpQx8Kq2LmN5rT7vW9zAb",
  "type": "video.completed",
  "created_at": 1794057600,
  "data": {
    "id": "abc123",
    "object": "video.generation",
    "status": "completed",
    "model": "…",
    "error": null,
    "result": { "…": "the same body as GET by id" },
    "result_truncated": false
  }
}
```

Event types: `video.completed|failed|cancelled`, `audio.*`, `transcription.*`, `image.*` (same three), `response.completed|incomplete|failed|cancelled`, `batch.completed|failed|cancelled|expired`.

Where the file is in `data.result` (the same body as `GET` by id):

| `data.object` | Result |
| ------------- | ------ |
| `video.generation` | `result.video.url` |
| `audio.generation` | `result.audio_file.url` |
| `image.generation` | `result.data[].url` |
| `transcription` | `result.result` (model-specific transcript) |
| `response` | `result.output` |

| Field | Meaning |
| ----- | ------- |
| `data.object` | `video.generation`, `image.generation`, `audio.generation`, `transcription`, `response` |
| `data.error` | `null`, or on `….failed` `{"code": "generation_failed"}` / `{"code": "deadline_exceeded"}` |
| `data.result.meta.usage` | cost (`credits_used`, `usd_spent`) when recorded in time; otherwise `GET` by id shows it seconds later |
| `result_truncated: true` | result over 64 KiB or not ready: `result` is `null`; `GET` `result_url` (a full URL) with your API key before `result_expires_at` (Unix seconds) |
| `result_expired: true` | the job finished but its result is gone; `result_url` is `null` |

## Batch events

`data` holds the batch `id`, `status` (`completed`, `failed`, `cancelled`, `expired`), `request_counts` (`total`, `completed`, `failed`), `output_file_id`, `error_file_id`, and up to 10 `errors`. Download the files with `GET /v1/files/{file_id}/content` (`aimlapi-batch`).

## Retries

No `2xx` → retried after 5 s, 30 s, 2 min, 10 min, 30 min, 1 h, 2 h, 4 h, 8 h, 12 h, 20 h, 24 h (up to 10 % jitter), stopping 72 h after the job ended.

| Receiver answers | Result |
| ---------------- | ------ |
| `2xx` within 8 s (later attempts: 30 s) | delivered |
| `410 Gone` | stops; state `gone` |
| `3xx` | failure; redirects are not followed |
| anything else or no answer | retried |
| failure with `Retry-After` | next attempt waits at least that long, up to 1 h |

A receiver that fails five times in a row, or answers `429`/`502`/`503`/`504`, gets one attempt at a time until it answers `2xx`. At most 60 requests a minute go from one workspace to one IP (or /24, /48 for IPv6).

## Delivery log and re-sends

```bash
curl -s "https://api.aimlapi.com/v1/webhooks/events?task_id=abc123" -H "Authorization: Bearer $AIMLAPI_API_KEY"
curl -s "https://api.aimlapi.com/v1/webhooks/events/evt_…" -H "Authorization: Bearer $AIMLAPI_API_KEY"
curl -s -X POST "https://api.aimlapi.com/v1/webhooks/events/evt_…/retry" -H "Authorization: Bearer $AIMLAPI_API_KEY"
```

`GET /v1/webhooks/events` filters: `task_id`, `type`, `state`, `limit`, `after`. An API key sees events of the jobs it started.

| State | Meaning |
| ----- | ------- |
| `pending`, `delivering` | waiting for / running an attempt |
| `delivered` | a `2xx` came back |
| `gone` | the receiver answered `410` |
| `dead` | no more attempts; see `dead_reason` |

| `dead_reason` | Meaning |
| ------------- | ------- |
| `attempts_exhausted` | no `2xx` within 72 h; can be re-sent |
| `revoked` | the API key was revoked or disabled; cannot be re-sent |
| `no_signing_secret` | no secret when the event was due |
| `invalid_url` | the URL no longer passes the address rules |
| `client_backlog` | over 10,000 events were waiting; re-send once the receiver is back |
| `expired` | past the 7-day body retention |

Keep seen `webhook-id`s for at least 7 days: retries run for 72 h and a re-send can come while the body is kept (7 days).

A re-send keeps `webhook-id` and body and gets the whole retry schedule. It answers `409` while an attempt runs, `410` past retention or after revocation, `429` above 10 a minute / 200 a day per workspace / 5 a day per event. The log keeps each attempt's time, duration and status class for 30 days; the receiver's answer body is never stored.
