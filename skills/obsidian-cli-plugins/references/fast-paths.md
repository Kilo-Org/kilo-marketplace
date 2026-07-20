# Obsidian Fast Paths

Use this file first for common Obsidian requests. Prefer the listed script command over loading larger references. Load the referenced detail file only when the request is ambiguous, failed, or asks for behavior changes.

## Always do

- Run `doctor` first in a new host, container, SSH session, OpenClaw runtime, or unfamiliar Agent runtime.
- Stop on `ok=false`, `reason`, nonzero return codes, `unmerged`, or `merge_head`.
- Use JSON fields from script output instead of parsing human terminal formatting.
- Do not bypass the script for note edits, Git sync, attachment copying, journal creation, or task placement.

## Route by request

| User intent | Command | Extra reference |
| --- | --- | --- |
| `今日新增待办`, `今天新增任务` | `python3 <skill-dir>/scripts/obsidian_workflows.py tasks show --period day --date today` | `task-query.md` only if output is unclear |
| Full `今日待办`, overdue, recurring | `python3 <skill-dir>/scripts/obsidian_workflows.py today-tasks --source` | `task-query.md` |
| Full weekly todo report | `python3 <skill-dir>/scripts/obsidian_workflows.py week-tasks --source` | `task-query.md` |
| Add a todo/task | `python3 <skill-dir>/scripts/obsidian_workflows.py add-task-sync --period <period> --date today --kind auto --text "<task text>"` | `task-add.md` |
| Local-only task write | `python3 <skill-dir>/scripts/obsidian_workflows.py tasks add --period <period> --date today --kind auto --text "<task text>"` | `task-add.md` |
| Plain `记录 <content>` with no attachment | `python3 <skill-dir>/scripts/obsidian_workflows.py record-sync --mode inline --period day --date today --text "<original content>"` | `record-workflows.md` only if period/date/mode is unclear |
| Separate record file/card/note/analysis | `analyze-record`, Agent LLM analysis, then `scripts/obs_record_sync.py --mode file ... --analysis-json '<model json>'` | `record-workflows.md` and `record-body.md` |
| Add detail to a project note under `01_project/` | `project-template-structure --project "<project>"` when structure inspection is needed, then `analyze-project-record --project "<project>" --text "<detail>" --prompt-only`, Agent LLM analysis using `target_id`, optionally `--normalized-only`, then `project-record-sync --project "<project>" --text "<detail>" --analysis-json '<model json>'` | Use current project/template headings and fragment templates as source of truth; Linter runs by default |
| Record with uploaded/local attachment | file-mode `record-sync`/`obs_record_sync.py` with every `--attach`, `--require-attachment`, and possibly `--allow-external-attachments` | `record-workflows.md`; `openclaw.md` for staged/cross-agent media |
| Record media files that were uploaded in earlier channel messages | `python3 <skill-dir>/scripts/obsidian_workflows.py attachment-pending --batch-key "<conversation-or-sender-key>" --ttl-hours 48`, or omit `--batch-key` only when the current conversation has exactly one pending media batch; then use the returned `selector` in file-mode `obs_record_sync.py --staged-attachment "<selector>" --type mixed --require-attachment` | Treat images, videos, audio, and files as the same staged media workflow; do not use `attachment-list --batch-key default`, stale staged ids, or direct reads under `~/.cache/obsidian-cli-plugins/staged-attachments` |
| Safe vault read/search | `safe-read` or `safe-search` | `vault-safety.md` |
| Sync/pull/push/Git status/plugin command | `git-status`, `sync`, `commands`, `run` | `runtime-sync.md` |
| Native Obsidian CLI command lookup | `official-commands --search <keyword>` or `--category <category>` | `official-cli.md` |

## Accuracy gates

- For note-writing commands, use sync-backed commands by default: `add-task-sync` and `record-sync`. Use local-only variants only when the user explicitly asks.
- For file-mode records, semantic analysis requires the Agent application's model. The local script supplies and validates the contract; it does not replace model understanding.
- For project records, semantic analysis also requires the Agent application's model. Always derive the JSON from `analyze-project-record` output and the current `template_structure`; output must include a valid `target_id`. `project-record-sync` writes to that target section and runs Obsidian Linter before Git commit/push by default.
- Do not create a media/attachment record unless at least one real readable local file is copied by the record command. URL-only, stale staged id, missing path, or plain Markdown link is not enough.
- For staged media consumption, `attachment-pending` is the only listing command. `attachment-list --batch-key default` is a debugging footgun and must not be used for record workflows.
- Treat `Executed: <command-id>` as command dispatch only. Verify the actual file, Git, plugin, or vault effect before claiming success.
