# Agents the aimlapi CLI configures

Source: https://docs.aimlapi.com/quickstart/cli/aimlapi-setup.md

## Which agent am I?

Check only these names; never print the whole environment.

```sh
env | grep -E '^(CLAUDECODE|CODEX_THREAD_ID|CODEX_SANDBOX|OPENCODE|HERMES_AGENT)='
```

```powershell
Get-ChildItem Env: | Where-Object Name -in 'CLAUDECODE','CODEX_THREAD_ID','CODEX_SANDBOX','OPENCODE','HERMES_AGENT' | Select-Object Name, Value
```

| Variable present | Agent id |
| ---------------- | -------- |
| `CLAUDECODE=1` | `claude` |
| `CLAUDECODE=1`, and you are OpenClaude (it sets the same variable) | `openclaude` |
| `CODEX_THREAD_ID` or `CODEX_SANDBOX` | `codex` |
| `OPENCODE=1` | `opencode` |
| `HERMES_AGENT=true` | `hermes` |
| none, and you are Cline | `cline` |
| none, and you are ZCode | `zcode` |

## What `--config` changes

| Agent | Files changed | Where the key lives |
| ----- | ------------- | ------------------- |
| `claude` | `~/.claude/settings.json` (or `$CLAUDE_CONFIG_DIR`): `env` (base URL, models, headers) and `apiKeyHelper` | nowhere in the file: Claude Code runs `aimlapi key print` |
| `codex` | new profile `~/.codex/aimlapi.config.toml` (or `$CODEX_HOME`); `config.toml` untouched | nowhere in the file: Codex runs `aimlapi key print` |
| `opencode` | provider `aimlapi-cli` in the global `opencode.json`; sets `model` only if none is set | OpenCode's `auth.json` (mode 0600) |
| `cline` | provider `openai-compatible` in `~/.cline/data/settings/providers.json`, made default (CLI, VS Code, JetBrains) | `providers.json` |
| `openclaude` | `env` of `~/.openclaude/settings.json` (or `$OPENCLAUDE_CONFIG_DIR`) | `ANTHROPIC_AUTH_TOKEN` in that file (mode 0600) |
| `openclaw` | provider and secret provider `aimlapi-cli`, `agents.defaults.model` in `~/.openclaw/openclaw.json` | nowhere in the file: reads aimlapi's credentials (needs `aimlapi login`) |
| `zero` | profile `aimlapi-cli` in `~/.config/zero/config.json`, made default | nowhere in the file: zero reads `$AIMLAPI_CLI_KEY` |
| `zcode` | provider `aimlapi-cli` in `~/.zcode/v2/provider_config.json`, its model made default | `provider_config.json` (mode 0600) |
| `hermes` | provider `aimlapi-cli` in `~/.hermes/config.yaml` (or `$HERMES_HOME` / active profile), `model.default` and `model.provider` pointed at it | nowhere in the file: Hermes runs `aimlapi key print` |

Every dry run also shows a `create` of `~/.aimlapi/agents/<agent>/previous/<hash>.json`: the values `--undo` restores.

## Restart

| Agent | How to start using AI/ML API | Extra check |
| ----- | ---------------------------- | ----------- |
| `claude` | Quit Claude Code and start it again | `/status` shows the AI/ML API base URL |
| `codex` | `codex --profile aimlapi`; plain `codex` keeps the old provider | none |
| `opencode` | Restart OpenCode; if a default model was already set, pick an `aimlapi-cli/…` model with `/models` | `opencode models aimlapi-cli` |
| `cline` | Next CLI run; in VS Code: "Developer: Reload Window" | none |
| `openclaude` | Quit and start again. Switching provider with `/provider` later removes only part of the settings; use `aimlapi openclaude --undo` | `/status` shows the AI/ML API base URL |
| `openclaw` | A running Gateway reloads by itself; start a new session with `/new` | `openclaw config validate` |
| `zero` | `aimlapi zero` starts it with the key. Plain `zero` needs `AIMLAPI_CLI_KEY` in the user's shell: the user may add `export AIMLAPI_CLI_KEY="$(aimlapi key print)"` to their profile themselves; do not run it | `zero providers list` shows `aimlapi-cli` active |
| `zcode` | A running ZCode picks it up; start a new session | the model picker lists "AI/ML API" |
| `hermes` | New `hermes` session; a running gateway needs `hermes gateway restart` | `/model` shows "AI/ML API (aimlapi CLI)" |
