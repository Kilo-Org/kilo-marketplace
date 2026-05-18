#!/usr/bin/env bash
# export_pdf.sh — Export a .docx file to PDF using LibreOffice headless.
#
# Usage: bash export_pdf.sh <input.docx> [output-dir]
#
# The output PDF is placed in output-dir (defaults to the same directory as
# input). The output filename matches the input stem: input.docx -> input.pdf.
#
# Install LibreOffice:
#   Ubuntu/Debian: sudo apt-get install -y libreoffice
#   macOS:         brew install --cask libreoffice

set -euo pipefail

# ── Argument handling ────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <input.docx> [output-dir]" >&2
  exit 1
fi

INPUT="$(realpath "$1")"
OUTDIR="${2:-$(dirname "$INPUT")}"

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

"$SOFFICE" --headless --convert-to pdf "$INPUT" --outdir "$OUTDIR"

STEM="$(basename "${INPUT%.*}")"
OUT_PDF="${OUTDIR}/${STEM}.pdf"

if [[ -f "$OUT_PDF" ]]; then
  echo "Exported: $OUT_PDF"
else
  echo "Warning: expected output not found: $OUT_PDF" >&2
  exit 1
fi
