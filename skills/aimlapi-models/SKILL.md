---
name: aimlapi-models
description: >-
  Use when choosing an AI/ML API (aimlapi) model for a task, turning an informal
  model name into an exact id, comparing models or prices, checking which
  parameters a model accepts, or when a model id returns 404 or looks retired.
compatibility: Needs network access to api.aimlapi.com. No API key required.
metadata:
  version: 1.0.5
  docs: >-
    https://docs.aimlapi.com/api-references/service-endpoints/complete-model-list.md
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-models
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Choose an AI/ML API model

The catalogue changes every week: new models, aliases, retirements, prices. **Never take a model id, a parameter or a price from memory.** Read them from the API when you need them. None of these calls needs a key.

## When to use

- "Which model should I use for …", "what models do you have for video"
- "What does `<model>` cost", "compare these two", "which is fastest"
- "Use nano banana / sonnet / veo": an informal name to turn into an id
- "What parameters does `<model>` take", "is `duration: 12` allowed"
- "`<model>` returns 404 now", "is it being retired"

## Steps

### 1. Narrow the catalogue on the server

```bash
curl -s 'https://api.aimlapi.com/v1/models?output_modalities=video&capabilities=image_to_video&include=pricing'
python3 scripts/models.py search "veo"
python3 scripts/models.py list --type openai/chat-completions --sort newest --limit 20
```

Filters: `id` (id or alias), `type`, `tags`, `input_modalities`, `output_modalities`, `capabilities`; `include=pricing,modalities,capabilities` adds sections. Values of one parameter are OR, parameters are AND. A typo in `include` is ignored. Full shapes: [references/catalogue.md](references/catalogue.md).

### 2. Match the model's `type` to the endpoint

A model served through several endpoints appears once per `type`; `translatedFrom` marks a route the API translates (`aimlapi-protocols`).

| `type` | Endpoint | Skill |
| ------ | -------- | ----- |
| `openai/chat-completions`, `openai/responses/submit`, `anthropic/messages`, `openai/embeddings` | `/v1/chat/completions`, `/v1/responses`, `/v1/messages`, `/v1/embeddings` | `aimlapi-chat` |
| `openai/image-generations`, `openai/image-editing` | `/v1/images/generations`, `/v1/images/edits` | `aimlapi-images` |
| `internal/video-generations/submit`, `internal/audio-generations/submit` | `/v2/video/generations`, `/v2/generate/audio` | `aimlapi-async-jobs` |
| `internal/speech-to-text/submit`, `internal/text-to-speech` | `/v1/stt/create`, `/v1/tts` | `aimlapi-speech` |
| `internal/decisions` | `/v1/decisions` | `aimlapi-decisions` |
| `anthropic/batches*`, or any model with `pricing.batch` | `/v1/batches` | `aimlapi-batch` |

### 3. Read the parameters this model accepts

`info.docsJson` is an OpenAPI document for **this model on this endpoint**: enums, ranges, required fields, defaults. Models of one type differ (one video model takes `duration` 4 to 8, another 5 or 10), so read the exact model's schema. Features such as sound are request parameters there (e.g. `generate_audio`), not catalogue filters.

```bash
python3 scripts/models.py params google/veo-3.1-lite-generate-001
```

### 4. Read the price

```bash
python3 scripts/models.py price anthropic/claude-haiku-5-5 --tokens 150000
```

**Long prompts can cost several times more per token.** Many text models have `pricing.thresholds`: bands from N tokens of context, and the whole request is priced at one band (Haiku 5.5: 5× from 100,000 tokens). Quote the band for prompt plus `max_tokens` (the catalogue does not say which tokens count), and both bands near a boundary. `units` alone is only the lowest band.

Read `pricing.kind` first: `fixed` has one rate per unit, `variants` a rate per parameter combination (pick the one whose `when` keys, named after request parameters, match; a per-second rate times `duration` is the clip price), `variable` cannot be quoted before the call (read the cost afterwards, `aimlapi-costs`). **Always divide `price` by `per`** (`1000000` for most token rates, `1` for per-second or per-call rates). A model that can run in a batch also has `pricing.batch`, with its own bands (`--batch`). Unit fields: [references/catalogue.md](references/catalogue.md).

### 5. Compare speed, when it matters

```bash
python3 scripts/models.py speed openai/gpt-4o-mini google/gemini-2.5-flash-lite
```

`GET /models/metrics` (no key): live time to first token, tokens per second and duration, p50 to p99, over the last few minutes. For `tps` higher is faster; an absent model has no recent data. Details: [references/metrics.md](references/metrics.md).

### 6. Check that the model still works

```bash
python3 scripts/models.py status gpt-4o
```

The deprecation feed (`GET /v1/models/deprecations`, no key) says `deprecated` (still serving, retirement announced), `superseded` (old id resolves to `replaced_by`) or `withdrawn` (`404`; move to `replaced_by`). A name in neither the catalogue nor the feed never existed.

## Rules

- [ ] Write the canonical `id` (`anthropic/claude-haiku-5-5`) in code; aliases work but are easy to confuse.
- [ ] Never hard-code prices, context lengths or parameter lists into the user's code or docs. Read them at run time.
- [ ] For quality-sensitive work, shortlist two or three models by type, capability and price, and let the user compare live answers. Sandbox answers are fixed and say nothing about quality.

## Errors

| Response | Meaning | Do |
| -------- | ------- | -- |
| `404`, model id in the message | unknown or withdrawn model | step 6, then step 1 |
| `400` "Validation failed", `error.details[]` | a parameter the schema rejects | step 3 |
| `403 model_not_allowed` | the key is limited to other models | allow the model on the key, or pick an allowed one |
| empty `data` | nothing matches, or a typo in a filter | loosen the filter |

## Check before done

- [ ] `GET /v1/models?id=<id>` lists the id with the `type` of the endpoint you call.
- [ ] Every parameter you send is in that model's `docsJson`, with an allowed value.
- [ ] Any price you quoted came from `include=pricing` just now, from the band for the request's size, divided by `per`.

## Reference

- [references/catalogue.md](references/catalogue.md): catalogue, single-model lookup, deprecation feed, pricing units
- [references/metrics.md](references/metrics.md): live latency and throughput per model
- Docs: https://docs.aimlapi.com/api-references/service-endpoints/complete-model-list.md
