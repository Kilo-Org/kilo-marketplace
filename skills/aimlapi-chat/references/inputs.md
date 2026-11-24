# Images, PDFs, audio and video as input

A chat model can read more than text when its schema says so. Find the models with the catalogue filter, then check the exact part type in the model's `info.docsJson` (`aimlapi-models`): a model that does not list a part type refuses it with `400`.

```bash
curl -s 'https://api.aimlapi.com/v1/models?type=openai/chat-completions&input_modalities=image'   # also audio, video
```

Generating images, video or speech is a different job: `aimlapi-images`, `aimlapi-async-jobs`.

## Chat Completions (OpenAI shapes)

Put the parts in the `content` array of a user message, next to a `text` part.

| Input | Part | Value |
| ----- | ---- | ----- |
| Image | `{"type": "image_url", "image_url": {"url": …, "detail": "auto"}}` | a public HTTPS URL or `data:image/png;base64,…` |
| PDF | `{"type": "file", "file": {"filename": "report.pdf", "file_data": …}}` | `data:application/pdf;base64,…` |
| Audio | `{"type": "input_audio", "input_audio": {"data": …, "format": "mp3"}}` | a URL, base64, or `data:audio/…`; `format` such as `wav`, `mp3`, `audio/ogg` |
| Video | `{"type": "video_url", "video_url": {"url": …}}` | a public HTTPS URL or `data:video/mp4;base64,…` |

```python
import base64

with open("chart.png", "rb") as f:
    image = "data:image/png;base64," + base64.b64encode(f.read()).decode()

completion = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": [
        {"type": "text", "text": "What does this chart show?"},
        {"type": "image_url", "image_url": {"url": image}},
    ]}],
    max_tokens=300,
)
```

Audio and video work only on the models that take them (Gemini Flash models, the Qwen Omni models, `openai/gpt-audio` at the time of writing; the filter above is the current list).

## Messages (Anthropic shapes)

| Input | Block |
| ----- | ----- |
| Image | `{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "<base64>"}}`, or `"source": {"type": "url", "url": "https://…"}` |
| PDF or text file | `{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "<base64>"}}`, or a `url` source |

## Size and cost

- Images, PDF pages and audio count as input: as tokens, or as a unit of their own in the model's `pricing.units`. A large image or a long PDF can cost more than the text around it; resize images to what the task needs.
- A data URL makes the request body large. For big files, a public HTTPS URL is lighter, if the content may be fetched by the provider.
- Test the request shape for free in sandbox mode (`aimlapi-sandbox`): it checks the parts against the model's schema.
