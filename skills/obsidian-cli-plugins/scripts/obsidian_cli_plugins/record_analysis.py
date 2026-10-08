import datetime as dt
import json
from typing import Any

from .records import ANALYSIS_FIELDS, ANALYSIS_LIST_FIELDS, LEGACY_ANALYSIS_FIELD_ALIASES, parse_record_analysis_json


CONTRACT_VERSION = "record-analysis/v1"


def record_analysis_schema() -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for field in ANALYSIS_FIELDS:
        if field in ANALYSIS_LIST_FIELDS:
            properties[field] = {
                "type": "array",
                "items": {"type": "string"},
                "description": "Use an empty array when absent.",
            }
        else:
            properties[field] = {
                "type": "string",
                "description": "Use an empty string or omit the field when absent.",
            }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ObsidianRecordAnalysis",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }


def golden_examples(current_date: str) -> list[dict[str, Any]]:
    return [
        {
            "text": "下午工作过程中，突然冒出一个想法 活着的意义是什么？",
            "analysis": {
                "kind": "灵感",
                "headline": "活着的意义是什么？",
                "occurred_on": current_date,
                "time_hints": ["下午"],
                "scenes": ["工作过程中"],
                "actors": [],
                "insight": "",
                "question": "活着的意义是什么？",
                "reflection": "",
                "next_actions": [],
                "intent": "记录",
            },
        },
        {
            "text": "今天又下雨了 突然灵光乍现 天上的雨是从哪里来的？",
            "analysis": {
                "kind": "灵感",
                "headline": "天上的雨是从哪里来的？",
                "occurred_on": current_date,
                "time_hints": ["今天"],
                "scenes": ["下雨天"],
                "actors": [],
                "insight": "",
                "question": "天上的雨是从哪里来的？",
                "reflection": "",
                "next_actions": [],
                "intent": "记录",
            },
        },
        {
            "text": "记一下 今天停车位在 B2-126",
            "analysis": {
                "kind": "事件",
                "headline": "停车位在 B2-126",
                "occurred_on": current_date,
                "time_hints": ["今天"],
                "scenes": ["停车"],
                "actors": [],
                "insight": "停车位在 B2-126",
                "question": "",
                "reflection": "",
                "next_actions": [],
                "intent": "记录",
            },
        },
    ]


def build_record_analysis_prompt(text: str, current_date: str, timezone: str) -> str:
    fields = ", ".join(ANALYSIS_FIELDS)
    return f"""你是 Obsidian 记录语义分析器。请只输出一个 JSON object，不要输出 Markdown 或解释。

当前日期：{current_date}
当前时区：{timezone}

任务：
从用户原始话语中提取记录元数据。原文仍会由脚本通过 --text 写入正文，所以不要改写、扩写、润色、翻译原文。

只能使用这些字段：
{fields}

字段规则：
- kind：记录类型，如“灵感”“摘录”“事件”“反思”。
- headline：简洁标题，优先使用核心问题或核心事实，不要使用完整上下文句。
- occurred_on：把“今天”等相对日期解析为当前日期，格式为 YYYY-MM-DD；没有日期时可留空。
- time_hints：保留自然语言时间线索，如“今天”“下午”“昨晚”。
- scenes：提取触发场景或上下文，如“工作过程中”“下雨天”“开车路上”。
- actors：只提取明确出现的人或实体，不要默认填“我”。
- insight：核心想法或事实；如果核心是问题，可以留空并填 question。
- question：原文中的核心问题。
- reflection：只在原文有反思内容时填写，不要代写。
- next_actions：只在原文有后续行动时填写。
- intent：通常为“记录”。

数组字段必须输出数组：time_hints、scenes、actors、next_actions。
不要使用旧字段名：{", ".join(sorted(LEGACY_ANALYSIS_FIELD_ALIASES))}。

用户原文：
{text}
"""


def analysis_json_payload(analysis: dict[str, Any]) -> dict[str, Any]:
    return {field: analysis[field] for field in ANALYSIS_FIELDS if field in analysis}


def record_analysis_contract(
    *,
    text: str,
    current_date: str,
    timezone: str,
    analysis_json: str | None = None,
) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "ok": True,
        "version": CONTRACT_VERSION,
        "context": {
            "current_date": current_date,
            "timezone": timezone,
        },
        "allowed_fields": ANALYSIS_FIELDS,
        "array_fields": sorted(ANALYSIS_LIST_FIELDS),
        "legacy_aliases": LEGACY_ANALYSIS_FIELD_ALIASES,
        "schema": record_analysis_schema(),
        "prompt": build_record_analysis_prompt(text, current_date, timezone),
        "golden_examples": golden_examples(current_date),
    }
    if analysis_json is not None:
        analysis = parse_record_analysis_json(analysis_json, text)
        contract["analysis"] = analysis
        contract["normalized_analysis_json"] = json.dumps(
            analysis_json_payload(analysis),
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return contract


def local_timezone_name() -> str:
    now = dt.datetime.now().astimezone()
    offset = now.strftime("%z")
    if offset:
        return f"UTC{offset[:3]}:{offset[3:]}"
    return now.tzname() or str(now.tzinfo or "local")
