# Presentation Creator: PDF export + office-suite preview fallback

## Goal

1. **Save/export as PDF**: `scripts/build_deck.py` can emit a PDF deliverable alongside the `.pptx` (`--pdf`), and `scripts/render_preview.py` can export a PDF for an existing deck (`--pdf-out`).
2. **Preview without LibreOffice**: PDF preview/export works when LibreOffice is absent but another supported office app is installed — OpenOffice (soffice-compatible CLI) or Microsoft PowerPoint (Windows COM / macOS AppleScript).

## Acceptance criteria

- `python3 scripts/build_deck.py deck.json -o deck.pptx --pdf` writes `deck.pptx` and `deck.pdf` (default PDF path is `<out>.pdf`), prints the converter used, and exits 0.
- `--pdf custom/out.pdf` writes the PDF to the given path; `--force` is required to overwrite an existing `.pptx` or explicit PDF.
- `python3 scripts/render_preview.py deck.pptx -o previews` still works and now uses the first available converter, not only `soffice`.
- `python3 scripts/render_preview.py deck.pptx --pdf-out deck.pdf --no-png` exports a PDF from an existing deck without requiring PNG rendering.
- With no supported converter: optional preview prints a clear "skipped" message and exits 0; an explicit PDF request fails with exit 3 and does not claim success.
- Existing `build_deck.py`, `validate_deck.py`, and test behavior remains unchanged when no PDF flags are used.

## Current state (evidence)

- `skills/presentation-creator/scripts/render_preview.py:33-36` — hard-codes `soffice`/`libreoffice`; prints `skipped` when absent.
- `skills/presentation-creator/scripts/render_preview.py:38-79` — PDF is only an intermediate artifact; manual backup/restore logic.
- `skills/presentation-creator/scripts/build_deck.py:1550-1598` — builds `.pptx` only; no PDF option.
- `skills/presentation-creator/SKILL.md:100-112` — preview documented as LibreOffice-only.
- `skills/presentation-creator/references/troubleshooting.md:44-48` — says preview is skipped without `soffice`.
- `skills/presentation-creator/SKILL.md:8-11,15` — compatibility says "LibreOffice is optional for PDF previews"; version is `1.3.0`.
- `skills/presentation-creator/examples/example-brief.md:73` — final delivery note says PDF preview is skipped when `soffice` is absent.

## Decisions

- **PDF surface**: `build_deck.py --pdf [PATH]` (default `<out>.pdf`), plus `render_preview.py --pdf-out PATH` for existing decks.
- **Fallback apps**: soffice-compatible CLI (LibreOffice, OpenOffice, `ooffice`, `openoffice.org`, absolute install paths) and Microsoft PowerPoint (Windows COM, macOS AppleScript). OnlyOffice/WPS/Keynote/Google Slides are out of scope.
- **Converter order**: LibreOffice/OpenOffice first (best headless fidelity), then PowerPoint.
- **Failure policy**:
  - `build_deck.py --pdf`: explicit request → exit 3 if no converter or all conversions fail; the `.pptx` is still valid and remains on disk.
  - `render_preview.py` without `--pdf-out`: optional preview → no converter exits 0 with a skip message; converter present but conversion fails exits 1 (existing behavior).
  - `render_preview.py --pdf-out`: explicit request → exit 3 if no converter/all conversions fail; exit 2 if the target exists without `--force`.
- **Out of scope**: OnlyOffice, WPS, Keynote, Google Slides, pure-Python PDF rendering, PDF editing, and upstream repository synchronization.

## Implementation tasks

### 1. Add `skills/presentation-creator/scripts/office_convert.py`

A standalone converter registry/module (no `python-pptx` dependency) used by both scripts.

Data model:

```python
@dataclass(frozen=True)
class Converter:
    name: str      # "soffice", "openoffice", "powerpoint-com", "powerpoint-applescript"
    kind: str      # "cli" | "powerpoint"
    path: str      # executable / interpreter
    label: str     # human-readable label

@dataclass(frozen=True)
class ConversionResult:
    pdf: Path
    converter: str
    label: str

class ConversionError(RuntimeError):
    attempts: list[tuple[str, str]]
```

