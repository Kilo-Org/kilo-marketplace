from typing import Any


def compact_task_line(task: dict[str, Any]) -> str:
    line = task["line_text"].strip()
    if line.startswith("- "):
        line = line[2:].strip()
    return line


def format_task_section(title: str, tasks: list[dict[str, Any]], include_source: bool) -> list[str]:
    lines = [f"## {title} ({len(tasks)})"]
    if not tasks:
        lines.append("")
        lines.append("_无_")
        lines.append("")
        return lines
    for index, task in enumerate(tasks, 1):
        source = f"  ({task['path']}:{task['line']})" if include_source else ""
        lines.append(f"{index}. {compact_task_line(task)}{source}")
    lines.append("")
    return lines


def format_today_report(result: dict[str, Any], sync: dict[str, Any] | None = None, include_source: bool = False) -> str:
    summary = result["summary"]
    status_counts = summary["status_counts"]
    category_counts = summary["category_counts"]
    lines = [
        f"# 今日待办列表 {result['date']}",
        "",
        "## 结果汇总",
        "",
        f"- 总计: {summary['total']}",
        f"- TODO: {status_counts.get('TODO', 0)}",
        f"- IN_PROGRESS: {status_counts.get('IN_PROGRESS', 0)}",
        f"- DONE: {status_counts.get('DONE', 0)}",
        f"- 今日相关: {category_counts.get('today_related', 0)}",
        f"- 逾期未完成: {category_counts.get('overdue_unfinished', 0)}",
        f"- 循环任务: {category_counts.get('recurring', 0)}",
    ]
    if sync is not None:
        after = sync.get("after", {})
        lines.extend(
            [
                f"- Git 同步: {'正常' if sync.get('ok') else '异常'}",
                f"- Git 状态: ahead {after.get('ahead', '?')}, behind {after.get('behind', '?')}",
            ]
        )
    lines.append("")
    categories = result["categories"]
    lines.extend(format_task_section("今日相关", categories["today_related"], include_source))
    lines.extend(format_task_section("逾期未完成", categories["overdue_unfinished"], include_source))
    lines.extend(format_task_section("循环任务", categories["recurring"], include_source))
    return "\n".join(lines)


def format_week_report(result: dict[str, Any], sync: dict[str, Any] | None = None, include_source: bool = False) -> str:
    summary = result["summary"]
    status_counts = summary["status_counts"]
    lines = [
        f"# 本周待办列表 {result['week']}",
        "",
        "## 结果汇总",
        "",
        f"- 周期: {result['start']} 至 {result['end']}",
        f"- 查询: `{result['query']}`",
        f"- 总计: {summary['total']}",
        f"- TODO: {status_counts.get('TODO', 0)}",
        f"- IN_PROGRESS: {status_counts.get('IN_PROGRESS', 0)}",
        f"- DONE: {status_counts.get('DONE', 0)}",
        f"- CANCELLED: {status_counts.get('CANCELLED', 0)}",
        f"- 本周焦点非 #task 项: {summary['plain_focus_count']}",
    ]
    if sync is not None:
        after = sync.get("after", {})
        lines.extend(
            [
                f"- Git 同步: {'正常' if sync.get('ok') else '异常'}",
                f"- Git 状态: ahead {after.get('ahead', '?')}, behind {after.get('behind', '?')}",
            ]
        )
    lines.append("")
    groups = result["groups"]
    for status in ("TODO", "IN_PROGRESS", "DONE", "CANCELLED", "UNKNOWN"):
        if status in groups:
            lines.extend(format_task_section(status, groups[status], include_source))
    if result["plain_focus"]:
        lines.append("## 本周焦点中的非 #task 项")
        lines.append("")
        for item in result["plain_focus"]:
            source = f"  ({item['path']}:{item['line']})" if include_source else ""
            lines.append(f"- {item['line_text']}{source}")
        lines.append("")
    return "\n".join(lines)
