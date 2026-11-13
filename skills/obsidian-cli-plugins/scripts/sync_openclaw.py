#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import shutil
import sys
import time
from typing import Any


SKILL_NAME = "obsidian-cli-plugins"


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def default_source() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


def default_dest_root() -> pathlib.Path:
    return pathlib.Path(os.environ.get("OPENCLAW_SKILLS_DIR", "~/.openclaw/skills")).expanduser()


def ignore_names(_directory: str, names: list[str]) -> set[str]:
    ignored = {"__pycache__", ".pytest_cache", ".DS_Store"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def validate_source(source: pathlib.Path) -> None:
    skill_file = source / "SKILL.md"
    if not skill_file.exists():
        raise SystemExit(f"Source is not a skill directory: missing {skill_file}")


def remove_destination(dest: pathlib.Path) -> None:
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.exists():
        shutil.rmtree(dest)


def sync_skill(
    source: pathlib.Path,
    dest_root: pathlib.Path,
    force: bool,
    link: bool,
    dry_run: bool,
    backup_existing: bool = False,
) -> dict[str, Any]:
    source = source.expanduser().resolve()
    dest_root = dest_root.expanduser()
    dest = dest_root / source.name
    validate_source(source)
    result: dict[str, Any] = {
        "ok": False,
        "source": str(source),
        "dest_root": str(dest_root),
        "dest": str(dest),
        "mode": "symlink" if link else "copy",
        "dry_run": dry_run,
        "backup": None,
    }
    if source == dest.expanduser().resolve():
        result["ok"] = True
        result["reason"] = "source-already-at-openclaw-destination"
        result["skill_file"] = str(dest / "SKILL.md")
        return result
    if dry_run:
        result["ok"] = True
        result["would_replace"] = dest.exists() or dest.is_symlink()
        return result

    dest_root.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        if not force:
            result["reason"] = "destination-exists"
            result["hint"] = "Pass --force to replace it. Add --backup to keep a timestamped backup first."
            return result
        if backup_existing:
            backup = dest.with_name(f"{dest.name}.bak.{time.strftime('%Y%m%d-%H%M%S')}")
            dest.rename(backup)
            result["backup"] = str(backup)
        else:
            remove_destination(dest)

    if link:
        dest.symlink_to(source, target_is_directory=True)
    else:
        temp = dest.with_name(f".{dest.name}.tmp.{os.getpid()}")
        if temp.exists():
            shutil.rmtree(temp)
        shutil.copytree(source, temp, ignore=ignore_names)
        temp.rename(dest)

    result["ok"] = True
    result["skill_file"] = str(dest / "SKILL.md")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync this skill into an OpenClaw-compatible skills directory.")
    parser.add_argument("--source", default=str(default_source()), help="Skill source directory. Defaults to this script's skill folder.")
    parser.add_argument("--dest-root", "--dest", default=str(default_dest_root()), help="OpenClaw skills root. Defaults to OPENCLAW_SKILLS_DIR or ~/.openclaw/skills.")
    parser.add_argument("--force", action="store_true", help="Replace an existing destination.")
    parser.add_argument("--backup", action="store_true", help="With --force, create a timestamped backup before replacement.")
    parser.add_argument("--link", action="store_true", help="Create a symlink instead of copying. Copy is safer across platforms.")
    parser.add_argument("--dry-run", action="store_true", help="Report the target paths without changing files.")
    args = parser.parse_args()
    result = sync_skill(
        pathlib.Path(args.source),
        pathlib.Path(args.dest_root),
        args.force,
        args.link,
        args.dry_run,
        args.backup,
    )
    print_json(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
