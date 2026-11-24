---
name: aimlapi-errors
description: >-
  Use when an AI/ML API (aimlapi) request fails with a 4xx or 5xx status, times
  out, is refused for content policy, or gets a Cloudflare 403, and when adding
  retries, backoff or error handling to an AI/ML API integration.
compatibility: Applies to any language. Examples in Python and TypeScript.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/errors-and-messages/general-info.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-errors
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Handle errors and retries

## When to use

- A call to `api.aimlapi.com` fails and you need to know why and what to do
- Adding retries, timeouts or error handling to an integration

## Steps

### 1. Read the error body

Most errors are `application/problem+json` with `title`, `status`, `message`, `requestId` and an `error` object; validation errors list each bad field in `error.details[]` (`path`, `reason`). Provider errors may use the OpenAI shape `{"error": {"message", "type", "code"}}`. A code, when there is one, is in top-level `code` or `error.code`. Examples and a defensive parser: [references/error-shapes.md](references/error-shapes.md).

Every response has an `x-request-id` header (and `requestId` in error bodies). Log it; support needs it.

### 2. Look up the status in § Errors

It says whether to fix the request, wait, or retry.

### 3. Retry safely

Retry `429` and `500`, `502`, `503` with `Retry-After` or exponential backoff with jitter, three or four times at most: helpers in Python and TypeScript are in [references/retry.md](references/retry.md).

A `200` can still be an error: after 60 seconds the API keeps the connection open with spaces, which fixes the status at `200`, so a later failure arrives as `{"error": {...}}` in the body, without cost headers. Check the body too (the helpers do).

The OpenAI and Anthropic SDKs already retry `429` and `5xx` (`max_retries`, default 2): raise `max_retries` instead of wrapping them in a second loop, and set `timeout` high, since a long generation can take minutes.

### Do not pay twice

A timeout on your side does not cancel the request on ours: it may finish and be charged.

- **Video, music, speech-to-text, background Responses are async:** the submit answers at once with an id. Store it and poll (`aimlapi-async-jobs`, `aimlapi-speech`); never hold a request open for a generation. A `504` or timeout on a poll is safe to retry; resubmitting is not.
- **Synchronous calls (chat, images):** do not retry automatically after your own timeout or a `504`. A row in `GET /v2/logs` appears only once the request has ended, so a missing row means "still running or never arrived", not "safe to retry". Send `X-Client-Request-Id`, wait, then list rows with explicit `start` and `end` (a `period` window is cached for 60 seconds) and match `client_request_id`. Retry only when its row says `failed`, or when none has appeared long after any answer could have come (row shape: `aimlapi-costs`). Work that can outlast your timeout belongs on an async endpoint.
- **Batches:** `Idempotency-Key` on create (`aimlapi-batch`).

### Content policy

A `content_policy_violation` is the provider refusing the content. Refusals count toward restrictions on the end user, the provider's models, or the account, so:

- Do not resend the same content, and do not "fall back" to another model with it.
- Send `safety_identifier` (a stable, anonymous hash of your end user's id) on every request, so a restriction lands on that one user instead of the whole account.
- A `403` "Usage policy restriction" names what is restricted and until when. Retrying before then does not help.

Details: https://docs.aimlapi.com/capabilities/safety-guidance.md

## Rules

- [ ] Never retry `400`, `401`, `403`, `404`; they will fail the same way and some count against you.
- [ ] Always honour `Retry-After`.
- [ ] Cap retries (3 to 4) and total time. Log the `x-request-id` of the last attempt.
- [ ] Show the API's `message` verbatim when you cannot fix the cause.
- [ ] Debugging auth, check whether the key is set (`[ -n "$AIMLAPI_API_KEY" ]`), never print it.

## Errors

| Response | Retry? | Do |
| -------- | ------ | -- |
| `400` "Validation failed", `error.details[]` | no | fix each `path` from the model's `docsJson` (`aimlapi-models`) |
| `400` "… does not support 'system' with this model" | no | move the system text into the user message |
| `400 content_policy_violation`, `403` "Usage policy restriction" | **no**, not on another model either | § Content policy |
| `401` "requires a valid API key" | no | the key is missing, revoked or mistyped in the calling process |
| `403` "You've run out of credits" / `model_not_allowed` | no | top up at https://aimlapi.com/app/billing / allow the model on the key |
| `403` Cloudflare page, `error_code: 1010` | no | send your own `User-Agent`; if it persists, contact support with the `ray_id` |
| `404` | no | wrong path or base URL, or a withdrawn model (`GET /v1/models/deprecations`) |
| `429` | yes | wait `Retry-After`, else exponential backoff with jitter |
| `500`, `502`, `503` | yes, a few times | backoff; a lasting "model is under maintenance" goes to support with the request id |
| `504` "Generation timeout" | carefully | § Do not pay twice |

## Check before done

- [ ] Your handling passes scripted errors in sandbox mode (`[sandbox:error=429]`, `…=503`, `…=403`; `aimlapi-sandbox`).
- [ ] A `400` is not retried; a `429` waits for `Retry-After`.

## Reference

- https://docs.aimlapi.com/errors-and-messages/errors-with-status-code-4xx.md
- https://docs.aimlapi.com/errors-and-messages/errors-with-status-code-5xx.md
- [references/retry.md](references/retry.md): retry helpers in Python and TypeScript
