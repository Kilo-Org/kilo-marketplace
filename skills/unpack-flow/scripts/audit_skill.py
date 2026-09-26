#!/usr/bin/env python3
"""Audit files required by the public UnpackFlow Skill source."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    public_export = "--public-export" in sys.argv[2:]
    errors: list[str] = []
    required = (
        "SKILL.md", "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE",
        "SECURITY.md", "SUPPORT.md", "PUBLISHER.md",
        "agents/openai.yaml", "install.bat", "install-linux.sh", "install-macos.sh",
    )
    for relative in required:
        path = root / relative
        if not path.is_file() or not path.stat().st_size:
            errors.append(f"missing or empty public file: {relative}")

    locales = ("zh-CN", "es", "hi", "ar", "pt-BR", "fr", "de", "ja", "ru")
    documents = [root / "README.md", *(root / "docs" / f"README.{locale}.md" for locale in locales)]
    for path in documents:
        if not path.is_file():
            errors.append(f"missing localization: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        without_fences = re.sub(r"^```.*?^```\s*$", "", text, flags=re.MULTILINE | re.DOTALL)
        if len(re.findall(r"^#\s+\S", without_fences, flags=re.MULTILINE)) != 1:
            errors.append(f"localization must contain exactly one H1: {path}")
        for value in ("once-email.com", "github.com/pangxin12345", "tiantuowl@gmail.com"):
            if value not in text:
                errors.append(f"missing canonical public identity {value}: {path}")

    skill_path = root / "SKILL.md"
    skill = skill_path.read_text(encoding="utf-8") if skill_path.is_file() else ""
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", skill, flags=re.MULTILINE)
    if not match or match.group(1) != root.name:
        errors.append("SKILL.md name does not match folder name")

    if public_export:
        forbidden = (".internal", ".gitlab-ci.yml", "DISTRIBUTION.md", "REGRESSION.md", "REHEARSAL.md", "scripts/export-public-source.sh")
        for relative in forbidden:
            if (root / relative).exists():
                errors.append(f"internal file present in public export: {relative}")

    print(f"Public Skill audit: {root}")
    for error in errors:
        print(f"FAIL: {error}")
    print("RESULT: PASS" if not errors else f"RESULT: FAIL ({len(errors)} blocking issue(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
