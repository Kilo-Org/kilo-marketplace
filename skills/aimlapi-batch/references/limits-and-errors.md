# Batch limits, money and error codes

Source: https://docs.aimlapi.com/capabilities/batch-processing.md. Numbers can change; the docs page is the source of truth.

## Limits

| Limit | Value |
| ----- | ----- |
| `endpoint` | `/v1/chat/completions` only |
| `completion_window` | `24h` only |
| `POST /v1/files` | 50 MiB; larger answers `413` |
| `/v1/uploads` | 200 MiB; 20 open uploads per user; an upload expires after 1 hour |
| Line | 1 MiB |
| `custom_id` | 512 characters; 16 MiB for all of a file's ids |
| `metadata` | 16 keys; keys up to 64 characters, values up to 512 |
| Batches in progress | 3 per account (organization, or user without one) |
| Lines in progress | 100,000 per account; a batch over it fails during validation |
| Provider capacity | shared; when full, `429 batch_limit_exceeded` (`Retry-After: 300`) or failure during validation |
| Validation | a batch still validating after 1 hour fails with `validation_timeout` |
| Results | 4 GiB for output and error files together; lines past it fail with `batch_result_too_large`, not charged |

| Provider | Lines per file | File size |
| -------- | -------------- | --------- |
| Anthropic | 100,000 | 256 MB |
| OpenAI | 50,000 | 200 MB |
| Google | 100,000 | 1 GB |
| Alibaba Cloud | 50,000 | 500 MB |
| Mistral | 100,000 | 512 MB |
| xAI | 50,000 | 50 MB |

A batch runs at the model's own provider, with no fallback.

## Hold and charge

After the file check, the worst case of the whole batch is held on the balance. Per line:

- input as one token per 2 bytes of the line (plus 600 tokens with `tools`), at the batch input price;
- plus `max_tokens` at the batch output price;
- Gemini: plus a reasoning budget of half of `max_tokens`;
- xAI reasoning models: plus three times `max_tokens` at the reasoning price.

One charge when the batch ends, for the usage reported on succeeded lines, at the batch price; a succeeded line without reported usage is priced from an estimate. Failed, expired and cancelled lines are not charged. The batch object shows token `usage`, not money.

## Result lines

Output file, one line per succeeded request:

```json
{"id": "batch_req_Qm9X2c1vR8kLp3TzYw7aBn5D", "custom_id": "request-1", "response": {"status_code": 200, "request_id": null, "body": {"object": "chat.completion", "choices": [{"index": 0, "message": {"role": "assistant", "content": "..."}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 14, "completion_tokens": 761, "total_tokens": 775}}}, "error": null}
```

Error file, one line per failed, expired or cancelled request:

```json
{"id": "batch_req_Hk4Ws0eLq2NbV7xCz9mRt1Fy", "custom_id": "request-2", "response": null, "error": {"code": "batch_expired", "message": "The batch window ended before this line ran."}}
```

A failed batch carries `errors`: `{"object": "list", "data": [{code, message, param, line}]}`, up to 100 entries; `line` and `param` are `null` when they do not apply.

## Listing batches

`GET /v1/batches?limit=20` lists file-based batches, newest first, as `{data, has_more, last_id}`; pass `last_id` as `after` for the next page. Each batch carries the `metadata` you sent on create (up to 16 keys), which helps find a batch whose id was lost. `Retry-After` is in seconds.

## Files

A file belongs to the user and workspace of the key that uploaded it; others get `404`. Uploads take `purpose=batch` only; result files have `batch_output`. `GET /v1/files`, `GET /v1/files/{id}`, `DELETE /v1/files/{id}` work as in OpenAI.

## Cancel

| When | Result |
| ---- | ------ |
| `validating` | ends `cancelled` without running; nothing charged |
| `in_progress` | answer `cancelling`; finished lines returned and charged |
| provider refuses | `502 cancel_failed`; the batch keeps running and its hold stays; try again |
| already finishing or ended | the batch as it is; nothing changes |

## Request errors

| Status | `code` | Meaning |
| ------ | ------ | ------- |
| 400 | `unsupported_endpoint`, `unsupported_completion_window` | `endpoint` or `completion_window` is not the supported value |
| 400 | `invalid_metadata`, `invalid_idempotency_key` | `metadata` over limits; key over 255 characters |
| 400 | `invalid_file_purpose`, `empty_file` | not uploaded with `purpose=batch`; no requests |
| 400 | `invalid_json`, `invalid_line`, `line_too_large`, `max_tokens_required` | the first line is invalid (message starts `Line 1:`) |
| 400 | `model_not_supported_for_batch`, `model_not_allowed` | no batch price; not on the key's model list |
| 400 | `invalid_webhook_url`, `webhook_secret_required` | see `aimlapi-webhooks` |
| 400 | `invalid_limit`, `invalid_after` | paging of `GET /v1/batches` |
| 403 | `api_key_required` | batches are created with an API key |
| 404 | `file_not_found`, `batch_not_found` | not for this key and workspace |
| 409 | `idempotency_key_reused` | the key was used for a different request |
| 429 | `batch_limit_exceeded` | 3 batches in progress, or provider capacity full |

## Batch refusals (`status: failed`, `errors[].code`)

| Code | Meaning |
| ---- | ------- |
| `insufficient_credits` | the balance does not cover the worst case |
| `batch_hold_over_balance_share` | the worst case would take over 80 % of the available balance |
| `key_quota_exceeded` | the key's spend limit does not cover it |
| `tenant_spend_limit` | the organization or workspace budget does not cover it |
| `account_spend_limit` | a new account's spend limit does not cover it |
| `batch_limit_exceeded` | over the lines-in-progress limit or provider capacity |
| `validation_timeout` | still validating after 1 hour |

## Line errors (error file, `error.code`)

| Code | Meaning |
| ---- | ------- |
| `batch_expired` | the 24-hour window ended first |
| `batch_cancelled` | cancelled before the line ran |
| `batch_line_missing` | the provider returned nothing for the line |
| `batch_result_too_large` | past the 4 GiB results limit; split the file |
| any other | the provider refused or failed the line; `error.status` has its HTTP status |
