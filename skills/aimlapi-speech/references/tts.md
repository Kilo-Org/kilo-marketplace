# Text-to-speech details

`POST /v1/tts` is synchronous: one request, one answer. What the answer is depends on `stream`.

## The two answer shapes

| Request | Response `Content-Type` | Body | Cost |
| ------- | ----------------------- | ---- | ---- |
| `"stream": false` | `application/json` | `{"audio": {"url": "https://…"}, "meta": {"usage": {"credits_used": …, "usd_spent": …}}}` | `meta.usage` and the `x-aimlapi-usd-spent` header |
| `"stream": true` | `audio/wav` | the audio bytes, written as they are generated | not in the answer; read it from `GET /v2/logs` (`aimlapi-costs`) |

- The published schema (`info.docsJson`, response `200`) shows `audio` as a plain URL string. The live answer, the sandbox answer and the docs examples carry an object: read `audio["url"]`. Code that also accepts a string costs one line and survives either.
- The JSON link is a stored copy of the file and is not permanent: download it if the user needs to keep it.
- The binary answer is labelled `audio/wav` whatever it holds. The bytes follow the format the request asked for (`output_format`, `encoding`, `format`), so MP3 bytes can arrive in a response labelled `audio/wav`. Name the file from the format you requested, or look at the first bytes (`RIFF…WAVE` is WAV, `ID3` or `0xFF 0xFx` is MP3, `OggS` is Ogg). `speech.py tts` does this and warns when the file name does not match.
- A binary answer has already started with `200` when the audio begins, so a failure in the middle shows up as a cut-off file, not an error status. Check the file plays before you use it.

## The `stream` default differs per model

Read `stream` in the model's schema before you call it:

| Schema says | What happens when the request leaves `stream` out | What to send |
| ----------- | ------------------------------------------------- | ------------ |
| `"enum": [false]` | JSON answer | nothing, or `"stream": false` |
| `"default": true` (no enum) | the binary answer: `response.json()` fails | `"stream": false` for JSON, `"stream": true` to stream audio |
| no `stream` property | JSON answer | nothing |

On 2026-11-23 the Deepgram (`deepgram/aura*`) and ElevenLabs models had `"default": true`; the other families allowed only `false`. That changes: check the schema. The "leaves it out gives binary" row comes from the schema and the server code; the sandbox does not show it, because it answers JSON unless the request itself says `"stream": true` (and then refuses with `400 sandbox_unsupported`).

## Fields that differ between model families

Parameters are per model. This table is a map of where to look, taken from the live catalogue on 2026-11-23; read the exact model's `info.docsJson` for the real names, enums and limits.

| Family (id prefix) | Text field | Voice | Output format |
| ------------------ | ---------- | ----- | ------------- |
| `openai/` | `text` | `voice` | `response_format` |
| `elevenlabs/` | `text` | `voice` | `output_format` |
| `deepgram/` | `text` | `voice` | `encoding`, `container`, `sample_rate` |
| `minimax/` | `text` | `voice_setting.voice_id` | `audio_setting` |
| `hume/`, `inworld/` | `text` | `voice` | `format` |
| `alibaba/` | `text` | `voice` | (none) |
| `heygen/` | `text` | `voice_id` | (none) |
| `bytedance/` | `text` | `references[].speaker` | `audio_config.format` |
| `microsoft/`, `vibevoice` | `script` (not `text`) | `speakers` | (none) |

- The input is `text` (or `script`), not OpenAI's `input`: `input` alone gets `400`, `details[].path: "text"`.
- The longest allowed `text` (`maxLength`) ranges from a few hundred characters to hundreds of thousands, depending on the model. Split long text at sentence boundaries and join the files, or pick a model whose limit fits.
- Prices are per character, per token or per second of audio depending on the model: read `pricing` from `GET /v1/models?type=internal/text-to-speech&include=pricing`, never from memory.

## In your own code

```python
import os
import requests

API = "https://api.aimlapi.com"
HEADERS = {"Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}"}

resp = requests.post(f"{API}/v1/tts", headers=HEADERS, timeout=900, json={
    "model": "elevenlabs/eleven_v4",
    "text": "Your order has shipped.",
    "stream": False,  # this model defaults to true, which returns audio bytes instead of JSON
})
resp.raise_for_status()
if resp.headers.get("Content-Type", "").startswith("application/json"):
    audio = resp.json()["audio"]
    url = audio["url"] if isinstance(audio, dict) else audio
    data = requests.get(url, timeout=600).content  # no API key on the download
else:
    data = resp.content  # binary answer
with open("speech.mp3", "wb") as f:
    f.write(data)
```

Streaming to a player: send `"stream": true` (only where the schema allows it), and read the body in chunks (`requests.post(..., stream=True)`, `resp.iter_content()`).
