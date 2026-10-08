import datetime as dt
import pathlib
import re
import time
from typing import Any

from .constants import JOURNALS_COMMANDS, PLAN_DIRS
from .obsidian import obsidian_bin
from .utils import redact_text, run


class DateParseError(ValueError):
    pass


def target_date(value: str | None) -> dt.date:
    raw = (value or "today").strip()
    normalized = raw.lower()
    today = dt.date.today()
    aliases = {
        "today": 0,
        "today's": 0,
        "今天": 0,
        "今日": 0,
        "yesterday": -1,
        "yesterday's": -1,
        "昨天": -1,
        "昨日": -1,
        "tomorrow": 1,
        "tomorrow's": 1,
        "明天": 1,
        "明日": 1,
    }
    if normalized in aliases:
        return today + dt.timedelta(days=aliases[normalized])
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:
        raise DateParseError(
            f"Invalid date: {value!r}. Use YYYY-MM-DD, today, yesterday, or tomorrow."
        ) from exc


def period_path(path: pathlib.Path, period: str, date: dt.date) -> pathlib.Path:
    if period == "day":
        name = f"{date:%Y-%m-%d}.md"
    elif period == "week":
        iso = date.isocalendar()
        name = f"{iso.year}-W{iso.week:02d}.md"
    elif period == "month":
        name = f"{date:%Y-%m}.md"
    elif period == "quarter":
        quarter = (date.month - 1) // 3 + 1
        name = f"{date.year}-Q{quarter}.md"
    elif period == "year":
        name = f"{date.year}.md"
    else:
        raise SystemExit(f"Unsupported period: {period}")
    return path / PLAN_DIRS[period] / name


def quarter_number(date: dt.date) -> int:
    return (date.month - 1) // 3 + 1


def period_offset(period: str, target: dt.date, base: dt.date) -> int | None:
    if period == "day":
        return (target - base).days
    if period == "week":
        target_monday = target - dt.timedelta(days=target.weekday())
        base_monday = base - dt.timedelta(days=base.weekday())
        return (target_monday - base_monday).days // 7
    if period == "month":
        return (target.year - base.year) * 12 + target.month - base.month
    if period == "quarter":
        return (target.year - base.year) * 4 + quarter_number(target) - quarter_number(base)
    if period == "year":
        return target.year - base.year
    return None


def journals_command_for_period(period: str, date: dt.date) -> str | None:
    offset = period_offset(period, date, dt.date.today())
    return JOURNALS_COMMANDS.get(period, {}).get(offset)


def template_auto_path(vault_path: pathlib.Path, period: str) -> pathlib.Path:
    return vault_path / "90_asset/templates" / f"journal-{period_name(period)}-auto.md"


def period_name(period: str) -> str:
    return {
        "day": "daily",
        "week": "weekly",
        "month": "monthly",
        "quarter": "quarterly",
        "year": "annual",
    }.get(period, period)


def target_section_titles(period: str) -> list[str]:
    return {
        "day": ["新增任务", "待办"],
        "week": ["本周焦点", "新增任务", "待办"],
        "month": ["本月目标", "月度目标", "新增任务", "待办"],
        "quarter": ["季度目标", "新增任务", "待办"],
        "year": ["年度目标", "年度计划", "新增任务", "待办"],
    }.get(period, ["新增任务", "待办"])


def record_section_titles(_period: str) -> list[str]:
    return ["记录", "记录与思考"]


def heading_info(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s*(.*?)\s*$", line)
    if not match:
        return None
    return len(match.group(1)), re.sub(r"\s+", " ", match.group(2)).strip()


def note_has_target_section(note: pathlib.Path, period: str) -> bool:
    if not note.exists():
        return False
    headings = []
    for line in note.read_text(encoding="utf-8").splitlines():
        info = heading_info(line)
        if info:
            headings.append(info[1])
    return any(title in headings for title in target_section_titles(period))


def render_auto_template(template: str, note: pathlib.Path, vault_path: pathlib.Path, date: dt.date) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    title = note.stem
    try:
        category = note.parent.relative_to(vault_path).as_posix()
    except ValueError:
        category = note.parent.as_posix()
    values = {
        "title": title,
        "date": date.isoformat(),
        "category": category,
        "created": now,
        "updated": now,
    }
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered if rendered.endswith("\n") else rendered + "\n"


def apply_auto_template(vault_path: pathlib.Path, note: pathlib.Path, period: str, date: dt.date) -> dict[str, Any]:
    template = template_auto_path(vault_path, period)
    if not template.exists():
        return {
            "ok": False,
            "reason": "journal-template-interactive-or-incomplete",
            "auto_template": str(template),
        }
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(render_auto_template(template.read_text(encoding="utf-8"), note, vault_path, date), encoding="utf-8")
    return {
        "ok": note_has_target_section(note, period),
        "reason": None if note_has_target_section(note, period) else "auto-template-missing-target-section",
        "auto_template": str(template),
    }


def ensure_period_note(vault: str, vault_path: pathlib.Path, note: pathlib.Path, period: str, date: dt.date, wait: float) -> dict[str, Any]:
    if note.exists():
        return {"ok": True, "created": False, "note": str(note), "method": "existing"}
    template = apply_auto_template(vault_path, note, period, date)
    if template.get("ok"):
        return {
            "ok": True,
            "created": True,
            "note": str(note),
            "method": "auto-template",
            "template": template,
        }
    if note.exists():
        return {
            "ok": False,
            "created": True,
            "note": str(note),
            "method": "auto-template",
            "reason": template.get("reason"),
            "template": template,
        }
    command_id = journals_command_for_period(period, date)
    if command_id is None:
        return {
            "ok": False,
            "created": False,
            "note": str(note),
            "method": "journals",
            "reason": "unsupported-journals-period-offset",
            "period": period,
            "date": date.isoformat(),
        }
    cp = run([obsidian_bin(), "command", f"vault={vault}", f"id={command_id}"])
    time.sleep(wait)
    exists = note.exists()
    if exists and not note_has_target_section(note, period):
        template = apply_auto_template(vault_path, note, period, date)
        if not template.get("ok"):
            return {
                "ok": False,
                "created": True,
                "note": str(note),
                "method": "journals",
                "command": command_id,
                "output": redact_text(cp.stdout.strip()),
                "returncode": cp.returncode,
                "reason": template.get("reason"),
                "template": template,
            }
    return {
        "ok": exists,
        "created": exists,
        "note": str(note),
        "method": "journals",
        "command": command_id,
        "output": redact_text(cp.stdout.strip()),
        "returncode": cp.returncode,
        "reason": None if exists else "journals-command-did-not-create-expected-note",
        "template": template,
    }