Public API:

- `find_converters() -> list[Converter]` — ordered, de-duplicated by resolved path.
- `convert_to_pdf(deck: Path, out: Path, timeout: float = 300.0) -> ConversionResult`.
- `describe_environment() -> dict` — converters plus detected-but-unsupported apps.
- `main()` — `python3 scripts/office_convert.py --list [--json]` for troubleshooting/tests.

Detection:

- soffice-compatible names: `soffice`, `libreoffice`, `openoffice`, `openoffice.org`, `ooffice` via `shutil.which`.
- Absolute candidates: `/usr/lib64/libreoffice/program/soffice`, `/usr/lib/libreoffice/program/soffice`, `/opt/libreoffice*/program/soffice`, `/opt/openoffice*/program/soffice`, `/usr/lib64/openoffice*/program/soffice`, `/usr/lib/openoffice*/program/soffice`, `/Applications/LibreOffice.app/Contents/MacOS/soffice`, `/Applications/OpenOffice.app/Contents/MacOS/soffice`, Windows `Program Files` paths.
- PowerPoint:
  - Windows: `powershell`/`pwsh` plus `POWERPNT.EXE` (PATH or common Office paths).
  - macOS: `osascript` plus `/Applications/Microsoft PowerPoint.app`.
- Detection-only reporting for `onlyoffice-desktopeditors`, `/opt/onlyoffice/desktopeditors/DesktopEditors`, `wps`, `wpp`, `et`, `/opt/kingsoft/wps-office/office6/wps`; these are reported but never used for conversion.

Conversion:

- soffice-compatible:
  - `<exe> --headless --convert-to pdf --outdir <tmpdir> <deck>`
  - On failure/no output, retry once with `-env:UserInstallation=file://<private temp profile>`.
  - Locate `<tmpdir>/<deck.stem>.pdf` (case-insensitive fallback `*.pdf`).
- PowerPoint Windows COM:
  - Write a temporary `.ps1` file and run `powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File <script> -InputPath <deck> -OutputPath <out>`.
  - Script: reuse an existing `PowerPoint.Application` via `Marshal.GetActiveObject` when possible; otherwise create one and quit only if created; open read-only with `Presentations.Open($InputPath, -1, 0, 0)` (`ReadOnly=msoTrue`, `Untitled=msoFalse`, `WithWindow=msoFalse`), call `SaveAs($OutputPath, 32)` (`ppSaveAsPDF`), close only the presentation we opened. Never quit an instance we did not create. If opening with `WithWindow=0` fails, retry with `WithWindow=-1`.
- PowerPoint macOS AppleScript:
  - `osascript <temp>.applescript <deck> <out>`; script opens the deck, `save active presentation in (POSIX file outPath) as save as PDF`, closes only the presentation we opened. Do not quit PowerPoint.
- Shared `_run(cmd, timeout)`:
  - `Popen` with `start_new_session=True` on POSIX / `CREATE_NEW_PROCESS_GROUP` on Windows.
  - On `TimeoutExpired`, kill the whole process group (SIGTERM, then SIGKILL) so `soffice.bin`/`POWERPNT.EXE` children are not orphaned.
- Output validation: file exists, size > 0, and first 1024 bytes contain `b"%PDF-"`.
- Conversion is atomic: convert into a temporary directory inside `out.parent`, validate, then `os.replace` to the final path. If conversion fails, the existing target file is untouched.
- Error aggregation: `ConversionError` includes each attempted converter and its failure; the top-level message lists checked converters and detected-but-unsupported apps.

### 2. Update `skills/presentation-creator/scripts/build_deck.py`

- Import `ConversionError`, `convert_to_pdf` from `office_convert`.
- Add arguments:
  - `--pdf [PATH]` with `nargs="?"`, `const=""`; default PDF is `out_path.with_suffix(".pdf")`.
  - `--timeout` (seconds, default 300).
