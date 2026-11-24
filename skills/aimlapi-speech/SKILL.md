---
name: aimlapi-speech
description: >-
  Use when turning text into speech or transcribing audio through AI/ML API
  (aimlapi): read text aloud, voice-over or narration, an MP3 of a script,
  transcribe a meeting, call, podcast or local audio file, subtitles from
  speech, or when a text-to-speech answer is not JSON or a transcription never
  finishes.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment. Script needs python3 3.9+.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/api-references/speech-models.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-speech
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Speech: text-to-speech and speech-to-text

Text-to-speech is one synchronous call, `POST /v1/tts`. Speech-to-text is a job: `POST /v1/stt/create` answers with a `generation_id`, and you poll `GET /v1/stt/<generation_id>` for the transcript.

## When to use

- "Read this text aloud", "make a voice-over", "give me an MP3 of this script"
- "Transcribe this meeting / call / podcast", "subtitles from this audio", an audio file on disk
- A TTS response that breaks `response.json()`, or a transcription that stays `generating`

## Steps

### 1. Pick the model and read its parameters

```bash
curl -s 'https://api.aimlapi.com/v1/models?type=internal/text-to-speech&include=pricing'
curl -s 'https://api.aimlapi.com/v1/models?type=internal/speech-to-text/submit&include=pricing'
```

Then read the model's `info.docsJson` (with `aimlapi-models`: `models.py params openai/tts-1`). Field names change between families: the TTS text is `script` for VibeVoice, the voice is `voice`, `voice_id` or `voice_setting`, the STT file field is `file` or `audio`. Maps: [references/tts.md](references/tts.md), [references/stt.md](references/stt.md).

### 2. Text-to-speech

```bash
python3 scripts/speech.py tts --out speech.mp3 --body '{
  "model": "openai/tts-1",
  "text": "Your order has shipped.",
  "voice": "alloy",
  "response_format": "mp3"
}'
```

The answer is JSON with a link:

```json
{ "audio": { "url": "https://…/speech.mp3" }, "meta": { "usage": { "credits_used": 0, "usd_spent": 0 } } }
```

- Download `audio.url`; the link does not last. The published schema shows `audio` as a string, so accept that too.
- With `"stream": true` the body is the audio itself, labelled `audio/wav` whatever the format, with no cost in it (`GET /v2/logs` has it).
- Some models default `stream` to `true` (Deepgram and ElevenLabs on 2026-11-23): leave it out and you get bytes. Read `stream` in the schema; send `"stream": false` for JSON.

### 3. Speech-to-text

```bash
python3 scripts/speech.py stt --model deepgram/nova-3 --url https://example.com/meeting.mp3
python3 scripts/speech.py stt --model openai/gpt-4o-mini-transcribe --file meeting.mp3 --out answer.json
```

The script submits (JSON with `url`, or a multipart upload in the file field the model's schema names), polls, and prints the transcript; `--out` keeps the whole answer; more fields go in `--body '{"language": "en"}'`.

The final poll is `{"generation_id": …, "status": "completed", "result": …}`. `result` is the provider's own answer: `result.text` for most models, `result.results.channels[0].alternatives[0].transcript` for Deepgram. Shapes and a full Python loop: [references/stt.md](references/stt.md).

Instead of polling, add `"webhook_url"` to the submit (not in sandbox): `aimlapi-webhooks`.

### 4. Exit codes of `speech.py`

`0` done; `1` job failed (`status: "error"`) or no audio in the answer; `2` still running at `--timeout` or polls kept failing (resume: `python3 scripts/speech.py poll <generation_id>`); `3` HTTP or network error; `4` audio generated and charged but not saved (fetch the printed URL again). `--sandbox` makes any command free.

## Rules

- [ ] Send only fields from the model's schema, with its names. OpenAI's `input` is not the TTS text field here: `input` alone is `400`.
- [ ] TTS: check `Content-Type` before parsing. `application/json` carries `audio.url`; anything else is the audio.
- [ ] TTS text has a per-model `maxLength`; split long text at sentence ends.
- [ ] STT: store the `generation_id` as soon as the submit answers. After a restart, poll it; never resubmit (a second, billed job).
- [ ] STT: poll every 5 to 15 s with a deadline; `queued` and `generating` mean wait, `error` is final. Save the result: transcripts are kept for one hour.
- [ ] A multipart upload sends every field as text: booleans pass, but a number (`temperature`) was refused in sandbox mode. For numeric fields, send the audio by `url` in JSON.
- [ ] Quote prices from `pricing` in the catalogue (per character, token or second, depending on the model), never from memory.
- [ ] No API key in browser code or on audio downloads.

## Errors

| When | Response | Do |
| ---- | -------- | -- |
| TTS or STT submit | `400` "Validation failed", `error.details[]` | fix each `path` from `docsJson`; "One of url or file is required" names the file field the model wants |
| TTS `stream: true`, sandbox | `400 sandbox_unsupported` | test streaming with a small live call |
| TTS | `200` but `response.json()` fails | it is the binary answer: send `"stream": false`, or save the bytes |
| any | `403`, `429`, `5xx` | `aimlapi-errors`; for `429` wait `Retry-After` |
| poll | `404` "Inference not found" | wrong id, or the result is older than its retention |
| poll | `status: "error"` with `error.message` | the job failed; fix the audio or try another model |

## Check before done

- [ ] `python3 scripts/speech.py tts --sandbox --out t.mp3 --body '…'` and `python3 scripts/speech.py stt --sandbox --model <id> --file <audio>` succeed with your real body and model (free, checked against the schema).
- [ ] TTS code handles both answer shapes or sets `stream`; STT code stores the `generation_id` and reads the transcript for its model family.

## Reference

- [references/tts.md](references/tts.md): answer shapes, `stream` defaults, fields per family
- [references/stt.md](references/stt.md): uploads, statuses, transcript shapes per family
- Speech model docs: https://docs.aimlapi.com/api-references/speech-models.md
