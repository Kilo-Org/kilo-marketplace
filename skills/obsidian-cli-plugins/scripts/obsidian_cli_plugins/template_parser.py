import datetime as dt
import pathlib
import re
from typing import Any

from .journals import heading_info
from .records import render_template_shell

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover - exercised through monkeypatch tests
    MarkdownIt = None  # type: ignore[assignment]


ICON_RE = re.compile(
    r"^[\s\W_]*(?:[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]+[\s\W_]*)+",
    re.UNICODE,
)
LEADING_NUMBER_RE = re.compile(
    r"^\s*(?:(?:\d+(?:[.．、])?)|(?:[一二三四五六七八九十]+[、.．]))\s*",
    re.UNICODE,
)


def strip_heading_marker(line: str) -> tuple[int, str] | None:
    info = heading_info(line)
    if info is None:
        return None
    return info


def normalize_template_title(title: str) -> str:
    cleaned = title.strip()
    cleaned = ICON_RE.sub("", cleaned).strip()
    cleaned = LEADING_NUMBER_RE.sub("", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def escape_target_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def target_id(title_path: list[str]) -> str:
    return "/".join(
        escape_target_part(normalize_template_title(item))
        for item in title_path
        if normalize_template_title(item)
    )


def heading_nodes_from_markdown_it(markdown: str) -> list[dict[str, Any]]:
    if MarkdownIt is None:
        return []
    parser = MarkdownIt("commonmark")
    tokens = parser.parse(markdown)
    nodes: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.type != "heading_open" or not token.tag.startswith("h"):
            index += 1
            continue
        try:
            level = int(token.tag[1:])
        except ValueError:
            index += 1
            continue
        raw_title = ""
        if index + 1 < len(tokens) and tokens[index + 1].type == "inline":
            raw_title = tokens[index + 1].content
        line_no = int(token.map[0]) + 1 if token.map else 1
        nodes.append({"level": level, "raw_title": raw_title, "line": line_no})
        index += 3
    return nodes


def heading_nodes_from_lines(markdown: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for line_no, line in enumerate(markdown.splitlines(), start=1):
        info = strip_heading_marker(line)
        if info is None:
            continue
        level, raw_title = info
        nodes.append({"level": level, "raw_title": raw_title, "line": line_no})
    return nodes


def heading_tree_from_nodes(heading_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    for heading in heading_nodes:
        level = int(heading["level"])
        raw_title = str(heading["raw_title"])
        title = normalize_template_title(raw_title)
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        path = [*([item["title"] for item in stack]), title]
        node = {
            "id": target_id(path),
            "level": level,
            "line": int(heading["line"]),
            "raw_title": raw_title,
            "title": title,
            "title_path": path,
            "children": [],
        }
        if stack:
            stack[-1]["children"].append(node)
        else:
            nodes.append(node)
        stack.append(node)
    return nodes


def heading_tree(markdown: str) -> list[dict[str, Any]]:
    heading_nodes = heading_nodes_from_markdown_it(markdown)
    parser = "markdown-it-py" if heading_nodes or MarkdownIt is not None else "fallback"
    if not heading_nodes:
        heading_nodes = heading_nodes_from_lines(markdown)
        parser = "fallback"
    tree = heading_tree_from_nodes(heading_nodes)
    for node in flatten_tree(tree):
        node["parser"] = parser
    return tree


def flatten_tree(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for node in nodes:
        flat.append(node)
        flat.extend(flatten_tree(node.get("children", [])))
    return flat


def dedupe_node_ids(nodes: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for node in flatten_tree(nodes):
        base = node["id"] or f"heading-{node['line']}"
        count = counts.get(base, 0) + 1
        counts[base] = count
        node["id"] = base if count == 1 else f"{base}#{count}"


def field_names(markdown: str) -> list[str]:
    names: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^\s*(?:-\s*)?([^:：\n]+)[：:]\s*(.*)$", line)
        if not match:
            continue
        name = match.group(1).strip()
        if name and name not in names:
            names.append(name)
    return names


def vault_relative(vault_path: pathlib.Path, item: pathlib.Path) -> str:
    return item.resolve().relative_to(vault_path.resolve()).as_posix()


def render_project_template(
    vault_path: pathlib.Path,
    template_path: pathlib.Path,
    note: pathlib.Path,
    title: str,
    now: dt.datetime,
) -> str:
    return render_template_shell(
        template_path=template_path.resolve(),
        note=note.resolve(),
        vault_path=vault_path.resolve(),
        title=title,
        now=now,
    )


def parse_markdown_structure(
    markdown: str,
    *,
    source: str,
    fragment_schemas: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tree = heading_tree(markdown)
    dedupe_node_ids(tree)
    flat = flatten_tree(tree)
    by_id = {node["id"]: {key: value for key, value in node.items() if key != "children"} for node in flat}
    return {
        "source": source,
        "sections": tree,
        "flat_sections": flat,
        "by_id": by_id,
        "fragment_schemas": fragment_schemas or {},
    }


def parse_fragment_template(vault_path: pathlib.Path, path: pathlib.Path, *, kind: str) -> dict[str, Any]:
    markdown = path.read_text(encoding="utf-8")
    return {
        "kind": kind,
        "path": vault_relative(vault_path, path),
        "fields": field_names(markdown),
        "body": markdown.strip("\n"),
    }


def attach_fragments_to_structure(structure: dict[str, Any], fragment_schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    title_to_fragment = {
        "功能需求": "functional",
        "非功能需求": "nonfunctional",
        "决策": "decision",
        "决策记录": "decision",
    }
    for node in structure.get("flat_sections", []):
        kind = title_to_fragment.get(node.get("title", ""))
        if kind and kind in fragment_schemas:
            node["fragment"] = fragment_schemas[kind]
            structure["by_id"][node["id"]]["fragment"] = fragment_schemas[kind]
    structure["fragment_schemas"] = fragment_schemas
    return structure
