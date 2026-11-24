---
name: aimlapi-setup
description: >-
  Use when a coding agent (Claude Code, Codex, OpenCode, Cline, OpenClaude,
  OpenClaw, Hermes Agent, zero, ZCode) should run on AI/ML API (aimlapi) models,
  when someone wants to sign in to AI/ML API from a terminal, switch an agent's
  provider to AI/ML API, or undo that setup.
compatibility: >-
  Needs Node.js 18+, npm, network access to aimlapi.com, and a shell the agent
  can run commands in.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/quickstart/cli/aimlapi-setup.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-setup
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Connect an agent to AI/ML API

The `aimlapi` CLI (npm `aimlapi`) signs the user in, stores the key on this machine and edits the agent's config. Run it in order, show the user what changes, never touch the key. Where a step says "ask", stop and wait.

## When to use

- "Use AI/ML API models in Claude Code / Codex / OpenCode / …"
- "Sign me in to AI/ML API", "set up aimlapi", "switch my agent to aimlapi"
- "Undo the aimlapi setup"

## When not to use

- Calling the API from the user's own code: `aimlapi-chat`, `aimlapi-images`, `aimlapi-async-jobs`.
- An MCP client (Claude Desktop, claude.ai): the MCP server `https://mcp.aimlapi.com/mcp` signs in with OAuth.

## Rules

- [ ] **Never ask for an API key or accept one in the chat.** Sign-in is `aimlapi login` in the browser. If the user pastes a key anyway, do not repeat, store or pass it; say it is now in the transcript and suggest revoking it at https://aimlapi.com/app/keys.
- [ ] **Never print, read or copy the key**: no `aimlapi key print`, no opening `~/.aimlapi/credentials` or the agent files that hold it, no `env`/`printenv`/`set`.
- [ ] **Never put a key on a command line** (`--apikey …`, `AIMLAPI_API_KEY=… aimlapi …`, `export AIMLAPI_API_KEY=…`).
- [ ] **Preview before changing config.** Run `--dry-run` first, show the user what changes, wait for a clear yes. Never re-run `--config` on your own to "fix" something.
- [ ] **Always pass `--model <id>`** to every `--config` command, the same id each time. Without it the CLI opens an interactive picker you cannot answer.
- [ ] **Never run `aimlapi <agent>` without `--config`, `--dry-run` or `--undo`**: plain `aimlapi claude` launches an interactive session and hangs your shell.
- [ ] Prefix every command with `AIMLAPI_NO_UPDATE_CHECK=1`; close stdin with `</dev/null` on `--config` (PowerShell: [references/troubleshooting.md](references/troubleshooting.md)).
- [ ] No `sudo`, no system changes, no installing Node.js or the agent without asking.
- [ ] Do not commit the changed files; warn the user if their dotfiles are in git.

## Exit codes

`0` success · `1` general error: show stderr, stop, ask · `2` usage error or `--config` from `npx`: step 5 · `3` not signed in or key rejected: step 4 · `4` agent not installed: step 6.

## Steps

### 1. Pick the agent

Ids: `claude`, `codex`, `opencode`, `cline`, `openclaude`, `zcode`, `hermes`; `openclaw`, `zero` only when named. Default to the agent you run in ([references/agents.md](references/agents.md)); Claude Code and OpenClaude share one variable, so if unsure, ask.

### 2. Check Node.js 18+

`node --version && npm --version`. If missing or older, ask the user to install the LTS from https://nodejs.org.

### 3. Check sign-in

```sh
[ -n "$AIMLAPI_API_KEY" ] && echo set || echo unset
AIMLAPI_NO_UPDATE_CHECK=1 npx -y aimlapi@latest status
```

If `set`, tell the user it overrides the stored key and ask whether to continue. `status` exit `0` → step 5, `3` → step 4.

### 4. Sign in

Tell the user a browser window opens and the CLI, not you, stores the key. Run `AIMLAPI_NO_UPDATE_CHECK=1 npx -y aimlapi@latest login` (long timeout or background; `--device` without a browser) and relay every link or code it prints. Then `status` again, expecting `0`.

### 5. Install or update the CLI globally

If `aimlapi --version` works, keep it; otherwise `npm install -g aimlapi` (on `EACCES` ask the user, never `sudo`). Then use `aimlapi …`, not `npx`. Updates and install errors: [references/troubleshooting.md](references/troubleshooting.md).

### 6. Choose the model and preview

```sh
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi models --agent <agent>
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi <agent> --config --dry-run --model <id> </dev/null
```

Offer the row marked `default`; never guess an id. Summarize the dry run for the user ([references/agents.md](references/agents.md)). Exit `4`: ask once whether to install the agent; on a yes, add `--yes` in step 7. Ask "Apply these changes?" and go on only on a clear yes.

### 7. Apply

```sh
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi <agent> --config --model <id> </dev/null
```

Relay the `Note:` lines and the backup directory.

### 8. Verify and restart

`aimlapi status` exits `0` and the step 6 dry run shows every file `unchanged` (if not, show it and ask; never re-apply). Tell the user how to restart their agent ([references/agents.md](references/agents.md) § Restart).

To undo: `aimlapi <agent> --undo --dry-run`, show it, then `--undo` on a yes ([references/troubleshooting.md](references/troubleshooting.md) § Roll back).

## Errors

A `--config` command that shows a menu and never ends was run without `--model`: stop it and re-run with `--model <id> </dev/null`. Every other symptom: [references/troubleshooting.md](references/troubleshooting.md).

## Check before done

- [ ] `aimlapi status` exits `0`.
- [ ] The dry run after applying shows every file `unchanged`.
- [ ] You told the user how to restart their agent.
- [ ] No key appeared in your output, in a command line or in a file you wrote.

## Reference

- [references/agents.md](references/agents.md): agent detection, files changed per agent, restart steps
- [references/troubleshooting.md](references/troubleshooting.md): step details, install errors, roll back, symptoms
- CLI docs: https://docs.aimlapi.com/quickstart/cli.md
