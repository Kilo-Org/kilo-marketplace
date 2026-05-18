#!/usr/bin/env bash
# export_pdf.sh — Export a .pptx file to PDF (or PNG) using LibreOffice headless.
#
# Usage:
#   bash export_pdf.sh <input.pptx> [output-dir] [format]
#
# format: pdf (default) | png | jpg | svg
#
# PDF:  one multi-page PDF containing all slides
# PNG:  one PNG per slide — output/stem-slideN.png
#
# Install LibreOffice:
#   Ubuntu/Debian: sudo apt-get install -y libreoffice
#   macOS:         brew install --cask libreoffice

set -euo pipefail

# ── Argument handling ────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <input.pptx> [output-dir] [format]" >&2
  exit 1
fi

INPUT="$(realpath "$1")"
OUTDIR="${2:-$(dirname "$INPUT")}"
FORMAT="${3:-pdf}"

if [[ ! -f "$INPUT" ]]; then
  echo "Error: file not found: $INPUT" >&2
  exit 1
fi

# ── Locate LibreOffice ───────────────────────────────────────────────────────
SOFFICE=""
for candidate in soffice libreoffice \
    /usr/bin/soffice /usr/lib/libreoffice/program/soffice \
    "/Applications/LibreOffice.app/Contents/MacOS/soffice"; do
  if command -v "$candidate" &>/dev/null || [[ -x "$candidate" ]]; then
    SOFFICE="$candidate"
    break
  fi
done

if [[ -z "$SOFFICE" ]]; then
  echo "Error: LibreOffice not found. Install with:" >&2
  echo "  Ubuntu/Debian: sudo apt-get install -y libreoffice" >&2
  echo "  macOS:         brew install --cask libreoffice" >&2
  exit 1
fi

# ── Convert ──────────────────────────────────────────────────────────────────
mkdir -p "$OUTDIR"

"$SOFFICE" --headless --convert-to "$FORMAT" "$INPUT" --outdir "$OUTDIR"

STEM="$(basename "${INPUT%.*}")"
EXPECTED="${OUTDIR}/${STEM}.${FORMAT}"

if [[ "$FORMAT" == "png" ]]; then
  # LibreOffice names slides: stem.png, stem1.png, stem2.png …
  COUNT=$(find "$OUTDIR" -maxdepth 1 -name "${STEM}*.png" | wc -l)
  echo "Exported ${COUNT} PNG slide(s) to ${OUTDIR}/"
elif [[ -f "$EXPECTED" ]]; then
  echo "Exported: $EXPECTED"
else
  echo "Warning: expected output not found: $EXPECTED" >&2
  exit 1
fi
