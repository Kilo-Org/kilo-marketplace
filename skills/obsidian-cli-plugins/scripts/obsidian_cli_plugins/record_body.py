from __future__ import annotations

import json
import pathlib
from typing import Any


DEFAULT_RECORD_BODY_SECTIONS: list[dict[str, Any]] = [
    {
        "heading": "时间",
        "fields": ["occurred_on", "time_hints"],
        "formatter": "time",
        "on_missing": "blank",
    },
    {
        "heading": "场景",
        "fields": ["scenes"],
        "formatter": "scenes",
        "on_missing": "blank",
        "required": True,
    },
    {
        "heading": "人物",
        "fields": ["actors"],
        "formatter": "actors",
        "on_missing": "blank",
    },
    {
        "heading": "灵感",
        "fields": ["original_text", "question", "attachment_links"],
        "formatter": "insight",
        "on_missing": "blank",
        "required": True,
    },
    {
        "heading": "思考",
        "fields": ["reflection"],
        "formatter": "blank",
        "fill": "never",
        "on_missing": "blank",
    },
    {
        "heading": "后续行动",
        "fields": ["next_actions"],
        "formatter": "blank",
        "fill": "never",
        "on_missing": "blank",
        "required": True,
    },
]

FORMATTERS = {"time", "scenes", "actors", "insight", "bullets", "blank"}
ON_MISSING = {"blank", "preserve"}
FILL_POLICIES = {"auto", "never"}
RESERVED_APPENDIX_FIELDS = {
    "source",
    "sources",
    "source_links",
    "reference",
    "references",
    "reference_links",
    "term",
    "terms",
    "term_links",
    "target",
    "targets",
    "target_links",
    "task",
    "tasks",
    "task_links",
    "appendix",
    "appendix_sources",
    "appendix_references",
}


def load_record_body_sections(config_path: pathlib.Path | None = None) -> list[dict[str, Any]]:
    if config_path is None:
        return [dict(section) for section in DEFAULT_RECORD_BODY_SECTIONS]
    data = json.loads(config_path.read_text(encoding="utf-8"))
    sections = data.get("sections") if isinstance(data, dict) else data
    if not isinstance(sections, list):
        raise ValueError("record body config must be a list or an object with a sections list")
    return validate_record_body_sections(sections)


def validate_record_body_sections(sections: list[Any]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"section {index} must be an object")
        heading = str(section.get("heading", "")).strip()
        if not heading:
            raise ValueError(f"section {index} missing heading")
        formatter = str(section.get("formatter", "bullets")).strip()
        if formatter not in FORMATTERS:
            raise ValueError(f"section {heading} has unsupported formatter: {formatter}")
        on_missing = str(section.get("on_missing", "blank")).strip()
        if on_missing not in ON_MISSING:
            raise ValueError(f"section {heading} has unsupported on_missing: {on_missing}")
        fill = str(section.get("fill", "auto")).strip()
        if fill not in FILL_POLICIES:
            raise ValueError(f"section {heading} has unsupported fill: {fill}")
        if "sources" in section:
            raise ValueError(f"section {heading} must use fields, not sources")
        fields = section.get("fields", [])
        if isinstance(fields, str):
            fields = [fields]
        if not isinstance(fields, list) or any(not isinstance(item, str) or not item.strip() for item in fields):
            raise ValueError(f"section {heading} fields must be strings")
        field_names = [item.strip() for item in fields]
        reserved = [item for item in field_names if item in RESERVED_APPENDIX_FIELDS]
        if reserved:
            raise ValueError(f"section {heading} uses appendix-reserved fields: {','.join(reserved)}")
        cleaned.append(
            {
                "heading": heading,
                "fields": field_names,
                "formatter": formatter,
                "on_missing": on_missing,
                "fill": fill,
                "required": bool(section.get("required", False)),
                "label": str(section.get("label", "")).strip(),
            }
        )
    return cleaned


def required_body_headings(sections: list[dict[str, Any]]) -> list[str]:
    return [section["heading"] for section in sections if section.get("required")]


def list_value(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def field_values(context: dict[str, Any], fields: list[str]) -> list[str]:
    values: list[str] = []
    for field in fields:
        values.extend(list_value(context.get(field)))
    return values


def blank_lines() -> list[str]:
    return [""]


def section_lines(section: dict[str, Any], context: dict[str, Any]) -> list[str] | None:
    if section.get("fill") == "never":
        return blank_lines()
    formatter = section["formatter"]
    if formatter == "blank":
        return blank_lines()

    lines = format_section_lines(formatter, section, context)
    if lines:
        return ["", *lines, ""]
    if section.get("on_missing") == "preserve":
        return None
    return blank_lines()


def format_section_lines(formatter: str, section: dict[str, Any], context: dict[str, Any]) -> list[str]:
    fields = section.get("fields", [])
    if formatter == "time":
        lines = []
        for value in list_value(context.get("occurred_on")):
            lines.append(f"- 发生时间：{value}")
        for value in list_value(context.get("time_hints")):
            lines.append(f"- 时间线索：{value}")
        return lines
    if formatter == "scenes":
        return [f"- 触发场景：{value}" for value in field_values(context, fields or ["scenes"])]
    if formatter == "actors":
        return [f"- 相关人物：{value}" for value in field_values(context, fields or ["actors"])]
    if formatter == "insight":
        lines = [f"- 核心内容：{value}" for value in list_value(context.get("original_text"))]
        question = context.get("question")
        original = context.get("original_text")
        if question and question != original:
            lines.extend(f"- 待分析问题：{value}" for value in list_value(question))
        lines.extend(f"- 附件：{value}" for value in list_value(context.get("attachment_links")))
        return lines
    label = section.get("label")
    values = field_values(context, fields)
    if label:
        return [f"- {label}：{value}" for value in values]
    return [f"- {value}" for value in values]
