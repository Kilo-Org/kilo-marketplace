import argparse
import datetime as dt
import json
import pathlib
import time
from typing import Any

from .attachments import (
    DEFAULT_BATCH_KEY,
    DEFAULT_STAGE_TTL_HOURS,
    clear_staged_attachments,
    list_staged_attachments,
    load_staged_attachment_selector,
    prune_staged_attachments,
    redact_staged_attachment,
    remove_staged_attachment,
    safe_batch_key,
    stage_attachment,
    staged_attachment_batches,
    staged_attachment_arg,
)
from .constants import DEFAULT_VAULT, OFFICIAL_CLI_COMMANDS
from .git_ops import git_commit_push, git_preflight_clean, git_status, git_sync, host_git_found, sync_pull
from .journals import DateParseError, ensure_period_note, period_path, target_date
from .obsidian import (
    command_risk,
    command_prefix,
    enabled_plugins,
    list_commands,
    obsidian_bin,
    plugin_manifests,
    runtime_report,
    vault_cli_name,
    vault_path,
)
from .official_cli import format_official_cli_index, official_cli_index
from .project_records import append_project_entry, create_project_note, project_record_analysis_contract, project_structure_for_project
from .record_analysis import local_timezone_name, record_analysis_contract
from .records import append_record_to_note, create_fleeting_record, inline_record_line, record_index_line
from .reports import format_today_report, format_week_report
from .task_dates import infer_task_kind, resolve_new_task_dates, serialize_task_dates, task_line
from .tasks import append_task_to_note, query_today_tasks, query_week_tasks, read_tasks
from .utils import assert_obsidian_vault, print_json, private_output_path, redact_text, run, write_private_text
from .vault_content import safe_read, safe_search


def cmd_doctor(args: argparse.Namespace) -> None:
    print_json(runtime_report(args.vault, args.vault_path, args.verbose))


