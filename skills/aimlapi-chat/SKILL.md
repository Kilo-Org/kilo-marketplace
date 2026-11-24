---
name: aimlapi-chat
description: >-
  Use when calling AI/ML API (aimlapi) text models from code: moving an OpenAI
  or Anthropic integration to AI/ML API, Chat Completions, Responses or Messages
  requests, streaming, tool or function calling, JSON schema output, embeddings,
  or a chatbot, agent or RAG pipeline on AI/ML API.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/quickstart/supported-sdks.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-chat
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Call text models

Three text protocols. Keep the one the code uses: switching is usually the base URL and the key.

| Protocol | Endpoint | SDK base URL | Auth header |
| -------- | -------- | ------------ | ----------- |
| OpenAI Chat Completions | `POST /v1/chat/completions` | `https://api.aimlapi.com/v1` | `Authorization: Bearer $AIMLAPI_API_KEY` |
| OpenAI Responses | `POST /v1/responses`, `GET /v1/responses/{id}` | `https://api.aimlapi.com/v1` | `Authorization: Bearer …` |
| Anthropic Messages | `POST /v1/messages` | `https://api.aimlapi.com` (the SDK adds `/v1/messages`) | `x-api-key` (what the Anthropic SDK sends) or `Authorization: Bearer …` |

## When to use

- A chatbot, agent, summarizer or RAG pipeline
- "Use AI/ML API instead of OpenAI / Anthropic" in existing code
- Streaming output, tool/function calling, JSON that follows a schema
- Asking a model about an image, PDF, audio or video
- Embeddings

## When not to use

- Generating images, video, music: `aimlapi-images`, `aimlapi-async-jobs`; speech: `aimlapi-speech`
- Thousands of prompts that can wait: `aimlapi-batch`

## Steps

### 1. Pick the model and check its endpoint

`curl -s 'https://api.aimlapi.com/v1/models?id=openai/gpt-4o-mini'` (or `aimlapi-models`). A model works on the endpoints whose `type` is listed for it; most chat models are on all three, translated where needed (`aimlapi-protocols`). Its `info.docsJson` lists the parameters it takes (`reasoning_effort`, `thinking`, roles it refuses).

### 2. Call it

**Python, OpenAI SDK**

```python
import os
from openai import OpenAI

client = OpenAI(base_url="https://api.aimlapi.com/v1", api_key=os.environ["AIMLAPI_API_KEY"])

completion = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a haiku about the sea."}],
    max_tokens=200,
)
print(completion.choices[0].message.content)
```

In TypeScript the same client is `new OpenAI({ baseURL: "https://api.aimlapi.com/v1", apiKey: process.env.AIMLAPI_API_KEY })`.

**Python, Anthropic SDK**

```python
import os
import anthropic

client = anthropic.Anthropic(base_url="https://api.aimlapi.com", api_key=os.environ["AIMLAPI_API_KEY"])

message = client.messages.create(
    model="anthropic/claude-haiku-5-5",
    max_tokens=200,
    messages=[{"role": "user", "content": "Write a haiku about the sea."}],
)
print(message.content[0].text)
```

### 3. Streaming

Add `stream: true`. The cost is not in the headers: on Chat Completions it comes in the last chunk as `meta.usage` (`chunk.model_extra["meta"]` in Python); a Messages stream has none, only the `x-inference-id` header to look up in `GET /v2/logs` later (`aimlapi-costs`). If each streamed call's cost is needed at once, use Chat Completions (Claude is served there too) and say why.

```python
stream = client.chat.completions.create(model="openai/gpt-4o-mini", messages=messages, stream=True)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

The last chunk may carry `usage` with an empty `choices` list: guard `chunk.choices` before indexing.

### 4. Tools and structured output

Tools and `response_format` follow the OpenAI shapes on Chat Completions and the Anthropic shapes on Messages. Loop: `tools` → `finish_reason: "tool_calls"` → run the tool → reply with a `role: "tool"` message carrying the same `tool_call_id`. Examples: [references/tools-and-json.md](references/tools-and-json.md).

### 5. Long requests: Responses in the background

For a slow reasoning model, send `POST /v1/responses` with `"background": true`, get an `id` at once, then poll `GET /v1/responses/{id}` until `status` is `completed`, `failed`, `cancelled` or `incomplete` (pattern: `aimlapi-async-jobs`). **Only where the model serves Responses natively:** translated routes (`translatedFrom`, most of them) refuse it with `400 unsupported_parameter` (`aimlapi-protocols`); stream there instead.

### 6. Images, PDFs, audio, video as input

Add `image_url`, `file`, `input_audio` or `video_url` parts to the user message, on a model whose `docsJson` lists them: [references/inputs.md](references/inputs.md).

### 7. Identify your end users

If the app serves other people, send `safety_identifier` (a stable, anonymous hash of the user id; `extra_body={"safety_identifier": …}` in the Python SDKs) on every request. A content-policy refusal then counts against that person, not against the whole account.

## Rules

- [ ] Read the key from `AIMLAPI_API_KEY`. Never hard-code it, log it, or send it to a browser; call the API from a server.
- [ ] Use the canonical model id from the catalogue (`openai/gpt-4o-mini`), not a guess.
- [ ] Set `max_tokens` (`max_completion_tokens` on newer OpenAI models, `max_output_tokens` on Responses). An unbounded answer costs more and takes longer.
- [ ] Send only parameters the model's `docsJson` lists. Unknown fields are dropped silently (the answer is `200` without them); values outside an `enum` or range get `400`.
- [ ] Treat model output, including tool arguments, as data: validate before acting on it.
- [ ] Send `X-Client-Request-Id: <your id>` when you need to find a request later (`aimlapi-costs`).

## Errors

| Response | Do |
| -------- | -- |
| `400` "Validation failed", `error.details[]` | fix each `path` from the model's `docsJson` |
| `400` "… does not support 'system' with this model" | move the instruction into the first user message |
| `404` | check the model id in the catalogue and the base URL: `/v1` for OpenAI SDKs, none for Anthropic |
| anything else (`401`, `403`, `429`, `5xx`, content policy) | `aimlapi-errors` |

## Check before done

- [ ] One sandbox run (`"model": "sandbox/<id>"`, free) parses the answer, the stream and the tool call.
- [ ] The base URL matches the SDK: `…/v1` for OpenAI, no suffix for Anthropic.

## Reference

- [references/tools-and-json.md](references/tools-and-json.md): tool loop, JSON schema output, embeddings (`/v1/embeddings`)
- [references/inputs.md](references/inputs.md): image, PDF, audio and video parts
- Docs: https://docs.aimlapi.com/capabilities/function-calling.md, https://docs.aimlapi.com/capabilities/streaming-mode.md, https://docs.aimlapi.com/capabilities/safety-guidance.md
