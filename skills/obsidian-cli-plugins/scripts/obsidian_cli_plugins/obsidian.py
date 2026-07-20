import json
import os
import pathlib
import shutil
from typing import Any

from .constants import DANGEROUS_COMMAND_RE, DEFAULT_VAULT, DEFAULT_VAULT_PATH, SENSITIVE_COMMAND_RE
from .utils import redact_path, run


def command_risk(command_id: str, commands: list[dict[str, Any]]) -> dict[str, Any]:
    command = next((item for item in commands if item.get("id") == command_id), None)
    if command is None:
        return {
            "command_id": command_id,
            "name": "",
            "risk": "unknown",
            "matched": None,
            "reason": "command-id-not-found",
        }
    name = str(command.get("name") or "")
    target = f"{command_id} {name}"
    destructive_match = DANGEROUS_COMMAND_RE.search(target)
    sensitive_match = SENSITIVE_COMMAND_RE.search(target)
    risk = "destructive" if destructive_match else "sensitive" if sensitive_match else "normal"
    return {
        "command_id": command_id,
        "name": name,
        "risk": risk,
        "matched": (destructive_match or sensitive_match).group(0) if destructive_match or sensitive_match else None,
        "reason": None,
    }


def obsidian_config_candidates() -> list[pathlib.Path]:
    explicit = os.environ.get("OBSIDIAN_CONFIG")
    home = pathlib.Path.home()
    candidates = []
    if explicit:
        candidates.append(pathlib.Path(explicit).expanduser())
    if os.environ.get("APPDATA"):
        candidates.append(pathlib.Path(os.environ["APPDATA"]) / "obsidian/obsidian.json")
    if os.environ.get("XDG_CONFIG_HOME"):
        candidates.append(pathlib.Path(os.environ["XDG_CONFIG_HOME"]) / "obsidian/obsidian.json")
    candidates.extend(
        [
            home / "Library/Application Support/obsidian/obsidian.json",
            home / ".config/obsidian/obsidian.json",
        ]
    )
    result = []
    seen = set()
    for candidate in candidates:
        resolved = candidate.expanduser()
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def configured_vaults() -> list[dict[str, Any]]:
    vaults: list[dict[str, Any]] = []
    seen = set()
    for config in obsidian_config_candidates():
        if not config.exists():
            continue
        try:
            data = json.loads(config.read_text(encoding="utf-8"))
        except Exception:
            continue
        for key, item in data.get("vaults", {}).items():
            path_value = item.get("path")
            if not path_value:
                continue
            path = pathlib.Path(path_value).expanduser()
            dedupe_key = str(path)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            vaults.append(
                {
                    "id": key,
                    "name": path.name,
                    "path": str(path),
                    "open": bool(item.get("open")),
                    "config": str(config),
                }
            )
    return vaults