def cmd_commands(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    commands = list_commands(cli_vault)
    if args.plugin:
        commands = [c for c in commands if c["id"].startswith(args.plugin + ":")]
    if args.json:
        print_json(commands)
        return
    for c in commands:
        print(f"{c['id']}\t{c.get('name','')}")


def cmd_official_commands(args: argparse.Namespace) -> None:
    data = official_cli_index(args.category, args.search)
    if args.json:
        print_json(data)
        return
    print(format_official_cli_index(data))


def cmd_plugins(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    commands = list_commands(cli_vault)
    grouped: dict[str, list[dict[str, str]]] = {}
    for c in commands:
        grouped.setdefault(command_prefix(c["id"]), []).append(c)
    manifests = plugin_manifests(path)
    rows = []
    for pid in enabled_plugins(path):
        manifest = manifests.get(pid, {})
        rows.append(
            {
                "id": pid,
                "name": manifest.get("name", ""),
                "version": manifest.get("version", ""),
                "commands": len(grouped.get(pid, [])),
            }
        )
    print_json(rows) if args.json else [print(f"{r['id']}\t{r['name']}\t{r['version']}\t{r['commands']}") for r in rows]


def cmd_safe_read(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    target_path = resolve_safe_read_path_arg(args)
    if target_path.get("ok") is False:
        print_json(target_path)
        return
    print_json(safe_read(path, target_path["path"], args.start, args.end, args.max_lines))


def cmd_safe_search(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    print_json(safe_search(path, args.query, args.max_results))


def cmd_run(args: argparse.Namespace) -> None:
    if args.command_id.startswith("obsidian-git:") and host_git_found():
        print_json(
            {
                "ok": False,
                "reason": "host-git-available-use-host-git-instead",
                "command_id": args.command_id,
                "hint": "Use host Git via `git-status` or `sync --mode <pull|push|commit-sync|pull-push>`. Obsidian Git plugin commands are fallback-only when host git is not found.",
            }
        )
        return
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    commands = list_commands(cli_vault)
    risk = command_risk(args.command_id, commands)
    if risk["risk"] == "unknown":
        print_json({"ok": False, "reason": "command-id-not-found", "risk": risk})
        return
    if risk["risk"] != "normal" and not (args.yes and args.risk == risk["risk"]):
        print_json(
            {
                "ok": False,
                "reason": f"{risk['risk']}-command-requires-confirmation",
                "risk": risk,
                "hint": f"Re-run with --risk {risk['risk']} --yes only after the user explicitly confirms this exact command.",
            }
        )
        return
    cp = run([obsidian_bin(), "command", f"vault={cli_vault}", f"id={args.command_id}"])
    output = redact_text(cp.stdout.strip())
    print(output)
    raise SystemExit(cp.returncode)

def cmd_git_status(args: argparse.Namespace) -> None:
    print_json(git_status(vault_path(args.vault, args.vault_path)))


def resolve_safe_read_path_arg(args: argparse.Namespace) -> dict[str, Any]:
    positional = getattr(args, "path", None)
    option = getattr(args, "path_option", None)
    if positional and option and positional != option:
        return {
            "ok": False,
            "reason": "safe-read-path-conflict",
            "path": positional,
            "path_option": option,
        }
    target = positional or option
    if not target:
        return {"ok": False, "reason": "safe-read-path-required"}
    return {"ok": True, "path": target}


def cmd_analyze_record(args: argparse.Namespace) -> None:
    current_date = target_date(args.date).isoformat()
    timezone = args.timezone or local_timezone_name()
    contract = record_analysis_contract(
        text=args.text,
        current_date=current_date,
        timezone=timezone,
        analysis_json=args.analysis_json,
    )
    if args.prompt_only:
        print(contract["prompt"])
        return
    if args.normalized_only:
        print(contract.get("normalized_analysis_json", ""))
        return
    print_json(contract)


def cmd_attachment_stage(args: argparse.Namespace) -> None:
    print_json(stage_attachment(args.path, args.label, args.type, args.batch_key))


def cmd_attachment_list(args: argparse.Namespace) -> None:
    if args.batch_key and safe_batch_key(args.batch_key) == DEFAULT_BATCH_KEY:
        print_json(
            {
                "ok": False,
                "reason": "unsafe-default-batch-key",
                "batch_key": args.batch_key,
                "replacement": "attachment-pending --ttl-hours 48",
                "hint": "Do not use attachment-list --batch-key default for media record consumption. Use attachment-pending and then consume the returned selector.",
            }
        )
        return
    items = list_staged_attachments(args.batch_key, args.type)
    if not args.verbose:
        items = [redact_staged_attachment(item) for item in items]
    print_json({"ok": True, "count": len(items), "batch_key": args.batch_key, "type": args.type, "attachments": items})


def cmd_attachment_pending(args: argparse.Namespace) -> None:
    pruned = prune_staged_attachments(args.ttl_hours)
    items = list_staged_attachments(args.batch_key, args.type)
    resolved_batch_key = args.batch_key
    resolution = None
    if args.batch_key and not items:
        batches = staged_attachment_batches(args.type)
        if len(batches) == 1:
            resolved_batch_key, items = next(iter(batches.items()))
            resolution = {
                "ok": True,
                "reason": "staged-attachment-selector-resolved-by-unique-pending-batch",
                "requested_batch_key": args.batch_key,
                "resolved_batch_key": resolved_batch_key,
            }
        elif len(batches) > 1:
            resolution = {
                "ok": False,
                "reason": "ambiguous-staged-attachments",
                "requested_batch_key": args.batch_key,
                "candidate_batch_keys": sorted(batches),
            }
    elif not args.batch_key:
        batches = staged_attachment_batches(args.type)
        if len(batches) == 1:
            resolved_batch_key, items = next(iter(batches.items()))
            resolution = {
                "ok": True,
                "reason": "staged-attachment-selector-resolved-by-unique-pending-batch",
                "requested_batch_key": None,
                "resolved_batch_key": resolved_batch_key,
            }
        elif len(batches) > 1:
            resolution = {
                "ok": False,
                "reason": "ambiguous-staged-attachments",
                "requested_batch_key": None,
                "candidate_batch_keys": sorted(batches),
            }
    if args.limit is not None:
        items = items[: args.limit]
    output_items = items if args.verbose else [redact_staged_attachment(item) for item in items]
    result = {
        "ok": resolution.get("ok", True) if resolution else True,
        "count": len(output_items),
        "batch_key": args.batch_key,
        "resolved_batch_key": resolved_batch_key,
        "type": args.type,
        "ttl_hours": args.ttl_hours,
        "limit": args.limit,
        "ids": [str(item.get("id", "")) for item in items],
        "selector": f"batch:{resolved_batch_key}" if resolved_batch_key else None,
        "attachments": output_items,
        "pruned": pruned,
        "resolution": resolution,
    }
    if resolution and not resolution.get("ok", True):
        result["reason"] = resolution.get("reason")
        if "candidate_batch_keys" in resolution:
            result["candidate_batch_keys"] = resolution["candidate_batch_keys"]
    print_json(result)


def cmd_attachment_prune(args: argparse.Namespace) -> None:
    print_json(prune_staged_attachments(args.ttl_hours, args.type))


def cmd_attachment_clear(args: argparse.Namespace) -> None:
    print_json(clear_staged_attachments(args.batch_key, args.type, args.older_than_hours))


def resolve_record_attachments(args: argparse.Namespace) -> tuple[list[str], list[dict[str, Any]], dict[str, Any] | None]:
    attachments = list(args.attach or [])
    staged_items: list[dict[str, Any]] = []
    media_type = getattr(args, "type", None)
    for selector in getattr(args, "staged_attachment", []) or []:
        selected_items, error = load_staged_attachment_selector(
            selector,
            media_type=media_type,
            allow_unique_batch_fallback=True,
        )
        if error and not error.get("ok"):
            return attachments, staged_items, error
        for item in selected_items:
            if any(existing.get("id") == item.get("id") for existing in staged_items):
                continue
            staged_items.append(item)
            attachments.append(staged_attachment_arg(item))
    return attachments, staged_items, None


def cleanup_staged_attachments(staged_items: list[dict[str, Any]]) -> None:
    for item in staged_items:
        remove_staged_attachment(str(item.get("id", "")))


def cmd_sync(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    print_json(git_sync(path, mode=args.mode, message=args.message, allow_non_vault=args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait))


def cmd_tasks(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    date = target_date(args.date)
    note = period_path(path, args.period, date)
    if args.action == "show":
        assert_obsidian_vault(path, args.allow_non_vault)
        tasks = read_tasks(note)
        print_json({"note": str(note), "exists": note.exists(), "count": len(tasks), "tasks": tasks})
        return
    if args.action == "query":
        assert_obsidian_vault(path, args.allow_non_vault)
        if args.period != "day":
            raise SystemExit("tasks query currently implements the daily Tasks query workflow; use --period day.")
        result = query_today_tasks(path, date)
        result["note"] = str(note)
        print_json(result)
        return
    if args.action == "add":
        if not args.text:
            raise SystemExit("--text is required for tasks add")
        assert_obsidian_vault(path, args.allow_non_vault)
        ensure = ensure_period_note(cli_vault, path, note, args.period, date, args.wait)
        if not ensure.get("ok"):
            print_json({"ok": False, "reason": "journal-note-create-failed", "ensure": ensure})
            return
        task_kind = infer_task_kind(args.text, args.kind)
        task_dates = resolve_new_task_dates(args.text, date, args.period, args.task_date)
        line = task_line(args.text, task_kind, task_dates)
        result = append_task_to_note(note, line, args.period)
        if not result.get("ok"):
            print_json({"ok": False, "reason": result.get("reason"), "task": result, "journal": ensure})
            return
        serialized_dates = serialize_task_dates(task_dates)
        result["task_date"] = serialized_dates.get("due") if serialized_dates else None
        result["task_dates"] = serialized_dates
        result["task_kind"] = task_kind
        result["local_only"] = True
        result["preflight"] = None
        result["journal"] = ensure
        print_json(result)


def cmd_add_task_sync(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    date = target_date(args.date)
    before = git_status(path)
    if before["unmerged"] or before["merge_head"]:
        print_json({"ok": False, "reason": "git-conflict", "before": before})
        return
    if not args.no_pull:
        preflight = git_preflight_clean(path, args.preflight_message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
        if not preflight.get("ok"):
            print_json({"ok": False, "reason": "git-preflight-failed", "preflight": preflight})
            return
    else:
        preflight = None
    note = period_path(path, args.period, date)
    ensure = ensure_period_note(cli_vault, path, note, args.period, date, args.wait)
    if not ensure.get("ok"):
        print_json({"ok": False, "reason": "journal-note-create-failed", "ensure": ensure})
        return
    task_kind = infer_task_kind(args.text, args.kind)
    task_dates = resolve_new_task_dates(args.text, date, args.period, args.task_date)
    line = task_line(args.text, task_kind, task_dates)
    task_result = append_task_to_note(note, line, args.period)
    if not task_result.get("ok"):
        print_json({"ok": False, "reason": task_result.get("reason"), "journal": ensure, "task": task_result, "preflight": preflight})
        return
    message = args.message or f"vault task: add {args.period} task {date.isoformat()}"
    git_result = git_commit_push(path, message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
    result = {
        "ok": bool(git_result.get("ok")),
        "period": args.period,
        "date": date.isoformat(),
        "task_date": serialize_task_dates(task_dates).get("due") if task_dates else None,
        "task_dates": serialize_task_dates(task_dates),
        "task_kind": task_kind,
        "preflight": preflight,
        "journal": ensure,
        "task": task_result,
        "git": git_result,
    }
    print_json(result)


def wait_for_file_stable(
    note: pathlib.Path,
    quiet_seconds: float = 1.0,
    timeout: float = 5.0,
    interval: float = 0.25,
) -> dict[str, Any]:
    """Wait until asynchronous Obsidian plugins stop rewriting a note."""
    deadline = time.monotonic() + timeout
    stable_since: float | None = None
    last_signature: tuple[int, int] | None = None
    checks = 0

    while time.monotonic() < deadline:
        try:
            stat = note.stat()
        except FileNotFoundError:
            return {"ok": False, "reason": "lint-note-missing-during-stability-wait", "checks": checks}

        checks += 1
        signature = (stat.st_mtime_ns, stat.st_size)
        now = time.monotonic()
        if signature != last_signature:
            last_signature = signature
            stable_since = now
        elif stable_since is not None and now - stable_since >= quiet_seconds:
            return {"ok": True, "checks": checks, "quiet_seconds": quiet_seconds}

        time.sleep(interval)

    return {
        "ok": False,
        "reason": "lint-note-not-stable",
        "checks": checks,
        "quiet_seconds": quiet_seconds,
        "timeout": timeout,
    }


def lint_note(cli_vault: str, vault_root: pathlib.Path, relative_note: str, wait: float) -> dict[str, Any]:
    note = vault_root / relative_note
    if not note.exists():
        return {"ok": False, "reason": "project-lint-note-missing", "note": relative_note, "commands": []}
    commands = []
    open_cmd = [obsidian_bin(), "open", f"vault={cli_vault}", f"path={relative_note}"]
    cp = run(open_cmd)
    commands.append({"cmd": redact_text(" ".join(open_cmd)), "returncode": cp.returncode, "output": redact_text(cp.stdout.strip())})
    if cp.returncode != 0:
        return {"ok": False, "reason": "project-lint-open-failed", "note": relative_note, "commands": commands}
    time.sleep(wait)
    lint_cmd = [obsidian_bin(), "command", f"vault={cli_vault}", "id=obsidian-linter:lint-file"]
    cp = run(lint_cmd)
    commands.append({"cmd": redact_text(" ".join(lint_cmd)), "returncode": cp.returncode, "output": redact_text(cp.stdout.strip())})
    stability = wait_for_file_stable(note, quiet_seconds=max(wait, 0.5), timeout=max(wait * 4, 5.0))
    ok = cp.returncode == 0 and note.exists() and stability.get("ok")
    return {
        "ok": ok,
        "reason": None if ok else ("project-lint-command-failed" if cp.returncode != 0 or not note.exists() else stability.get("reason")),
        "note": relative_note,
        "commands": commands,
        "stability": stability,
    }


def cmd_project_create(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    result = create_project_note(
        path,
        title=args.title,
        folder=args.folder,
        status=args.status,
        priority=args.priority,
        project_stage=args.project_stage,
        landing_threshold=args.landing_threshold,
    )
    result["local_only"] = True
    result["preflight"] = None
    if result.get("ok") and not args.no_lint:
        lint = lint_note(cli_vault, path, result["relative_note"], args.wait)
        result["lint"] = lint
        result["ok"] = bool(lint.get("ok"))
    print_json(result)


def cmd_project_create_sync(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    before = git_status(path)
    if before["unmerged"] or before["merge_head"]:
        print_json({"ok": False, "reason": "git-conflict", "before": before})
        return
    if not args.no_pull:
        preflight = git_preflight_clean(path, args.preflight_message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
        if not preflight.get("ok"):
            print_json({"ok": False, "reason": "git-preflight-failed", "preflight": preflight})
            return
    else:
        preflight = None
    project_result = create_project_note(
        path,
        title=args.title,
        folder=args.folder,
        status=args.status,
        priority=args.priority,
        project_stage=args.project_stage,
        landing_threshold=args.landing_threshold,
    )
    if not project_result.get("ok"):
        print_json({"ok": False, "reason": project_result.get("reason"), "project": project_result, "preflight": preflight})
        return
    lint = None if args.no_lint else lint_note(cli_vault, path, project_result["relative_note"], args.wait)
    if lint is not None and not lint.get("ok"):
        print_json({"ok": False, "reason": "project-lint-failed", "project": project_result, "lint": lint, "preflight": preflight})
        return
    message = args.message or f"vault project: create {args.title}"
    git_result = git_commit_push(path, message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
    print_json({"ok": bool(git_result.get("ok")), "project": project_result, "lint": lint, "preflight": preflight, "git": git_result})


def cmd_analyze_project_record(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    contract = project_record_analysis_contract(
        path,
        project=args.project,
        text=args.text,
        section=args.section,
        analysis_json=args.analysis_json,
    )
    if args.prompt_only:
        print(contract.get("prompt", ""))
        return
    if args.normalized_only:
        print(contract.get("normalized_analysis_json", ""))
        return
    print_json(contract)


def cmd_project_template_structure(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    print_json(project_structure_for_project(path, args.project))


def cmd_project_record(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    result = append_project_entry(path, project=args.project, text=args.text, section=args.section, analysis_json=args.analysis_json)
    result["local_only"] = True
    result["preflight"] = None
    if result.get("ok") and not args.no_lint:
        lint = lint_note(cli_vault, path, result["relative_note"], args.wait)
        result["lint"] = lint
        result["ok"] = bool(lint.get("ok"))
    print_json(result)


def cmd_project_record_sync(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    before = git_status(path)
    if before["unmerged"] or before["merge_head"]:
        print_json({"ok": False, "reason": "git-conflict", "before": before})
        return
    if not args.no_pull:
        preflight = git_preflight_clean(path, args.preflight_message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
        if not preflight.get("ok"):
            print_json({"ok": False, "reason": "git-preflight-failed", "preflight": preflight})
            return
    else:
        preflight = None
    project_result = append_project_entry(path, project=args.project, text=args.text, section=args.section, analysis_json=args.analysis_json)
    if not project_result.get("ok"):
        print_json({"ok": False, "reason": project_result.get("reason"), "project": project_result, "preflight": preflight})
        return
    lint = None if args.no_lint else lint_note(cli_vault, path, project_result["relative_note"], args.wait)
    if lint is not None and not lint.get("ok"):
        print_json({"ok": False, "reason": "project-lint-failed", "project": project_result, "lint": lint, "preflight": preflight})
        return
    message = args.message or f"vault project: add {project_result.get('target_id')} to {project_result.get('relative_note')}"
    git_result = git_commit_push(path, message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
    print_json({"ok": bool(git_result.get("ok")), "project": project_result, "lint": lint, "preflight": preflight, "git": git_result})


def inline_record_blockers(args: argparse.Namespace) -> list[str]:
    blockers = []
    if args.type != "text":
        blockers.append("--type")
    if args.attach:
        blockers.append("--attach")
    if getattr(args, "staged_attachment", None):
        blockers.append("--staged-attachment")
    if getattr(args, "require_attachment", False):
        blockers.append("--require-attachment")
    if args.related:
        blockers.append("--related")
    if args.external_source:
        blockers.append("--external-source")
    return blockers


def file_record_attachment_blocker(args: argparse.Namespace) -> dict[str, Any] | None:
    media_types = {"image", "audio", "video", "mixed"}
    if args.attach:
        return None
    if args.type in media_types:
        return {
            "ok": False,
            "reason": "media-record-requires-attachment",
            "type": args.type,
            "hint": "Pass one or more --attach values in the same record command. Use --allow-external-attachments for explicit user-provided files outside the vault.",
        }
    if getattr(args, "require_attachment", False):
        return {
            "ok": False,
            "reason": "record-attachment-required",
            "hint": "The user request included an attachment or media file, so the record must be created with --attach in the same command.",
        }
    return None


def attachment_source_exists(path: pathlib.Path, raw: str) -> bool:
    if raw.startswith(("http://", "https://")):
        return True
    candidate = pathlib.Path(raw.split("=", 1)[1] if "=" in raw else raw).expanduser()
    if not candidate.is_absolute():
        candidate = path / candidate
    return candidate.exists()


def validate_required_attachment_sources(path: pathlib.Path, args: argparse.Namespace) -> dict[str, Any] | None:
    media_types = {"image", "audio", "video", "mixed"}
    if not (args.require_attachment or args.type in media_types):
        return None
    missing = [raw for raw in args.attach if not attachment_source_exists(path, raw)]
    if missing:
        return {
            "reason": "attachment-path-unavailable",
            "attachments": [{"input": raw, "reason": "attachment-path-unavailable"} for raw in missing],
        }
    return None


def prepare_record_attachments(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    attachments, staged_items, staged_error = resolve_record_attachments(args)
    if staged_error:
        return staged_items, {"reason": staged_error.get("reason"), "staged_attachment": staged_error}
    args.attach = attachments
    if staged_items:
        args.allow_external_attachments = True
    if args.mode == "file":
        blocker = file_record_attachment_blocker(args)
        if blocker:
            return staged_items, blocker
    return staged_items, None


def append_inline_record(journal_note: pathlib.Path, args: argparse.Namespace) -> dict[str, Any]:
    line = inline_record_line(args.text, dt.datetime.now())
    return append_record_to_note(journal_note, line, args.period)


def cmd_record(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    date = target_date(args.date)
    journal_note = period_path(path, args.period, date)
    assert_obsidian_vault(path, args.allow_non_vault)
    if args.mode == "inline":
        blockers = inline_record_blockers(args)
        if blockers:
            print_json({"ok": False, "reason": "inline-record-requires-file-mode", "mode": args.mode, "blockers": blockers, "journal_note": str(journal_note)})
            return
    staged_items, attachment_error = prepare_record_attachments(args)
    if attachment_error:
        print_json({"ok": False, **attachment_error, "mode": args.mode, "journal_note": str(journal_note)})
        return
    source_error = validate_required_attachment_sources(path, args)
    if source_error:
        print_json({"ok": False, **source_error, "mode": args.mode, "journal_note": str(journal_note)})
        return
    ensure = ensure_period_note(cli_vault, path, journal_note, args.period, date, args.wait)
    if not ensure.get("ok"):
        print_json({"ok": False, "reason": "journal-note-create-failed", "ensure": ensure})
        return
    if args.mode == "inline":
        index_result = append_inline_record(journal_note, args)
        if not index_result.get("ok"):
            print_json({"ok": False, "reason": index_result.get("reason"), "journal": ensure, "index": index_result})
            return
        print_json(
            {
                "ok": True,
                "mode": "inline",
                "period": args.period,
                "date": date.isoformat(),
                "local_only": True,
                "preflight": None,
                "journal": ensure,
                "record_file": None,
                "index": index_result,
            }
        )
        return
    record_file = create_fleeting_record(
        vault_path=path,
        text=args.text,
        title=args.title,
        record_type=args.type,
        status=args.status,
        source=args.source,
        topic=args.topic,
        issue=args.issue,
        scenarios=args.scenario,
        attachments=args.attach,
        related=args.related,
        external_sources=args.external_source,
        analysis_json=args.analysis_json,
        choice=args.quickadd_choice,
        body_config=args.body_config,
        allow_external_attachments=args.allow_external_attachments,
        require_attachment=args.require_attachment,
    )
    if not record_file.get("ok"):
        print_json({"ok": False, "reason": record_file.get("reason"), "journal": ensure, "record_file": record_file})
        return
    index_line = record_index_line(journal_note, pathlib.Path(record_file["note"]), record_file["headline"])
    index_result = append_record_to_note(journal_note, index_line, args.period)
    if not index_result.get("ok"):
        print_json({"ok": False, "reason": index_result.get("reason"), "journal": ensure, "record_file": record_file, "index": index_result})
        return
    print_json(
        {
            "ok": True,
            "mode": "file",
            "period": args.period,
            "date": date.isoformat(),
            "local_only": True,
            "preflight": None,
            "journal": ensure,
            "record_file": record_file,
            "staged_attachments": [redact_staged_attachment(item) for item in staged_items],
            "index": index_result,
        }
    )
    cleanup_staged_attachments(staged_items)


def cmd_record_sync(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    date = target_date(args.date)
    before = git_status(path)
    if before["unmerged"] or before["merge_head"]:
        print_json({"ok": False, "reason": "git-conflict", "before": before})
        return
    if args.mode == "inline":
        blockers = inline_record_blockers(args)
        if blockers:
            print_json({"ok": False, "reason": "inline-record-requires-file-mode", "mode": args.mode, "blockers": blockers, "before": before})
            return
    staged_items, attachment_error = prepare_record_attachments(args)
    if attachment_error:
        print_json({"ok": False, **attachment_error, "mode": args.mode, "before": before})
        return
    source_error = validate_required_attachment_sources(path, args)
    if source_error:
        print_json({"ok": False, **source_error, "mode": args.mode, "before": before})
        return
    if not args.no_pull:
        preflight = git_preflight_clean(path, args.preflight_message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
        if not preflight.get("ok"):
            print_json({"ok": False, "reason": "git-preflight-failed", "preflight": preflight})
            return
    else:
        preflight = None
    journal_note = period_path(path, args.period, date)
    ensure = ensure_period_note(cli_vault, path, journal_note, args.period, date, args.wait)
    if not ensure.get("ok"):
        print_json({"ok": False, "reason": "journal-note-create-failed", "ensure": ensure, "preflight": preflight})
        return
    if args.mode == "inline":
        index_result = append_inline_record(journal_note, args)
        if not index_result.get("ok"):
            print_json({"ok": False, "reason": index_result.get("reason"), "journal": ensure, "index": index_result, "preflight": preflight})
            return
        message = args.message or f"vault record: add {args.period} inline record {date.isoformat()}"
        git_result = git_commit_push(path, message, args.allow_non_vault, fallback_vault=cli_vault, wait=args.wait)
        result = {
            "ok": bool(git_result.get("ok")),
            "mode": "inline",
            "period": args.period,
            "date": date.isoformat(),
            "preflight": preflight,
            "journal": ensure,
            "record_file": None,
            "index": index_result,
            "git": git_result,
        }
        print_json(result)
        return
    record_file = create_fleeting_record(
        vault_path=path,
        text=args.text,
        title=args.title,
        record_type=args.type,
        status=args.status,
        source=args.source,
        topic=args.topic,
        issue=args.issue,
        scenarios=args.scenario,
        attachments=args.attach,
        related=args.related,
        external_sources=args.external_source,
        analysis_json=args.analysis_json,
        choice=args.quickadd_choice,
        body_config=args.body_config,
        allow_external_attachments=args.allow_external_attachments,
        require_attachment=args.require_attachment,
    )
    if not record_file.get("ok"):
        print_json({"ok": False, "reason": record_file.get("reason"), "journal": ensure, "record_file": record_file, "preflight": preflight})
        return
    index_line = record_index_line(journal_note, pathlib.Path(record_file["note"]), record_file["headline"])
    index_result = append_record_to_note(journal_note, index_line, args.period)
    if not index_result.get("ok"):
        print_json({"ok": False, "reason": index_result.get("reason"), "journal": ensure, "record_file": record_file, "index": index_result, "preflight": preflight})
        return
    message = args.message or f"vault record: add {args.period} record {date.isoformat()}"
    force_add_paths = [item["path"] for item in record_file.get("copied_attachments", []) if item.get("path")]
    git_result = git_commit_push(path, message, args.allow_non_vault, force_add_paths=force_add_paths, fallback_vault=cli_vault, wait=args.wait)
    result = {
        "ok": bool(git_result.get("ok")),
        "mode": "file",
        "period": args.period,
        "date": date.isoformat(),
        "preflight": preflight,
        "journal": ensure,
        "record_file": record_file,
        "staged_attachments": [redact_staged_attachment(item) for item in staged_items],
        "index": index_result,
        "git": git_result,
    }
    print_json(result)
    if git_result.get("ok"):
        cleanup_staged_attachments(staged_items)


def cmd_today_tasks(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    date = target_date(args.date)
    sync = None if args.no_sync else sync_pull(cli_vault, path, args.wait, args.allow_non_vault)
    if sync is not None and not sync.get("ok"):
        print_json(sync)
        return
    result = query_today_tasks(path, date)
    result["note"] = str(period_path(path, "day", date))
    result["sync"] = sync
    output = pathlib.Path(args.output).expanduser()
    write_private_text(output, json.dumps(result, ensure_ascii=False, indent=2, default=str))
    report = format_today_report(result, sync=sync, include_source=args.source)
    if args.report:
        write_private_text(pathlib.Path(args.report).expanduser(), report + "\n")
    print(report)


def cmd_week_tasks(args: argparse.Namespace) -> None:
    path = vault_path(args.vault, args.vault_path)
    assert_obsidian_vault(path, args.allow_non_vault)
    cli_vault = vault_cli_name(args.vault, args.vault_path)
    date = target_date(args.date)
    sync = None if args.no_sync else sync_pull(cli_vault, path, args.wait, args.allow_non_vault)
    if sync is not None and not sync.get("ok"):
        print_json(sync)
        return
    result = query_week_tasks(path, date)
    result["note"] = str(period_path(path, "week", date))
    result["sync"] = sync
    output = pathlib.Path(args.output).expanduser()
    write_private_text(output, json.dumps(result, ensure_ascii=False, indent=2, default=str))
    report = format_week_report(result, sync=sync, include_source=args.source)
    if args.report:
        write_private_text(pathlib.Path(args.report).expanduser(), report + "\n")
    print(report)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Obsidian CLI and plugin workflows")
    p.add_argument("--vault", default=DEFAULT_VAULT)
    p.add_argument("--vault-path")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("commands")
    c.add_argument("--plugin")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_commands)

    c = sub.add_parser("official-commands")
    c.add_argument("--category", choices=sorted(OFFICIAL_CLI_COMMANDS))
    c.add_argument("--search")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_official_commands)

    c = sub.add_parser("plugins")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_plugins)

    c = sub.add_parser("safe-read")
    c.add_argument("path", nargs="?")
    c.add_argument("--path", dest="path_option", help="Vault-relative Markdown path. Kept for compatibility; the positional path is preferred.")
    c.add_argument("--start", type=int)
    c.add_argument("--end", type=int)
    c.add_argument("--max-lines", type=int, default=120)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_safe_read)

    c = sub.add_parser("safe-search")
    c.add_argument("query")
    c.add_argument("--max-results", type=int, default=50)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_safe_search)

    c = sub.add_parser("run")
    c.add_argument("command_id")
    c.add_argument("--risk", choices=["normal", "sensitive", "destructive"], default="normal")
    c.add_argument("--yes", action="store_true")
    c.set_defaults(func=cmd_run)

    c = sub.add_parser("git-status")
    c.set_defaults(func=cmd_git_status)

    c = sub.add_parser("analyze-record")
    c.add_argument("--text", required=True)
    c.add_argument("--date", default="today")
    c.add_argument("--timezone")
    c.add_argument("--analysis-json", help="Model-produced JSON to validate and normalize against the shared record schema.")
    c.add_argument("--prompt-only", action="store_true", help="Print only the model prompt for the current text/date context.")
    c.add_argument("--normalized-only", action="store_true", help="Print only normalized analysis JSON. Requires --analysis-json.")
    c.set_defaults(func=cmd_analyze_record)

    c = sub.add_parser("attachment-stage")
    c.add_argument("--path", required=True, help="Readable local media/file path supplied by the current channel or Agent runtime")
    c.add_argument("--label")
    c.add_argument("--type", choices=["image", "audio", "video", "file", "mixed"])
    c.add_argument("--batch-key", default="default", help="Conversation/thread key used to collect multiple staged attachments")
    c.set_defaults(func=cmd_attachment_stage)

    c = sub.add_parser("attachment-list")
    c.add_argument("--batch-key", help="Only show staged attachments for this conversation/thread key")
    c.add_argument("--type", choices=["image", "audio", "video", "file", "mixed"], help="Only show staged attachments of this media type")
    c.add_argument("--verbose", action="store_true", help="Show full local staged attachment paths")
    c.set_defaults(func=cmd_attachment_list)

    c = sub.add_parser("attachment-pending")
    c.add_argument("--batch-key", help="Only show pending staged attachments for this conversation/thread key")
    c.add_argument("--type", choices=["image", "audio", "video", "file", "mixed"], help="Only show pending staged attachments of this media type")
    c.add_argument("--ttl-hours", type=float, default=DEFAULT_STAGE_TTL_HOURS, help="Prune staged attachments older than this before listing")
    c.add_argument("--limit", type=int, help="Return only the oldest N matching staged attachments")
    c.add_argument("--verbose", action="store_true", help="Show full local staged attachment paths")
    c.set_defaults(func=cmd_attachment_pending)

    c = sub.add_parser("attachment-prune")
    c.add_argument("--ttl-hours", type=float, default=DEFAULT_STAGE_TTL_HOURS)
    c.add_argument("--type", choices=["image", "audio", "video", "file", "mixed"], help="Only prune staged attachments of this media type")
    c.set_defaults(func=cmd_attachment_prune)

    c = sub.add_parser("attachment-clear")
    c.add_argument("--batch-key", help="Only remove staged attachments for this conversation/thread key")
    c.add_argument("--type", choices=["image", "audio", "video", "file", "mixed"], help="Only remove staged attachments of this media type")
    c.add_argument("--older-than-hours", type=float, help="Only remove staged attachments older than this many hours")
    c.set_defaults(func=cmd_attachment_clear)

    c = sub.add_parser("doctor")
    c.add_argument("--verbose", action="store_true", help="Show full local paths and environment values instead of redacted paths")
    c.set_defaults(func=cmd_doctor)

    c = sub.add_parser("sync")
    c.add_argument("--mode", choices=["pull", "push", "commit-sync", "pull-push"], default="pull-push")
    c.add_argument("--message", help="Commit message for --mode commit-sync when local changes exist")
    c.add_argument("--wait", type=float, default=5)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_sync)

    c = sub.add_parser("tasks")
    c.add_argument("action", choices=["show", "query", "add"])
    c.add_argument("--period", choices=["day", "week", "month", "quarter", "year"], default="day")
    c.add_argument("--date", default="today")
    c.add_argument("--task-date")
    c.add_argument("--kind", default="auto")
    c.add_argument("--text")
    c.add_argument("--preflight-message")
    c.add_argument("--wait", type=float, default=5)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_tasks)

    c = sub.add_parser("add-task-sync")
    c.add_argument("--period", choices=["day", "week", "month", "quarter", "year"], default="day")
    c.add_argument("--date", default="today")
    c.add_argument("--task-date")
    c.add_argument("--kind", default="auto")
    c.add_argument("--text", required=True)
    c.add_argument("--message")
    c.add_argument("--preflight-message")
    c.add_argument("--no-pull", action="store_true")
    c.add_argument("--wait", type=float, default=5)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_add_task_sync)

    c = sub.add_parser("project-create")
    c.add_argument("--title", required=True)
    c.add_argument("--folder", default="01_project")
    c.add_argument("--status", default="idea")
    c.add_argument("--priority", default="medium")
    c.add_argument("--project-stage", default="idea")
    c.add_argument("--landing-threshold", default="")
    c.add_argument("--no-lint", action="store_true")
    c.add_argument("--wait", type=float, default=1)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_project_create)

    c = sub.add_parser("project-create-sync")
    c.add_argument("--title", required=True)
    c.add_argument("--folder", default="01_project")
    c.add_argument("--status", default="idea")
    c.add_argument("--priority", default="medium")
    c.add_argument("--project-stage", default="idea")
    c.add_argument("--landing-threshold", default="")
    c.add_argument("--message")
    c.add_argument("--preflight-message")
    c.add_argument("--no-pull", action="store_true")
    c.add_argument("--no-lint", action="store_true")
    c.add_argument("--wait", type=float, default=1)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_project_create_sync)

    c = sub.add_parser("project-template-structure")
    c.add_argument("--project", required=True, help="Project note path, title, or alias under 01_project")
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_project_template_structure)

    c = sub.add_parser("analyze-project-record")
    c.add_argument("--project", required=True, help="Project note path, title, or alias under 01_project")
    c.add_argument("--text", required=True)
    c.add_argument("--section", help="Optional section hint, for example idea, functional, task, 功能需求, 任务")
    c.add_argument("--analysis-json", help="Model-produced JSON to validate and normalize against the project template schema.")
    c.add_argument("--prompt-only", action="store_true", help="Print only the model prompt for this project/text context.")
    c.add_argument("--normalized-only", action="store_true", help="Print only normalized analysis JSON. Requires --analysis-json.")
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_analyze_project_record)

    c = sub.add_parser("project-record")
    c.add_argument("--project", required=True, help="Project note path, title, or alias under 01_project")
    c.add_argument("--section", help="Optional section override, for example idea, functional, task, 功能需求, 任务")
    c.add_argument("--text", required=True)
    c.add_argument("--analysis-json", required=True, help="Model-produced project record JSON from analyze-project-record.")
    c.add_argument("--no-lint", action="store_true")
    c.add_argument("--wait", type=float, default=1)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_project_record)

    c = sub.add_parser("project-record-sync")
    c.add_argument("--project", required=True, help="Project note path, title, or alias under 01_project")
    c.add_argument("--section", help="Optional section override, for example idea, functional, task, 功能需求, 任务")
    c.add_argument("--text", required=True)
    c.add_argument("--analysis-json", required=True, help="Model-produced project record JSON from analyze-project-record.")
    c.add_argument("--message")
    c.add_argument("--preflight-message")
    c.add_argument("--no-pull", action="store_true")
    c.add_argument("--no-lint", action="store_true")
    c.add_argument("--wait", type=float, default=1)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_project_record_sync)

    c = sub.add_parser("record")
    c.add_argument("--mode", choices=["inline", "file"], default="inline")
    c.add_argument("--period", choices=["day", "week", "month", "quarter", "year"], default="day")
    c.add_argument("--date", default="today")
    c.add_argument("--text", required=True)
    c.add_argument("--title")
    c.add_argument("--type", choices=["text", "image", "audio", "video", "mixed"], default="text")
    c.add_argument("--status", default="ai_pending")
    c.add_argument("--source", default="agent/codex")
    c.add_argument("--topic", default="")
    c.add_argument("--issue")
    c.add_argument("--scenario", action="append", default=[])
    c.add_argument("--analysis-json", help="Agent-produced semantic analysis JSON. Invalid or missing JSON is ignored.")
    c.add_argument("--body-config", help="Optional JSON config for record body sections. Relative paths resolve from the vault root.")
    c.add_argument("--attach", action="append", default=[])
    c.add_argument("--staged-attachment", action="append", default=[], help="Attachment id returned by attachment-stage")
    c.add_argument("--require-attachment", action="store_true", help="Fail file-mode records unless at least one --attach value is passed")
    c.add_argument("--related", action="append", default=[])
    c.add_argument("--external-source", action="append", default=[])
    c.add_argument("--quickadd-choice", default="fleeting")
    c.add_argument("--allow-external-attachments", action="store_true", help="Allow copying explicitly provided attachment files from outside the vault")
    c.add_argument("--wait", type=float, default=5)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_record)

    c = sub.add_parser("record-sync")
    c.add_argument("--mode", choices=["inline", "file"], default="inline")
    c.add_argument("--period", choices=["day", "week", "month", "quarter", "year"], default="day")
    c.add_argument("--date", default="today")
    c.add_argument("--text", required=True)
    c.add_argument("--title")
    c.add_argument("--type", choices=["text", "image", "audio", "video", "mixed"], default="text")
    c.add_argument("--status", default="ai_pending")
    c.add_argument("--source", default="agent/codex")
    c.add_argument("--topic", default="")
    c.add_argument("--issue")
    c.add_argument("--scenario", action="append", default=[])
    c.add_argument("--analysis-json", help="Agent-produced semantic analysis JSON. Invalid or missing JSON is ignored.")
    c.add_argument("--body-config", help="Optional JSON config for record body sections. Relative paths resolve from the vault root.")
    c.add_argument("--attach", action="append", default=[])
    c.add_argument("--staged-attachment", action="append", default=[], help="Attachment id returned by attachment-stage")
    c.add_argument("--require-attachment", action="store_true", help="Fail file-mode records unless at least one --attach value is passed")
    c.add_argument("--related", action="append", default=[])
    c.add_argument("--external-source", action="append", default=[])
    c.add_argument("--quickadd-choice", default="fleeting")
    c.add_argument("--allow-external-attachments", action="store_true", help="Allow copying explicitly provided attachment files from outside the vault")
    c.add_argument("--message")
    c.add_argument("--preflight-message")
    c.add_argument("--no-pull", action="store_true")
    c.add_argument("--wait", type=float, default=5)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_record_sync)

    c = sub.add_parser("today-tasks")
    c.add_argument("--date", default="today")
    c.add_argument("--output", default=str(private_output_path("obsidian-today-query.json")))
    c.add_argument("--report", default=str(private_output_path("obsidian-today-report.md")))
    c.add_argument("--source", action="store_true", help="Include source path and line for each task")
    c.add_argument("--no-sync", action="store_true")
    c.add_argument("--wait", type=float, default=5)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_today_tasks)

    c = sub.add_parser("week-tasks")
    c.add_argument("--date", default="today")
    c.add_argument("--output", default=str(private_output_path("obsidian-week-query.json")))
    c.add_argument("--report", default=str(private_output_path("obsidian-week-report.md")))
    c.add_argument("--source", action="store_true", help="Include source path and line for each task")
    c.add_argument("--no-sync", action="store_true")
    c.add_argument("--wait", type=float, default=5)
    c.add_argument("--allow-non-vault", action="store_true", help="Dangerous test-only override for directories without .obsidian")
    c.set_defaults(func=cmd_week_tasks)
    return p


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except DateParseError as exc:
        raise SystemExit(str(exc)) from None
