import datetime as dt
import json
import os
import pathlib
import re
import shutil
from typing import Any

from .journals import heading_info, record_section_titles
from .record_body import load_record_body_sections, required_body_headings, section_lines
from .utils import redact_path


DEFAULT_QUICKADD_CHOICE = "fleeting"
DEFAULT_AUTHOR = "dxshelley"
REQUIRED_APPENDIX_HEADINGS = ["来源(Source)", "关联(Reference)"]
ANALYSIS_FIELDS = [
    "kind",
    "headline",
    "occurred_on",
    "time_hints",
    "scenes",
    "actors",
    "insight",
    "question",
    "reflection",
    "next_actions",
    "intent",
]
ANALYSIS_LIST_FIELDS = {"time_hints", "scenes", "actors", "next_actions"}
LEGACY_ANALYSIS_FIELD_ALIASES = {
    "classification": "kind",
    "type": "kind",
    "title": "headline",
    "event_date": "occurred_on",
    "date": "occurred_on",
    "time_clues": "time_hints",
    "time_hint": "time_hints",
    "time": "time_hints",
    "scene": "scenes",
    "scenario": "scenes",
    "scenarios": "scenes",
    "people": "actors",
    "person": "actors",
    "persons": "actors",
    "inspiration": "insight",
    "idea": "insight",
    "issue": "question",
    "problem": "question",
    "action": "next_actions",
    "actions": "next_actions",
}


