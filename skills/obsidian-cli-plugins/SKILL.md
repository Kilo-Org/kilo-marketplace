---
name: obsidian-cli-plugins
description: >-
  Use this skill when working with a real Obsidian vault through CLI-backed
  workflows for vault diagnostics, Git sync, tasks, records, project notes,
  attachments, plugin commands, safe vault reads, or OpenClaw sync.
metadata:
  category: productivity
  source:
    repository: 'https://github.com/DXShelley/obsidian-cli-plugins-skill'
    path: skills/obsidian-cli-plugins
    license_path: LICENSE
    ref: main
    commit: 6cd2d59f2faa64311c056a1b851ea16b680efd19
---

# Obsidian CLI Plugins

## Operating Model

Use the bundled Python scripts as the stable interface. All executable code and launchers must live under `scripts/`; do not add root-level compatibility scripts. When a workflow needs repeatable parsing, Git coordination, attachment handling, or note edits, extend `scripts/obsidian_cli_plugins/` instead of writing ad hoc shell snippets.

Run `doctor` first on a new host, container, SSH session, OpenClaw runtime, or unfamiliar Agent runtime. Return and consume JSON for cross-agent handoff, and stop on `ok=false`, `reason`, nonzero return codes, `unmerged`, or `merge_head`.

## Plugin Relationship

This skill is the required component for Obsidian functionality. It owns vault discovery, Git preflight, record creation, attachment copying, staged-attachment consumption, and sync.

The `obsidian-media-claim` OpenClaw plugin is optional. It does not replace this skill and cannot create Obsidian records by itself. Its main purpose is to claim media-only channel uploads before OpenClaw sends them to the LLM, stage readable media paths for this skill, and avoid unnecessary token spend. If the plugin is absent, text records and explicit local `--attach` records still work through this skill, but media-only-then-text channel uploads need manual/runtime staging and may otherwise involve the model.

## Trigger Rules

Use this skill when the user is operating a real Obsidian vault, especially a configured vault such as `obsidian-2026`.

Strong triggers:

- Explicit skill or tooling: `$obsidian-cli-plugins`, `obsidian_workflows.py`, `obs_record_sync.py`, `sync_openclaw.py`.
- Vault operations: `使用 vault ...`, `obsidian-2026`, `doctor`, Obsidian 状态, host Git status/sync, pull/push/commit inside a vault.
- Obsidian content workflows: daily/weekly/monthly/quarterly/yearly journals, Tasks todos, `今日新增待办`, `今日待办`, `记录/记一条`, QuickAdd records, attachments copied into notes, safe vault reads/searches.
- Project record workflows when tied to Obsidian or a vault: `01_project`, 项目文件, 项目记录, 创建项目文件, 查看项目结构对象, `project-template-structure`, `analyze-project-record`, `project-record-sync`, `target_id`, `template_structure`, `记到<项目>`, or project-file updates such as 功能需求、非功能需求、决策记录、项目任务、项目问题.
- Obsidian plugin/native commands: Journals, Tasks plugin, Linter, `commands --plugin`, `official-commands`, `run <command-id>`. Use `obsidian-git:*` command IDs only as a fallback when the host `git` executable is not found.

Conditional triggers: plain words such as `记录`, `任务`, `项目`, `笔记`, `Markdown`, `同步`, `附件`, or `搜索` require Obsidian/vault/journal/plugin/project-file context before using this skill.

Do not use this skill for generic project management, generic Markdown editing, unrelated Git operations, database/business records, or screen/audio/video recording unless the result is explicitly going into an Obsidian vault.

## Quick Start

