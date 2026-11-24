---
name: aimlapi-protocols
description: >-
  Use when a model should be called through a protocol it does not natively
  speak on AI/ML API (aimlapi): DeepSeek, Gemini, Qwen, Kimi or GPT through the
  Anthropic Messages API, the Anthropic SDK or Claude Code; Claude, Gemini or
  DeepSeek through the OpenAI Responses API or Codex; or when such a call fails
  with previous_response_unavailable, unsupported_parameter,
  unsupported_tool_type or 'not available on /v1/messages'.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment.
metadata:
  version: 1.0.5
  docs: >-
    https://docs.aimlapi.com/api-references/service-endpoints/complete-model-list.md
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-protocols
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Any chat model on any protocol

Most chat models on AI/ML API answer on all three text protocols: `POST /v1/chat/completions`, `POST /v1/responses` and `POST /v1/messages`. When a model does not speak a protocol natively, the API translates the request and the answer. That lets an Anthropic-SDK app or Claude Code run DeepSeek or Gemini, and a Responses-API app or Codex run Claude or Qwen. A translated call costs the same as the native one.

## When to use

- "Run Gemini / DeepSeek / Kimi in Claude Code or with the Anthropic SDK"
- "Use Claude or Qwen through the Responses API or Codex"
- A translated call answers `400` with one of the codes in § Errors

## Steps

### 1. Check that the model serves the protocol

```bash
curl -s 'https://api.aimlapi.com/v1/models?id=deepseek/deepseek-chat' | python3 -c 'import json,sys; [print(m["type"], m.get("translatedFrom", "native")) for m in json.load(sys.stdin)["data"]]'
```

- The model must list the route's `type`: `openai/responses/submit` for `/v1/responses`, `anthropic/messages` for `/v1/messages`. `translatedFrom` marks a translated route.
- A model without that type answers `400` "Model '…' is not available on /v1/messages … call it there instead": use `/v1/chat/completions`.
- Parameters of the translated route are in that entry's `info.docsJson` (`aimlapi-models`).

### 2. Responses on a translated route: no stored state

| Request | Translated route |
| ------- | ---------------- |
| `previous_response_id` | `400 previous_response_unavailable`: send the whole conversation in `input` every turn |
| `background: true`, `conversation`, `prompt` | `400 unsupported_parameter`: run the request in the open connection |
| `store` | ignored; the answer says `store: false` and `GET /v1/responses/{id}` answers `404` |
| response `id` | `resp_aiml_…`: a translated answer, not stored |

With the OpenAI SDK: keep your own list of `input` items, append the answer's `output` items to it, and send the list each turn.

### 3. Return the model's state exactly as you got it

Gemini, DeepSeek and Kimi need their reasoning state back on the next turn of a tool loop, or the turn fails. The state rides in fields the client returns anyway:

- **Responses:** pass `reasoning` items (with `encrypted_content`, sent whenever there is state, no `include` needed) and `function_call` items back in `input` unchanged.
- **Messages:** pass `thinking` blocks (with `signature`) and `tool_use` blocks back unchanged.
- **Tool-call ids** may look like `aimlc1_…`. Answer each call with that exact id; never shorten, rename or regenerate it.

Changing the model mid-conversation is fine: state from another model is dropped, not refused.

### 4. Know what is translated and what is not

- **Thinking.** On `/v1/messages` a request without `thinking` runs with reasoning off, also on models that think by default. Ask for it with `thinking` (or `output_config.effort`); on `/v1/responses` with `reasoning.effort`, rounded to the nearest level the model has.
- **Forced tool choice.** Some thinking models refuse `tool_choice` `required` or a named tool; the translated route then sends `auto`.
- **Hosted tools.** `web_search` is dropped silently, so no search happens: give the model your own search function instead. Other non-function types (`file_search`, `code_interpreter`, `computer`, `mcp`, …) answer `400 unsupported_tool_type`.
- **Prompt cache.** `cache_control` is used on Claude models and dropped on others, which cache automatically on a stable prefix.
- **Usage in a Messages stream.** `message_start` carries zeros; the real counts are in the final `message_delta`.

### 5. Agents

Claude Code on a non-Claude model: connect it with `aimlapi-setup`. Codex sends the full history with `store: false`, which suits a translated Responses route.

## Rules

- [ ] Check `type` in the catalogue before relying on a translated route; never assume every model is on every protocol.
- [ ] Do not build on stored Responses state (`previous_response_id`, `background`, `GET` by id) unless the model serves Responses natively (no `translatedFrom`).
- [ ] Never edit thinking blocks, reasoning items or tool-call ids between turns.
- [ ] Sandbox mode (`aimlapi-sandbox`) does not apply these limits: test translated-route behaviour with a small live request.

## Errors

| Response | Do |
| -------- | -- |
| `400` "not available on /v1/messages" (or `/v1/responses`) | step 1; call `/v1/chat/completions` |
| `400 previous_response_unavailable` | send the full conversation in `input` |
| `400 unsupported_parameter` naming `background`, `conversation` or `prompt` | drop it; keep the request open |
| `400 unsupported_tool_type` | replace the hosted tool with a function tool |
| second turn of a tool loop fails | step 3: return thinking, reasoning items and call ids unchanged |

## Check before done

- [ ] The model lists the route's `type` in `GET /v1/models?id=<id>`.
- [ ] A two-turn tool loop runs live: the second turn sends back the first turn's reasoning and call ids unchanged.
- [ ] No `previous_response_id`, `background` or `GET /v1/responses/{id}` on a translated route.

## Reference

- `aimlapi-chat`: calling the three protocols; `aimlapi-models`: catalogue and schemas; `aimlapi-setup`: connecting Claude Code, Codex and other agents
- Catalogue: https://docs.aimlapi.com/api-references/service-endpoints/complete-model-list.md
