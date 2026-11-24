# Catalogue response shapes

Source: https://docs.aimlapi.com/api-references/service-endpoints/complete-model-list.md

## `GET /v1/models`

```json
{
  "object": "list",
  "data": [
    {
      "id": "openai/gpt-4o-mini",
      "info": {
        "releasedAt": "2024-07-18",
        "name": "GPT-4o Mini",
        "developer": "Open AI",
        "description": "GPT-4o Mini: Cost-efficient, advanced model for diverse AI applications.",
        "contextLength": 128000,
        "url": "https://aimlapi.com/models/chat-gpt-4o-mini",
        "docsUrl": "https://docs.aimlapi.com/api-references/text-models-llm/openai/gpt-4o-mini",
        "docsJson": "https://api.aimlapi.com/docs-json?model=openai%2Fgpt-4o-mini&endpoint=openai%2Fchat-completions"
      },
      "type": "openai/chat-completions",
      "aliases": ["gpt-4o-mini"],
      "tags": ["playground:chat", "tier:tier_2"]
    }
  ]
}
```

| Field | Always present | Note |
| ----- | -------------- | ---- |
| `id`, `aliases`, `type`, `info.name`, `info.developer`, `tags` | yes | |
| `info.contextLength`, `info.outputMax` | text models only, not always both | tokens |
| `info.docsJson` | almost always | OpenAPI for this model on this endpoint |
| `info.docsUrl` | often | human docs page |
| `modalities` | with `include=modalities` | `{input: [...], output: [...]}` |
| `capabilities` | with `include=capabilities` | e.g. `image_to_video` |
| `pricing` | with `include=pricing` | see SKILL.md § Read the price |

The response carries an `ETag`; send `If-None-Match` to get `304` when nothing changed.

## `GET /model/{id}`

The same projection for one model, wrapped as `{"object": "model", "data": {…}}`, or `404`. Takes `include` and `details`. A `deprecated` model that has a shutdown date is dropped from `GET /v1/models` but still answers here with its sunset dates.

## `GET /v1/models/deprecations`

No key required. Filters: `status` (`deprecated`, `superseded`, `withdrawn`; repeat or comma-separate) and `since` (`YYYY-MM-DD`).

```json
{
  "object": "list",
  "generated_at": "2026-11-12T10:00:00Z",
  "data": [
    {
      "id": "provider/old-model",
      "aliases": ["old-model"],
      "status": "withdrawn",
      "deprecated_at": "2026-09-01",
      "shutdown_at": "2026-10-01",
      "replaced_by": "provider/new-model",
      "reason": "provider_delisted"
    }
  ]
}
```

Match the id you integrated against both `id` and `aliases`.

## `docsJson`

An OpenAPI 3.0 document with one path and one method. The request schema is at `paths.<path>.<method>.requestBody.content["application/json"].schema`; read `properties`, `required`, `enum`, `minimum`, `maximum`, `default`. Some schemas use `anyOf`/`oneOf` for alternative input shapes (text-to-video vs image-to-video).

## Filters of `GET /v1/models`

| Parameter | Keeps models that | Example |
| --------- | ----------------- | ------- |
| `id` | have this id or alias | `?id=openai/gpt-4o-mini` |
| `type` | are served through this endpoint type | `?type=openai/chat-completions` |
| `tags` | carry this tag | `?tags=playground:video` |
| `output_modalities`, `input_modalities`, `modalities` | produce / accept this modality | `?output_modalities=video` |
| `capabilities` | declare this capability | `?capabilities=image_to_video` |
| `include` | (no filter) attaches `pricing`, `modalities`, `capabilities` or `all` | `?include=pricing` |

Values are case-insensitive; comma-separated and repeated values merge.

## Pricing units

With `include=pricing`, `pricing.kind` decides the shape:

| `kind` | Shape |
| ------ | ----- |
| `fixed` | `units: [{type, name, content, measure, origin, author, price, per, tag?}]` |
| `variants` | `dimensions: [...]`, `variants: [{when: {...}, price, unit, per}]` |
| `variable` | no quote before the request |

`thresholds`, when it has more than one entry, is a list of context-size bands: `[{"from": 0, "units": […]}, {"from": 100000, "units": […]}]`. The whole request is priced at the band with the highest `from` not above its size in tokens. Depending on the model, the size is the prompt (cached tokens included) or every priced token, output included; the catalogue does not say which, so estimate with prompt plus `max_tokens`. Units missing from the bands (server-tool calls) cost the same in every band. `pricing.batch` has the same shape.

A `fixed` unit is identified by `name` (what is counted: `token`, `call`, `second`, …), `origin` and `author`:

| `origin` / `author` | Means |
| ------------------- | ----- |
| `provided` / `user` | input tokens you send |
| `cached` / `user` | input read from the prompt cache |
| `cache_write`, `cache_write_1h` / `user` | input written to the cache |
| `generated` / `model` | output tokens |
| `generated` / `tool`, with `tag.name` | a server tool call such as `web_search` |

`price` is the charge for `per` units. `per` is `1000000` for most token rates, `1000` for some, `1` for per-second, per-call and per-megapixel rates. A model that can run in a batch also carries `pricing.batch` with its own units.
