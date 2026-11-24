# Sandbox errors and limits

Source: https://docs.aimlapi.com/capabilities/sandbox-mode.md

## Error codes

| Code | Status | Meaning |
| ---- | ------ | ------- |
| `sandbox_header_invalid` | 400 | `X-AIMLAPI-Sandbox` value not in `1`, `true`, `0`, `false`, empty |
| `sandbox_mixed_models` | 400 | sandbox and live models in one request with the prefix only |
| `sandbox_unsupported` | 400 | route not supported, TTS with `stream: true`, router outside chat, or over a per-request limit |
| `sandbox_disabled` | 400 | sandbox switched off; the request never runs live |
| `sandbox_key_not_allowed` | 403 | sandbox key on a route it may not use |
| `sandbox_management_key` | 400 | a sandbox key cannot be a management key |

The code is in top-level `code` of the `application/problem+json` body.

## Limits

| Limit | Value |
| ----- | ----- |
| Sandbox requests | 60 a minute and 1,000 a UTC day per user; above that `429` with `Retry-After` |
| Embeddings | 2,048 inputs; 512,000 values (inputs × `dimensions`) |
| Requests in an inline batch | 1,000 |
| `n` in Chat Completions | capped at 128 |
| Stored answers (async, Responses with `store`) | 1 MB each, kept 1 hour, 32 MB per user per hour |