- Before building, if `--pdf` was requested and the target PDF exists, require `--force` (same exit 2 behavior as `.pptx`).
- After the `.pptx` atomic save:
  - Call `convert_to_pdf(out_path, pdf_path, timeout=args.timeout)`.
  - On success print `Rendered PDF: <path> (via <label>)`.
  - On `ConversionError` print the error plus `The .pptx was written to <path>.` and return 3.
- Preserve current output/exit codes when `--pdf` is absent.

### 3. Update `skills/presentation-creator/scripts/render_preview.py`

- Replace direct `soffice` detection and the backup/restore block with `convert_to_pdf`.
- Arguments:
  - Keep `-o/--outdir` for preview artifacts.
  - Add `--pdf-out PATH` (file path; if it is an existing directory, write `<dir>/<deck.stem>.pdf`).
  - Add `--no-png` and `--force`.
  - `--timeout` description becomes "converter timeout (seconds)".
- Validation:
  - Require `-o` or `--pdf-out`; if only `--pdf-out` is given, skip PNGs.
  - If `--pdf-out` exists and `--force` is absent, exit 2 before converting.
  - Default preview PDF (`<outdir>/<stem>.pdf`) keeps the existing overwrite behavior.
- Behavior:
  - No converter and no explicit `--pdf-out`: print `skipped: no PDF converter available; checked ...`, return 0.
  - No converter and explicit `--pdf-out`: print the same detail, return 3.
  - Converter present but conversion fails: return 1 (explicit `--pdf-out`: 3).
  - After a successful PDF, run `pdftoppm` unless `--no-png`; keep current PNG messages/cleanup.

### 4. Tests

Add `skills/presentation-creator/tests/test_office_convert.py`:

- Detection order: prefers `soffice`; falls back to `openoffice`; de-dupes `soffice`/`libreoffice` resolving to the same binary.
- Conversion: fake executable writes a valid PDF; output is moved to the requested path.
- Retry: fake converter fails without `-env:UserInstallation` and succeeds with it.
- Validation: a converter that writes a non-PDF is rejected and the next converter is tried.
- All converters fail: `ConversionError` includes each attempt.
- No converter: clear error.
- `describe_environment`/`--list --json` shape.
- PowerPoint adapters: unit-test command/script construction with `platform.system`, `shutil.which`, and `_run` patched; do not launch PowerPoint.

Add `skills/presentation-creator/tests/test_pdf_export.py` (or extend `tests/test_examples.py`):

- `build_deck.py --pdf` with a fake `soffice` on `PATH` produces both `.pptx` and a valid `.pdf`.
- `--force` is required when the `.pptx` or explicit PDF already exists.
- No converter: exit 3, `.pptx` still exists.
- `render_preview.py --pdf-out --no-png` with a fake converter produces the PDF and no PNGs.
- `render_preview.py` with no converter: exit 0 and a skip message.

Use temporary executable scripts for the fake converter (POSIX); skip or adapt on Windows. Keep existing tests (`test_deck.py`, `test_layouts.py`, `test_examples.py`) passing.

### 5. Documentation

- `skills/presentation-creator/SKILL.md`:
  - Update `description` to mention optional PDF export/preview.
  - Update `compatibility`: "LibreOffice, OpenOffice, or PowerPoint (Windows/macOS) is optional for PDF export/previews."
  - Bump `metadata.version` to `1.4.0`.
  - Rewrite step 6 as "Optional preview and PDF export" with:
    - `python3 scripts/build_deck.py deck.json -o deck.pptx --pdf`
    - `python3 scripts/render_preview.py deck.pptx -o previews`
    - `python3 scripts/render_preview.py deck.pptx --pdf-out deck.pdf --no-png`
    - converter order, fallback behavior, and the no-converter message.
  - Step 7: report the PDF path and converter used.
- `skills/presentation-creator/references/troubleshooting.md`:
  - Replace "LibreOffice preview unavailable" with "No PDF converter available" (what was checked, install options, GUI-only apps such as OnlyOffice/WPS are not automatable).
  - Add "OpenOffice conversion fails" (profile lock; private-profile retry).
  - Add "PowerPoint export fails" (requires an interactive desktop session; never quit an existing instance).
  - Add "PDF export requested but no converter" (exit 3).
