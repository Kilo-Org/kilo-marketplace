import datetime as dt
import json
import pathlib
import re
from typing import Any

from .journals import heading_info, period_path, target_section_titles
from .utils import iter_vault_markdown_files


TASK_RE = re.compile(r"^[ \t]*[-*][ \t]+\[[ xX/-]\][ \t]+.*#task\b.*$", re.MULTILINE)
TASK_LINE_RE = re.compile(r"^(?P<indent>[ \t]*)[-*][ \t]+\[(?P<status>.)\][ \t]+(?P<body>.*)$")
TASK_DATE_PATTERNS = {
    "due": re.compile(r"📅\s*(\d{4}-\d{2}-\d{2})"),
    "scheduled": re.compile(r"⏳\s*(\d{4}-\d{2}-\d{2})"),
    "start": re.compile(r"🛫\s*(\d{4}-\d{2}-\d{2})"),
    "created": re.compile(r"➕\s*(\d{4}-\d{2}-\d{2})"),
    "done": re.compile(r"✅\s*(\d{4}-\d{2}-\d{2})"),
    "cancelled": re.compile(r"❌\s*(\d{4}-\d{2}-\d{2})"),
}
TASK_PRIORITY_ORDER = {"⏫": 0, "🔺": 1, "🔼": 1, "🔽": 3, "⏬": 4}
SENSITIVE_PATH_RE = re.compile(
    r"(^|/)(90_asset/keepassxc|\.env$|\.gitcredentials$|.*(?:password|passwd|secret|token|apikey|api-key|private-key|credential|credentials|keepass).*)",
    re.IGNORECASE,
)


def is_sensitive_vault_path(relative_path: str) -> bool:
    return bool(SENSITIVE_PATH_RE.search(relative_path))


def read_tasks(note: pathlib.Path) -> list[str]:
    if not note.exists():
        return []
    return TASK_RE.findall(note.read_text(encoding="utf-8"))


def task_status_map(path: pathlib.Path) -> dict[str, str]:
    data = path / ".obsidian/plugins/obsidian-tasks-plugin/data.json"
    fallback = {" ": "TODO", "/": "IN_PROGRESS", "x": "DONE", "X": "DONE", "-": "CANCELLED"}
    if not data.exists():
        return fallback
    try:
        settings = json.loads(data.read_text(encoding="utf-8"))
        result = dict(fallback)
        status_settings = settings.get("statusSettings", {})
        for entry in status_settings.get("coreStatuses", []) + status_settings.get("customStatuses", []):
            symbol = entry.get("symbol")
            stype = entry.get("type")
            if symbol is not None and stype:
                result[symbol] = stype
        return result
    except Exception:
        return fallback


def parse_task_date(value: str | None) -> dt.date | None:
    return dt.date.fromisoformat(value) if value else None


def parse_task_dates(body: str) -> dict[str, dt.date | None]:
    result: dict[str, dt.date | None] = {}
    for key, pattern in TASK_DATE_PATTERNS.items():
        match = pattern.search(body)
        result[key] = parse_task_date(match.group(1)) if match else None
    return result


def all_vault_tasks(path: pathlib.Path) -> list[dict[str, Any]]:
    statuses = task_status_map(path)
    tasks: list[dict[str, Any]] = []
    for note, rel in iter_vault_markdown_files(path):
        if rel.startswith(".obsidian/") or is_sensitive_vault_path(rel):
            continue
        try:
            lines = note.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(lines, 1):
            match = TASK_LINE_RE.match(line)
            if not match:
                continue
            body = match.group("body")
            if "#task" not in body:
                continue
            symbol = match.group("status")
            tasks.append(
                {
                    "line_text": line.strip(),
                    "body": body,
                    "status": symbol,
                    "status_type": statuses.get(symbol, "UNKNOWN"),
                    "dates": parse_task_dates(body),
                    "recurring": "🔁" in body,
                    "path": rel,
                    "line": line_no,
                }
            )
    return tasks


def task_happens_on(task: dict[str, Any], date: dt.date) -> bool:
    return any(value == date for value in task["dates"].values() if value is not None)


def week_bounds(date: dt.date) -> tuple[dt.date, dt.date]:
    start = date - dt.timedelta(days=date.weekday())
    return start, start + dt.timedelta(days=6)


def task_happens_between(task: dict[str, Any], start: dt.date, end: dt.date) -> bool:
    return any(start <= value <= end for value in task["dates"].values() if value is not None)


def task_sort_key(task: dict[str, Any]) -> tuple[Any, ...]:
    body = task["body"]
    priority = min([order for marker, order in TASK_PRIORITY_ORDER.items() if marker in body] or [2])
    due = task["dates"].get("due") or dt.date.max
    scheduled = task["dates"].get("scheduled") or dt.date.max
    return (priority, due, scheduled, task["path"], task["line"])


