import datetime as dt
import json
import pathlib
import re
from typing import Any

from .journals import heading_info
from .records import filename_from_title, normalize_heading_title, yaml_scalar
from .template_parser import (
    attach_fragments_to_structure,
    field_names,
    parse_fragment_template,
    parse_markdown_structure,
    render_project_template,
    vault_relative,
)


PROJECT_ROOT = "01_project"
DEFAULT_PROJECT_FOLDER = "01_project"
PROJECT_TEMPLATE = "90_asset/templates/card-project-incubating-note.md"
FRAGMENT_TEMPLATE_CANDIDATES = {
    "functional": [
        "90_asset/templates/card-project-fr.md",
    ],
    "nonfunctional": [
        "90_asset/templates/card-project-nfr.md",
    ],
    "decision": [
        "90_asset/templates/card-project-decision.md",
    ],
}


SECTION_ALIASES = {
    "原始灵感": "idea",
    "灵感": "idea",
    "功能需求": "functional",
    "非功能需求": "nonfunctional",
    "边界约束": "boundary",
    "信息结构": "structure",
    "交互流程": "flow",
    "实现入口": "entry",
    "决策": "decision",
    "决策记录": "decision",
    "风险": "risk",
    "取舍": "tradeoff",
    "当前状态": "status",
    "阶段回顾": "review",
    "下一步": "next",
    "下一步摘要": "next",
    "来源": "source",
    "关联": "reference",
    "术语": "term",
    "应用": "target",
    "任务": "task",
    "问题": "question",
}


def normalize_section(value: str | None) -> str:
    if not value:
        return "idea"
    raw = value.strip()
    key = raw.lower()
    return SECTION_ALIASES.get(raw, key)


def format_multiline(prefix: str, value: str) -> list[str]:
    lines = value.strip().splitlines()
    if not lines:
        return [prefix]
    rendered = [prefix + lines[0].strip()]
    rendered.extend("  " + line.rstrip() if line.strip() else "" for line in lines[1:])
    return rendered


def template_field_names(lines: list[str]) -> list[str]:
    return field_names("\n".join(lines))


def default_entry_lines(section: str, text: str, now: dt.datetime) -> list[str]:
    stripped = text.strip()
    if section == "idea":
        return format_multiline(f"- {now:%H:%M} 原始想法：", stripped)
    if section == "functional":
        return [
            f"- 需求：{stripped}",
            "  来源：",
            "  使用场景：",
            "  价值：",
            "  优先级：",
            "  状态：",
        ]
    if section == "nonfunctional":
        return [
            f"- 约束：{stripped}",
            "  类型：",
            "  影响：",
            "  判断标准：",
            "  状态：",
        ]
    if section == "decision":
        return [
            f"- 时间：{now:%Y-%m-%d %H:%M}",
            "  背景：",
            f"  决策：{stripped}",
            "  原因：",
            "  影响：",
        ]
    if section == "task":
        return format_multiline("- [ ] ", stripped)
    if section == "question":
        return format_multiline("- 问题：", stripped)
    if section in {"status", "review"}:
        return format_multiline(f"- {now:%Y-%m-%d} ", stripped)
    return format_multiline("- ", stripped)


def first_existing_fragment(vault_path: pathlib.Path, section: str) -> pathlib.Path | None:
    for rel in FRAGMENT_TEMPLATE_CANDIDATES.get(section, []):
        path = vault_path / rel
        if path.is_file():
            return path
    return None


def load_fragment_schemas(vault_path: pathlib.Path) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for kind in FRAGMENT_TEMPLATE_CANDIDATES:
        fragment = first_existing_fragment(vault_path, kind)
        if fragment is None:
            continue
        schemas[kind] = parse_fragment_template(vault_path, fragment, kind=kind)
    return schemas


def project_template_structure(vault_path: pathlib.Path, note: pathlib.Path, markdown: str) -> dict[str, Any]:
    structure = parse_markdown_structure(
        markdown,
        source=vault_relative(vault_path, note),
        fragment_schemas=load_fragment_schemas(vault_path),
    )
    return attach_fragments_to_structure(structure, structure["fragment_schemas"])


def default_primary_field(section: str) -> str:
    return {
        "functional": "需求",
        "nonfunctional": "约束",
        "decision": "决策",
        "question": "问题",
        "task": "任务",
    }.get(section, "内容")


