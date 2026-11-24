---
name: aimlapi-images
description: >-
  Use when generating or editing images through AI/ML API (aimlapi):
  text-to-image, image editing, reference images, logos or product shots, or
  when an image request is refused for its parameters.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/api-references/image-models.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-images
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Generate and edit images

Image generation is synchronous: one request, the answer holds the images. The catch is that **every image model has its own parameters**. FLUX takes `image_size` and `num_images`; OpenAI's image models take `size` and `n`; others take `aspect_ratio` or `image_urls`. Read the schema of the model you call; do not carry parameters over from another model.

## When to use

- "Generate an image of …", "make a logo / thumbnail / product shot"
- "Edit this image", "put this product on a beach", "combine these two photos"

## Steps

### 1. Pick the model and read its parameters

```bash
curl -s 'https://api.aimlapi.com/v1/models?type=openai/image-generations&include=pricing'
```

Then read the model's `info.docsJson` for its parameters. With the `aimlapi-models` skill installed, `models.py params flux/schnell` prints them. Models of type `openai/image-editing` also serve `POST /v1/images/edits`.

### 2. Generate

```bash
curl -sS https://api.aimlapi.com/v1/images/generations \
  -H "Authorization: Bearer $AIMLAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "flux/schnell", "prompt": "A lighthouse at dawn, watercolor", "image_size": "landscape_16_9", "num_images": 1}'
```

```python
import os
import requests

resp = requests.post(
    "https://api.aimlapi.com/v1/images/generations",
    headers={"Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}"},
    json={"model": "flux/schnell", "prompt": "A lighthouse at dawn, watercolor"},
    timeout=900,
)
resp.raise_for_status()
for image in resp.json()["data"]:
    print(image["url"])
```

Answer:

```json
{
  "data": [{ "url": "https://cdn.aimlapi.com/…/image.png", "b64_json": null }],
  "meta": { "usage": { "credits_used": 7800, "usd_spent": 0.0039 } }
}
```

- `data[].url` is a link to the file; download it if the user needs to keep it, links are not permanent. Some models return `b64_json` instead or as well; handle both.
- `meta.usage` is the cost of this call (`aimlapi-costs`); the OpenAI SDK keeps it in `r.model_extra["meta"]`.
- With the OpenAI SDK, `client.images.generate(...)` works for OpenAI image models. For other models, pass their own fields through `extra_body={...}` (Python) or call the endpoint over HTTP; `n` and `size` are not translated to `num_images` and `image_size`.

### 3. Edit or use reference images

Two ways, depending on the model's schema:

| Model schema has | Call | How the image goes in |
| ---------------- | ---- | --------------------- |
| `image_urls`, `image_url` or similar on `/v1/images/generations` | `POST /v1/images/generations` | public HTTPS URLs (or data URLs where the schema allows) |
| type `openai/image-editing` | `POST /v1/images/edits` | a multipart file upload, as with OpenAI: `client.images.edit(model=…, image=open("in.png", "rb"), prompt=…)` |

## Rules

- [ ] Send only fields from the model's schema. Unknown fields are dropped silently: the call answers `200` with the defaults (`n` and `size` on flux/schnell give one default image). Values outside an `enum`, or a custom size outside its `minimum`/`maximum` (flux/schnell: 64 to 1536 per side), return `400`; prefer a preset.
- [ ] Set a client timeout well above a minute; large or high-quality images can take a while. Do not set a short timeout and retry: each retry is a new, billed generation.
- [ ] Store the files you need. Do not hot-link `cdn.aimlapi.com` URLs from a product page.
- [ ] Do not put an API key in browser code to call this endpoint; proxy through your server.
- [ ] For apps that serve other people, send `safety_identifier` on every request (see `aimlapi-errors` § Content policy).

## Errors

| Response | Meaning | Do |
| -------- | ------- | -- |
| `400` "Validation failed", `error.details[]` names `path` and `reason` | a value the model does not accept, or a missing required field | read `docsJson`, fix that field |
| `400` `content_policy_violation` | the provider refused the prompt or image | change the content; do not resend it to another model |
| `403` "You've run out of credits" | balance exhausted | the user tops up |
| `404` | unknown model, or a generation model on `/v1/images/edits` | check the model's `type` |
| `5xx` / timeout | provider failure | retry once or twice with backoff; check `GET /v2/logs` first if you are not sure whether the first call was charged |

## Check before done

- [ ] Run the request once with `"model": "sandbox/<model id>"` (free, `aimlapi-sandbox`): the answer has the live shape with placeholder PNGs.
- [ ] Your code reads `data[].url` and handles `b64_json`.
- [ ] Every parameter you send is in the model's schema.

## Reference

- Image model docs: https://docs.aimlapi.com/api-references/image-models.md
- Getting the image by webhook instead of in the response (some FLUX models): `aimlapi-webhooks`
