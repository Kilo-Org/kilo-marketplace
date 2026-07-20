import datetime as dt
import pathlib
import shutil
import time
from typing import Any

from .obsidian import obsidian_bin
from .utils import assert_obsidian_vault, redact_text, redacted_command_record, run


def host_git_found() -> bool:
    return shutil.which("git") is not None


def git_unavailable_status() -> dict[str, Any]:
    return {
        "git_found": False,
        "reason": "host-git-not-found",
        "status": "",
        "ahead": None,
        "behind": None,
        "upstream": None,
        "counts_ok": False,
        "unmerged": [],
        "merge_head": "",
    }


def git_upstream(path: pathlib.Path) -> str | None:
    if not host_git_found():
        return None
    cp = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=path)
    return cp.stdout.strip() if cp.returncode == 0 and cp.stdout.strip() else None


def git_counts(path: pathlib.Path, upstream: str | None = None) -> tuple[int | None, int | None, bool]:
    if not host_git_found():
        return None, None, False
    if upstream is None:
        return None, None, False
    cp = run(["git", "rev-list", "--left-right", "--count", f"HEAD...{upstream}"], cwd=path)
    if cp.returncode != 0:
        return None, None, False
    left, right = cp.stdout.strip().split()
    return int(left), int(right), True


def git_status(path: pathlib.Path) -> dict[str, Any]:
    if not host_git_found():
        return git_unavailable_status()
    short = run(["git", "status", "--short", "--branch"], cwd=path).stdout.strip()
    unmerged = run(["git", "diff", "--name-only", "--diff-filter=U"], cwd=path).stdout.splitlines()
    merge_head = run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"], cwd=path).stdout.strip()
    upstream = git_upstream(path)
    ahead, behind, counts_ok = git_counts(path, upstream)
    return {
        "git_found": True,
        "status": short,
        "ahead": ahead,
        "behind": behind,
        "upstream": upstream,
        "counts_ok": counts_ok,
        "unmerged": unmerged,
        "merge_head": merge_head,
    }


def git_worktree_dirty(path: pathlib.Path) -> bool:
    if not host_git_found():
        return False
    return bool(run(["git", "status", "--porcelain"], cwd=path).stdout.strip())


def git_is_clean_synced(path: pathlib.Path) -> bool:
    if not host_git_found():
        return False
    status = git_status(path)
    return (
        not git_worktree_dirty(path)
        and status["counts_ok"]
        and status["ahead"] == 0
        and status["behind"] == 0
        and not status["unmerged"]
        and not status["merge_head"]
    )


def normalize_force_add_paths(path: pathlib.Path, paths: list[str] | None) -> tuple[list[str], dict[str, Any] | None]:
    if not paths:
        return [], None
    repo = path.resolve()
    rels: list[str] = []
    for raw in paths:
        item = pathlib.Path(raw).expanduser()
        if not item.is_absolute():
            item = path / item
        try:
            resolved = item.resolve(strict=True)
            rel = resolved.relative_to(repo).as_posix()
        except FileNotFoundError:
            return [], {"ok": False, "reason": "force-add-path-missing", "path": str(item)}
        except ValueError:
            return [], {"ok": False, "reason": "force-add-path-outside-repo", "path": str(item)}
        if rel not in rels:
            rels.append(rel)
    return rels, None


def obsidian_git_plugin_sync(vault: str | None, path: pathlib.Path, mode: str, wait: float = 5.0) -> dict[str, Any]:
    before = git_status(path)
    if not vault:
        return {
            "ok": False,
            "reason": "host-git-not-found-and-vault-name-unavailable",
            "fallback": "obsidian-git-plugin",
            "mode": mode,
            "before": before,
            "after": before,
            "commands": [],
        }
    ids = {
        "pull": ["obsidian-git:pull"],
        "push": ["obsidian-git:push2"],
        "commit-sync": ["obsidian-git:push"],
        "pull-push": ["obsidian-git:pull", "obsidian-git:push2"],
    }.get(mode)
    if ids is None:
        return {
            "ok": False,
            "reason": "unsupported-git-sync-mode",
            "fallback": "obsidian-git-plugin",
            "mode": mode,
            "before": before,
            "after": before,
            "commands": [],
        }
    commands = []
    for command_id in ids:
        cmd = [obsidian_bin(), "command", f"vault={vault}", f"id={command_id}"]
        cp = run(cmd)
        commands.append({"cmd": redact_text(" ".join(cmd)), "returncode": cp.returncode, "output": redact_text(cp.stdout.strip())})
        time.sleep(wait)
        if cp.returncode != 0:
            return {
                "ok": False,
                "reason": "obsidian-git-plugin-command-failed",
                "fallback": "obsidian-git-plugin",
                "mode": mode,
                "before": before,
                "after": git_status(path),
                "commands": commands,
            }
    return {
        "ok": True,
        "fallback": "obsidian-git-plugin",
        "mode": mode,
        "before": before,
        "after": git_status(path),
        "commands": commands,
    }


