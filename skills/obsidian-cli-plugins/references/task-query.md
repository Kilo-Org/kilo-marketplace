# Obsidian Task Query Workflows

Use this file for todo/task queries. Use `task-add.md` for adding tasks.

## Newly added tasks in today's daily note

Use this compact workflow for `今日新增待办`, `今天新增任务`, `今日新增任务`, or tasks directly written into today's daily note:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py tasks show --period day --date today
```

Interpret the result as raw task lines in today's daily note target section, usually `### 新增任务`. Return the `count`, task lines, and note path only. If `exists=false` or `count=0`, report that there are no newly added tasks for the daily note.

This is not the same as the full `今日待办` Tasks query. Do not run `today-tasks --source`, `safe-search "➕ YYYY-MM-DD"`, or broad vault reads unless the user explicitly asks for the full today list, asks for creation-date semantics, or requests additional verification.

## Full today todo report

Use this when the user asks for `今日待办`, `今天待办`, overdue tasks, recurring tasks, or a full Tasks query report:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py today-tasks --source
```

The command pulls latest content unless `--no-sync` is passed, writes private cache files under `~/.cache/obsidian-cli-plugins`, and prints the full Markdown report.

Interpret it as the daily note's `今日待办` Tasks query:

```tasks
(happens in today) OR (((status.type is TODO) OR (status.type is IN_PROGRESS)) AND ((due before today) OR (scheduled before today) OR (is recurring)))
sort by priority due scheduled
group by status.type
hide postpone button
hide task count
short mode
```

Display these sections by default:

- `结果汇总`: total, status counts, and category counts.
- `今日相关`: tasks in `categories.today_related`.
- `逾期未完成`: tasks in `categories.overdue_unfinished`.
- `循环任务`: tasks in `categories.recurring`.

Include concrete data, including `逾期未完成`; do not replace results with only a file link unless the user asks for a compact summary. If `total=0`, ask whether to add a task and request task text.

## Weekly todo report

Use this for `本周待办`, `本周任务`, or equivalent full weekly queries:

```bash
python3 <skill-dir>/scripts/obsidian_workflows.py week-tasks --source
```

The command pulls latest content unless `--no-sync` is passed, writes private cache files under `~/.cache/obsidian-cli-plugins`, and prints the full Markdown report.

Interpret it as the weekly note's `本周任务` Tasks query: `happens this week`.

Display these sections by default:

- `结果汇总`: week range, total, status counts, Git sync status, and plain focus count.
- Status groups: `TODO`, `IN_PROGRESS`, `DONE`, `CANCELLED`, and `UNKNOWN` when present.
- `本周焦点中的非 #task 项`: checkbox items under `本周焦点` that do not contain `#task`.

Do not silently merge non-`#task` focus items into Tasks results. They are visible planning checkboxes but are outside the Tasks plugin query until converted to Tasks format with `#task` and dates.

Use `tasks show` only for raw task lines written directly in the current period note, usually under `新增任务`; prefer it for "新增待办" queries to avoid large full-report outputs.
