# Obsidian CLI Plugins Field Guide

Use this file when onboarding a new agent, updating this skill after real use, or deciding which workflow/reference to load. It condenses lessons from local Codex sessions that mentioned `obsidian-cli-plugins`, `obsidian_workflows.py`, `add-task-sync`, `record-sync`, `today-tasks`, `QuickAdd fleeting`, and `obsidian-2026`.

## Session-Derived Scope

Recent local sessions showed these recurring jobs:

- Query available Obsidian native/plugin commands and explain whether commands such as `editor:attach-file` can add media.
- Add daily, weekly, monthly, quarterly, or yearly Tasks todos with Git preflight, Journals/template creation, correct target section placement, commit, and push.
- Show compact newly added tasks with `tasks show`, and show full task reports with `today-tasks --source` or `week-tasks --source`.
- Write short records such as `记录 王老师 183...` inline under the journal `记录` section by default; create independent QuickAdd `fleeting` record files only when explicitly requested.
- Copy explicitly attached media files into a record-local assets folder as Markdown embeds when supported, or ordinary Markdown links for non-previewable files.
- Safely read/search vault content without following outside-vault symlinks or returning sensitive private notes.
- Sync this skill into OpenClaw and verify whether the target runtime can actually discover it.
- Refactor and harden the skill after failures, then add tests for the regression.

## Entry Decisions

- Run `doctor` first in an unfamiliar runtime, after switching Agents, or before any write.
- Use `tasks show --period day --date today` for "今日新增待办" and similar compact queries.
- Use `today-tasks --source` for the full "今日待办" report, overdue tasks, recurring tasks, or Tasks query semantics.
- Use `add-task-sync` for normal task writes because it handles preflight, note creation, placement, commit, push, and verification.
- Use `tasks add` only when the user explicitly asks for local-only/no commit/no push behavior.
- Use `record-sync` for "记录 ..." and journal reflection entries; use `record` only for explicitly local-only record writes.
- Use `safe-search` and `safe-read` before returning arbitrary vault content.
- Use `official-commands` for native Obsidian CLI lookup; use `commands --plugin <plugin-id>` for runtime community plugin command IDs.

## Skill Source Workflow

- Treat the vault copy at `90_asset/skill/obsidian-cli-plugins` as the default source of truth for future skill edits.
- Make behavior, documentation, and test changes in the vault copy first.
- After tests pass, sync the vault copy to `<skill-dir>`.
- Then sync the same vault copy to OpenClaw using `scripts/sync_openclaw.py --source 90_asset/skill/obsidian-cli-plugins --force`.
- Avoid editing only the installed Codex or OpenClaw copies, because those changes are easy to lose.
- If the source, Codex copy, and OpenClaw copy have diverged, do not bulk-sync one copy over another until the intended source of truth is clear. Patch the durable rule in the source first, then reconcile runtime copies deliberately.

## Documentation Freshness

- Record durable workflow rules, invariants, failure modes, validation criteria, and current source-of-truth paths. Skip one-off command transcripts, timestamped backup paths, temporary file names, and old incident details.
- When a lesson is specific to record creation, media attachments, OpenClaw channels, project notes, or sync behavior, update the matching reference file first; keep `SKILL.md` as routing and high-level execution guidance.
- Treat channel capability notes as time-sensitive. Keep only currently verified behavior, and mark unverified or stale channel/media support as unknown instead of preserving old positive claims.
- When a fix changes behavior, add or update a regression test before documenting it as a supported workflow.

## Trigger And Boundary Notes

- Strong triggers must connect to Obsidian semantics: Obsidian/ob/OB/黑曜石, vaults, notes inside the vault, journals, QuickAdd records, Tasks todos, plugin/native commands, safe vault reads/searches, or vault sync.
- Weak words such as `记录`, `任务`, `待办`, `笔记`, `日志`, `Markdown`, `同步`, `附件`, and `搜索` trigger this skill only when the request also implies Obsidian, a vault, a journal, a plugin, or an Obsidian-managed note.
- Do not use this skill for unrelated database records, screen/audio/video recording, generic logs, generic Markdown editing, generic Git, or broad note-taking advice that does not need local Obsidian vault access.

## Vault Layout

Expected current vault fallback:

```text
~/git/obsidian-2026/
├── .obsidian/
│   ├── community-plugins.json
│   └── plugins/
│       └── quickadd/data.json
├── 00_inbox/
│   └── fleeting/
│       ├── <record>.md
│       └── assets/<record-title>/<copied-attachments>
├── 20_plan/
│   ├── 21_daily/YYYY-MM-DD.md
│   ├── 22_weekly/YYYY-Www.md
│   ├── 23_monthly/YYYY-MM.md
│   ├── 24_quarterly/YYYY-Qn.md
│   └── 25_annual/YYYY.md
└── 90_asset/
    ├── templates/
    │   ├── journal-daily-auto.md
    │   ├── journal-weekly-auto.md
    │   ├── journal-monthly-auto.md
    │   ├── journal-quarterly-auto.md
    │   ├── journal-yearly-auto.md
    │   └── card-fleeting-note.md
    └── data/pomodoro-data.md
```