def normalize_analysis_json(value: str, original_text: str) -> dict[str, Any]:
    try:
        raw = json.loads(value)
    except json.JSONDecodeError as exc:
        return {"ok": False, "reason": "project-analysis-json-invalid", "detail": str(exc)}
    if not isinstance(raw, dict):
        return {"ok": False, "reason": "project-analysis-json-not-object"}
    target = re.sub(r"\s+", " ", str(raw.get("target_id") or "")).strip()
    section = normalize_section(str(raw.get("section") or "")) if raw.get("section") else ""
    fields = raw.get("fields") or {}
    if not isinstance(fields, dict):
        return {"ok": False, "reason": "project-analysis-fields-not-object"}
    cleaned_fields = {
        str(key).strip(): re.sub(r"\s+", " ", str(value)).strip()
        for key, value in fields.items()
        if str(key).strip() and value is not None
    }
    text = re.sub(r"\s+", " ", str(raw.get("text") or original_text)).strip()
    if not text:
        return {"ok": False, "reason": "project-analysis-text-empty"}
    return {
        "ok": True,
        "target_id": target,
        "section": section,
        "text": text,
        "fields": cleaned_fields,
        "raw": raw,
    }


def fill_fragment_line(line: str, fields: dict[str, str]) -> str:
    match = re.match(r"^(\s*(?:-\s*)?)([^:：\n]+)([：:])(\s*)(.*)$", line)
    if not match:
        return line
    prefix, name, colon, spacing, existing = match.groups()
    key = name.strip()
    value = fields.get(key, "")
    if not value or existing.strip():
        return line
    return f"{prefix}{name}{colon}{spacing}{value}"


def replace_fragment_tokens(body: str, fields: dict[str, str], text: str, now: dt.datetime) -> str:
    replacements = {
        "{{text}}": text,
        "{{datetime}}": now.strftime("%Y-%m-%d %H:%M"),
        "{{date}}": now.strftime("%Y-%m-%d"),
        "{{time}}": now.strftime("%H:%M"),
    }
    for key, value in fields.items():
        replacements[f"{{{{{key}}}}}"] = value
    for token, value in replacements.items():
        body = body.replace(token, value)
    return body


def field_value(fields: dict[str, str], *names: str) -> str:
    for name in names:
        if fields.get(name):
            return fields[name]
    return ""


def generic_entry_lines(target: dict[str, Any], text: str, now: dt.datetime) -> list[str]:
    title = str(target.get("title") or "")
    if title == "原始灵感":
        return format_multiline(f"- {now:%H:%M} 原始想法：", text)
    if title.startswith("任务"):
        return format_multiline("- [ ] ", text)
    if title.startswith("问题"):
        return format_multiline("- 问题：", text)
    return format_multiline("- ", text)


def render_fragment_block(fragment: dict[str, Any], fields: dict[str, str], text: str, now: dt.datetime) -> list[str]:
    body = str(fragment.get("body") or "").strip("\n")
    if not body.strip():
        return format_multiline("- ", text)
    body = replace_fragment_tokens(body, fields, text, now)
    lines: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^(\s*(?:-\s*)?)([^:：\n]+)([：:])(\s*)(.*)$", line)
        if not match:
            if line.strip():
                lines.append(line)
            continue
        prefix, name, colon, spacing, existing = match.groups()
        key = name.strip()
        value = existing.strip() or fields.get(key, "")
        if not value:
            continue
        lines.append(f"{prefix}{name}{colon}{spacing}{value}")
    return lines


def analysis_entry_lines(
    target: dict[str, Any],
    analysis: dict[str, Any],
    now: dt.datetime,
) -> list[str]:
    text = str(analysis["text"]).strip()
    fields = dict(analysis.get("fields") or {})
    fragment = target.get("fragment") or {}
    if fragment.get("kind"):
        fields.setdefault(default_primary_field(str(fragment["kind"])), text)
    if fragment.get("kind") == "decision":
        fields.setdefault("时间", now.strftime("%Y-%m-%d %H:%M"))
    if fragment:
        lines = render_fragment_block(fragment, fields, text, now)
        return lines or generic_entry_lines(target, text, now)
    return generic_entry_lines(target, text, now)


