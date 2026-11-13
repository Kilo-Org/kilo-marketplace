# Obsidian Task Add Workflows

Use this file when adding daily, weekly, monthly, quarterly, or yearly tasks.

## Command

Default to sync-backed task addition:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py add-task-sync --period <day|week|month|quarter|year> --date today --kind auto --text "<task text>"
```

Use local-only writes only when the user explicitly asks for no commit, no pull, no push, or local-only behavior:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py tasks add --period <period> --date <date> --kind auto --text "<task text>"
```

## Task line format

Prefer Tasks plugin compatible Markdown:

```markdown
- [ ] #task #work 合并mr1分支到xcgz分支 🛫 2026-06-29 📅 2026-06-29
```

Conventions:

- `#task` is required for task discovery.
- `#work`, `#agent`, `#life`, `#study`, or another domain tag follows `#task`.
- `🛫 YYYY-MM-DD` is the start date.
- `⏳ YYYY-MM-DD` is the scheduled/planned date.
- `📅 YYYY-MM-DD` is the due date.
- Preserve existing task lines exactly unless the user asks to edit them.

## Natural language analysis

Before adding a task, decide:

1. Time clue: parse specific dates, relative dates, weekdays, relative month days, and period words.
2. Target period and note: choose `day`, `week`, `month`, `quarter`, or `year`, then choose the note date that contains the task date or requested period.
3. Task type/tag: use explicit `#tag` if present, explicit `--kind` if provided, otherwise pass `--kind auto`.
4. Task dates: use single-day dates for concrete dates; use period default ranges only when the user asks for a period task without a concrete date.
5. Journal creation: if the chosen note does not exist, create it from the period's non-interactive `90_asset/templates/journal-*-auto.md` template and verify the expected file exists and contains the target task section before writing.
6. Verification: after writing, inspect the target section and Git status; do not claim success unless the note contains the expected task line and Git is clean/synced after push.

Task kind inference:

- `#work`: work, meeting, project, requirement, defect, bug, branch, commit, release, report.
- `#study`: exam, study, reading, course, certificate, review, practice questions.
- `#life`: birthday, family, personal reminder, meal, health, hospital, repayment, bill, housework, exercise.
- `#agent`: skill, plugin, script, automation, Codex, Obsidian command workflow.

If several categories match, prefer an explicit tag in text, then explicit `--kind`, then the most specific domain (`study`/`life`/`agent`) before `work`.

## Date inference

Treat `--date` as the period note selection date. Infer `🛫`, `⏳`, and `📅` from text unless the user provides explicit Tasks plugin dates or `--task-date`.

Supported date clues:

- Relative days: `今天`, `今日`, `明天`, `后天`, `大后天`.
- Relative past days: `3天前`, `三天前`, `3 days ago`; resolve backwards from `--date`.
- Weekdays: `周五`, `本周五`, `星期五`, `礼拜五`; resolve to that weekday in the same week as `--date`.
- Previous/next week: `上周五`, `下周五`, `上星期五`, `下星期五`; resolve to the previous or next week.
- English weekdays: `last Friday`, `this Friday`, `next Monday`; resolve relative to `--date`.
- Relative month days: `本月12号`, `下个月12号`, `下月12号`, `下下个月12号`; resolve from the request date, then pass `--task-date` if selected period note differs.
- Explicit dates: `2026-07-03`, `7-3`, `7/3`, `7月3日`.

Examples on Monday `2026-06-29`:

- `周五刷鞋` writes to `20_plan/22_weekly/2026-W27.md` and generates `🛫 2026-07-03 📅 2026-07-03`.
- `上周五复盘` resolves to `2026-06-26`.
- `3天前回顾` resolves to `2026-06-26`.
- `next Monday plan` resolves to `2026-07-06`.
- `下个月12号有人过生日` resolves to `2026-07-12`; use `--period month --date 2026-07-01 --task-date 2026-07-12 --kind life`.

Period task defaults when text has no date clue, explicit Tasks date, or `--task-date`:

- Week: `🛫` Monday, `⏳` Friday, `📅` Sunday.
- Month: `🛫` month start, `⏳` five days before month end, `📅` month end.
- Quarter: `🛫` quarter start, `⏳` fifteen days before quarter end, `📅` quarter end.
- Year: `🛫` year start, `⏳` two months before year end, `📅` year end.

Explicit dates such as `7月3日体检` or `--task-date 2026-07-03` override period defaults.

## Placement guardrail

Write only inside the target task section:

- Missing journal notes must be created from the period's non-interactive auto template first. Use Journals plugin only when that auto template is unavailable.
- If Journals creates an incomplete stub because an interactive template prompt did not finish, reapply the auto template when present; otherwise stop with `journal-template-interactive-or-incomplete`.
- Daily notes prefer `### 新增任务`.
- Weekly notes prefer `本周焦点`.
- Monthly notes prefer `本月目标`, then `月度目标`.
- Quarterly notes prefer `季度目标`.
- Yearly notes prefer `年度目标`, then `年度计划`.
- Replace a blank `- [ ]` placeholder only if it is inside the target section.
- If the target section exists but has no placeholder, insert before the next heading at the same or higher level.
- Do not scan the whole note for blank checkboxes. Reflection sections such as `### 改进` can contain blank `- [ ]` lines.

If the target task section is still missing, return `target-section-missing` and do not commit/push.

## Sync-backed behavior

`add-task-sync` performs:

1. Git conflict check.
2. Preflight cleanup: commit local vault changes, `git pull --no-rebase`, `git push`, then verify clean with `ahead=0`, `behind=0`.
3. Journal creation when needed.
4. Task date inference.
5. Target-section insertion.
6. Native `git add -A`, `git commit -m ...`, and `git push`.
7. JSON return with `ok`, preflight result, note path, journal creation result, task line, `task_date`, command outputs, and final Git status.

If `ok=false`, report the failing command output and do not claim the task was pushed.
