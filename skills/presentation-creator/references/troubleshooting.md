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
- If it is truly a false positive, confirm visually with the LibreOffice preview before
  overriding; document the override in the deck notes.

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

## LibreOffice preview unavailable

`soffice` is optional. If `soffice --version` fails, the PDF preview step is skipped — say so
in the delivery summary. The deck is still valid; open it in PowerPoint, Keynote, Google
Slides, or the VS Code PowerPoint viewer.

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
