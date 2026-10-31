#!/usr/bin/env python3
"""Optional visual QA helper.

Converts a .pptx to PDF (and, if pdftoppm is available, to PNG keyframes) using
LibreOffice. Skips gracefully when the tooling is absent.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a .pptx preview (optional).")
    parser.add_argument("deck", help="path to the .pptx file")
    parser.add_argument("-o", "--outdir", required=True, help="output directory")
    parser.add_argument("--dpi", type=int, default=110, help="PNG resolution")
    parser.add_argument("--timeout", type=int, default=300, help="LibreOffice timeout (seconds)")
    args = parser.parse_args()

    deck = Path(args.deck).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    if not deck.is_file():
        print(f"error: deck not found: {deck}", file=sys.stderr)
        return 2

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("skipped: LibreOffice (soffice) not available; preview not rendered.")
        return 0

    # Clean stale pdf to detect failure
    pdf = outdir / (deck.stem + ".pdf")
    try:
        if pdf.exists():
            pdf.unlink()
    except OSError:
        pass

    try:
        proc = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(deck)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"error: LibreOffice timed out after {args.timeout}s.", file=sys.stderr)
        return 1
    if proc.returncode != 0:
        print(f"error: LibreOffice failed (rc={proc.returncode}): {proc.stderr.decode(errors='replace').strip()}", file=sys.stderr)
    if not pdf.is_file():
        print("skipped: PDF conversion failed.")
        return 1
    print(f"Rendered PDF: {pdf}")

    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        prefix = outdir / "slide"
        # remove stale pngs
        for old in outdir.glob("slide*.png"):
            try:
                old.unlink()
            except OSError:
                pass
        try:
            proc2 = subprocess.run(
                [pdftoppm, "-png", "-r", str(args.dpi), str(pdf), str(prefix)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.timeout,
            )
        except subprocess.TimeoutExpired:
            print("warning: pdftoppm timed out; PNG keyframes may be partial.")
            return 0
        pngs = sorted(outdir.glob("slide*.png"))
        if pngs:
            print(f"Rendered {len(pngs)} PNG keyframe(s) in: {outdir}")
            print(f"  first: {pngs[0].name}")
        else:
            print(f"warning: pdftoppm produced no PNGs: {proc2.stderr.decode(errors='replace').strip()}")
    else:
        print("skipped: pdftoppm not available; PNG keyframes not rendered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
