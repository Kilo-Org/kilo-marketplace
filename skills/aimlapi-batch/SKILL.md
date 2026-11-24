---
name: aimlapi-batch
description: >-
  Use when many chat-completion requests can wait hours and should cost less on
  AI/ML API (aimlapi): evaluations, labelling or summarizing a dataset, a JSONL
  file with input_file_id, the OpenAI Batch API, or a batch that failed, expired
  or whose results cannot be downloaded.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment. Script needs python3 3.9+.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/capabilities/batch-processing.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-batch
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Run a batch

A batch runs a JSONL file of `/v1/chat/completions` requests within 24 hours at the model's batch price (for most providers half the list price). The format is OpenAI's: with the OpenAI SDK, `files.create`, `batches.*` and `files.content` work after changing `base_url`.

## When to use

- Many prompts nobody waits for: evaluations, labelling, summarizing a dataset
- "Cheapest way to run all of these", "OpenAI Batch API", "input_file_id"
- A batch ended `failed` or `expired`, or its result file will not download

Not for: anything a user is waiting for (`aimlapi-chat`); images, audio, embeddings (only chat lines are accepted).

## Steps

### 1. Pick a model that has a batch price

```bash
curl -s 'https://api.aimlapi.com/v1/models?id=anthropic/claude-haiku-5-5&include=pricing'
```

Only a model whose entry has `pricing.batch` can run; use its id exactly as listed. Some short aliases (`gpt-5.5`, `o3`) route to another provider and are refused with `model_not_supported_for_batch`.

### 2. Write the file, then check it locally

```json
{"custom_id": "review-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "anthropic/claude-haiku-5-5", "max_tokens": 5, "messages": [{"role": "user", "content": "Sentiment of: 'Great product'. One word."}]}}
```

- One model per file; `max_tokens` (or `max_completion_tokens`) on **every** line, as low as the task allows: the hold is priced from it.
- `custom_id` unique, up to 512 characters. Text and function tools only; no images, audio or server tools; `stream` false, `n` 1. Other fields fail the line. `cache_control` is accepted, so long shared instructions can be cached.

```bash
python3 scripts/batch.py check requests.jsonl
```

### 3. Split to fit the account limits

At most **3 batches** and **100,000 lines** in progress per account (a fourth create gets `429 batch_limit_exceeded` with `Retry-After`). A file is at most 50 MiB in one request, 200 MiB in parts, and under its provider's cap (Anthropic 100,000 lines, OpenAI 50,000). A large job is a queue: split into files under the limits, keep at most 3 running, start the next when one ends. More limits: [references/limits-and-errors.md](references/limits-and-errors.md).

### 4. Upload, create, wait, read

```bash
python3 scripts/batch.py run requests.jsonl --out results/
```

The script uploads (single request or parts), creates the batch, polls, and saves the output and error files. A re-run on the same file resumes its batch (state in `<file>.aimlapi-batch.json`); a changed file stops. In the user's own code:

- **Create once.** Send `Idempotency-Key` (up to 255 characters, from the file content); store the batch id before polling.
- **Large files** go through `/v1/uploads`: `POST /v1/uploads` → `POST /v1/uploads/{id}/parts` `{"part_number": n}` → `PUT` the bytes to the returned `url` (no `Authorization`; parts ≥ 5 MiB except the last) → `POST /v1/uploads/{id}/complete` with `{"parts": [{"part_number", "etag"}]}` → `file.id`. The OpenAI SDK's `uploads.*` helpers do not work here.
- **Download** with `GET /v1/files/{id}/content`: it redirects (`302`) to a signed link valid 5 minutes. Follow it **without** the `Authorization` header (`requests` and the OpenAI SDK do; Python's `urllib` does not).
- **Notify instead of polling:** `webhook_url` on create (`aimlapi-webhooks`).

### 5. Read the outcome correctly

- `validating`, `in_progress`, `finalizing`, `cancelling` are still running.
- `completed` means the batch ran to the end, **even if every line failed**: read `request_counts` and the error file.
- `failed` means it was refused as a whole (file check, hold, provider): `errors` lists up to 100 problems with line numbers, and nothing is charged.
- `expired` and `cancelled`: finished lines are in the output file and charged, the rest in the error file.

Output lines come in any order: join them by `custom_id`; `response.body` is a Chat Completions response. Line and `errors` shapes: [references/limits-and-errors.md](references/limits-and-errors.md). Error-file lines are not charged. Result files are deleted after 30 days.

## Rules

- [ ] Never create the same batch twice: `Idempotency-Key`, and poll the stored id after a crash.
- [ ] Keep the hold small: `max_tokens` sized to the task. A hold over 80 % of the available balance fails the batch with `batch_hold_over_balance_share`.
- [ ] Do not delete an input file while its batch runs (`409`).
- [ ] Do not use the older inline `"requests": [...]` format.

## Errors

| Symptom | Do |
| ------- | -- |
| `400 model_not_supported_for_batch` | step 1 |
| `400` `Line 1: …`, or batch `failed` with `errors[].line` | fix those lines (`batch.py check`), upload, create again |
| batch `failed` with `insufficient_credits`, `batch_hold_over_balance_share`, `key_quota_exceeded` | lower `max_tokens`, split, or top up |
| `429 batch_limit_exceeded` | wait `Retry-After`; keep ≤ 3 running |
| result download fails with an auth error | step 4, follow the redirect without `Authorization` |

Every code: [references/limits-and-errors.md](references/limits-and-errors.md).

## Check before done

- [ ] `python3 scripts/batch.py check requests.jsonl` reports no problems.
- [ ] A 2-line batch ran end to end and both result files were read before the full set.
- [ ] The code joins results by `custom_id`, reads the error file, runs at most 3 batches.

## Reference

- [references/limits-and-errors.md](references/limits-and-errors.md): limits, hold formula, refusal and line error codes
- `scripts/batch.py`: check, upload (single or parts), create, wait, download, cancel
- Docs: https://docs.aimlapi.com/capabilities/batch-processing.md
