#!/usr/bin/env python3
"""Install a Skill into an isolated or real Codex home on Windows, Linux, or macOS."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def skill_name(source: Path) -> str:
    text = (source / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError("SKILL.md has no valid hyphen-case name")
    if source.name != match.group(1):
        raise ValueError(f"folder name {source.name!r} does not match Skill name {match.group(1)!r}")
    return match.group(1)


def ignored(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in {".git", ".internal", ".gitlab-ci.yml", "dist"}
        or name == "__pycache__"
        or name.endswith(".pyc")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--codex-home", type=Path, help="Destination Codex home; defaults to CODEX_HOME or the user profile")
    parser.add_argument("--replace", action="store_true", help="Back up an existing installation and replace it")
    parser.add_argument("--skip-audit", action="store_true", help="Install without running the bundled audit")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        print(f"FAIL: invalid Skill source: {source}", file=sys.stderr)
        return 2
    try:
        name = skill_name(source)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    configured = os.environ.get("CODEX_HOME")
    codex_home = (args.codex_home or (Path(configured) if configured else Path.home() / ".codex")).expanduser().resolve()
    skills_root = codex_home / "skills"
    target = skills_root / name
    backup: Path | None = None
    skills_root.mkdir(parents=True, exist_ok=True)

    if target.exists():
        if not args.replace:
            print(f"FAIL: installation already exists: {target}", file=sys.stderr)
            return 3
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = skills_root / f"{name}.backup-{stamp}"
        if backup.exists():
            print(f"FAIL: backup path already exists: {backup}", file=sys.stderr)
            return 3
        target.rename(backup)

    staging = skills_root / f".{name}.installing-{os.getpid()}"
    try:
        shutil.copytree(source, staging, ignore=ignored)
        staging.rename(target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup and backup.exists() and not target.exists():
            backup.rename(target)
        raise

    if not args.skip_audit:
        audit = target / "scripts" / "audit_skill.py"
        if audit.is_file():
            result = subprocess.run([sys.executable, str(audit), str(target)], check=False)
            if result.returncode:
                print(f"FAIL: installed Skill audit returned {result.returncode}", file=sys.stderr)
                return result.returncode

    print(f"INSTALLED: {target}")
    if backup:
        print(f"BACKUP: {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
