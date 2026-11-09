# kilo-plugin-antigravity

Native Kilo Code Plugin for Google Antigravity (AGY) local model services.
Provides OpenAI-compatible endpoints with full token usage telemetry, cost modeling, and thought signatures for Gemini/Claude models.

## Features

- **Models Included**:
  - `agy/gemini-4-argon`: Google Flagship Coding Model (1M context)
  - `agy/gemini-3.8-flash`: Fast & Efficient Coding Model (1M context)
  - `agy/gemini-2.5-flash-thinking`: Deep Reasoning Model (1M context)
  - `agy/claude-sonnet-5-5`: Anthropic Sonnet 5.5 (1M context)
  - `agy/claude-opus-5-5`: Anthropic Opus 5.5 (1M context)
  - `agy/gpt-oss-120b-medium`: GPT-OSS 120B (128K context)
- **Token & Cost Tracking**: Accurately reports input, output, reasoning tokens, and official API cost calculations.
- **Thought Signatures**: Full bidirectional handling of Gemini `thoughtSignature` for multi-turn agent tool calling.
- **Thinking Effort**: Supports `low`, `medium`, `high` variants via `Shift + Tab` in VS Code or `--variant` in CLI.
- **Auto-Refresh OAuth**: Uses Antigravity's macOS Keychain credentials with automatic token refresh.

## Installation

Add to your `~/.config/kilo/kilo.json` or project `./kilo.json`:

```jsonc
{
  "plugin": [
    "kilo-plugin-antigravity"
  ]
}
```

Or for local development:
```jsonc
{
  "plugin": [
    "file:///path/to/kilo-plugin-antigravity"
  ]
}
```

## License

MIT