- `skills/presentation-creator/examples/example-brief.md`: update the final delivery note to mention `--pdf` and the fallback chain.
- `skills/marketplace.yaml`: generated artifact — do not hand-edit. CI regenerates it; run `cd bin && pnpm exec tsx generate-skill-marketplace.ts` only if local consistency is needed.

## CLI contracts

```sh
# Build .pptx + PDF (default PDF path: <output>.pdf)
python3 scripts/build_deck.py deck.json -o deck.pptx --pdf [--force] [--timeout 300]

# Build .pptx + PDF at a specific path
python3 scripts/build_deck.py deck.json -o deck.pptx --pdf exports/deck.pdf --force

# Preview an existing deck (PDF + PNGs when pdftoppm is available)
python3 scripts/render_preview.py deck.pptx -o previews

# Export a PDF only (no PNGs)
python3 scripts/render_preview.py deck.pptx --pdf-out deck.pdf --no-png [--force]

# Inspect detected converters
python3 scripts/office_convert.py --list [--json]
```

Exit codes: `0` success/optional skip; `2` usage/IO/overwrite protection; `3` explicit PDF conversion unavailable or failed; `1` optional preview conversion failure.

## Failure modes and mitigations

- **No office app**: explicit PDF request exits 3 with a list of checked converters; optional preview exits 0 and says skipped.
- **LibreOffice/OpenOffice profile lock or concurrent runs**: retry with a private `-env:UserInstallation` profile.
- **Converter exits 0 but writes nothing**: validate the PDF magic bytes; try the next converter.
- **Timeout leaves child processes**: kill the process group, not just the parent.
- **PowerPoint already running**: reuse the COM instance; close only the presentation we opened; never call `Quit` on an instance we did not create.
- **Headless/service Windows session**: PowerPoint COM cannot run; report the limitation and suggest LibreOffice/OpenOffice.
- **macOS path/encoding quirks**: use `POSIX file` coercion and a temporary `.applescript` file; test on macOS.
- **Partial output**: convert into a temp directory and `os.replace` only after validation.
- **PDF export succeeds but QA gate not run**: document that `--pdf` does not replace `validate_deck.py`; the workflow still requires the QA gate before delivery.
- **OnlyOffice/WPS installed**: report them as detected but not automatable; do not claim preview/export.

## Validation plan

1. Unit/integration tests:
   ```sh
   python3 -m unittest discover -s skills/presentation-creator/tests -p 'test_*.py'
   python3 skills/presentation-creator/scripts/test_deck.py
   ```
2. Syntax check:
   ```sh
   python3 -m py_compile skills/presentation-creator/scripts/*.py
   ```
3. Manual end-to-end on a machine with LibreOffice (this workspace has `soffice`):
   ```sh
   python3 skills/presentation-creator/scripts/build_deck.py \
     skills/presentation-creator/examples/example-deck.json \
     -o /tmp/kilo/deck.pptx --pdf --force
   file /tmp/kilo/deck.pdf

   python3 skills/presentation-creator/scripts/render_preview.py \
     /tmp/kilo/deck.pptx -o /tmp/kilo/preview \
     --pdf-out /tmp/kilo/preview.pdf --no-png

   python3 skills/presentation-creator/scripts/office_convert.py --list
   ```
4. Fallback simulation (no real office app needed):
   - Put a fake `soffice` that fails and a fake `openoffice` that writes a valid PDF earlier on `PATH`; assert the PDF is produced via `openoffice`.
   - Remove all converters from `PATH`; assert `build_deck --pdf` exits 3 and `render_preview` exits 0 with a skip message.
5. Skill validation (CI): `skills-ref validate skills/presentation-creator`.
6. If `SKILL.md` metadata is touched and local marketplace consistency is required: `cd bin && pnpm exec tsx generate-skill-marketplace.ts` and run `pnpm test`.

## Rollout notes

- Changes are backward-compatible: no PDF flags means unchanged behavior.
- If `nitsan57/presentation_skill` is the canonical upstream for this skill, mirror the same changes there and update `metadata.source.commit` to the new full SHA. This is not required for local implementation and is out of scope unless requested.