Use these commands as representative entry points. For common requests, load `references/fast-paths.md` first.

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py doctor
python3 <skill-dir>/scripts/obsidian_workflows.py tasks show --period day --date today
python3 <skill-dir>/scripts/obsidian_workflows.py add-task-sync --period day --date today --kind auto --text "<task text>"
python3 <skill-dir>/scripts/obsidian_workflows.py record-sync --mode inline --period day --date today --text "<original record content>"
python3 <skill-dir>/scripts/obs_record_sync.py --mode file --period day --date today --text "<record text>" --analysis-json '<model json>'
python3 <skill-dir>/scripts/obsidian_workflows.py project-template-structure --project "<project>"
python3 <skill-dir>/scripts/obsidian_workflows.py analyze-project-record --project "<project>" --text "<project detail>" --prompt-only
python3 <skill-dir>/scripts/obsidian_workflows.py project-record-sync --project "<project>" --text "<project detail>" --analysis-json '<model json>'
```

Configure per host or agent with environment variables instead of editing scripts:

```bash
export OBSIDIAN_VAULT=obsidian-2026
export OBSIDIAN_VAULT_PATH=~/git/obsidian-2026
export OBSIDIAN_BIN=obsidian
```

Use `--vault current` or `--vault auto` to target the single currently open vault from Obsidian config. Use `--vault-path` for one-off calls when environment variables are unavailable.

## Reference Routing

User-facing and Agent-facing examples live under `docs/`:

- `docs/user-usage.md`: user utterance examples grouped by feature.
- `docs/agent-usage-examples.md`: matching Agent script examples and handling rules.

Load only the reference needed for the request. Start with `references/fast-paths.md` for common operations, then load the smallest specific file:

- `references/fast-paths.md`: common request routing and high-frequency commands.
- `references/runtime-sync.md`: runtime config, Git sync, plugin command IDs, security gates, portability, and cross-agent handoff.
- `references/task-query.md`: `今日新增待办`, full today todo reports, and weekly todo reports.
- `references/task-add.md`: adding tasks, date/tag inference, journal creation, and placement rules.
- `references/record-workflows.md`: inline records, file-mode records, attachments, and staged media handoff.
- `references/record-body.md`: file-mode record body sections, formatter behavior, and unified LLM analysis fields.
- `references/vault-safety.md`: safe read/search/summarization of arbitrary vault content or files outside `20_plan/`.
- `references/openclaw.md`: OpenClaw install/sync, channel media compatibility, phone-client multi-image/video input, and media-only messages followed by later text records.
- `references/official-cli.md`: native Obsidian CLI command lookup beyond installed community plugin command IDs.
- `references/extensions.md`: adding workflow support for newly installed Obsidian plugins.
- `references/field-guide.md`: onboarding a new Agent, reviewing the vault directory map, or updating the skill from real-session lessons.

## Execution Rules

- On multi-vault hosts, inspect `doctor.configured_vaults` and `doctor.resolved_vault`; use `--vault current` only when the single-open-vault result is clear.
- Use `safe-read` or `safe-search` before returning vault content. Otherwise apply `references/vault-safety.md` and redact sensitive content.
- Use `add-task-sync` for task additions and `record-sync` for record additions unless the user explicitly asks for local-only writes.
- For `记录 <content>` with no explicit period/date, write an inline record to today's daily journal `记录` section with the original text unchanged. Load `references/record-workflows.md` before changing record behavior.
- Use file-mode records only for separate cards/notes, analysis, long-term capture, knowledge processing, or any attachment/media workflow. Load `references/record-body.md`; for staged or cross-agent media, also load `references/openclaw.md`.
- For media files uploaded in earlier channel messages, treat images, videos, audio, and files as one staged media workflow. Prefer staged media created by `obsidian-media-claim` when that optional plugin is installed; otherwise require manual/runtime staging with readable local paths. First call `attachment-pending --ttl-hours 48` with the stable conversation/sender `--batch-key` when available, then consume the returned `selector` with file-mode `obs_record_sync.py --mode file --period <period> --date <date> --text "<text>" --staged-attachment "<selector>" --type mixed --require-attachment`. Do not use `attachment-list --batch-key default`, stale staged ids from model memory, or direct cache directory reads.
- For file-mode semantic analysis, obtain the shared prompt/schema via `analyze-record`, use the Agent application's own LLM/model, validate with `--normalized-only` when useful, and pass model-produced `--analysis-json`. Do not present hand-built JSON as semantic analysis.
- For project notes under `01_project/`, use `project-template-structure` or `analyze-project-record` first. The current project/template headings and fragment templates produce a standard `template_structure` with `target_id` values. The Agent application's own LLM/model must output project record JSON using one of those `target_id` values, then `project-record-sync` writes it with `--analysis-json`. Do not bypass the project templates or hand-build semantic analysis JSON.
- Project template parsing uses `markdown-it-py` when available for CommonMark-compatible heading tokens and line maps; if it is not installed, the scripts fall back to the built-in heading parser so users are not required to install optional dependencies.
- `project-record-sync` opens the updated project note and runs Obsidian Linter (`obsidian-linter:lint-file`) before Git commit/push unless explicitly passed `--no-lint` for a controlled local-only test.
- If a supplied attachment has no readable local path, stop with script-emitted `record-attachment-required` or `attachment-path-unavailable` instead of writing a partial record. Use `unsupported-channel-attachment-record` only as an Agent-level judgment when the runtime cannot expose or preserve attachment state for the CLI.
- Before `pull`, `push`, `commit-sync`, or note edits, run `git-status`; stop on conflict state. Prefer `add-task-sync`, `record-sync`, or `git_preflight_clean` so host `git` clean/pull/push/commit sequencing is enforced. Fall back to Obsidian Git plugin commands only when the host `git` executable is not found, not when host Git returns a conflict, auth, pull, push, or commit error.
- Treat `Executed: <command-id>` as dispatch success only; verify the actual vault/file/plugin effect afterward.
- Ask before destructive operations such as discard, delete, reset, uninstall, vault-wide cleanup, or permanent deletion.
- For "今日新增待办", "今天新增任务", or equivalents, prefer `tasks show --period day --date today`; do not run broad vault searches unless the user asks for them.

For OpenClaw, sync into the current managed skills directory, typically `~/.openclaw/skills/obsidian-cli-plugins`, with:

```bash
python3 <skill-dir>/scripts/sync_openclaw.py
```
