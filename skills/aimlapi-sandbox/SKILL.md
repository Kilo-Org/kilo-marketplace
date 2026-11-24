---
name: aimlapi-sandbox
description: >-
  Use when testing, mocking or running CI against AI/ML API (aimlapi) without
  spending credits, checking that code parses responses, streams and tool calls,
  or triggering 403, 429, 500 or 503 errors, slow answers or failed jobs on
  purpose.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY (a live or a
  sandbox key) in the environment.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/capabilities/sandbox-mode.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-sandbox
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Test for free in sandbox mode

Sandbox mode runs the real request path (key, model id, body validation against the model's schema) and answers in the live format, but calls no model and charges nothing, even at a zero balance. It tests **your code**, not a model: answers are fixed.

## When to use

- Write or run tests, CI, or a demo against AI/ML API without spending credits
- Check parsing of text, streams, tool calls, JSON, images, async jobs, and handling of `403`, `429`, `500`, `503`

## Steps

### 1. Turn it on

| Method | How | Best for |
| ------ | --- | -------- |
| Model prefix | `"model": "sandbox/openai/gpt-4o-mini"` | one string to change, works in any SDK |
| Header | `X-AIMLAPI-Sandbox: 1` with the usual model id | set once as an SDK default header |
| Sandbox key | a key created with `"mode": "sandbox"` | CI and test environments: it can never start a paid request |

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key=os.environ["AIMLAPI_API_KEY"],
    default_headers={"X-AIMLAPI-Sandbox": "1"},
)
```

- Header values: `1`/`true` on, `0`/`false`/empty off; anything else is `400 sandbox_header_invalid`.
- A sandbox key is created in the dashboard (**API Keys**, **Sandbox key** on) or with `POST /v1/keys` and `"mode": "sandbox"`; the mode cannot change later.

### 2. Recognise a sandbox answer

`x-aimlapi-sandbox: true`; `model` starts with `sandbox/`; `system_fingerprint: "aimlapi-sandbox"` on Chat Completions; cost `0`.

### 3. Script the answer you need

Put a marker in the main text of the request (last user message, `prompt` for media, `input` for embeddings and TTS). First marker wins; case is ignored.

| Marker | Answer |
| ------ | ------ |
| `[sandbox:text]` | short text, even with `tools` |
| `[sandbox:long]` | ~12,000 characters; a token limit cuts it and sets `finish_reason: "length"` |
| `[sandbox:tool]` | a tool call whose arguments match the tool's JSON Schema (needs `tools`) |
| `[sandbox:json]` | JSON that follows the request's schema; `{"sandbox": true}` without one |
| `[sandbox:error=403]` | the live "out of funds" `403` |
| `[sandbox:error=429]` | a rate-limit `429` with `Retry-After: 1` |
| `[sandbox:error=500]` / `[sandbox:error=503]` | provider errors in the OpenAI error format |
| `[sandbox:fail]` | the async job (video, music) ends `failed` with an `error` object |
| `[sandbox:slow=<ms>]` | the answer waits 0 to 20,000 ms |

`400` and `404` are not scenarios: send a really invalid body, or `sandbox/does-not-exist`.

A marker fails **every** attempt: it tests give-up, not recovery. To test recovery, send the marker on the first attempt only. The scripted `429` is `application/problem+json` with `Retry-After: 1` (OpenAI SDK: `RateLimitError`); `500`/`503` use the OpenAI error shape (`InternalServerError`). Testing your own retry loop, set the SDK's `max_retries=0`.

`python3 scripts/try.py chat '{"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "[sandbox:error=429] hi"}]}'` shows the status and headers your code will see.

### 4. What is covered

Chat Completions (JSON and SSE), Responses (incl. `background: true`), Messages, image generation and edits, embeddings, TTS (not `stream: true`), OCR, decisions, video, music, speech-to-text, and the older inline Message Batches. Not covered: limits of translated routes (`aimlapi-protocols`), `webhook_url` (`400 webhook_url_not_supported`), the file-based Batch API with `/v1/files` (a sandbox key gets `403`), Realtime, Agent Tools and MCP. Test those with a small live request.

Async jobs in sandbox finish about 10 seconds after submit; the answer is kept for one hour, then polls return `404`.

### 5. Go live

Remove the switch: drop the `sandbox/` prefix, the header, or swap the sandbox key for a live key. The response format does not change. Live answers are billed.

## Rules

- [ ] Use a **sandbox key** for CI and shared test environments, so a misconfigured test can never spend money.
- [ ] Do not assert on answer text, token counts or `usage` from the sandbox: they are fixed or estimated (about one token per four characters).
- [ ] A sandbox key works only on inference (submit, poll, cancel), `/v2/usage` and `/v2/logs`; elsewhere `403 sandbox_key_not_allowed`.
- [ ] Keep suites small: 60 sandbox requests a minute and 1,000 a day per user ([references/errors.md](references/errors.md)).
- [ ] File uploads (`/v1/images/edits`, speech-to-text) with a balance under $1: use the header or a sandbox key, not the prefix.

## Errors

`400 sandbox_header_invalid` (header value not `1`/`true`/`0`/`false`/empty), `400 sandbox_mixed_models`, `400 sandbox_unsupported` (route or size not covered), `403 sandbox_key_not_allowed` (sandbox key outside inference, usage and logs). Every code: [references/errors.md](references/errors.md).

## Check before done

- [ ] Your real body through `python3 scripts/try.py chat @request.json` returns `x-aimlapi-sandbox: true` and the expected shape.
- [ ] Each error your code handles was triggered once with its marker.
- [ ] Production config has no `sandbox/` prefix, no sandbox header, no sandbox key.

## Reference

- https://docs.aimlapi.com/capabilities/sandbox-mode.md (limits, per-endpoint defaults, streaming details)
- `scripts/try.py`: send one request in sandbox mode and print status, sandbox and cost headers, and the body
- [references/errors.md](references/errors.md): sandbox error codes and limits
