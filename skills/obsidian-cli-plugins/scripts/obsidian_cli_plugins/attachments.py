import datetime as dt
import json
import pathlib
import re
import shutil
import time
import uuid
from typing import Any

from .constants import PRIVATE_OUTPUT_DIR
from .utils import redact_path


STAGED_ATTACHMENT_DIR = PRIVATE_OUTPUT_DIR / "staged-attachments"
DEFAULT_BATCH_KEY = "default"
DEFAULT_STAGE_TTL_HOURS = 48
STAGED_ID_RE = re.compile(r"^[0-9]{14}-[0-9a-f]{10}$")


def safe_attachment_name(value: str) -> str:
    name = pathlib.Path(value).name.strip() or "attachment"
    name = re.sub(r'[<>:"/\\|?*\0]+', "-", name).strip().strip(".")
    return name or "attachment"


def safe_batch_key(value: str | None) -> str:
    key = (value or DEFAULT_BATCH_KEY).strip() or DEFAULT_BATCH_KEY
    key = re.sub(r"[^A-Za-z0-9_.@-]+", "-", key).strip(".-")
    return key[:160] or DEFAULT_BATCH_KEY


def safe_media_type(value: str | None) -> str | None:
    media_type = (value or "").strip().lower()
    return media_type or None


def stage_attachment(
    path: str,
    label: str | None = None,
    media_type: str | None = None,
    batch_key: str | None = None,
) -> dict[str, Any]:
    source = pathlib.Path(path).expanduser()
    if not source.exists() or not source.is_file():
        return {"ok": False, "reason": "attachment-path-unavailable", "path": redact_path(source)}
    prune_staged_attachments(DEFAULT_STAGE_TTL_HOURS)
    STAGED_ATTACHMENT_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    attachment_id = dt.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:10]
    folder = STAGED_ATTACHMENT_DIR / attachment_id
    folder.mkdir(mode=0o700)
    dest = folder / safe_attachment_name(source.name)
    shutil.copy2(source, dest)
    manifest = {
        "id": attachment_id,
        "ok": True,
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "created_at_ns": time.time_ns(),
        "label": label or dest.stem,
        "type": safe_media_type(media_type) or "",
        "batch_key": safe_batch_key(batch_key),
        "path": str(dest),
        "source": redact_path(source),
        "size": dest.stat().st_size,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def staged_manifest_path(attachment_id: str) -> pathlib.Path:
    if not STAGED_ID_RE.match(attachment_id):
        raise ValueError("invalid-staged-attachment-id")
    return STAGED_ATTACHMENT_DIR / attachment_id / "manifest.json"


def load_staged_attachment(attachment_id: str) -> dict[str, Any]:
    try:
        manifest_path = staged_manifest_path(attachment_id)
    except ValueError as exc:
        return {"ok": False, "reason": str(exc), "id": attachment_id}
    if not manifest_path.exists():
        return {"ok": False, "reason": "staged-attachment-not-found", "id": attachment_id}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    path = pathlib.Path(data.get("path", "")).expanduser()
    if not path.exists() or not path.is_file():
        return {"ok": False, "reason": "attachment-path-unavailable", "id": attachment_id, "path": redact_path(path)}
    data["ok"] = True
    data["batch_key"] = safe_batch_key(str(data.get("batch_key") or DEFAULT_BATCH_KEY))
    return data


def redact_staged_attachment(item: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(item)
    if "path" in redacted:
        redacted["path"] = redact_path(redacted["path"])
    return redacted


def list_staged_attachments(batch_key: str | None = None, media_type: str | None = None) -> list[dict[str, Any]]:
    if not STAGED_ATTACHMENT_DIR.exists():
        return []
    wanted = safe_batch_key(batch_key) if batch_key else None
    wanted_type = safe_media_type(media_type)
    items: list[dict[str, Any]] = []
    for manifest_path in STAGED_ATTACHMENT_DIR.glob("*/manifest.json"):
        attachment_id = manifest_path.parent.name
        if not STAGED_ID_RE.match(attachment_id):
            continue
        item = load_staged_attachment(attachment_id)
        if not item.get("ok"):
            continue
        if wanted and item.get("batch_key") != wanted:
            continue
        if wanted_type and safe_media_type(str(item.get("type") or "")) != wanted_type:
            continue
        items.append(item)
    return sorted(items, key=lambda item: (int(item.get("created_at_ns") or 0), str(item.get("id") or "")))


def staged_attachment_batches(media_type: str | None = None) -> dict[str, list[dict[str, Any]]]:
    batches: dict[str, list[dict[str, Any]]] = {}
    for item in list_staged_attachments(media_type=media_type):
        batch_key = safe_batch_key(str(item.get("batch_key") or DEFAULT_BATCH_KEY))
        batches.setdefault(batch_key, []).append(item)
    return batches


def prune_staged_attachments(ttl_hours: float = DEFAULT_STAGE_TTL_HOURS, media_type: str | None = None) -> dict[str, Any]:
    if not STAGED_ATTACHMENT_DIR.exists():
        return {"ok": True, "ttl_hours": ttl_hours, "removed": [], "kept": 0}
    threshold_ns = time.time_ns() - int(ttl_hours * 60 * 60 * 1_000_000_000)
    wanted_type = safe_media_type(media_type)
    removed: list[str] = []
    kept = 0
    for manifest_path in STAGED_ATTACHMENT_DIR.glob("*/manifest.json"):
        attachment_id = manifest_path.parent.name
        if not STAGED_ID_RE.match(attachment_id):
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            created = int(data.get("created_at_ns") or 0)
        except (OSError, ValueError, json.JSONDecodeError):
            created = 0
            data = {}
        if wanted_type and safe_media_type(str(data.get("type") or "")) != wanted_type:
            kept += 1
            continue
        if created and created >= threshold_ns:
            kept += 1
            continue
        remove_staged_attachment(attachment_id)
        removed.append(attachment_id)
    return {"ok": True, "ttl_hours": ttl_hours, "removed": removed, "kept": kept}


def clear_staged_attachments(
    batch_key: str | None = None,
    media_type: str | None = None,
    older_than_hours: float | None = None,
) -> dict[str, Any]:
    if not STAGED_ATTACHMENT_DIR.exists():
        return {"ok": True, "removed": [], "kept": 0}
    wanted = safe_batch_key(batch_key) if batch_key else None
    wanted_type = safe_media_type(media_type)
    threshold_ns = None
    if older_than_hours is not None:
        threshold_ns = time.time_ns() - int(older_than_hours * 60 * 60 * 1_000_000_000)
    removed: list[str] = []
    kept = 0
    for manifest_path in STAGED_ATTACHMENT_DIR.glob("*/manifest.json"):
        attachment_id = manifest_path.parent.name
        if not STAGED_ID_RE.match(attachment_id):
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if wanted and safe_batch_key(str(data.get("batch_key") or DEFAULT_BATCH_KEY)) != wanted:
            kept += 1
            continue
        if wanted_type and safe_media_type(str(data.get("type") or "")) != wanted_type:
            kept += 1
            continue
        if threshold_ns is not None:
            try:
                created = int(data.get("created_at_ns") or 0)
            except (TypeError, ValueError):
                created = 0
            if created and created >= threshold_ns:
                kept += 1
                continue
        remove_staged_attachment(attachment_id)
        removed.append(attachment_id)
    return {"ok": True, "removed": removed, "kept": kept}


def load_staged_attachment_selector(
    selector: str,
    media_type: str | None = None,
    allow_unique_batch_fallback: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if selector in {"pending", "latest", "batch", "batch:default", "pending:default"}:
        return [], {
            "ok": False,
            "reason": "unsafe-default-staged-attachment-selector",
            "selector": selector,
            "batch_key": DEFAULT_BATCH_KEY,
            "type": safe_media_type(media_type),
            "replacement": "attachment-pending --ttl-hours 48",
            "hint": "Do not consume default staged media selectors. Use attachment-pending and then pass the returned selector such as batch:<resolved-batch-key>.",
        }
    elif selector.startswith("batch:"):
        batch_key = selector.split(":", 1)[1]
    elif selector.startswith("pending:"):
        batch_key = selector.split(":", 1)[1]
    else:
        item = load_staged_attachment(selector)
        return ([item], None) if item.get("ok") else ([], item)

    batch_key = safe_batch_key(batch_key)
    items = list_staged_attachments(batch_key, media_type)
    if not items:
        if allow_unique_batch_fallback and batch_key != DEFAULT_BATCH_KEY:
            batches = staged_attachment_batches(media_type)
            if len(batches) == 1:
                resolved_batch_key, resolved_items = next(iter(batches.items()))
                return resolved_items, {
                    "ok": True,
                    "reason": "staged-attachment-selector-resolved-by-unique-pending-batch",
                    "selector": selector,
                    "requested_batch_key": batch_key,
                    "resolved_batch_key": resolved_batch_key,
                    "type": safe_media_type(media_type),
                    "count": len(resolved_items),
                }
            if len(batches) > 1:
                return [], {
                    "ok": False,
                    "reason": "ambiguous-staged-attachments",
                    "selector": selector,
                    "requested_batch_key": batch_key,
                    "type": safe_media_type(media_type),
                    "candidate_batch_keys": sorted(batches),
                }
        return [], {"ok": False, "reason": "staged-attachments-not-found", "selector": selector, "batch_key": batch_key}
    return items, None


def staged_attachment_arg(item: dict[str, Any]) -> str:
    label = str(item.get("label") or pathlib.Path(str(item["path"])).stem)
    return f"{label}={item['path']}"


def remove_staged_attachment(attachment_id: str) -> None:
    try:
        folder = staged_manifest_path(attachment_id).parent
    except ValueError:
        return
    if folder.exists() and folder.is_dir():
        shutil.rmtree(folder)
