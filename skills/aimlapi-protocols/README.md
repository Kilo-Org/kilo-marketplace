# aimlapi-protocols

Run any chat model through Chat Completions, Responses or Messages on AI/ML API: DeepSeek or Gemini behind the Anthropic SDK or Claude Code, Claude or Qwen behind the Responses API or Codex.

## Install

```bash
gh skill install aimlapi/skills aimlapi-protocols
```

Or install every skill: see the [root README](https://github.com/aimlapi/skills#install).

## What it covers

- Which models serve which protocol (`type`, `translatedFrom` in the catalogue)
- What a translated Responses route does not keep: `previous_response_id`, `background`, stored responses
- Returning thinking, reasoning items and tool-call ids unchanged across turns
- Thinking defaults, hosted tools, prompt cache and usage on translated routes

The agent reads [SKILL.md](SKILL.md).

## Requirements

`AIMLAPI_API_KEY`.
