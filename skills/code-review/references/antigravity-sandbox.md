# Antigravity CLI sandbox recovery

Follow the [shared execution boundary](auth-recovery.md#execution-boundary)
before using this fallback.

Offer this fallback only when the host is identified as Antigravity CLI with the
terminal sandbox enabled, not for host-native CLI sessions or the desktop app.
When discovery or a needed version/help check is denied, hand the following
command to the user to run from their repository in a new terminal session.
Replace the placeholder only with a trusted canonical absolute path matching
`^/[A-Za-z0-9._/-]+$`. If unresolved, ask the user for the resolved canonical
absolute path from their terminal and confirmation of its source, not just a
symlink path. For other path characters, stop and link the sandbox permissions
documentation below instead of constructing a permission rule. Keep the prompt literal and
give the original review scope separately for the user to supply in the new
session. Do not change permissions or relaunch the agent yourself.

Ask the user to run `agy --help` in their host terminal before using the command
below and confirm it lists `--settings` and `--prompt-interactive`. Both are
present in CLI 1.4.12's built-in help; if either is unavailable, stop and link
the host documentation below. Do not try to elevate these diagnostics yourself.

```sh
agy --sandbox \
  --settings '{"agentMode":"","toolPermission":"proceed-in-sandbox","permissions":{"allow":["read_file(/absolute/path/to/coderabbit)"]}}' \
  --prompt-interactive 'Use the CodeRabbit code-review skill. Ask me for the review scope before running a review. Keep version/help sandboxed and use the normal per-command approval flow for authentication and review.'
```

Tested with Antigravity CLI 1.4.12 and curl-installed CodeRabbit CLI 0.9.1 on
macOS arm64: the exact executable read grant allows sandboxed version/help.
The user-run command selects default agent mode (`agentMode: ""`) so host
requests retain normal approval, and `proceed-in-sandbox` lets sandboxed commands
run without prompting. Explain these permission changes to the user with the
handoff. `--settings` is session-only; existing permissions may
still apply. The read grant adds no credential-store, network, or review-state
access. Continue with the
[shared auth/review procedure](auth-recovery.md#before-review); do not add
credential directories to the allowlist or interpret an auth-file `EPERM` as signed out.

Use an interactive session for first-time permissions. A headless permission
denial can exit 0 with no result; require actual review completion, not just the
agent process exit code. If a different skill copy loads, ask the user to run
`agy plugin list --json` in their host terminal and compare it with the reported
skill path before retrying; do not delete user skills. If the recovery command
fails, report and stop.

See Antigravity's [CLI flag reference](https://antigravity.google/docs/cli/reference/),
[sandbox permissions](https://antigravity.google/docs/sandbox?tab=cli),
and [headless permission behavior](https://antigravity.google/docs/cli/headless/).
