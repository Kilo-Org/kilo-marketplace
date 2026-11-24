# Setup details and troubleshooting

PowerShell: set the variable in the same command line and close stdin with a leading `$null |`, e.g. `$env:AIMLAPI_NO_UPDATE_CHECK=1; $null | aimlapi <agent> --config --model <id>`.

Source: https://docs.aimlapi.com/quickstart/cli/aimlapi-setup.md. The steps below are the full text behind SKILL.md § Steps.

### 3. Check sign-in

Check, without printing it, whether a key is in the environment:

```sh
[ -n "$AIMLAPI_API_KEY" ] && echo set || echo unset
```

If `set`, tell the user it overrides the key stored by `aimlapi login`, and that for `opencode`, `cline`, `openclaude` and `zcode` it is the key `--config` writes into the agent's files. Ask whether to continue with it.

```sh
AIMLAPI_NO_UPDATE_CHECK=1 npx -y aimlapi@latest status
```

Exit `0`: signed in, go to step 5. Exit `3`: step 4. Otherwise show the error and stop. A zero or low balance does not stop setup, but tell the user requests will fail until they top up at https://aimlapi.com/app.

### 4. Sign in

Tell the user: "A browser window will open. Sign in to AI/ML API and approve the aimlapi CLI. The CLI stores the key on this computer; I never see it."

```sh
AIMLAPI_NO_UPDATE_CHECK=1 npx -y aimlapi@latest login
```

- It waits up to 10 minutes for approval. Run it with a long timeout or in the background, and relay every link or code it prints on stderr exactly as printed.
- Over SSH or without a browser it switches to a device code; `--device` forces that.
- If you cannot keep a command running that long, ask the user to run it in their own terminal (in Claude Code: `! AIMLAPI_NO_UPDATE_CHECK=1 npx -y aimlapi@latest login`).
- Exit `3`: denied, expired or timed out. Ask whether to try again.

On success it prints only a short key prefix. Run `status` again and expect `0`.

### 5. Install or update the CLI globally

`--config` for Claude Code, Codex and Hermes stores the path of the `aimlapi` binary, so it refuses to run from `npx` (exit `2`).

```sh
aimlapi --version
```

- **Installed:** keep it. Compare with `npx -y aimlapi@latest --version`. If older, show both versions and ask before `AIMLAPI_NO_UPDATE_CHECK=1 aimlapi update`.
- **Not found:** `npm install -g aimlapi`, then `aimlapi --version`.
  - `EEXIST`: an `aimlapi` from the `aimlapi-cli` alias exists already; keep it, no `--force`.
  - `EACCES`: do not retry with `sudo`. Ask the user to run `sudo npm install -g aimlapi` themselves or fix their npm prefix.
  - Not on `PATH` after install: show `npm prefix -g` and ask the user to add its `bin` to `PATH`.

From here use `aimlapi …`, not `npx`.

### 6. Choose the model and preview

```sh
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi models --agent <agent>
```

Offer the row whose `PRESET` column says `default` (with `--json`: `"default": true`). Use another id only if the user asks. If no row says `default` and the command failed, ask the user for an id (https://aimlapi.com/models lists them); do not guess one.

```sh
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi <agent> --config --dry-run --model <id> </dev/null
```

Summarize the dry run: files changed, what is added and replaced, the notes. What each agent gets is in [references/agents.md](agents.md). Every changed file is backed up under `~/.aimlapi/backups/<agent>/<timestamp>/`.

Exit `4` (agent not installed): describe the change and ask once: "<Agent> is not installed. Install it with `<printed npm command>` and apply this setup?" On a clear yes, run step 7 with `--yes` added. `hermes` and `zcode` are not installed by npm: show their command and let the user install them.

Then ask: "Apply these changes?" Continue only on a clear yes.

### 7. Apply

```sh
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi <agent> --config --model <id> </dev/null
```

Relay the `Note:` lines and the backup directory. Exit `3`: step 4. Exit `4`: step 6.

### 8. Verify and restart

```sh
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi status
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi <agent> --config --dry-run --model <id> </dev/null
```

`status` exits `0` and the dry run lists every file as `unchanged`. If it shows changes, do not run `--config` again: show the output and ask. Then tell the user how to start using it ([references/agents.md](agents.md) § Restart). This session keeps its current provider until the user restarts; say so.

## Roll back

```sh
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi <agent> --undo --dry-run </dev/null
AIMLAPI_NO_UPDATE_CHECK=1 aimlapi <agent> --undo </dev/null
```

Show the dry run and confirm first. `--undo` removes only what `--config` added and restores what it replaced. After undoing every agent, the user may sign out with `aimlapi logout` (revokes the CLI's key) and remove the CLI with `npm uninstall -g aimlapi`; only after `--undo`, because Claude Code and Codex configs point at the binary.

## Symptoms

| Symptom | Cause | Do |
| ------- | ----- | -- |
| `--config … runs from a temporary package-runner cache (npx)`, exit `2` | `--config` through `npx` | step 5 |
| `not logged in to AI/ML API`, exit `3` | no stored key | step 4 |
| `<Agent> is not installed`, exit `4` | agent not on `PATH` | show the install command, install only on a yes |
| `codex … cannot load profile files`, exit `1` | Codex older than 0.131 | ask the user to update Codex, repeat step 6 |
| a `--config` command shows a menu and never ends | `--model` missing in a terminal | stop it, re-run with `--model <id>` and `</dev/null` |
| `warning: AIMLAPI_API_KEY is set` | the environment key overrides the stored one | tell the user; do not print it |
