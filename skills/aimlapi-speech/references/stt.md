# Speech-to-text details

Transcription is asynchronous: `POST /v1/stt/create` answers at once with `{"generation_id": "…", "status": "queued"}`, and `GET /v1/stt/<generation_id>` returns the result when the job is done.

## Sending the audio

Exactly one of a URL or a file. Both, or neither, is `400` ("One of url or audio is required", "Only one of url or audio can be provided").

| Audio is | Request | Body |
| -------- | ------- | ---- |
| at a public URL | `Content-Type: application/json` | `{"model": "…", "url": "https://…", …other fields}` |
| a local file | `multipart/form-data` | a `model` field, the file in the model's file field, other fields as form fields |

The file field name differs per model. Read it from `info.docsJson`: the request property with `"format": "binary"`.

| Family (id prefix), 2026-11-23 | File field |
| ------------------------------ | ---------- |
| `openai/` | `file` |
| `deepgram/`, `aai/`, `elevenlabs/`, `google/` | `audio` |

Sending the file under the other name is `400` with `details[].reason` "One of url or file is required" (or "… url or audio …"): the message names the field the model expects. `speech.py stt --file` reads the field from the schema; `--field` overrides it.

In a multipart upload every form field is text. In sandbox mode, `true`/`false` passed for boolean fields (`smart_format`, `diarize`), and a JSON array passed for `keyterm`, which also accepts a string; a number sent as text (`temperature=0.2` on `openai/gpt-4o-mini-transcribe`) was refused with "Expected number, received string". When you need a numeric parameter, put the audio at a URL and send JSON.

Size: some schemas state a limit in the file field's description (for example "Up to 20 MB"). For long recordings prefer a URL to an upload.

## Polling

| `status` | Meaning |
| -------- | ------- |
| `queued`, `generating` | keep polling, every 5 to 15 s |
| `completed` | `result` holds the transcript |
| `error` | the job failed; `error` is `{"name", "message"}` |

- A poll for an unknown id, or for a result past its retention, is `404` "Inference not found". The docs keep transcripts for 1 hour after creation (sandbox: 1 hour too): save the result when it arrives.
- `429` and `5xx` on a poll are transient: wait and poll again. Never resubmit: a second submit is a second billed job.
- Instead of polling, add `"webhook_url": "https://…"` to the submit (not in sandbox) and get a signed event when the job ends: `aimlapi-webhooks`.

## The transcript in `result`

With an API key, `result` is what the provider returned, so its shape depends on the model:

| Family | Transcript | Also there (when asked for) |
| ------ | ---------- | --------------------------- |
| `deepgram/` | `result.results.channels[0].alternatives[0].transcript` | `words[]` with `start`, `end`, `confidence`, `punctuated_word`; `paragraphs`; `metadata.duration` |
| `aai/` | `result.text` | `words[]`, `utterances[]` with `speaker`, `chapters`, `summary`, `entities` |
| `openai/` | `result.text` | `usage` |
| `elevenlabs/`, `google/` | `result.text` | `words[]` (with timings or speaker labels on) |

The published poll schema shows Deepgram's `channels` as an object; the answer seen in sandbox mode has a list. Accept both. The `aai/`, `elevenlabs/` and `google/` rows come from the server code: sandbox mode answers `{"text": …}` for every non-Deepgram model and cannot show their extra fields.

## In your own code

```python
import os
import time
import requests

API = "https://api.aimlapi.com"
HEADERS = {"Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}"}

with open("meeting.mp3", "rb") as f:  # the model's file field: "file" here, "audio" for most others
    job = requests.post(f"{API}/v1/stt/create", headers=HEADERS, timeout=600,
                        data={"model": "openai/gpt-4o-mini-transcribe"},
                        files={"file": ("meeting.mp3", f, "audio/mpeg")}).json()
generation_id = job["generation_id"]  # store it now: after a restart, poll it again, never resubmit

deadline = time.monotonic() + 30 * 60
while True:
    r = requests.get(f"{API}/v1/stt/{generation_id}", headers=HEADERS, timeout=60)
    if r.status_code in (429, 500, 502, 503, 504):
        time.sleep(10)
        continue
    r.raise_for_status()
    state = r.json()
    if state["status"] == "completed":
        result = state["result"]
        if "text" in result:
            text = result["text"]
        else:
            channels = result["results"]["channels"]
            text = (channels[0] if isinstance(channels, list) else channels)["alternatives"][0]["transcript"]
        print(text)
        break
    if state["status"] not in ("queued", "generating"):
        raise RuntimeError(f"transcription {state['status']}: {state.get('error')}")
    if time.monotonic() > deadline:
        raise TimeoutError(f"still {state['status']}; keep {generation_id} and poll later")
    time.sleep(5)
```

With a URL instead of a file: `requests.post(..., json={"model": "deepgram/nova-3", "url": "https://example.com/meeting.mp3"})`.
