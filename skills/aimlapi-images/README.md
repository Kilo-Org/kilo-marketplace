# aimlapi-images

Generate and edit images.

## Install

```bash
gh skill install aimlapi/skills aimlapi-images
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- Each model's own parameters (`num_images`, `image_size`, …) read from its schema, and how to pass them through the OpenAI SDK
- Generation and editing, with results as `url` or `b64_json`

The agent reads [SKILL.md](SKILL.md).

## Requirements

`AIMLAPI_API_KEY`.