def project_headings(markdown: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        info = heading_info(line)
        if info:
            headings.append({"level": info[0], "title": info[1]})
    return headings


def fragment_schema(vault_path: pathlib.Path, section: str) -> dict[str, Any] | None:
    fragment = first_existing_fragment(vault_path, section)
    if fragment is None:
        return None
    lines = fragment.read_text(encoding="utf-8").strip("\n").splitlines()
    return {
        "template": vault_relative(vault_path, fragment),
        "fields": template_field_names(lines),
        "body": "\n".join(lines),
    }


def target_id_for_section_hint(template_structure: dict[str, Any], section_hint: str) -> str | None:
    title_hints = {
        "idea": ["原始灵感"],
        "functional": ["功能需求"],
        "nonfunctional": ["非功能需求"],
        "boundary": ["边界约束"],
        "structure": ["信息结构"],
        "flow": ["交互流程"],
        "entry": ["实现入口"],
        "decision": ["决策", "决策记录"],
        "risk": ["风险"],
        "tradeoff": ["取舍"],
        "status": ["当前状态"],
        "review": ["阶段回顾"],
        "next": ["下一步摘要"],
        "source": ["来源(Source)", "来源"],
        "reference": ["关联(Reference)", "关联"],
        "term": ["术语(Term)", "术语"],
        "target": ["应用(Target)", "应用"],
        "task": ["任务(Task)", "任务"],
        "question": ["问题(Question)", "问题"],
    }.get(section_hint, [section_hint])
    for node in template_structure.get("flat_sections", []):
        if node.get("title") in title_hints or node.get("raw_title") in title_hints:
            return node.get("id")
    return None


def project_record_prompt(
    *,
    project: str,
    text: str,
    section_hint: str | None,
    template_structure: dict[str, Any],
) -> str:
    section_lines = []
    for node in template_structure.get("flat_sections", []):
        fragment = node.get("fragment") or {}
        fields = ", ".join(fragment.get("fields") or [])
        field_part = f" fields=[{fields}]" if fields else ""
        section_lines.append(
            f"- target_id={node['id']} level={node['level']} title_path={' > '.join(node.get('title_path', []))}{field_part}"
        )
    hint = section_hint or ""
    return "\n".join(
        [
            "你是 Obsidian 项目记录语义分析器。必须根据 template_structure，把用户输入整理成标准 JSON。",
            "只输出 JSON，不要输出 Markdown 或解释。",
            "",
            f"项目: {project}",
            f"用户原文: {text}",
            f"用户指定 section hint: {hint}",
            "",
            "template_structure 可用目标节点:",
            *section_lines,
            "",
            "输出 JSON schema:",
            '{ "target_id": "必须来自 template_structure 的某个 target_id", "text": "保留原始含义的记录文本", "fields": { "模板字段名": "字段值" } }',
            "",
            "规则:",
            "- target_id 必须逐字复制上方某个 target_id。",
            "- 如果目标节点带 fields，只能使用该节点列出的字段名。",
            "- 没有内容的字段不要输出。",
            "- 如果用户明确指定 section hint，优先选择语义最接近的目标节点。",
            "- task/question/source/reference 等附录内容也必须通过 target_id 指向附录节点。",
            "- 不确定时选择原始灵感相关 target_id，并把原文放入 text。",
            "",
            "template_structure JSON:",
            json.dumps(template_structure, ensure_ascii=False),
        ]
    )


def project_record_analysis_contract(
    vault_path: pathlib.Path,
    *,
    project: str,
    text: str,
    section: str | None = None,
    analysis_json: str | None = None,
) -> dict[str, Any]:
    resolved = resolve_project_note(vault_path, project)
    if not resolved.get("ok"):
        return resolved
    note = pathlib.Path(resolved["note"])
    markdown = note.read_text(encoding="utf-8")
    template_structure = project_template_structure(vault_path, note, markdown)
    section_hint = normalize_section(section) if section else ""
    contract: dict[str, Any] = {
        "ok": True,
        "project": resolved["relative_note"],
        "text": text,
        "section_hint": section_hint,
        "template_structure": template_structure,
    }
    contract["prompt"] = project_record_prompt(
        project=resolved["relative_note"],
        text=text,
        section_hint=section_hint,
        template_structure=template_structure,
    )
    if analysis_json is not None:
        analysis = normalize_analysis_json(analysis_json, text)
        if analysis.get("ok"):
            if section_hint and not analysis.get("target_id"):
                hinted = target_id_for_section_hint(template_structure, section_hint)
                if hinted:
                    analysis["target_id"] = hinted
            target = template_structure.get("by_id", {}).get(analysis.get("target_id"))
            if not target:
                analysis = {"ok": False, "reason": "project-analysis-target-not-found", "target_id": analysis.get("target_id")}
            else:
                fields = analysis.get("fields") or {}
                fragment = target.get("fragment") or {}
                allowed = set(fragment.get("fields") or [])
                if allowed:
                    analysis["fields"] = {key: value for key, value in fields.items() if key in allowed and value}
                else:
                    analysis["fields"] = {key: value for key, value in fields.items() if value}
                analysis["target"] = target
        if analysis.get("ok"):
            normalized = {key: analysis[key] for key in ("target_id", "text", "fields") if key in analysis}
            contract["normalized_analysis_json"] = json.dumps(normalized, ensure_ascii=False)
        else:
            contract["normalized_analysis_json"] = ""
        contract["analysis"] = analysis
    return contract


def project_structure_for_project(vault_path: pathlib.Path, project: str) -> dict[str, Any]:
    resolved = resolve_project_note(vault_path, project)
    if not resolved.get("ok"):
        return resolved
    note = pathlib.Path(resolved["note"])
    markdown = note.read_text(encoding="utf-8")
    return {
        "ok": True,
        "project": resolved["relative_note"],
        "template_structure": project_template_structure(vault_path, note, markdown),
    }


def vault_relative(vault_path: pathlib.Path, item: pathlib.Path) -> str:
    return item.resolve().relative_to(vault_path.resolve()).as_posix()


def render_project_note(
    vault_path: pathlib.Path,
    note: pathlib.Path,
    title: str,
    *,
    status: str = "idea",
    priority: str = "medium",
    project_stage: str = "idea",
    landing_threshold: str = "",
    now: dt.datetime | None = None,
) -> str:
    now = now or dt.datetime.now()
    template = vault_path / PROJECT_TEMPLATE
    if not template.exists():
        raise FileNotFoundError(PROJECT_TEMPLATE)
    rendered = render_project_template(vault_path, template, note, title, now)
    lines = rendered.splitlines()
    set_frontmatter_scalar(lines, "title", title, quote=True)
    set_frontmatter_list(lines, "aliases", [title])
    set_frontmatter_scalar(lines, "uid", f"{title}-{now:%Y%m%d%H%M%S}", quote=True)
    set_frontmatter_scalar(lines, "status", status, quote=True)
    set_frontmatter_scalar(lines, "priority", priority, quote=True)
    set_frontmatter_scalar(lines, "project_stage", project_stage, quote=True)
    set_frontmatter_scalar(lines, "landing_threshold", landing_threshold, quote=True)
    return "\n".join(lines).rstrip() + "\n"


def resolve_project_folder(vault_path: pathlib.Path, folder: str) -> tuple[pathlib.Path, str] | dict[str, Any]:
    rel = pathlib.PurePosixPath(folder.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts:
        return {"ok": False, "reason": "project-folder-invalid", "folder": folder}
    if not rel.parts or rel.parts[0] != PROJECT_ROOT:
        rel = pathlib.PurePosixPath(PROJECT_ROOT, *rel.parts)
    path = (vault_path / pathlib.Path(*rel.parts)).resolve()
    try:
        rel_text = path.relative_to(vault_path.resolve()).as_posix()
    except ValueError:
        return {"ok": False, "reason": "project-folder-outside-vault", "folder": folder}
    return path, rel_text


def create_project_note(
    vault_path: pathlib.Path,
    *,
    title: str,
    folder: str = DEFAULT_PROJECT_FOLDER,
    status: str = "idea",
    priority: str = "medium",
    project_stage: str = "idea",
    landing_threshold: str = "",
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    clean_title = re.sub(r"\s+", " ", title.strip())
    if not clean_title:
        return {"ok": False, "reason": "project-title-empty"}
    resolved = resolve_project_folder(vault_path, folder)
    if isinstance(resolved, dict):
        return resolved
    folder_path, folder_rel = resolved
    folder_path.mkdir(parents=True, exist_ok=True)
    note = folder_path / f"{filename_from_title(clean_title)}.md"
    if note.exists():
        return {
            "ok": False,
            "reason": "project-note-exists",
            "note": str(note),
            "relative_note": vault_relative(vault_path, note),
        }
    try:
        content = render_project_note(
            vault_path,
            note,
            clean_title,
            status=status,
            priority=priority,
            project_stage=project_stage,
            landing_threshold=landing_threshold,
            now=now,
        )
    except FileNotFoundError:
        return {"ok": False, "reason": "project-template-missing", "template": PROJECT_TEMPLATE}
    note.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "note": str(note),
        "relative_note": vault_relative(vault_path, note),
        "title": clean_title,
        "folder": folder_rel,
        "created": True,
    }


def frontmatter_end(lines: list[str]) -> int | None:
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index
    return None


def set_frontmatter_scalar(lines: list[str], key: str, value: str, *, quote: bool = False) -> None:
    end = frontmatter_end(lines)
    if end is None:
        return
    rendered_value = yaml_scalar(value) if quote else value
    pattern = re.compile(rf"^{re.escape(key)}\s*:")
    for index in range(1, end):
        if pattern.match(lines[index]):
            lines[index] = f"{key}: {rendered_value}"
            return
    lines.insert(end, f"{key}: {rendered_value}")


def set_frontmatter_list(lines: list[str], key: str, values: list[str]) -> None:
    end = frontmatter_end(lines)
    if end is None:
        return
    pattern = re.compile(rf"^{re.escape(key)}\s*:")
    start = None
    for index in range(1, end):
        if pattern.match(lines[index]):
            start = index
            break
    replacement = [f"{key}:", *[f"  - {yaml_scalar(value)}" for value in values]]
    if start is None:
        lines[end:end] = replacement
        return
    stop = start + 1
    while stop < end and (lines[stop].startswith(" ") or not lines[stop].strip()):
        stop += 1
    lines[start:stop] = replacement


def frontmatter_scalar(lines: list[str], key: str) -> str | None:
    end = frontmatter_end(lines)
    if end is None:
        return None
    pattern = re.compile(rf"^{re.escape(key)}\s*:\s*(.*)$")
    for index in range(1, end):
        match = pattern.match(lines[index])
        if match:
            return match.group(1).strip()
    return None


def update_project_capture_fields(lines: list[str], now: dt.datetime) -> None:
    set_frontmatter_scalar(lines, "updated", now.strftime("%Y-%m-%d %H:%M:%S"))
    set_frontmatter_scalar(lines, "last_capture", now.strftime("%Y-%m-%d %H:%M:%S"))
    raw_count = frontmatter_scalar(lines, "capture_count") or "0"
    try:
        count = int(raw_count)
    except ValueError:
        count = 0
    set_frontmatter_scalar(lines, "capture_count", str(count + 1))


def heading_range(lines: list[str], heading: str) -> tuple[int, int, int] | None:
    target = normalize_heading_title(heading)
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


def insert_under_heading(lines: list[str], heading: str, entry: list[str]) -> dict[str, Any]:
    found = heading_range(lines, heading)
    if found is None:
        return {"ok": False, "reason": "project-section-missing", "section": heading}
    start, end, _level = found
    insert_index = start + 1
    if insert_index < end and lines[insert_index].strip() == "":
        insert_index += 1
    block = [*entry, ""]
    lines[insert_index:insert_index] = block
    return {"ok": True, "section": heading, "line": insert_index + 1}


def insert_at_heading_end(lines: list[str], target: dict[str, Any], entry: list[str]) -> dict[str, Any]:
    start = int(target["line"]) - 1
    level = int(target["level"])
    end = len(lines)
    for index in range(start + 1, len(lines)):
        info = heading_info(lines[index])
        if info and info[0] <= level:
            end = index
            break
    block: list[str] = []
    if end > start + 1 and lines[end - 1].strip():
        block.append("")
    block.extend(entry)
    block.append("")
    lines[end:end] = block
    return {"ok": True, "target_id": target["id"], "line": end + len(block) - len(entry)}


def project_aliases(markdown: str) -> list[str]:
    lines = markdown.splitlines()
    end = frontmatter_end(lines)
    if end is None:
        return []
    aliases: list[str] = []
    in_aliases = False
    for line in lines[1:end]:
        if line.startswith("aliases:"):
            in_aliases = True
            value = line.split(":", 1)[1].strip()
            if value:
                aliases.append(value.strip('"\''))
            continue
        if in_aliases:
            if re.match(r"^\S", line):
                break
            stripped = line.strip()
            if stripped.startswith("- "):
                aliases.append(stripped[2:].strip().strip('"\''))
    return aliases


def resolve_project_note(vault_path: pathlib.Path, project: str) -> dict[str, Any]:
    raw = project.strip()
    if not raw:
        return {"ok": False, "reason": "project-empty"}
    candidate = pathlib.Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = vault_path / candidate
    if candidate.suffix != ".md":
        candidate = candidate.with_suffix(".md")
    try:
        resolved = candidate.resolve(strict=True)
        rel = resolved.relative_to(vault_path.resolve()).as_posix()
        if resolved.is_file():
            return {"ok": True, "note": resolved, "relative_note": rel, "match": "path"}
    except (FileNotFoundError, ValueError):
        pass

    matches: list[tuple[pathlib.Path, str, str]] = []
    project_root = vault_path / PROJECT_ROOT
    for note in project_root.rglob("*.md") if project_root.exists() else []:
        rel = vault_relative(vault_path, note)
        if note.stem == raw:
            matches.append((note, rel, "title"))
            continue
        try:
            aliases = project_aliases(note.read_text(encoding="utf-8"))
        except OSError:
            aliases = []
        if raw in aliases:
            matches.append((note, rel, "alias"))
    if not matches:
        return {"ok": False, "reason": "project-note-not-found", "project": raw}
    unique = {(note.resolve(), rel, kind) for note, rel, kind in matches}
    if len(unique) > 1:
        return {
            "ok": False,
            "reason": "project-note-ambiguous",
            "project": raw,
            "matches": [{"note": rel, "match": kind} for _note, rel, kind in sorted(unique, key=lambda item: item[1])],
        }
    note, rel, kind = next(iter(unique))
    return {"ok": True, "note": note, "relative_note": rel, "match": kind}


def append_project_entry(
    vault_path: pathlib.Path,
    *,
    project: str,
    text: str,
    section: str | None = None,
    analysis_json: str | None = None,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    now = now or dt.datetime.now()
    clean_text = text.strip()
    if not clean_text:
        return {"ok": False, "reason": "project-record-text-empty"}
    if not analysis_json:
        return {
            "ok": False,
            "reason": "project-analysis-required",
            "hint": "Run analyze-project-record --prompt-only, produce model JSON, then pass it with --analysis-json.",
        }
    analysis = normalize_analysis_json(analysis_json, clean_text)
    if not analysis.get("ok"):
        return analysis
    resolved = resolve_project_note(vault_path, project)
    if not resolved.get("ok"):
        return resolved
    note = pathlib.Path(resolved["note"])
    current = note.read_text(encoding="utf-8")
    lines = current.splitlines()
    template_structure = project_template_structure(vault_path, note, current)
    if section and not analysis.get("target_id"):
        hinted = target_id_for_section_hint(template_structure, normalize_section(section))
        if hinted:
            analysis["target_id"] = hinted
    target = template_structure.get("by_id", {}).get(analysis.get("target_id"))
    if not target:
        return {
            "ok": False,
            "reason": "project-analysis-target-not-found",
            "target_id": analysis.get("target_id"),
            "available_targets": sorted(template_structure.get("by_id", {})),
        }
    fields = dict(analysis.get("fields") or {})
    fragment = target.get("fragment") or {}
    allowed = set(fragment.get("fields") or [])
    if allowed:
        fields = {key: value for key, value in fields.items() if key in allowed and value}
        analysis["fields"] = fields
    entry = analysis_entry_lines(target, analysis, now)
    inserted = insert_at_heading_end(lines, target, entry)
    if not inserted.get("ok"):
        return {"ok": False, **inserted, "note": str(note), "relative_note": resolved["relative_note"]}
    update_project_capture_fields(lines, now)
    note.write_text("\n".join(lines) + ("\n" if current.endswith("\n") else ""), encoding="utf-8")
    return {
        "ok": True,
        "note": str(note),
        "relative_note": resolved["relative_note"],
        "target_id": target["id"],
        "target": target,
        "entry": "\n".join(entry),
        "line": inserted["line"],
        "match": resolved.get("match"),
        "analysis": {key: analysis[key] for key in ("target_id", "text", "fields") if key in analysis},
    }