def obsidian_bin() -> str:
    candidates = [
        os.environ.get("OBSIDIAN_BIN"),
        shutil.which("obsidian"),
        "/Applications/Obsidian.app/Contents/MacOS/obsidian",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Obsidian\Obsidian.exe"),
        os.path.expandvars(r"%ProgramFiles%\Obsidian\Obsidian.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Obsidian\Obsidian.exe"),
        "/usr/bin/obsidian",
        "/usr/local/bin/obsidian",
        "/snap/bin/obsidian",
        "/var/lib/flatpak/exports/bin/md.obsidian.Obsidian",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = pathlib.Path(candidate).expanduser()
        if path.exists() or shutil.which(str(candidate)):
            return str(path if path.exists() else candidate)
    return "obsidian"


def resolve_vault(vault: str, explicit: str | None = None) -> dict[str, Any]:
    if explicit:
        path = pathlib.Path(explicit).expanduser().resolve()
        name = path.name if vault in {"auto", "current", "active", "open"} else vault
        return {"name": name, "path": path, "source": "explicit"}
    vaults = configured_vaults()
    if vault in {"auto", "current", "active", "open"}:
        open_vaults = [item for item in vaults if item.get("open")]
        if len(open_vaults) == 1:
            item = open_vaults[0]
            return {"name": item["name"], "path": pathlib.Path(item["path"]), "source": "obsidian-config-open"}
        if len(vaults) == 1:
            item = vaults[0]
            return {"name": item["name"], "path": pathlib.Path(item["path"]), "source": "obsidian-config-single"}
        if DEFAULT_VAULT_PATH.exists():
            return {"name": DEFAULT_VAULT, "path": DEFAULT_VAULT_PATH, "source": "default-fallback"}
        raise SystemExit("Cannot resolve current vault; pass --vault <name> or --vault-path.")
    for item in vaults:
        path = pathlib.Path(item["path"])
        if path.name == vault or item.get("id") == vault or str(path) == vault:
            return {"name": path.name, "path": path, "source": "obsidian-config"}
    if vault == DEFAULT_VAULT and DEFAULT_VAULT_PATH.exists():
        return {"name": DEFAULT_VAULT, "path": DEFAULT_VAULT_PATH, "source": "default-fallback"}
    raise SystemExit(f"Cannot resolve vault path for {vault!r}; pass --vault-path or set OBSIDIAN_VAULT_PATH.")


def vault_path(vault: str, explicit: str | None = None) -> pathlib.Path:
    return resolve_vault(vault, explicit)["path"]


def vault_cli_name(vault: str, explicit: str | None = None) -> str:
    return str(resolve_vault(vault, explicit)["name"])


def strip_eval_prefix(text: str) -> str:
    text = text.strip()
    if text.startswith("=>"):
        return text[2:].strip()
    return text


def obsidian_eval(vault: str, code: str) -> str:
    cp = run([obsidian_bin(), "eval", f"vault={vault}", f"code={code}"])
    if cp.returncode != 0:
        raise SystemExit(cp.stdout)
    return strip_eval_prefix(cp.stdout)


def list_commands(vault: str) -> list[dict[str, Any]]:
    code = (
        "JSON.stringify(Object.values(app.commands.commands)"
        ".map(c=>({id:c.id,name:c.name||''}))"
        ".sort((a,b)=>a.id.localeCompare(b.id)))"
    )
    return json.loads(obsidian_eval(vault, code))


def enabled_plugins(path: pathlib.Path) -> list[str]:
    p = path / ".obsidian/community-plugins.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def plugin_manifests(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for manifest in (path / ".obsidian/plugins").glob("*/manifest.json"):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            result[data.get("id") or manifest.parent.name] = data
        except Exception:
            continue
    return result


def command_prefix(command_id: str) -> str:
    return command_id.split(":", 1)[0]


def runtime_report(vault: str, explicit_path: str | None = None, verbose: bool = False) -> dict[str, Any]:
    bin_path = obsidian_bin()
    report: dict[str, Any] = {
        "vault": vault,
        "env": {
            "OBSIDIAN_VAULT": os.environ.get("OBSIDIAN_VAULT"),
            "OBSIDIAN_VAULT_PATH": redact_path(os.environ.get("OBSIDIAN_VAULT_PATH"), verbose),
            "OBSIDIAN_CONFIG": redact_path(os.environ.get("OBSIDIAN_CONFIG"), verbose),
            "OBSIDIAN_BIN": redact_path(os.environ.get("OBSIDIAN_BIN"), verbose),
        },
        "obsidian_bin": redact_path(bin_path, verbose),
        "obsidian_bin_found": pathlib.Path(bin_path).exists() or bool(shutil.which(bin_path)),
        "obsidian_config_candidates": [redact_path(p, verbose) for p in obsidian_config_candidates()],
        "obsidian_config_found": [redact_path(p, verbose) for p in obsidian_config_candidates() if p.exists()],
        "configured_vaults": [
            {**item, "path": redact_path(item.get("path"), verbose), "config": redact_path(item.get("config"), verbose)}
            for item in configured_vaults()
        ],
        "git_found": bool(shutil.which("git")),
        "redacted": not verbose,
    }
    try:
        resolved = resolve_vault(vault, explicit_path)
        path = resolved["path"]
        report["resolved_vault"] = {"name": resolved["name"], "path": redact_path(path, verbose), "source": resolved["source"]}
        report["vault_path"] = redact_path(path, verbose)
        report["vault_path_exists"] = path.exists()
        report["is_git_repo"] = (path / ".git").exists()
        report["is_obsidian_vault"] = (path / ".obsidian").is_dir()
        report["enabled_plugins_count"] = len(enabled_plugins(path))
    except SystemExit as exc:
        report["vault_error"] = str(exc)
    return report