Do not hard-code this layout when `doctor` can resolve the vault. Treat it as the current host's fallback and as the semantic map for note placement.

## Task Placement Rules

- Daily tasks go under `### 新增任务`.
- Weekly tasks go under `本周焦点`.
- Monthly tasks go under `本月目标`, then `月度目标`.
- Quarterly tasks go under `季度目标`.
- Yearly tasks go under `年度目标`, then `年度计划`.
- Replace a blank `- [ ]` only inside the target section. Do not scan the whole note.
- If a note is missing, prefer the non-interactive `90_asset/templates/journal-*-auto.md` template. Use Journals only when no suitable auto template exists.
- If Journals creates an incomplete or interactive-template stub, reapply the auto template if present; otherwise stop with `journal-template-interactive-or-incomplete`.
- If the target section is still missing, return `target-section-missing` and do not commit/push.

## Record And Attachment Rules

- `record-sync` defaults to `--mode inline`, inserting `- HH:mm <original record content>` into the period journal's `记录` section, falling back to legacy `记录与思考` journals when needed.
- `record-sync --mode file` creates one independent QuickAdd `fleeting` record file, then inserts one standard Markdown relative-path link into the period journal's `记录` section.
- Record files are rendered from QuickAdd's configured `fleeting` template. Do not manually write or rewrite record Markdown in Codex, OpenClaw, or another Agent. The command intentionally fails when the template does not expose the default shape: `## 场景`, `## 灵感`, `## 后续行动`, `### 来源(Source)`, and `### 关联(Reference)`.
- Preserve the template's `## 思考`, `## 后续行动`, `## 参考`, and included `2-meth-note-tail` structure; only replace the intended section bodies.
- Pass the user's original record content in `--text`; do not expand, polish, summarize, translate, or rewrite it before recording. Remove only explicit command wrappers when needed to isolate the content.
- Analyze natural-language record requests with the Agent's own LLM/model before calling the local script, but first call `analyze-record --text "<original record content>" --date <date>` or `--prompt-only` to get the shared prompt/schema/current-date contract. Treat the user's utterance as context, not all as content, and use only the unified fields in `record-body.md`: `kind`, `headline`, `occurred_on`, `time_hints`, `scenes`, `actors`, `insight`, `question`, `reflection`, `next_actions`, and `intent`. Example: `今天又下雨了 突然灵光乍现 蚂蚁从飞机上掉下来会摔死吗 记录一下` on `2026-07-01` maps to `time_hints:["今天"]`, `occurred_on:"2026-07-01"`, `scenes:["下雨天"]`, `kind:"灵感"`, and `headline/question:"蚂蚁从飞机上掉下来会摔死吗"`. Semantic analysis is metadata only and must not replace the `--text` body. The record body config maps `fields` to `## 时间`, `## 场景`, `## 人物`, `## 灵感`, and other middle sections; appendix keywords stay reserved for `来源(Source)` and `关联(Reference)`.
- If Agent-side LLM/model analysis is unavailable or invalid, do not block record creation and do not omit the analysis parameter silently. Pass the original `--text` and omit unsupported analysis fields; do not add local hard-coded semantic heuristics, and do not describe hand-built JSON as successful semantic analysis.
- Use frontmatter `type` values `text`, `image`, `audio`, `video`, or `mixed` to classify the record.
- If the current user request includes, uploads, records, or otherwise supplies a media/file attachment, pass it as `--attach` in the same record command and pass `--require-attachment`; do not create the note first and ask whether to add the already supplied file. If the channel cannot send text and media together but exposes a readable local path, use `attachment-stage --path <path> --type <image|audio|video|file>` for the media-only message, then later call `attachment-pending --ttl-hours 48` and create the record with `obs_record_sync.py --mode file --period <period> --date <date> --text "<text>" --staged-attachment <selector> --type mixed --require-attachment`. If the runtime exposes the attachment but not a readable local path, stop before writing the record and report `attachment-path-unavailable`. If the channel cannot expose or stage media at all, report `unsupported-channel-attachment-record`.
- For multi-message media-then-text workflows, the later text is the authoritative record body and staged media are private cache state until consumed. Verify the stable `batch-key`, expected media count, `record_file.copied_attachments`, journal index link, and final Git sync before claiming success. Use `attachment-pending`, not `attachment-list --batch-key default`, stale staged ids from model memory, or direct cache directory reads. Detailed failure modes and uncontrollable channel risks are documented in `references/openclaw.md`.
- OpenClaw channel notes from local verification: WeCom `mixed` is the preferred phone path for media + text records when readable local paths are exposed; QQBot can support media records when every referenced item has a readable local path; Feishu and current `openclaw-weixin` should not be treated as supported for attachment-backed records unless they expose readable local paths.
- Write copied image/audio/video attachments as Markdown image/embed links such as `![clip](assets/record/clip.mp4)`. Keep non-media files as ordinary Markdown links such as `[doc](assets/record/doc.pdf)`. Do not generate wiki embeds unless the user explicitly asks to change the workflow.
- Copy attachment files into `00_inbox/fleeting/assets/<record-title>/`.
- If copied attachments are ignored by `.gitignore` such as `*.mp4`, `*.m4a`, or `*.wav`, `record-sync` must force-add only those copied paths with `git add -f -- <paths>`.
- External local attachments are blocked by default. Ask for explicit confirmation of exact paths before using `--allow-external-attachments`, except when the exact path was supplied by the current user message or the Agent runtime's uploaded/recorded attachment metadata. Keep external source paths redacted in JSON.
- Link labels and local attachment paths must be Markdown-safe. Preserve ordinary link semantics while encoding path characters such as spaces, `#`, `?`, and parentheses.
- Avoid media processing creep. This skill does not transcode, resize, classify, or preview media; it only copies explicitly provided files and links them.