def git_preflight_clean(
    path: pathlib.Path,
    message: str | None = None,
    allow_non_vault: bool = False,
    fallback_vault: str | None = None,
    wait: float = 5.0,
) -> dict[str, Any]:
    assert_obsidian_vault(path, allow_non_vault)
    before = git_status(path)
    if not before.get("git_found", True):
        result = obsidian_git_plugin_sync(fallback_vault, path, "commit-sync", wait)
        result["reason"] = result.get("reason", "host-git-not-found-used-obsidian-git-plugin")
        return result
    if before["unmerged"] or before["merge_head"]:
        return {"ok": False, "reason": "git-conflict", "before": before, "after": before, "commands": []}

    commands = []
    if git_worktree_dirty(path):
        commit_message = message or f"vault sync: save local changes {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        for cmd in (["git", "add", "-A"], ["git", "commit", "-m", commit_message]):
            cp = run(cmd, cwd=path)
            commands.append(redacted_command_record(cmd, cp))
            if cp.returncode != 0:
                return {
                    "ok": False,
                    "reason": "git-preflight-commit-failed",
                    "before": before,
                    "after": git_status(path),
                    "commands": commands,
                }

    for cmd in (["git", "pull", "--no-rebase"], ["git", "push"]):
        cp = run(cmd, cwd=path)
        commands.append(redacted_command_record(cmd, cp))
        if cp.returncode != 0:
            return {
                "ok": False,
                "reason": "git-preflight-command-failed",
                "before": before,
                "after": git_status(path),
                "commands": commands,
            }

    after = git_status(path)
    if not git_is_clean_synced(path):
        return {"ok": False, "reason": "git-preflight-not-clean", "before": before, "after": after, "commands": commands}
    return {"ok": True, "before": before, "after": after, "commands": commands}


def git_sync(
    path: pathlib.Path,
    mode: str = "pull-push",
    message: str | None = None,
    allow_non_vault: bool = False,
    fallback_vault: str | None = None,
    wait: float = 5.0,
) -> dict[str, Any]:
    assert_obsidian_vault(path, allow_non_vault)
    before = git_status(path)
    if not before.get("git_found", True):
        result = obsidian_git_plugin_sync(fallback_vault, path, mode, wait)
        result["reason"] = result.get("reason", "host-git-not-found-used-obsidian-git-plugin")
        return result
    if before["unmerged"] or before["merge_head"]:
        return {"ok": False, "reason": "git-conflict", "before": before, "after": before, "commands": []}

    commands: list[dict[str, Any]] = []
    dirty = git_worktree_dirty(path)
    if mode == "commit-sync" and dirty:
        commit_message = message or f"vault sync: save local changes {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        for cmd in (["git", "add", "-A"], ["git", "commit", "-m", commit_message]):
            cp = run(cmd, cwd=path)
            commands.append(redacted_command_record(cmd, cp))
            if cp.returncode != 0:
                return {"ok": False, "reason": "git-sync-command-failed", "before": before, "after": git_status(path), "commands": commands}

    if mode == "pull":
        git_commands = [["git", "pull", "--no-rebase"]]
    elif mode == "push":
        git_commands = [["git", "push"]]
    elif mode == "commit-sync":
        git_commands = [["git", "pull", "--no-rebase"], ["git", "push"]]
    elif mode == "pull-push":
        git_commands = [["git", "pull", "--no-rebase"], ["git", "push"]]
    else:
        return {"ok": False, "reason": "unsupported-git-sync-mode", "mode": mode, "before": before, "after": before, "commands": commands}

    for cmd in git_commands:
        cp = run(cmd, cwd=path)
        commands.append(redacted_command_record(cmd, cp))
        if cp.returncode != 0:
            return {"ok": False, "reason": "git-sync-command-failed", "before": before, "after": git_status(path), "commands": commands}

    after = git_status(path)
    ok = (
        bool(after["counts_ok"])
        and not after["unmerged"]
        and not after["merge_head"]
        and (mode in {"pull", "push"} or (after["ahead"] == 0 and after["behind"] == 0))
    )
    return {
        "ok": ok,
        "mode": mode,
        "commands": commands,
        "before": before,
        "after": after,
    }


def sync_pull(vault: str, path: pathlib.Path, wait: float, allow_non_vault: bool = False) -> dict[str, Any]:
    return git_sync(path, mode="pull", allow_non_vault=allow_non_vault, fallback_vault=vault, wait=wait)

def git_commit_push(
    path: pathlib.Path,
    message: str,
    allow_non_vault: bool = False,
    force_add_paths: list[str] | None = None,
    fallback_vault: str | None = None,
    wait: float = 5.0,
) -> dict[str, Any]:
    assert_obsidian_vault(path, allow_non_vault)
    before = git_status(path)
    if not before.get("git_found", True):
        result = obsidian_git_plugin_sync(fallback_vault, path, "commit-sync", wait)
        result["reason"] = result.get("reason", "host-git-not-found-used-obsidian-git-plugin")
        if force_add_paths:
            result["warning"] = "force-add paths cannot be verified when falling back to the Obsidian Git plugin"
        return result
    if before["unmerged"] or before["merge_head"]:
        return {"ok": False, "reason": "git-conflict", "before": before, "after": before, "commands": []}
    force_paths, force_error = normalize_force_add_paths(path, force_add_paths)
    if force_error:
        return {"ok": False, **force_error, "before": before, "after": before, "commands": []}
    commands = []
    add_commands = [["git", "add", "-A"]]
    if force_paths:
        add_commands.append(["git", "add", "-f", "--", *force_paths])
    for cmd in (*add_commands, ["git", "commit", "-m", message], ["git", "push"]):
        cp = run(cmd, cwd=path)
        commands.append(redacted_command_record(cmd, cp))
        if cp.returncode != 0:
            return {"ok": False, "reason": "git-command-failed", "before": before, "after": git_status(path), "commands": commands}
    after = git_status(path)
    if not git_is_clean_synced(path):
        return {"ok": False, "reason": "git-post-commit-not-clean", "before": before, "after": after, "commands": commands}
    return {"ok": True, "before": before, "after": after, "commands": commands}
