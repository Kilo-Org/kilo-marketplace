import pathlib
import re
from typing import Any

from .tasks import is_sensitive_vault_path
from .utils import iter_vault_markdown_files, redact_text, resolve_vault_relative_path


PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)")
ID_CARD_RE = re.compile(r"(?<!\d)(\d{3})\d{11,12}([\dXx]{4})(?!\d)")
BANK_CARD_RE = re.compile(r"(?<!\d)(\d{12,15})(\d{4})(?!\d)")
INTERNAL_ENDPOINT_RE = re.compile(r"\b((?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3})(?::\d{2,5})?\b")


def redact_vault_content(text: str) -> str:
    redacted = redact_text(text)
    redacted = PHONE_RE.sub(r"\1****\2", redacted)
    redacted = ID_CARD_RE.sub(r"\1***********\2", redacted)
    redacted = BANK_CARD_RE.sub(r"**** **** **** \2", redacted)
    redacted = INTERNAL_ENDPOINT_RE.sub("<internal-endpoint>", redacted)
    return redacted


def safe_read(vault: pathlib.Path, relative_path: str, start: int | None = None, end: int | None = None, max_lines: int = 120) -> dict[str, Any]:
    try:
        path, rel = resolve_vault_relative_path(vault, relative_path)
    except ValueError as exc:
        return {"ok": False, "reason": str(exc), "path": relative_path}
    if is_sensitive_vault_path(rel):
        return {"ok": False, "reason": "sensitive-path-skipped", "path": rel}
    if not path.exists() or not path.is_file():
        return {"ok": False, "reason": "file-not-found", "path": rel}
    if path.suffix.lower() != ".md":
        return {"ok": False, "reason": "unsupported-file-type", "path": rel}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return {"ok": False, "reason": "decode-failed", "path": rel}
    first = max((start or 1), 1)
    last = min(end or len(lines), len(lines))
    if last < first:
        return {"ok": False, "reason": "invalid-line-range", "path": rel}
    selected = lines[first - 1 : last]
    truncated = len(selected) > max_lines
    selected = selected[:max_lines]
    return {
        "ok": True,
        "path": rel,
        "start": first,
        "end": first + len(selected) - 1 if selected else first,
        "truncated": truncated,
        "content": redact_vault_content("\n".join(selected)),
    }


def safe_search(vault: pathlib.Path, query: str, max_results: int = 50) -> dict[str, Any]:
    if not query:
        return {"ok": False, "reason": "query-required", "matches": [], "skipped": []}
    matches: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    needle = query.casefold()
    for note, rel in iter_vault_markdown_files(vault):
        if rel.startswith(".obsidian/"):
            continue
        if is_sensitive_vault_path(rel):
            skipped.append({"path": rel, "reason": "sensitive-path"})
            continue
        try:
            lines = note.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            skipped.append({"path": rel, "reason": "decode-failed"})
            continue
        for line_no, line in enumerate(lines, 1):
            if needle in line.casefold():
                matches.append({"path": rel, "line": line_no, "text": redact_vault_content(line.strip())})
                if len(matches) >= max_results:
                    return {"ok": True, "query": query, "total": len(matches), "truncated": True, "matches": matches, "skipped": skipped}
    return {"ok": True, "query": query, "total": len(matches), "truncated": False, "matches": matches, "skipped": skipped}
