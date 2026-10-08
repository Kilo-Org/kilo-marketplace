import datetime as dt
import re

from .journals import target_date


WEEKDAY_ALIASES = {
    "一": 0,
    "1": 0,
    "二": 1,
    "2": 1,
    "三": 2,
    "3": 2,
    "四": 3,
    "4": 3,
    "五": 4,
    "5": 4,
    "六": 5,
    "6": 5,
    "日": 6,
    "天": 6,
    "7": 6,
}
ENGLISH_WEEKDAY_ALIASES = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}
CHINESE_NUMERAL_ALIASES = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}
RELATIVE_DATE_OFFSETS = {
    "大后天": 3,
    "后天": 2,
    "明天": 1,
    "今天": 0,
    "今日": 0,
}

TASK_KIND_RULES = [
    ("study", ("考试", "备考", "学习", "读书", "课程", "证书", "复习", "刷题")),
    ("life", ("生日", "家庭", "家人", "吃饭", "一日三餐", "体检", "看病", "医院", "还款", "缴费", "刷鞋", "健康", "锻炼", "买菜")),
    ("agent", ("技能", "agent", "Codex", "Obsidian命令", "自动化", "脚本", "插件")),
    ("work", ("工作", "会议", "项目", "需求", "缺陷", "bug", "Bug", "MR", "mr", "分支", "提交", "发布", "上线", "报告")),
]


def infer_task_kind(text: str, explicit_kind: str | None) -> str:
    if explicit_kind and explicit_kind != "auto":
        return explicit_kind
    existing = re.search(r"#(work|agent|life|study)\b", text)
    if existing:
        return existing.group(1)
    for kind, keywords in TASK_KIND_RULES:
        if any(keyword in text for keyword in keywords):
            return kind
    return "work"


def has_task_date_marker(text: str) -> bool:
    return any(marker in text for marker in ("🛫", "⏳", "📅", "➕"))


def date_or_none(year: int, month: int, day: int) -> dt.date | None:
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def infer_task_date_from_clue(text: str, base: dt.date) -> dt.date | None:
    if has_task_date_marker(text):
        return None
    explicit = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
    if explicit:
        return date_or_none(int(explicit.group(1)), int(explicit.group(2)), int(explicit.group(3)))
    month_day = re.search(r"(?<!\d)(\d{1,2})[-/月](\d{1,2})(?:日|号)?", text)
    if month_day:
        return date_or_none(base.year, int(month_day.group(1)), int(month_day.group(2)))
    days_ago = re.search(r"(?<!\d)(\d{1,3})(?:\s*)(?:天|日)前", text)
    if days_ago:
        return base - dt.timedelta(days=int(days_ago.group(1)))
    english_days_ago = re.search(r"\b(\d{1,3})\s+days?\s+ago\b", text, re.IGNORECASE)
    if english_days_ago:
        return base - dt.timedelta(days=int(english_days_ago.group(1)))
    chinese_days_ago = re.search(r"([一二两三四五六七八九十])(?:天|日)前", text)
    if chinese_days_ago:
        return base - dt.timedelta(days=CHINESE_NUMERAL_ALIASES[chinese_days_ago.group(1)])
    relative_month_day = re.search(r"(下下个月|下个月|下月|本月|这个月|上个月|上月)(\d{1,2})(?:日|号)", text)
    if relative_month_day:
        offset = {
            "上个月": -1,
            "上月": -1,
            "本月": 0,
            "这个月": 0,
            "下个月": 1,
            "下月": 1,
            "下下个月": 2,
        }[relative_month_day.group(1)]
        target_month = shift_months(base.replace(day=1), offset)
        day = int(relative_month_day.group(2))
        max_day = month_end(target_month.year, target_month.month).day
        return dt.date(target_month.year, target_month.month, min(max(day, 1), max_day))
    for phrase, offset in RELATIVE_DATE_OFFSETS.items():
        if phrase in text:
            return base + dt.timedelta(days=offset)
    prefixed_weekday = re.search(r"(上周|上星期|上礼拜|下周|下星期|下礼拜|本周|这周|本星期|这星期|本礼拜|这礼拜)([一二三四五六日天1-7])", text)
    if prefixed_weekday:
        prefix = prefixed_weekday.group(1)
        monday = base - dt.timedelta(days=base.weekday())
        if prefix in {"上周", "上星期", "上礼拜"}:
            monday -= dt.timedelta(days=7)
        elif prefix in {"下周", "下星期", "下礼拜"}:
            monday += dt.timedelta(days=7)
        return monday + dt.timedelta(days=WEEKDAY_ALIASES[prefixed_weekday.group(2)])
    weekday = re.search(r"(上周|上星期|上礼拜|下周|下星期|下礼拜|本周|这周|本星期|这星期|本礼拜|这礼拜)?(?:周|星期|礼拜)([一二三四五六日天1-7])", text)
    if weekday:
        prefix = weekday.group(1) or "本周"
        monday = base - dt.timedelta(days=base.weekday())
        if prefix in {"上周", "上星期", "上礼拜"}:
            monday -= dt.timedelta(days=7)
        elif prefix in {"下周", "下星期", "下礼拜"}:
            monday += dt.timedelta(days=7)
        return monday + dt.timedelta(days=WEEKDAY_ALIASES[weekday.group(2)])
    english_weekday = re.search(r"\b(last|this|next)?\s*(monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|saturday|sat|sunday|sun)\b", text, re.IGNORECASE)
    if english_weekday:
        prefix = (english_weekday.group(1) or "this").lower()
        monday = base - dt.timedelta(days=base.weekday())
        if prefix == "last":
            monday -= dt.timedelta(days=7)
        elif prefix == "next":
            monday += dt.timedelta(days=7)
        return monday + dt.timedelta(days=ENGLISH_WEEKDAY_ALIASES[english_weekday.group(2).lower()])
    return None