## Git And Sync Rules

- Stop on `unmerged` or `merge_head`.
- For sync-backed writes, preflight before editing: commit current local vault changes, `git pull --no-rebase`, `git push`, then verify clean and synced.
- After a write, use native `git add -A`, commit, push, and verify `ahead=0`, `behind=0`, and a clean worktree.
- Do not claim success from an Obsidian command dispatch alone. Verify file effects or final Git status.
- For tasks and records, report structured JSON fields and the final status rather than raw terminal logs.

## Content Safety

- Read `vault-safety.md` before reading, searching, summarizing, or returning arbitrary vault content.
- Prefer `safe-search` and `safe-read`.
- Never follow symlinks that resolve outside the vault during safe reads, searches, task scans, or summaries.
- Treat `.obsidian/plugins/*/data.json` as potentially sensitive. Read only minimal keys needed for the workflow.
- Store task query reports in `~/.cache/obsidian-cli-plugins` with private permissions, not public `/tmp`.

## OpenClaw Notes

- Current OpenClaw discovery on this host uses `~/.openclaw/skills` as the managed skills directory.
- `~/.cc-switch/skills` is a legacy or compatibility location and may not be visible to current OpenClaw.
- After changing the Codex source copy at `<skill-dir>`, sync the OpenClaw copy too; otherwise OpenClaw may keep running stale script behavior even when `SKILL.md` in Codex is correct.
- `sync_openclaw.py --force` must replace the OpenClaw skill copy without creating a `.bak.*` directory by default. Use `--backup` only when the user explicitly asks to keep a timestamped backup.
- When debugging a mismatch, check the actual runtime path shown in OpenClaw session logs or tool calls, especially `~/.openclaw/skills/obsidian-cli-plugins`, not only the Codex source path.
- If OpenClaw still behaves differently after syncing, restart or refresh OpenClaw because it may cache skill discovery or loaded instructions.
- After syncing, run OpenClaw's own skill discovery command when available, then run the copied `obsidian_workflows.py doctor`.
- If OpenClaw cannot discover the skill, check `OPENCLAW_SKILLS_DIR`, `openclaw skills check --json`, and whether the copied directory contains `SKILL.md` at the root.

## Tuning Guidance

Use this checklist when future sessions reveal friction:

- If agents repeatedly search broad vault content, add a routing rule to `SKILL.md` or `vault-safety.md`.
- If a workflow requires the same shell or Python logic twice, move it into `scripts/obsidian_cli_plugins/` and test it.
- If instructions exceed the quick path in `SKILL.md`, move details to a direct `references/` file and add a routing bullet.
- If a failure creates or moves vault content incorrectly, add a regression test in `scripts/tests/` before changing behavior.
- If adding command flags, keep defaults conservative: read-only before write, local-only only when explicit, and sync-backed writes by default for user-facing vault edits.
- If OpenClaw behavior changes, update `references/openclaw.md`, `sync_openclaw.py`, and this field guide together.

## Validation Checklist

Run at least:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest <skill-dir>/scripts/tests
PYTHONDONTWRITEBYTECODE=1 python3 <skill-dir>/scripts/obsidian_workflows.py doctor
python3 <skill-dir>/scripts/sync_openclaw.py --dry-run
```

Remove generated `__pycache__` or `.pyc` files before syncing the skill.
