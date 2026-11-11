#!/usr/bin/env python3
"""Office-suite detection and PDF conversion.

Shared by build_deck.py (``--pdf``) and render_preview.py. Deliberately free of
python-pptx imports so it also works in minimal environments.

Supported converters, in order:
  1. Any soffice-compatible CLI (LibreOffice, OpenOffice, ooffice, ...).
  2. Microsoft PowerPoint on Windows (COM) or macOS (AppleScript).

GUI-only suites (OnlyOffice, WPS) are detected for reporting but never used:
they cannot be driven headlessly.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

SOFFICE_NAMES = ("soffice", "libreoffice", "openoffice", "openoffice.org", "ooffice")

SOFFICE_GLOBS = (
    "/usr/lib64/libreoffice/program/soffice",
    "/usr/lib/libreoffice/program/soffice",
    "/opt/libreoffice*/program/soffice",
    "/opt/openoffice*/program/soffice",
    "/usr/lib64/openoffice*/program/soffice",
    "/usr/lib/openoffice*/program/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/Applications/OpenOffice.app/Contents/MacOS/soffice",
)

WINDOWS_SOFFICE_GLOBS = (
    "{base}\\LibreOffice\\program\\soffice.exe",
    "{base}\\OpenOffice*\\program\\soffice.exe",
)

WINDOWS_POWERPOINT_GLOBS = (
    "{base}\\Microsoft Office\\root\\Office*\\POWERPNT.EXE",
    "{base}\\Microsoft Office\\Office*\\POWERPNT.EXE",
)

# Detected but never driven: GUI-only applications.
UNSUPPORTED_APPS = (
    ("onlyoffice", "OnlyOffice", ("onlyoffice-desktopeditors",),
     ("/opt/onlyoffice/desktopeditors/DesktopEditors",
      "/Applications/OnlyOffice.app")),
    ("wps", "WPS Office", ("wps", "et", "wpp"),
     ("/opt/kingsoft/wps-office/office6/wps",)),
)

UNSUPPORTED_GLOBS = tuple(
    path for _name, _label, _names, paths in UNSUPPORTED_APPS for path in paths
)

PDF_MAGIC = b"%PDF-"

CHECKED_TEXT = (
    "soffice, libreoffice, openoffice, openoffice.org, ooffice, "
    "Microsoft PowerPoint (Windows/macOS)"
)


@dataclass(frozen=True)
class Converter:
    name: str
    kind: str
    path: str
    label: str


@dataclass(frozen=True)
class ConversionResult:
    pdf: Path
    converter: str
    label: str


class ConversionError(RuntimeError):
    """Raised when no converter is available or every attempt failed."""

    def __init__(
        self,
        deck: Path,
        attempts=None,
        converters=None,
        unsupported=None,
        *,
        reason: str | None = None,
    ) -> None:
        self.deck = Path(deck)
        self.attempts = list(attempts or [])
        self.converters = list(converters or [])
        self.unsupported = list(unsupported or [])
        self.reason = reason
        super().__init__(self._message())

    def _message(self) -> str:
        lines = [f"error: could not export a PDF from {self.deck}"]
        if self.reason:
            lines.append(f"  {self.reason}")
        for name, why in self.attempts:
            lines.append(f"  {name}: {why}")
        if not self.converters:
            lines.append(f"  {no_converter_detail()}")
        return "\n".join(lines)


class _Timeout(Exception):
    pass


def _label_for(path: str) -> str:
    lowered = path.replace("\\", "/").lower()
    if "openoffice" in lowered and "libreoffice" not in lowered:
        return "OpenOffice"
    return "LibreOffice"


def _cli_converter(path: str) -> Converter:
    label = _label_for(path)
    name = "openoffice" if label == "OpenOffice" else "soffice"
    return Converter(name=name, kind="cli", path=path, label=label)


def _resolve(path: str) -> str:
    try:
        return str(Path(path).resolve())
    except OSError:
        return path


def _dedupe(converters) -> list[Converter]:
    """Drop duplicates by resolved path and by product (a name maps to one suite)."""
    seen_paths: set[str] = set()
    seen_products: set[tuple[str, str]] = set()
    out: list[Converter] = []
    for conv in converters:
        key = _resolve(conv.path)
        if key in seen_paths or (conv.kind, conv.name) in seen_products:
            continue
        seen_paths.add(key)
        seen_products.add((conv.kind, conv.name))
        out.append(conv)
    return out


def _windows_bases() -> list[str]:
    bases = []
    for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        base = os.environ.get(var)
        if base:
            bases.append(base)
    return bases


def _windows_glob(patterns) -> list[str]:
    hits: list[str] = []
    for base in _windows_bases():
        for pattern in patterns:
            expanded = pattern.format(base=base)
            hits.extend(p for p in sorted(glob.glob(expanded)) if os.path.isfile(p))
    return hits


def _powerpoint_converter() -> Converter | None:
    system = platform.system()
    if system == "Windows":
        interpreter = shutil.which("powershell") or shutil.which("pwsh")
        if not interpreter:
            return None
        exe = shutil.which("POWERPNT.EXE") or next(iter(_windows_glob(WINDOWS_POWERPOINT_GLOBS)), None)
        if not exe:
            return None
        return Converter(
            name="powerpoint-com",
            kind="powerpoint",
            path=exe,
            label="Microsoft PowerPoint (COM)",
        )
    if system == "Darwin":
        if not shutil.which("osascript"):
            return None
        app = Path("/Applications/Microsoft PowerPoint.app")
        if not app.is_dir():
            return None
        return Converter(
            name="powerpoint-applescript",
            kind="powerpoint",
            path=str(app),
            label="Microsoft PowerPoint (AppleScript)",
        )
    return None


def find_converters() -> list[Converter]:
    """Return supported converters in preference order, de-duplicated by path."""
    found: list[Converter] = []
    if os.name == "nt":
        found.extend(_cli_converter(p) for p in _windows_glob(WINDOWS_SOFFICE_GLOBS))
    else:
        for name in SOFFICE_NAMES:
            hit = shutil.which(name)
            if hit:
                found.append(_cli_converter(hit))
        for hit in _windows_glob(SOFFICE_GLOBS):
            found.append(_cli_converter(hit))
    powerpoint = _powerpoint_converter()
    if powerpoint:
        found.append(powerpoint)
    return _dedupe(found)


def unsupported_apps() -> list[dict]:
    """Apps detected on this machine that cannot be automated."""
    found: list[dict] = []
    seen: set[str] = set()
    for name, label, names, paths in UNSUPPORTED_APPS:
        hit = next((shutil.which(n) for n in names if shutil.which(n)), None)
        if hit is None:
            hit = next((p for p in paths if os.path.exists(p)), None)
        if hit and name not in seen:
            seen.add(name)
            found.append({"name": name, "label": label, "path": hit})
    return found


def no_converter_detail() -> str:
    parts = [f"no PDF converter available; checked: {CHECKED_TEXT}"]
    detected = unsupported_apps()
    if detected:
        labels = ", ".join(f"{app['label']} ({app['path']})" for app in detected)
        parts.append(f"detected but not automatable: {labels}")
    return "; ".join(parts)


def describe_environment() -> dict:
    return {
        "converters": [asdict(c) for c in find_converters()],
        "unsupported": unsupported_apps(),
    }


def _text(data) -> str:
    if isinstance(data, (bytes, bytearray)):
        return data.decode("utf-8", errors="replace").strip()
    return str(data).strip()


def _kill_tree(proc) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            proc.kill()
        except OSError:
            pass
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
    try:
        proc.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name != "nt":
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
    try:
        proc.kill()
    except OSError:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def _run(cmd, timeout: float):
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **kwargs)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        for stream in (proc.stdout, proc.stderr):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass
        raise _Timeout(f"timed out after {timeout:g}s") from None
    return proc.returncode, stdout, stderr


def _find_pdf(directory: Path, stem: str) -> Path | None:
    exact = directory / (stem + ".pdf")
    if exact.is_file():
        return exact
    for candidate in sorted(directory.glob("*")):
        if candidate.is_file() and candidate.suffix.lower() == ".pdf":
            return candidate
    return None


def _profile_flag(workdir: Path) -> str:
    profile = workdir / "lo-profile"
    profile.mkdir(parents=True, exist_ok=True)
    path = str(profile).replace("\\", "/")
    prefix = "file:///" if os.name == "nt" else "file://"
    return f"-env:UserInstallation={prefix}{path}"


def _convert_soffice(conv: Converter, deck: Path, workdir: Path, timeout: float) -> Path | None:
    last = "converter produced no output"
    for profile in (None, _profile_flag(workdir)):
        outdir = workdir if profile is None else workdir / "profile"
        outdir.mkdir(parents=True, exist_ok=True)
        cmd = [conv.path, "--headless"]
        if profile:
            cmd.append(profile)
        cmd += ["--convert-to", "pdf", "--outdir", str(outdir), str(deck)]
        try:
            rc, stdout, stderr = _run(cmd, timeout)
        except _Timeout as exc:
            raise RuntimeError(str(exc)) from None
        produced = _find_pdf(outdir, deck.stem)
        if rc == 0 and produced is not None:
            return produced
        detail = _text(stderr or stdout)
        last = f"exited {rc}" + (f": {detail}" if detail else "")
    raise RuntimeError(last)


PS_SCRIPT = r"""param([string]$InputPath, [string]$OutputPath)
$created = $false
try {
  $ppt = [Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application')
} catch {
  $ppt = New-Object -ComObject PowerPoint.Application
  $created = $true
}
try {
  $deck = $null
  try {
    $deck = $ppt.Presentations.Open($InputPath, -1, 0, 0)
  } catch {
    $deck = $ppt.Presentations.Open($InputPath, -1, 0, -1)
  }
  try {
    $deck.SaveAs($OutputPath, 32)
  } finally {
    $deck.Close()
  }
} finally {
  if ($created) {
    $ppt.Quit()
  }
}
"""

APPLESCRIPT = r"""on run argv
  set inPath to item 1 of argv
  set outPath to item 2 of argv
  tell application "Microsoft PowerPoint"
    launch
    open inPath
    set thePres to active presentation
    save thePres in (POSIX file outPath) as save as PDF
    close thePres saving no
  end tell
end run
"""


def _convert_powerpoint(conv: Converter, deck: Path, workdir: Path, timeout: float) -> Path | None:
    system = platform.system()
    out = workdir / (deck.stem + ".pdf")
    if system == "Windows":
        script = workdir / "export_pdf.ps1"
        script.write_text(PS_SCRIPT, encoding="utf-8")
        interpreter = shutil.which("powershell") or shutil.which("pwsh") or "powershell.exe"
        cmd = [
            interpreter, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(script), "-InputPath", str(deck), "-OutputPath", str(out),
        ]
    elif system == "Darwin":
        script = workdir / "export_pdf.applescript"
        script.write_text(APPLESCRIPT, encoding="utf-8")
        cmd = [shutil.which("osascript") or "osascript", str(script), str(deck), str(out)]
    else:
        raise RuntimeError(f"PowerPoint export is not supported on {system}")
    rc, stdout, stderr = _run(cmd, timeout)
    if rc != 0:
        detail = _text(stderr or stdout)
        raise RuntimeError(f"exited {rc}" + (f": {detail}" if detail else ""))
    return out if out.exists() else None


def _convert_with(conv: Converter, deck: Path, workdir: Path, timeout: float) -> Path | None:
    if conv.kind == "cli":
        return _convert_soffice(conv, deck, workdir, timeout)
    if conv.kind == "powerpoint":
        return _convert_powerpoint(conv, deck, workdir, timeout)
    raise RuntimeError(f"unknown converter kind: {conv.kind}")


def _valid_pdf(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size <= 0:
            return False
        with path.open("rb") as handle:
            return PDF_MAGIC in handle.read(1024)
    except OSError:
        return False


def convert_to_pdf(deck: Path, out: Path, timeout: float = 300.0) -> ConversionResult:
    """Convert ``deck`` to ``out``, atomically, using the first converter that works."""
    deck_path = Path(deck).resolve()
    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = out_path.resolve()
    if out_path.suffix.lower() != ".pdf":
        out_path = out_path.with_suffix(".pdf")

    converters = find_converters()
    if not converters:
        raise ConversionError(deck_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    attempts: list[tuple[str, str]] = []
    with tempfile.TemporaryDirectory(prefix=".pdf-export-", dir=str(out_path.parent)) as tmp:
        root = Path(tmp)
        for index, conv in enumerate(converters):
            workdir = root / f"{index}-{conv.name}"
            workdir.mkdir(parents=True, exist_ok=True)
            try:
                produced = _convert_with(conv, deck_path, workdir, timeout)
            except Exception as exc:  # noqa: BLE001 - every failure is an attempt
                attempts.append((conv.name, f"{type(exc).__name__}: {exc}"))
                continue
            if produced is None:
                attempts.append((conv.name, "exited without writing a PDF"))
                continue
            if not _valid_pdf(produced):
                attempts.append((conv.name, f"output is not a PDF: {produced}"))
                continue
            try:
                os.replace(produced, out_path)
            except OSError as exc:
                raise ConversionError(
                    deck_path,
                    [(conv.name, f"could not write {out_path}: {exc}")],
                    converters,
                    unsupported_apps(),
                ) from exc
            return ConversionResult(pdf=out_path, converter=conv.name, label=conv.label)
    raise ConversionError(deck_path, attempts, converters, unsupported_apps())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the available office converters.")
    parser.add_argument("--list", action="store_true", help="list detected converters")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    info = describe_environment()
    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
        return 0
    if info["converters"]:
        for conv in info["converters"]:
            print(f"{conv['name']}: {conv['label']} ({conv['path']})")
    else:
        print(no_converter_detail())
    if info["unsupported"]:
        print("detected but not automatable (GUI only):")
        for app in info["unsupported"]:
            print(f"  {app['name']}: {app['label']} ({app['path']})")
    if not args.list:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())