def month_end(year: int, month: int) -> dt.date:
    if month == 12:
        next_month = dt.date(year + 1, 1, 1)
    else:
        next_month = dt.date(year, month + 1, 1)
    return next_month - dt.timedelta(days=1)


def shift_months(date: dt.date, months: int) -> dt.date:
    total_month = date.year * 12 + date.month - 1 + months
    year, month_index = divmod(total_month, 12)
    month = month_index + 1
    return dt.date(year, month, min(date.day, month_end(year, month).day))


def subtract_months(date: dt.date, months: int) -> dt.date:
    return shift_months(date, -months)


def week_default_task_dates(base: dt.date) -> dict[str, dt.date]:
    start = base - dt.timedelta(days=base.weekday())
    scheduled = start + dt.timedelta(days=4)
    due = start + dt.timedelta(days=6)
    return {"start": start, "scheduled": scheduled, "due": due}


def month_default_task_dates(base: dt.date) -> dict[str, dt.date]:
    start = base.replace(day=1)
    due = month_end(base.year, base.month)
    scheduled = due - dt.timedelta(days=5)
    return {"start": start, "scheduled": scheduled, "due": due}


def quarter_default_task_dates(base: dt.date) -> dict[str, dt.date]:
    quarter = (base.month - 1) // 3
    start_month = quarter * 3 + 1
    end_month = start_month + 2
    start = dt.date(base.year, start_month, 1)
    due = month_end(base.year, end_month)
    scheduled = due - dt.timedelta(days=15)
    return {"start": start, "scheduled": scheduled, "due": due}


def year_default_task_dates(base: dt.date) -> dict[str, dt.date]:
    start = dt.date(base.year, 1, 1)
    due = dt.date(base.year, 12, 31)
    scheduled = subtract_months(due, 2)
    return {"start": start, "scheduled": scheduled, "due": due}


def single_day_task_dates(date: dt.date) -> dict[str, dt.date]:
    return {"start": date, "due": date}


def resolve_new_task_dates(text: str, base: dt.date, period: str, explicit_date: str | None) -> dict[str, dt.date] | None:
    if explicit_date:
        return single_day_task_dates(target_date(explicit_date))
    if has_task_date_marker(text):
        return None
    inferred = infer_task_date_from_clue(text, base)
    if inferred:
        return single_day_task_dates(inferred)
    if period == "week":
        return week_default_task_dates(base)
    if period == "month":
        return month_default_task_dates(base)
    if period == "quarter":
        return quarter_default_task_dates(base)
    if period == "year":
        return year_default_task_dates(base)
    return single_day_task_dates(base)


def task_line(text: str, kind: str, dates: dict[str, dt.date] | None, done: bool = False) -> str:
    body = text.strip()
    if "#task" not in body:
        if re.search(r"#\w+", body):
            body = f"#task {body}"
        else:
            body = f"#task #{kind} {body}"
    checkbox = "x" if done else " "
    if dates and not has_task_date_marker(body):
        parts = []
        if dates.get("start"):
            parts.append(f"🛫 {dates['start'].isoformat()}")
        if dates.get("scheduled"):
            parts.append(f"⏳ {dates['scheduled'].isoformat()}")
        if dates.get("due"):
            parts.append(f"📅 {dates['due'].isoformat()}")
        if parts:
            body = f"{body} {' '.join(parts)}"
    return f"- [{checkbox}] {body}"


def serialize_task_dates(dates: dict[str, dt.date] | None) -> dict[str, str] | None:
    if not dates:
        return None
    return {key: value.isoformat() for key, value in dates.items()}
