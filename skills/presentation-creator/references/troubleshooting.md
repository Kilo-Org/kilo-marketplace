# Troubleshooting

Symptom-first fixes for the presentation-creator workflow.

## `ModuleNotFoundError: No module named 'pptx'`

`python-pptx` is not installed for the interpreter you are using. Options, in order:

1. Use the venv the skill was set up with: `/tmp/pptx-venv/bin/python scripts/build_deck.py ...`.
2. Create one: `python3 -m venv /tmp/pptx-venv && /tmp/pptx-venv/bin/pip install python-pptx`.
3. `pip install --user python-pptx` (no root needed).

Ask before installing into system site-packages. Verify with
`python3 -c "import pptx; print(pptx.__version__)"`.

## Validator reports text overflow, but it looks fine (estimate)

The validator estimates overflow from font size, box width, and box height — it does not
render. False positives happen with long unbroken tokens, unusual fonts, or generous line
spacing. Fixes:

- Widen the box or lower the font size to the preset floor.
- Split the slide (the estimate is a signal that the slide is genuinely dense).
- Move detail into speaker notes.
- If it is truly a false positive, confirm visually with the LibreOffice preview, then fix the
  slide (widen the box, reduce text, or split it). The QA gate is a hard requirement and may
  not be overridden or skipped.

## Missing fonts

PowerPoint substitutes missing fonts and the layout can drift. `build_deck.py` uses
widely-available fonts (`Segoe UI`, `Calibri`) with fallbacks. If a brand font is required:

- State that the font must be installed on the machine that renders the deck.
- Keep to a font that is present on Windows and macOS when portability matters.
- Never fetch font files from the network without approval.

## Missing images

`add_picture` raises `FileNotFoundError` for a missing path. Confirm paths are absolute and
exist before building. The skill never downloads remote images; ask the user for a local file
or approval to fetch one.

## No PDF converter available

PDF export and previews need one of: LibreOffice, OpenOffice (any `soffice`-compatible CLI), or
Microsoft PowerPoint (Windows COM / macOS AppleScript). Check what this machine has:

```sh
python3 scripts/office_convert.py --list          # add --json for tooling
```

If the list is empty, the optional preview prints `skipped: no PDF converter available ...` and
exits 0, while an explicit `build_deck.py --pdf` or `render_preview.py --pdf-out` exits 3. The
deck itself is still valid; open it in PowerPoint, Keynote, Google Slides, or the VS Code
PowerPoint viewer. GUI-only suites (OnlyOffice, WPS) are reported as detected but are not
automatable — install LibreOffice for headless conversion.

## OpenOffice conversion fails

A stale profile lock makes the converter hang or exit immediately. `office_convert.py`
automatically retries once with a private `-env:UserInstallation` profile; if that still fails,
close running office instances and retry, or fall back to LibreOffice.

## PowerPoint export fails

PowerPoint export needs an interactive desktop session — it cannot run from a headless service
account. Reuse of a running instance is automatic: an existing `PowerPoint.Application` is reused,
and only a presentation opened by the export is closed. PowerPoint is never quit on your behalf.
If PowerPoint is installed but COM/AppleScript still fails, use LibreOffice or OpenOffice.

## PDF export requested but no converter

`build_deck.py --pdf` and `render_preview.py --pdf-out` exit 3 when nothing can convert. The
message lists every converter that was checked and the attempts that failed. The `.pptx` (when the
build produced one) is untouched and remains valid.

## Charts fail with a data error

- A pie chart takes exactly one series.
- `categories` length must equal each series' `values` length.
- Values must be numbers, not strings (`"1.2"` fails; `1.2` works).

## Table text is clipped

Empty cells are handled as blank strings; missing or short rows do not raise.

python-pptx does not auto-fit table row heights on save; the renderer does. Keep rows ≤8 and
columns ≤6, use the body font size, and let the validator flag oversized tables. For long
content, split into an appendix slide.

## `--force` refused / file exists

`build_deck.py` will not overwrite an existing `.pptx` unless `--force` is passed. This is
deliberate. Confirm with the user before overwriting, then re-run with `--force`.

## Contrast false positive

The validator compares the nearest solid-fill shape behind the text with the text color. If a
text box sits over a gradient or image, the estimate can be wrong. Prefer placing text on a
solid card (see `python-pptx-recipes.md`), which makes the contrast deterministic and the
check meaningful.
