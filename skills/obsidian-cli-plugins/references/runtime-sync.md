# Obsidian Runtime, Sync, and Commands

Use this file for runtime configuration, host Git sync, cross-agent handoff, and plugin/native command execution.

## Runtime configuration

Current host defaults:

- Vault name: `obsidian-2026`
- Vault path fallback: `~/git/obsidian-2026`
- Daily notes: `20_plan/21_daily/YYYY-MM-DD.md`
- Weekly notes: `20_plan/22_weekly/YYYY-Www.md`
- Monthly notes: `20_plan/23_monthly/YYYY-MM.md`
- Quarterly notes: `20_plan/24_quarterly/YYYY-Qn.md`
- Annual notes: `20_plan/25_annual/YYYY.md`

Do not edit scripts to move between hosts. Configure with environment variables or flags:

- `OBSIDIAN_VAULT`: vault display/name lookup key.
- `OBSIDIAN_VAULT_PATH`: absolute vault path when Obsidian config discovery is unavailable.
- `OBSIDIAN_CONFIG`: explicit `obsidian.json` path.
- `OBSIDIAN_BIN`: explicit Obsidian CLI binary or executable path.
- `--vault`, `--vault-path`: one-off overrides.
- `--vault current`, `--vault auto`, `--vault active`, or `--vault open`: resolve the single open vault from Obsidian config.

Run first in any new host/runtime:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py doctor
```

`doctor` searches common macOS, Windows, and Linux Obsidian config locations before falling back to `OBSIDIAN_VAULT_PATH`. It redacts paths by default; use `doctor --verbose` only for local debugging.

## Safety gates

- Use `vault-safety.md` before returning arbitrary vault content.
- Resolve the active vault dynamically; do not use obsolete paths from older skills.
- On multi-vault hosts, inspect `doctor.configured_vaults` and `doctor.resolved_vault`; do not guess.
- Do not bypass the `.obsidian` directory check for sync, Git-mutating, note-writing, or task-query workflows. `--allow-non-vault` is only for controlled tests.
- Execute sensitive or destructive-looking plugin commands only after explicit user confirmation with `run <command-id> --risk sensitive --yes` or `run <command-id> --risk destructive --yes`.
- Keep task query artifacts in private cache defaults unless the user explicitly requests another output path.
- Treat symlinks resolving outside the vault as outside-vault content.

## Git sync

Before `pull`, `push`, `commit-sync`, or note edits:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py git-status
```

Stop on `unmerged` or `merge_head`.

Git operations prefer the host environment's `git` executable through the bundled script. Fall back to `obsidian-git:*` plugin command IDs only when the host `git` executable is not found. Do not use the plugin fallback when host Git exists but returns a conflict, authentication, pull, push, or commit error.

For read-only queries, run:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py sync --mode pull-push
```

For sync-backed document edits, use `add-task-sync`, `record-sync`, or the script's preflight helper. The preflight sequence commits existing local vault changes, runs `git pull --no-rebase`, runs `git push`, and verifies clean/synced state before editing.

Do not manually append to journal files to bypass preflight. Use local-only write commands only when explicitly requested.

## Cross-agent contract

Use bundled Python scripts across Codex, OpenClaw, Claude Code, OpenCode, Cursor agents, shell agents, CI runners, and SSH sessions.

Agents should:

1. Call `doctor` and inspect JSON before executing plugin/native commands.
2. Pass `--vault-path` when environment variables are unavailable.
3. Prefer JSON-producing commands for handoff.
4. Treat `ok=false`, `reason`, nonzero return codes, `unmerged`, or `merge_head` as stop conditions.
5. Avoid parsing human terminal formatting; consume structured fields such as `task.task`, `task_kind`, `task_dates`, `journal`, `git.after`, and `preflight`.
6. Fall back to read-only Markdown/Git inspection only when Obsidian CLI is unavailable; do not claim Journals/plugin actions succeeded without command output and file verification.

For cross-agent record creation, prefer:

```bash
python3 <skill-dir>/scripts/obs_record_sync.py --period day --date today --text "<record text>" --topic <topic>
```

For OpenClaw install/sync and staged media workflows, read `openclaw.md`.

## Plugin command IDs

Prefer the script wrapper so vault path, platform discovery, JSON reporting, and verification stay consistent.

Discover current runtime plugin commands:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py plugins
```

Common non-Git IDs:

- `obsidian-tasks-plugin:edit-task`
- `obsidian-tasks-plugin:toggle-done`
- `journals::open-today's-note`
- `journals::open-weekly-note`
- `journals::open-monthly-note`
- `journals::open-quarterly-note`
- `journals::open-yearly-note`

Manual command execution:

1. Resolve command ID via `commands --plugin <plugin-id>` when needed.
2. Do not run `obsidian-git:*` command IDs when host `git` is available. Use `git-status` and `sync --mode ...` first; the script will choose the plugin fallback only when host `git` is missing.
3. Confirm risk for sensitive/destructive commands: developer/eval/debug, delete, discard, reset, uninstall, plugin/theme changes, restore, publish, or vault-wide operations.
4. Execute `run <command-id>` for normal commands. Use `--risk sensitive --yes` or `--risk destructive --yes` only after exact user confirmation.
5. Verify effect with Git status, command output, or note/file inspection.

## Official CLI lookup

Use this for native Obsidian CLI commands such as `create`, `read`, `append`, `search`, `properties`, `links`, `themes`, `plugins`, or developer commands:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py official-commands --search <keyword>
python3 <skill-dir>/scripts/obsidian_workflows.py official-commands --category <category>
```

Read `official-cli.md` only when syntax details, risk rules, or the imported category overview are needed. For plugin command IDs, use runtime `commands --plugin <plugin-id>` instead of the static official reference.
