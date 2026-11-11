#!/usr/bin/env python3
"""Optional visual QA helper.

Exports a .pptx to PDF with the first available office converter (LibreOffice,
OpenOffice, or PowerPoint) and, when pdftoppm is available, PNG keyframes.
Skips gracefully when no converter is available.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from office_convert import ConversionError, convert_to_pdf, find_converters, no_converter_detail


def _pdf_target(raw: str, deck: Path) -> Path:
    path = Path(raw)
    if path.is_dir():
        return path / (deck.stem + ".pdf")
    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a .pptx preview (optional).")
    parser.add_argument("deck", help="path to the .pptx file")
    parser.add_argument("-o", "--outdir", help="output directory for preview artifacts")
    parser.add_argument(
        "--pdf-out",
        metavar="PATH",
        help="export a PDF to this file path (or into this directory as <deck>.pdf)",
    )
    parser.add_argument("--no-png", action="store_true", help="skip PNG keyframes")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --pdf-out target")
    parser.add_argument("--dpi", type=int, default=110, help="PNG resolution")
    parser.add_argument("--timeout", type=float, default=300.0, help="converter timeout (seconds)")
    args = parser.parse_args()

    if not args.outdir and not args.pdf_out:
        parser.error("provide -o/--outdir and/or --pdf-out")

    deck = Path(args.deck).resolve()
    if not deck.is_file():
        print(f"error: deck not found: {deck}", file=sys.stderr)
        return 2

    outdir = None
    if args.outdir:
        outdir = Path(args.outdir).resolve()
        outdir.mkdir(parents=True, exist_ok=True)

    explicit_pdf = args.pdf_out is not None
    if explicit_pdf:
        pdf_path = _pdf_target(args.pdf_out, deck).resolve()
        if pdf_path.exists() and not args.force:
            print(f"error: {pdf_path} exists; pass --force to overwrite", file=sys.stderr)
            return 2
    elif outdir is not None:
        pdf_path = outdir / (deck.stem + ".pdf")
    else:  # pragma: no cover - argparse already guarantees one of the two
        pdf_path = None

    converters = find_converters()
    if not converters:
        if explicit_pdf:
            print(f"error: {no_converter_detail()}", file=sys.stderr)
            return 3
        print(f"skipped: {no_converter_detail()}; preview not rendered.")
        return 0

    assert pdf_path is not None
    try:
        result = convert_to_pdf(deck, pdf_path, timeout=args.timeout)
    except ConversionError as exc:
        print(str(exc), file=sys.stderr)
        if explicit_pdf:
            return 3
        print("skipped: PDF conversion failed.")
        return 1
    print(f"Rendered PDF: {result.pdf} (via {result.label})")

    if args.no_png or outdir is None:
        return 0

    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        prefix = outdir / "slide"
        for old in outdir.glob("slide*.png"):
            try:
                old.unlink()
            except OSError:
                pass
        try:
            proc2 = subprocess.run(
                [pdftoppm, "-png", "-r", str(args.dpi), str(result.pdf), str(prefix)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.timeout,
            )
        except subprocess.TimeoutExpired:
            print("warning: pdftoppm timed out; PNG keyframes may be partial.")
            return 0
        if proc2.returncode != 0:
            print(f"warning: pdftoppm failed (rc={proc2.returncode}): {proc2.stderr.decode(errors='replace').strip()}")
            return 1
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
