import json
import os
import pathlib
import subprocess
from collections.abc import Iterator
from typing import Any

from .constants import PRIVATE_OUTPUT_DIR, SECRET_REDACTIONS


def run(cmd: list[str], cwd: pathlib.Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check)


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_REDACTIONS:
        if pattern.pattern.startswith("(?i)(password"):
            redacted = pattern.sub(r"\1\2***", redacted)
        elif pattern.pattern.startswith("(?i)(https"):
            redacted = pattern.sub(r"\1***@", redacted)
        else:
            redacted = pattern.sub("***", redacted)
    return redacted


def redact_path(value: str | pathlib.Path | None, verbose: bool = False) -> str | None:
    if value is None:
        return None
    text = str(value)
    if verbose:
        return text
    try:
        home = str(pathlib.Path.home())
        if text == home:
            return "~"
        if text.startswith(home + os.sep):
            return "~" + text[len(home) :]
    except Exception:
        pass
    return text


def redacted_command_record(cmd: list[str], cp: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {"cmd": redact_text(" ".join(cmd)), "returncode": cp.returncode, "output": redact_text(cp.stdout.strip())}


def private_output_path(default_name: str) -> pathlib.Path:
    PRIVATE_OUTPUT_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    return PRIVATE_OUTPUT_DIR / default_name


def write_private_text(path: pathlib.Path, text: str) -> None:
    path = path.expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def resolve_vault_relative_path(vault: pathlib.Path, relative_path: str) -> tuple[pathlib.Path, str]:
    rel = pathlib.PurePosixPath(relative_path.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("path-must-be-relative-to-vault")
    path = (vault / pathlib.Path(*rel.parts)).resolve()
    root = vault.resolve()
    try:
        normalized = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("path-outside-vault") from exc
    return path, normalized


def resolved_vault_file(vault: pathlib.Path, candidate: pathlib.Path) -> tuple[pathlib.Path, str] | None:
    try:
        resolved = candidate.resolve(strict=True)
        rel = resolved.relative_to(vault.resolve()).as_posix()
    except (FileNotFoundError, ValueError):
        return None
    if not resolved.is_file():
        return None
    return resolved, rel


def iter_vault_markdown_files(vault: pathlib.Path) -> Iterator[tuple[pathlib.Path, str]]:
    seen: set[pathlib.Path] = set()
    for candidate in vault.rglob("*.md"):
        resolved = resolved_vault_file(vault, candidate)
        if resolved is None:
            continue
        path, rel = resolved
        if path in seen:
            continue
        seen.add(path)
        yield path, rel


def assert_obsidian_vault(path: pathlib.Path, allow_non_vault: bool = False) -> None:
    if allow_non_vault:
        return
    if not (path / ".obsidian").is_dir():
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "reason": "not-obsidian-vault",
                    "path": redact_path(path),
                    "hint": "Write and Git-mutating commands require a directory containing .obsidian; pass --allow-non-vault only for an explicit controlled test.",
                },
                ensure_ascii=False,
            )
        )

def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