def query_today_tasks(path: pathlib.Path, date: dt.date) -> dict[str, Any]:
    selected = []
    categories: dict[str, list[dict[str, Any]]] = {
        "today_related": [],
        "overdue_unfinished": [],
        "recurring": [],
    }
    for task in all_vault_tasks(path):
        dates = task["dates"]
        happens = task_happens_on(task, date)
        overdue = (
            task["status_type"] in {"TODO", "IN_PROGRESS"}
            and (
                (dates.get("due") is not None and dates["due"] < date)
                or (dates.get("scheduled") is not None and dates["scheduled"] < date)
            )
        )
        recurring = task["status_type"] in {"TODO", "IN_PROGRESS"} and task["recurring"]
        if happens or overdue or recurring:
            selected.append(task)
            if happens:
                categories["today_related"].append(task)
            elif recurring:
                categories["recurring"].append(task)
            elif overdue:
                categories["overdue_unfinished"].append(task)
    groups: dict[str, list[dict[str, Any]]] = {}
    for task in sorted(selected, key=task_sort_key):
        groups.setdefault(task["status_type"], []).append(task)
    for key, tasks in categories.items():
        categories[key] = sorted(tasks, key=task_sort_key)
    status_counts = {key: len(value) for key, value in groups.items()}
    category_counts = {key: len(value) for key, value in categories.items()}
    return {
        "date": date.isoformat(),
        "query": "(happens in today) OR (((status.type is TODO) OR (status.type is IN_PROGRESS)) AND ((due before today) OR (scheduled before today) OR (is recurring)))",
        "total": len(selected),
        "summary": {
            "total": len(selected),
            "status_counts": status_counts,
            "category_counts": category_counts,
        },
        "categories": categories,
        "groups": groups,
    }


def weekly_focus_plain_checkboxes(path: pathlib.Path, date: dt.date) -> list[dict[str, Any]]:
    note = period_path(path, "week", date)
    if not note.exists():
        return []
    result: list[dict[str, Any]] = []
    lines = note.read_text(encoding="utf-8").splitlines()
    in_focus = False
    for line_no, line in enumerate(lines, 1):
        info = heading_info(line)
        if info:
            in_focus = info[1] == "本周焦点"
            continue
        stripped = line.strip()
        if in_focus and re.match(r"^[-*]\s+\[[ xX/-]\]\s+", stripped) and "#task" not in stripped:
            result.append(
                {
                    "line_text": stripped,
                    "path": note.relative_to(path).as_posix(),
                    "line": line_no,
                }
            )
    return result


def query_week_tasks(path: pathlib.Path, date: dt.date) -> dict[str, Any]:
    start, end = week_bounds(date)
    selected = [task for task in all_vault_tasks(path) if task_happens_between(task, start, end)]
    plain_focus = weekly_focus_plain_checkboxes(path, date)
    groups: dict[str, list[dict[str, Any]]] = {}
    for task in sorted(selected, key=task_sort_key):
        groups.setdefault(task["status_type"], []).append(task)
    status_counts = {key: len(value) for key, value in groups.items()}
    iso = date.isocalendar()
    return {
        "date": date.isoformat(),
        "week": f"{iso.year}-W{iso.week:02d}",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "query": "happens this week",
        "total": len(selected),
        "summary": {
            "total": len(selected),
            "status_counts": status_counts,
            "plain_focus_count": len(plain_focus),
        },
        "groups": groups,
        "plain_focus": plain_focus,
    }

def append_task_to_note(note: pathlib.Path, line: str, period: str = "day") -> dict[str, Any]:
    target_titles = target_section_titles(period)
    if not note.exists():
        raise FileNotFoundError(f"Target journal note does not exist: {note}")
    current = note.read_text(encoding="utf-8")
    lines = current.splitlines()
    section_index = None
    section_level = None
    section_title = None
    headings = []
    for index, existing in enumerate(lines):
        info = heading_info(existing)
        if info:
            headings.append((index, info[0], info[1]))
    for title in target_titles:
        for index, level, existing_title in headings:
            if existing_title == title:
                section_index = index
                section_level = level
                section_title = existing_title
                break
        if section_index is not None:
            break
    if section_index is None:
        return {
            "ok": False,
            "reason": "target-section-missing",
            "note": str(note),
            "task": line,
            "section": None,
            "target_sections": target_titles,
        }
    insert_index = None
    if section_index is not None and section_level is not None:
        insert_index = len(lines)
        for index in range(section_index + 1, len(lines)):
            info = heading_info(lines[index])
            if info and info[0] <= section_level:
                insert_index = index
                break
    placeholder_index = None
    # Only target placeholders inside the intended task section. Other sections
    # such as "### 改进" may use blank checkboxes for reflection notes.
    if section_index is not None:
        start = section_index + 1
        stop = insert_index if insert_index is not None else len(lines)
        for index, existing in enumerate(lines[start:stop], start):
            if existing.strip() in {"- [ ]", "- [ ] #task"}:
                placeholder_index = index
                break
    if placeholder_index is not None:
        lines[placeholder_index] = line
        note.write_text("\n".join(lines) + ("\n" if current.endswith("\n") else ""), encoding="utf-8")
    else:
        if insert_index is not None:
            for index in range(section_index + 1, insert_index):
                if lines[index].lstrip().startswith(">"):
                    insert_index = index
                    break
            while insert_index > section_index + 1 and lines[insert_index - 1].strip() == "":
                insert_index -= 1
            lines.insert(insert_index, line)
            note.write_text("\n".join(lines) + ("\n" if current.endswith("\n") else ""), encoding="utf-8")
        else:
            sep = "" if current.endswith("\n") else "\n"
            note.write_text(current + sep + line + "\n", encoding="utf-8")
    return {"ok": True, "note": str(note), "created": False, "task": line, "section": section_title}