def normalize_heading_title(title: str) -> str:
    cleaned = re.sub(r"^[\s\W_]+", "", title, flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def markdown_url(path: str) -> str:
    normalized = path.replace("\\", "/")
    if re.match(r"^[a-z][a-z0-9+.-]*://", normalized, re.I):
        return normalized.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
    replacements = {
        "%": "%25",
        " ": "%20",
        "#": "%23",
        "?": "%3F",
        "(": "%28",
        ")": "%29",
        "<": "%3C",
        ">": "%3E",
    }
    return "".join(replacements.get(char, char) for char in normalized)


def markdown_label(label: str) -> str:
    return label.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def markdown_link(label: str, target: str) -> str:
    return f"[{markdown_label(label)}]({markdown_url(target)})"


def markdown_embed(label: str, target: str) -> str:
    return f"![{markdown_label(label)}]({markdown_url(target)})"


def relative_markdown_link(from_note: pathlib.Path, target: pathlib.Path, label: str) -> str:
    rel = pathlib.Path(
        os.path.relpath(target, start=from_note.parent)
    ).as_posix()
    return markdown_link(label, rel)


def relative_markdown_embed(from_note: pathlib.Path, target: pathlib.Path, label: str) -> str:
    rel = pathlib.Path(
        os.path.relpath(target, start=from_note.parent)
    ).as_posix()
    return markdown_embed(label, rel)


MEDIA_ATTACHMENT_EXTENSIONS = {
    ".3g2",
    ".3gp",
    ".aac",
    ".aif",
    ".aiff",
    ".apng",
    ".avi",
    ".avif",
    ".bmp",
    ".flac",
    ".flv",
    ".gif",
    ".heic",
    ".heif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".m4b",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpe",
    ".mpeg",
    ".mpg",
    ".oga",
    ".ogg",
    ".ogv",
    ".opus",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".ts",
    ".wav",
    ".webm",
    ".webp",
    ".wmv",
}


def is_media_attachment(target: str | pathlib.Path) -> bool:
    target_text = str(target)
    if re.match(r"^[a-z][a-z0-9+.-]*://", target_text, re.I):
        target_text = target_text.split("?", 1)[0].split("#", 1)[0]
    return pathlib.Path(target_text).suffix.lower() in MEDIA_ATTACHMENT_EXTENSIONS


def attachment_markdown_link(label: str, target: str, *, embed: bool) -> str:
    if embed:
        return markdown_embed(label, target)
    return markdown_link(label, target)


def relative_attachment_markdown_link(from_note: pathlib.Path, target: pathlib.Path, label: str) -> str:
    if is_media_attachment(target):
        return relative_markdown_embed(from_note, target, label)
    return relative_markdown_link(from_note, target, label)


def yaml_scalar(value: str | None) -> str:
    if value is None or value == "":
        return ""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def yaml_list(values: list[str]) -> list[str]:
    if not values:
        return []
    return [f"  - {yaml_scalar(value)}" for value in values]


def templater_date_format(fmt: str) -> str:
    return (
        fmt.replace("YYYY", "%Y")
        .replace("YY", "%y")
        .replace("MM", "%m")
        .replace("DD", "%d")
        .replace("HH", "%H")
        .replace("mm", "%M")
        .replace("ss", "%S")
    )


def safe_title(value: str, max_len: int = 80) -> str:
    title = re.sub(r"\s+", " ", value.strip()).strip()
    if not title:
        title = "未命名记录"
    return title[:max_len].rstrip()


def clean_analysis_scalar(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return re.sub(r"\s+", " ", value).strip()


def clean_analysis_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    cleaned = [clean_analysis_scalar(item) for item in values]
    return [item for item in cleaned if item]


def normalize_record_analysis(raw: dict[str, Any] | None, original: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"ok": False, "source": "skipped", "reason": "analysis-missing", "original": original}
    diagnostics: dict[str, Any] = {
        "unknown_fields": [],
        "legacy_fields": {},
        "invalid_fields": [],
        "missing_recommended": [],
    }
    unknown_fields = [
        key for key in raw
        if key not in ANALYSIS_FIELDS and key not in LEGACY_ANALYSIS_FIELD_ALIASES
    ]
    diagnostics["unknown_fields"] = sorted(unknown_fields)

    canonical: dict[str, str | list[str]] = {
        field: [] if field in ANALYSIS_LIST_FIELDS else "" for field in ANALYSIS_FIELDS
    }
    for field in ANALYSIS_FIELDS:
        if field not in raw:
            continue
        if field in ANALYSIS_LIST_FIELDS:
            canonical[field] = clean_analysis_list(raw.get(field))
        else:
            canonical[field] = clean_analysis_scalar(raw.get(field))
    for legacy, field in LEGACY_ANALYSIS_FIELD_ALIASES.items():
        if legacy not in raw:
            continue
        diagnostics["legacy_fields"][legacy] = field
        if field in ANALYSIS_LIST_FIELDS:
            existing = list(canonical[field]) if isinstance(canonical[field], list) else []
            additions = clean_analysis_list(raw.get(legacy))
            canonical[field] = existing or additions
        elif not canonical[field]:
            canonical[field] = clean_analysis_scalar(raw.get(legacy))

    kind = str(canonical["kind"])
    headline = str(canonical["headline"])
    occurred_on = str(canonical["occurred_on"])
    time_hints = list(canonical["time_hints"]) if isinstance(canonical["time_hints"], list) else []
    scenes = list(canonical["scenes"]) if isinstance(canonical["scenes"], list) else []
    actors = list(canonical["actors"]) if isinstance(canonical["actors"], list) else []
    insight = str(canonical["insight"])
    question = str(canonical["question"])
    reflection = str(canonical["reflection"])
    next_actions = list(canonical["next_actions"]) if isinstance(canonical["next_actions"], list) else []
    intent = str(canonical["intent"])
    if occurred_on and not re.match(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?$", occurred_on):
        diagnostics["invalid_fields"].append({"field": "occurred_on", "value": occurred_on, "expected": "YYYY-MM-DD or YYYY-MM-DD HH:mm"})
    if not (headline or question or insight):
        diagnostics["missing_recommended"].append("headline_or_question_or_insight")
    if not (time_hints or occurred_on):
        diagnostics["missing_recommended"].append("time_hints_or_occurred_on")
    if not scenes:
        diagnostics["missing_recommended"].append("scenes")
    return {
        "ok": bool(kind or headline or occurred_on or time_hints or scenes or actors or insight or question or reflection or next_actions or intent),
        "source": "agent",
        "kind": kind,
        "headline": headline,
        "occurred_on": occurred_on,
        "time_hints": time_hints,
        "scenes": scenes,
        "actors": actors,
        "insight": insight,
        "question": question,
        "reflection": reflection,
        "next_actions": next_actions,
        "intent": intent,
        "diagnostics": diagnostics,
        "original": original,
    }


def parse_record_analysis_json(value: str | None, original: str) -> dict[str, Any]:
    if not value:
        return normalize_record_analysis(None, original)
    try:
        raw = json.loads(value)
    except json.JSONDecodeError as exc:
        return {"ok": False, "source": "skipped", "reason": "analysis-json-invalid", "detail": str(exc), "original": original}
    if not isinstance(raw, dict):
        return {"ok": False, "source": "skipped", "reason": "analysis-json-not-object", "original": original}
    return normalize_record_analysis(raw, original)


def filename_from_title(title: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\0]+', "-", title).strip().strip(".")
    return name or "未命名记录"


def quickadd_fleeting_config(vault_path: pathlib.Path, choice_name: str = DEFAULT_QUICKADD_CHOICE) -> dict[str, Any]:
    config = vault_path / ".obsidian/plugins/quickadd/data.json"
    if not config.exists():
        return {"ok": False, "reason": "quickadd-config-missing", "config": str(config)}
    data = json.loads(config.read_text(encoding="utf-8"))
    choices = data.get("choices", [])
    choice = next((item for item in choices if item.get("name") == choice_name), None)
    if not choice:
        return {"ok": False, "reason": "quickadd-choice-missing", "choice": choice_name, "config": str(config)}
    template_path = choice.get("templatePath")
    folders = (choice.get("folder") or {}).get("folders") or []
    if not template_path or not folders:
        return {
            "ok": False,
            "reason": "quickadd-fleeting-incomplete",
            "choice": choice_name,
            "missing": [name for name, value in {"templatePath": template_path, "folder.folders": folders}.items() if not value],
        }
    template = vault_path / template_path
    folder = vault_path / folders[0]
    if not template.exists():
        return {"ok": False, "reason": "quickadd-template-missing", "template": template_path}
    folder.mkdir(parents=True, exist_ok=True)
    return {
        "ok": True,
        "choice": choice_name,
        "template": str(template),
        "template_relative": template_path,
        "folder": str(folder),
        "folder_relative": folders[0],
        "raw": choice,
    }


def template_include(template_path: pathlib.Path, name: str) -> str:
    include = template_path.parent / f"{name}.md"
    if not include.exists():
        return ""
    return include.read_text(encoding="utf-8").strip("\n")


def render_template_shell(
    *,
    template_path: pathlib.Path,
    note: pathlib.Path,
    vault_path: pathlib.Path,
    title: str,
    now: dt.datetime,
) -> str:
    category = note.parent.relative_to(vault_path).as_posix()
    template = template_path.read_text(encoding="utf-8")
    folder_tags = "\n".join(yaml_list([part for part in category.split("/") if part]))

    rendered = re.sub(r"<%\*.*?fullPath\.forEach.*?%\>", folder_tags, template, flags=re.S)
    rendered = re.sub(
        r'<% tp\.file\.include\("\[\[([^]]+)\]\]"\) %>',
        lambda match: template_include(template_path, match.group(1)),
        rendered,
    )
    rendered = rendered.replace("<% tp.file.title %>", title)
    rendered = rendered.replace('<% tp.file.path(true).split("/").slice(0, -1).join("/") %>', category)
    rendered = re.sub(
        r'<% tp\.date\.now\("([^"]+)"(?:,\s*\+?(\d+))?\) %>',
        lambda match: (now + dt.timedelta(days=int(match.group(2) or 0))).strftime(templater_date_format(match.group(1))),
        rendered,
    )
    rendered = re.sub(
        r'<% tp\.file\.last_modified_date\("([^"]+)"\) %>',
        lambda match: now.strftime(templater_date_format(match.group(1))),
        rendered,
    )
    rendered = re.sub(
        r'<% tp\.file\.title \+ "-" \+ tp\.date\.now\("YYYYMMDDHHmmss"\) %>',
        f"{title}-{now:%Y%m%d%H%M%S}",
        rendered,
    )
    rendered = rendered.replace("<% tp.file.cursor(1) %>", "")
    return rendered


def find_frontmatter_end(lines: list[str]) -> int | None:
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index
    return None


def set_frontmatter_scalar(lines: list[str], key: str, value: str | None, default_after: str | None = None) -> None:
    rendered = yaml_scalar(value)
    line = f"{key}: {rendered}" if rendered else f"{key}:"
    end = find_frontmatter_end(lines)
    if end is None:
        return
    key_pattern = re.compile(rf"^{re.escape(key)}:\s*")
    for index in range(1, end):
        if key_pattern.match(lines[index]):
            lines[index] = line
            return
    insert_at = end
    if default_after:
        after_pattern = re.compile(rf"^{re.escape(default_after)}:\s*")
        for index in range(1, end):
            if after_pattern.match(lines[index]):
                insert_at = index + 1
                break
    lines.insert(insert_at, line)


def set_frontmatter_list(lines: list[str], key: str, values: list[str]) -> None:
    end = find_frontmatter_end(lines)
    if end is None:
        return
    key_pattern = re.compile(rf"^{re.escape(key)}:\s*")
    for index in range(1, end):
        if not key_pattern.match(lines[index]):
            continue
        remove_to = index + 1
        while remove_to < end and lines[remove_to].startswith("  "):
            remove_to += 1
        replacement = [f"{key}:", *yaml_list(values)]
        lines[index:remove_to] = replacement
        return
    lines.insert(end, f"{key}:")
    for value in reversed(yaml_list(values)):
        lines.insert(end + 1, value)


def remove_frontmatter_key(lines: list[str], key: str) -> None:
    end = find_frontmatter_end(lines)
    if end is None:
        return
    key_pattern = re.compile(rf"^{re.escape(key)}:\s*")
    index = 1
    while index < end:
        if not key_pattern.match(lines[index]):
            index += 1
            continue
        remove_to = index + 1
        while remove_to < end and lines[remove_to].startswith("  "):
            remove_to += 1
        del lines[index:remove_to]
        return


def set_frontmatter_fields(
    markdown: str,
    *,
    status: str,
    record_type: str,
    kind: str,
    question: str,
    source: str,
    scenes: list[str],
    time_hints: list[str],
    occurred_on: str,
    actors: list[str],
) -> str:
    lines = markdown.splitlines()
    for key in ["topic", "issue", "scenarios", "time_clues", "event_date", "people"]:
        remove_frontmatter_key(lines, key)
    set_frontmatter_scalar(lines, "status", status)
    set_frontmatter_scalar(lines, "type", record_type, default_after="status")
    set_frontmatter_scalar(lines, "kind", kind)
    set_frontmatter_scalar(lines, "question", question)
    set_frontmatter_scalar(lines, "source", source)
    set_frontmatter_list(lines, "scenes", scenes)
    if time_hints:
        set_frontmatter_list(lines, "time_hints", time_hints)
    if occurred_on:
        set_frontmatter_scalar(lines, "occurred_on", occurred_on)
    if actors:
        set_frontmatter_list(lines, "actors", actors)
    return "\n".join(lines)


def find_heading_range(lines: list[str], title: str) -> tuple[int, int, int] | None:
    target = normalize_heading_title(title)
    for index, line in enumerate(lines):
        info = heading_info(line)
        if not info or normalize_heading_title(info[1]) != target:
            continue
        level = info[0]
        end = len(lines)
        for next_index in range(index + 1, len(lines)):
            next_info = heading_info(lines[next_index])
            if next_info and next_info[0] <= level:
                end = next_index
                break
        return index, end, level
    return None


def replace_heading_body(markdown: str, title: str, body: list[str]) -> str:
    lines = markdown.splitlines()
    found = find_heading_range(lines, title)
    if found is None:
        raise ValueError(f"required heading missing: {title}")
    start, end, _level = found
    replacement = body
    lines[start + 1 : end] = replacement
    return "\n".join(lines)


def replace_heading_body_if_present(markdown: str, title: str, body: list[str]) -> str:
    lines = markdown.splitlines()
    found = find_heading_range(lines, title)
    if found is None:
        return markdown
    start, end, _level = found
    lines[start + 1 : end] = body
    return "\n".join(lines)


def validate_record_template(markdown: str, body_sections: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if "<%" in markdown or "%>" in markdown:
        return {"ok": False, "reason": "quickadd-template-unsupported-templater-token"}
    lines = markdown.splitlines()
    required = [*required_body_headings(body_sections or []), *REQUIRED_APPENDIX_HEADINGS]
    missing = [title for title in dict.fromkeys(required) if find_heading_range(lines, title) is None]
    if missing:
        return {"ok": False, "reason": "quickadd-template-required-headings-missing", "missing": missing}
    if find_frontmatter_end(lines) is None:
        return {"ok": False, "reason": "quickadd-template-frontmatter-missing"}
    return {"ok": True}


def unique_record_path(folder: pathlib.Path, title: str, now: dt.datetime) -> pathlib.Path:
    base = filename_from_title(title)
    candidate = folder / f"{base}.md"
    if not candidate.exists():
        return candidate
    stamped = f"{base}-{now:%Y%m%d%H%M%S}.md"
    return folder / stamped


def unique_attachment_path(candidate: pathlib.Path) -> pathlib.Path:
    if not candidate.exists():
        return candidate
    for index in range(1, 1000):
        next_candidate = candidate.with_name(f"{candidate.stem}-{index}{candidate.suffix}")
        if not next_candidate.exists():
            return next_candidate
    raise FileExistsError(f"Cannot choose a unique attachment path for {candidate}")


def parse_link_arg(value: str) -> tuple[str, str]:
    if "=" in value:
        label, target = value.split("=", 1)
        return safe_title(label), target.strip()
    target = value.strip()
    label = pathlib.Path(target).stem if not re.match(r"^[a-z]+://", target, re.I) else target
    return safe_title(label), target


def resolve_vault_link(vault_path: pathlib.Path, target: str) -> pathlib.Path | None:
    if re.match(r"^[a-z]+://", target, re.I):
        return None
    path = pathlib.Path(target).expanduser()
    if not path.is_absolute():
        path = vault_path / path
    try:
        path.resolve().relative_to(vault_path.resolve())
    except ValueError:
        return None
    return path


def render_standard_link(from_note: pathlib.Path, vault_path: pathlib.Path, raw: str) -> str:
    label, target = parse_link_arg(raw)
    vault_target = resolve_vault_link(vault_path, target)
    if vault_target is None:
        return markdown_link(label, target)
    return relative_markdown_link(from_note, vault_target, label)


def copy_attachment(
    vault_path: pathlib.Path,
    record_note: pathlib.Path,
    raw: str,
    allow_external_attachments: bool = False,
) -> dict[str, Any]:
    label, target = parse_link_arg(raw)
    if re.match(r"^[a-z]+://", target, re.I):
        return {
            "input": raw,
            "link": attachment_markdown_link(label, target, embed=is_media_attachment(target)),
            "copied": False,
        }
    source = pathlib.Path(target).expanduser()
    if not source.is_absolute():
        source = vault_path / source
    if not source.exists():
        link = render_standard_link(record_note, vault_path, raw)
        if is_media_attachment(target):
            vault_target = resolve_vault_link(vault_path, target)
            link = relative_markdown_embed(record_note, vault_target, label) if vault_target else markdown_embed(label, target)
        return {
            "input": label or pathlib.Path(target).name,
            "link": link,
            "copied": False,
            "missing": True,
            "reason": "attachment-path-unavailable",
        }
    source_rel: str | None = None
    try:
        source_rel = source.resolve().relative_to(vault_path.resolve()).as_posix()
    except ValueError:
        if not allow_external_attachments:
            return {
                "input": label or source.name,
                "copied": False,
                "blocked": True,
                "reason": "external-attachment-requires-confirmation",
            }
    assets = record_note.parent / "assets" / record_note.stem
    assets.mkdir(parents=True, exist_ok=True)
    initial_dest = assets / source.name
    dest = initial_dest if source.resolve() == initial_dest.resolve() else unique_attachment_path(initial_dest)
    if source.resolve() != dest.resolve():
        shutil.copy2(source, dest)
    return {
        "input": label or source.name,
        "source": source_rel or "<external-file>",
        "path": str(dest),
        "relative_path": dest.relative_to(vault_path).as_posix(),
        "link": relative_attachment_markdown_link(record_note, dest, label or dest.stem),
        "copied": True,
    }


def render_record_note(
    *,
    title: str,
    text: str,
    note: pathlib.Path,
    vault_path: pathlib.Path,
    config: dict[str, Any],
    record_type: str,
    status: str,
    source: str,
    kind: str,
    question: str,
    scenes: list[str],
    time_hints: list[str],
    occurred_on: str,
    actors: list[str],
    reflection: str,
    next_actions: list[str],
    attachments: list[str],
    related: list[str],
    external_sources: list[str],
    body_sections: list[dict[str, Any]],
    allow_external_attachments: bool,
    now: dt.datetime,
) -> tuple[str, list[dict[str, Any]]]:
    body = render_template_shell(
        template_path=pathlib.Path(config["template"]),
        note=note,
        vault_path=vault_path,
        title=title,
        now=now,
    )
    body = set_frontmatter_fields(
        body,
        status=status,
        record_type=record_type,
        kind=kind,
        question=question,
        source=source,
        scenes=scenes,
        time_hints=time_hints,
        occurred_on=occurred_on,
        actors=actors,
    )
    validation = validate_record_template(body, body_sections)
    if not validation.get("ok"):
        raise ValueError(validation["reason"] + ":" + ",".join(validation.get("missing", [])))
    attachment_results = [copy_attachment(vault_path, note, item, allow_external_attachments) for item in attachments]
    attachment_links = [item["link"] for item in attachment_results if "link" in item]
    related_links = [render_standard_link(note, vault_path, item) for item in related]
    source_links = [render_standard_link(note, vault_path, item) for item in external_sources]
    body_context = {
        "occurred_on": occurred_on,
        "time_hints": time_hints,
        "scenes": scenes,
        "actors": actors,
        "original_text": text.strip(),
        "question": question,
        "attachment_links": attachment_links,
        "reflection": reflection,
        "next_actions": next_actions,
    }
    for section in body_sections:
        lines = section_lines(section, body_context)
        if lines is None:
            continue
        body = replace_heading_body_if_present(body, section["heading"], lines)
    body = replace_heading_body(body, "来源(Source)", ["", *[f"- {link}" for link in source_links], ""])
    body = replace_heading_body(body, "关联(Reference)", ["", *[f"- {link}" for link in related_links], ""])
    return body.rstrip() + "\n", attachment_results


def validate_required_attachments(
    attachment_results: list[dict[str, Any]],
    record_type: str,
    require_attachment: bool = False,
) -> dict[str, Any] | None:
    media_types = {"image", "audio", "video", "mixed"}
    required = require_attachment or record_type in media_types
    if not required:
        return None
    copied = [item for item in attachment_results if item.get("copied")]
    if copied:
        return None
    missing = [item for item in attachment_results if item.get("missing")]
    if missing:
        return {
            "ok": False,
            "reason": "attachment-path-unavailable",
            "attachments": missing,
        }
    return {
        "ok": False,
        "reason": "record-attachment-required",
        "attachments": attachment_results,
    }


def create_fleeting_record(
    *,
    vault_path: pathlib.Path,
    text: str,
    title: str | None,
    record_type: str,
    status: str,
    source: str,
    topic: str,
    issue: str | None,
    scenarios: list[str],
    attachments: list[str],
    related: list[str],
    external_sources: list[str],
    analysis_json: str | None = None,
    choice: str = DEFAULT_QUICKADD_CHOICE,
    body_config: str | pathlib.Path | None = None,
    allow_external_attachments: bool = False,
    require_attachment: bool = False,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {"ok": False, "reason": "record-text-empty"}
    now = now or dt.datetime.now()
    config = quickadd_fleeting_config(vault_path, choice)
    if not config.get("ok"):
        return config
    body_config_path: pathlib.Path | None = None
    if body_config:
        body_config_path = pathlib.Path(body_config).expanduser()
        if not body_config_path.is_absolute():
            body_config_path = vault_path / body_config_path
    try:
        body_sections = load_record_body_sections(body_config_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"ok": False, "reason": "record-body-config-invalid", "detail": str(exc)}
    analysis = parse_record_analysis_json(analysis_json, stripped)
    # Keep the note body faithful to --text. Agent analysis is metadata only.
    record_text = stripped
    record_scenes = scenarios or analysis.get("scenes", [])
    record_kind = topic or analysis.get("kind", "")
    analysis_insight = analysis.get("insight", "")
    record_question = clean_analysis_scalar(issue or analysis.get("question") or "")
    record_title = safe_title(
        title or issue or analysis.get("headline") or analysis.get("question") or analysis_insight or record_text
    )
    occurred_on = analysis.get("occurred_on", "")
    time_hints = analysis.get("time_hints", [])
    actors = analysis.get("actors", [])
    reflection = analysis.get("reflection", "")
    next_actions = analysis.get("next_actions", [])
    folder = pathlib.Path(config["folder"])
    note = unique_record_path(folder, record_title, now)
    try:
        content, attachment_results = render_record_note(
            title=record_title,
            text=record_text,
            note=note,
            vault_path=vault_path,
            config=config,
            record_type=record_type,
            status=status,
            source=source,
            kind=record_kind,
            question=record_question,
            scenes=record_scenes,
            time_hints=time_hints,
            occurred_on=occurred_on,
            actors=actors,
            reflection=reflection,
            next_actions=next_actions,
            attachments=attachments,
            related=related,
            external_sources=external_sources,
            body_sections=body_sections,
            allow_external_attachments=allow_external_attachments,
            now=now,
        )
    except ValueError as exc:
        reason, _, detail = str(exc).partition(":")
        result: dict[str, Any] = {"ok": False, "reason": reason, "template": config["template_relative"]}
        if detail:
            result["detail"] = detail
        return result
    blocked_attachments = [item for item in attachment_results if item.get("blocked")]
    if blocked_attachments:
        return {
            "ok": False,
            "reason": "external-attachment-requires-confirmation",
            "attachments": blocked_attachments,
        }
    required_attachment_error = validate_required_attachments(attachment_results, record_type, require_attachment)
    if required_attachment_error:
        return required_attachment_error
    note.write_text(content, encoding="utf-8")
    copied_attachments = [item for item in attachment_results if item.get("copied")]
    return {
        "ok": True,
        "note": str(note),
        "relative_note": note.relative_to(vault_path).as_posix(),
        "headline": record_title,
        "question": record_question,
        "type": record_type,
        "status": status,
        "source": source,
        "kind": record_kind,
        "scenes": record_scenes,
        "time_hints": time_hints,
        "occurred_on": occurred_on,
        "actors": actors,
        "reflection": reflection,
        "next_actions": next_actions,
        "body_config": str(body_config_path) if body_config_path else "default",
        "body_sections": [section["heading"] for section in body_sections],
        "analysis": analysis,
        "attachments": attachment_results,
        "copied_attachments": copied_attachments,
        "quickadd": {
            "choice": config["choice"],
            "template": config["template_relative"],
            "folder": config["folder_relative"],
        },
    }


def record_index_line(journal_note: pathlib.Path, record_note: pathlib.Path, title: str) -> str:
    return f"- {relative_markdown_link(journal_note, record_note, title)}"


def inline_record_line(text: str, now: dt.datetime | None = None) -> str:
    lines = text.strip().splitlines()
    if not lines:
        raise ValueError("inline record text is empty")
    now = now or dt.datetime.now()
    entry = [f"- {now:%H:%M} {lines[0].strip()}"]
    entry.extend(f"  {line.rstrip()}" if line.strip() else "" for line in lines[1:])
    return "\n".join(entry)


def append_record_to_note(note: pathlib.Path, text: str, period: str = "day") -> dict[str, Any]:
    target_titles = [normalize_heading_title(title) for title in record_section_titles(period)]
    if not note.exists():
        raise FileNotFoundError(f"Target journal note does not exist: {note}")
    current = note.read_text(encoding="utf-8")
    lines = current.splitlines()
    section_index = None
    section_title = None
    for index, existing in enumerate(lines):
        info = heading_info(existing)
        if not info:
            continue
        title = normalize_heading_title(info[1])
        if title in target_titles:
            section_index = index
            section_title = info[1]
            break
    entry = text.strip()
    if not entry:
        raise ValueError("record index text is empty")
    if section_index is None:
        return {
            "ok": False,
            "reason": "record-section-missing",
            "note": str(note),
            "record": entry,
            "section": None,
            "target_sections": record_section_titles(period),
        }

    insert_index = section_index + 1
    if insert_index < len(lines) and lines[insert_index].strip() == "":
        insert_index += 1
    lines.insert(insert_index, entry)
    after_entry = insert_index + 1
    if after_entry < len(lines) and heading_info(lines[after_entry]) and lines[after_entry - 1].strip():
        lines.insert(after_entry, "")
    note.write_text("\n".join(lines) + ("\n" if current.endswith("\n") else ""), encoding="utf-8")
    return {"ok": True, "note": str(note), "created": False, "record": entry, "section": section_title}
