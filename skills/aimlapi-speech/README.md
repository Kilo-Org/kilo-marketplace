# aimlapi-speech

Text-to-speech and speech-to-text: synthesize audio, transcribe files and URLs.

## Install

```bash
gh skill install aimlapi/skills aimlapi-speech
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- Text-to-speech: the JSON answer with `audio.url`, the binary answer with `stream: true`, and models that default to streaming
- Speech-to-text: submit by URL or by uploading a local file, poll, and read the transcript for each model family
- A standard-library script with sandbox mode, deadlines and resumable polling

The agent reads [SKILL.md](SKILL.md).

## Requirements

`AIMLAPI_API_KEY`; `python3` for the script.
