---
name: aimlapi-async-jobs
description: >-
  Use when generating video or music, or running a background Responses request
  through AI/ML API (aimlapi), or when such a job looks stuck, never finishes,
  or its result URL has expired.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment. Script needs python3 3.9+.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/api-references/video-models.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-async-jobs
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Run long jobs: video, music, background responses

These jobs take seconds to many minutes: the submit answers at once with an id, and you poll for the result. Tell the user the job was submitted, so the wait does not look like a hang.

| Job | Submit | Poll | Result in the final poll |
| --- | ------ | ---- | ------------------------ |
| Video | `POST /v2/video/generations` → `{id, status}` | `GET /v2/video/generations?id=<id>` | `video.url` |
| Music | `POST /v2/generate/audio` → `{id, status}` | `GET /v2/generate/audio?id=<id>` | `audio_file.url` |
| Background response | `POST /v1/responses` with `"background": true` → `{id, status}` | `GET /v1/responses/<id>` | `output` |

The poll query parameter is `id`. Older examples use `generation_id`; it still works but is deprecated.

`background: true` works only where the model serves Responses natively. Most `/v1/responses` routes are translated (`translatedFrom` in the catalogue) and refuse it with `400 unsupported_parameter` (`aimlapi-protocols`).

Speech (text-to-speech, speech-to-text) has its own skill: `aimlapi-speech`.

## When to use

- "Generate a video of …", "animate this image", "make a 5-second clip"
- "Generate a song or background music"
- A slow reasoning request (background Responses)

## Steps

### 1. Pick the model and read its parameters

Parameters differ per model (`duration` may be `[4, 6, 8]` for one video model and `[5, 10]` for another), so read the exact model's schema:

```bash
curl -s 'https://api.aimlapi.com/v1/models?type=internal/video-generations/submit&include=pricing'
```

and its `info.docsJson` (`aimlapi-models`). Video prices depend on `resolution`, `duration` and audio: quote them from `pricing.variants` before an expensive job.

### 2. Submit and wait

```bash
python3 scripts/job.py submit video --download clip.mp4 --body '{
  "model": "google/veo-3.1-lite-generate-001",
  "prompt": "A paper boat drifting down a rainy street, close-up",
  "duration": 4,
  "resolution": "720P"
}'
```

It submits, polls at a sensible interval, prints the final answer, and saves the file. `--sandbox` runs the same flow for free with a placeholder video (`aimlapi-sandbox`). Exit codes: `0` completed (or `incomplete` with partial output), `1` failed, `2` still running at `--timeout` or after repeated failed polls (the job continues; resume with `job.py poll video <id>`), `3` HTTP error, `4` completed and charged but the download failed (fetch the URL again).

In the user's own code, the same loop:

```python
import os
import time
import requests

API = "https://api.aimlapi.com"
HEADERS = {"Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}"}

job = requests.post(f"{API}/v2/video/generations", headers=HEADERS, timeout=120, json={
    "model": "google/veo-3.1-lite-generate-001",
    "prompt": "A paper boat drifting down a rainy street, close-up",
}).json()

deadline = time.monotonic() + 30 * 60
while True:
    state = requests.get(f"{API}/v2/video/generations", params={"id": job["id"]}, headers=HEADERS, timeout=60).json()
    if state["status"] == "completed":
        print(state["video"]["url"])
        break
    if state["status"] not in ("queued", "generating", "waiting", "active"):
        raise RuntimeError(f"generation {state['status']}: {state.get('error')}")
    if time.monotonic() > deadline:
        raise TimeoutError(f"still {state['status']}; keep the id {job['id']} and poll later")
    time.sleep(15)
```

### 3. Keep the result

Result URLs are temporary: download the file and store it where the user's app serves it from.

### 4. Or get a webhook instead of polling

Add `"webhook_url": "https://…"` to the submit body (not in sandbox), and the result arrives as a signed event when the job ends: `aimlapi-webhooks`. Keep the poll as a fallback.

## Rules

- [ ] Store the job id as soon as the submit answers; after a restart poll it, never resubmit (a second, billed job). Also send `X-Client-Request-Id` on the submit: if the process died before storing the id, find it in `GET /v2/logs` (`inference_id` is the job id; shape: `aimlapi-costs` references/logs.md; the row may appear only after the job ends).
- [ ] Poll every 5 to 15 s, with a deadline of tens of minutes; past it, keep the id: the job may still finish.
- [ ] Any status other than `queued`, `pending`, `generating`, `waiting`, `active`, `processing`, `in_progress` is final. `completed` carries the result; `incomplete` (Responses) partial output and `incomplete_details.reason`. On a failure, show `error` to the user.
- [ ] Send only parameters from the model's schema. A wrong `duration` is a `400` at submit, not a failed job.
- [ ] Cost: a failed generation is not charged. The charge lands after `completed`; read it from `meta.usage` in the final poll or from `GET /v2/logs` (`aimlapi-costs`).

## Errors

| When | Response | Do |
| ---- | -------- | -- |
| submit | `400` "Validation failed", `error.details[]` | fix each `path` from `docsJson` |
| submit | `403`, `429`, `5xx` | `aimlapi-errors`; for `429` wait `Retry-After`, then submit once |
| poll | `404` | wrong id, wrong job type's endpoint, or the result has expired |
| poll | `status: "error"` or `"failed"` with `error` | the job failed and was not charged; fix the input or try another model |
| poll | still `generating` past your deadline | keep the id, poll later; do not resubmit |

## Check before done

- [ ] `python3 scripts/job.py submit <kind> --sandbox --body '…'` completes with your real body (free; validated against the schema).
- [ ] Your code stores the job id before polling and downloads the result file.

## Reference

- Video models: https://docs.aimlapi.com/api-references/video-models.md
- Music: https://docs.aimlapi.com/api-references/music-models.md
- Speech: `aimlapi-speech`
