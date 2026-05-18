#!/usr/bin/env python3
"""
thumbnail.py — Create a visual thumbnail grid from a .pptx file.

Converts each slide to a JPEG via LibreOffice + pdftoppm, then assembles
them into a labelled grid image. Useful for template analysis and QA.

Usage:
  python thumbnail.py INPUT.pptx [OUTPUT_PREFIX] [--cols N]

Outputs: OUTPUT_PREFIX.jpg  (or OUTPUT_PREFIX-1.jpg, -2.jpg for large decks)
Default OUTPUT_PREFIX: thumbnails

Examples:
  python scripts/thumbnail.py deck.pptx
  python scripts/thumbnail.py template.pptx grid --cols 4

Requirements:
  pip install Pillow
  apt-get install libreoffice poppler-utils   # or equivalent
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

THUMBNAIL_W   = 320
CONVERSION_DPI = 100
DEFAULT_COLS  = 3
MAX_COLS      = 6
MAX_PER_GRID  = 12
JPEG_QUALITY  = 90
PADDING       = 16
BORDER        = 2
LABEL_RATIO   = 0.09

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

try:
    from office.soffice import get_soffice_env
except ImportError:
    import os
    def get_soffice_env():
        env = os.environ.copy()
        env["SAL_USE_VCLPLUGIN"] = "svp"
        return env


def _convert_to_images(pptx: Path, tmpdir: Path) -> list[Path]:
    env    = get_soffice_env()
    result = subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", str(pptx), "--outdir", str(tmpdir)],
        env=env, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"LibreOffice error: {result.stderr}", file=sys.stderr)
        return []

    pdf = tmpdir / (pptx.stem + ".pdf")
    if not pdf.exists():
        print(f"PDF not created: {pdf}", file=sys.stderr)
        return []

    prefix = str(tmpdir / "slide")
    result = subprocess.run(
        ["pdftoppm", "-jpeg", "-r", str(CONVERSION_DPI), str(pdf), prefix],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"pdftoppm error: {result.stderr}", file=sys.stderr)
        return []

    return sorted(tmpdir.glob("slide-*.jpg")) or sorted(tmpdir.glob("slide*.jpg"))


def _slide_name_for(img: Path, slides_dir: Path | None) -> str:
    """Best-effort: map image index → slide N.xml."""
    m = None
    import re
    m = re.search(r"-?(\d+)\.jpg$", img.name)
    if m:
        n = int(m.group(1))
        return f"slide{n}.xml"
    return img.name


def _build_grid(images: list[Path], output: str, cols: int,
                slides_dir: Path | None = None) -> None:
    if not images:
        print("No images to grid.", file=sys.stderr)
        return

    sample  = Image.open(images[0])
    ar      = sample.height / sample.width
    thumb_h = int(THUMBNAIL_W * ar)
    font_sz = max(10, int(thumb_h * LABEL_RATIO))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_sz)
    except (IOError, OSError):
        font = ImageFont.load_default()

    label_h = font_sz + 6
    cell_w  = THUMBNAIL_W + PADDING * 2
    cell_h  = thumb_h     + PADDING * 2 + label_h

    chunks = [images[i:i + MAX_PER_GRID]
              for i in range(0, len(images), MAX_PER_GRID)]

    for page_idx, chunk in enumerate(chunks):
        rows     = (len(chunk) + cols - 1) // cols
        canvas_w = cell_w * cols
        canvas_h = cell_h * rows
        canvas   = Image.new("RGB", (canvas_w, canvas_h), (245, 245, 245))
        draw     = ImageDraw.Draw(canvas)

        for i, img_path in enumerate(chunk):
            col, row = i % cols, i // cols
            x0, y0   = col * cell_w + PADDING, row * cell_h + PADDING

            thumb = Image.open(img_path).resize(
                (THUMBNAIL_W, thumb_h), Image.LANCZOS
            )
            if BORDER:
                bordered = Image.new("RGB",
                                     (THUMBNAIL_W + BORDER * 2, thumb_h + BORDER * 2),
                                     (200, 200, 200))
                bordered.paste(thumb, (BORDER, BORDER))
                canvas.paste(bordered, (x0 - BORDER, y0 - BORDER))
            else:
                canvas.paste(thumb, (x0, y0))

            label = _slide_name_for(img_path, slides_dir)
            draw.text((x0, y0 + thumb_h + 4), label, fill=(80, 80, 80), font=font)

        suffix = f"-{page_idx + 1}" if len(chunks) > 1 else ""
        out    = f"{output}{suffix}.jpg"
        canvas.save(out, "JPEG", quality=JPEG_QUALITY)
        print(f"Saved: {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input",           help="Input .pptx")
    ap.add_argument("output_prefix",   nargs="?", default="thumbnails",
                    help="Output file prefix (default: thumbnails)")
    ap.add_argument("--cols", type=int, default=DEFAULT_COLS,
                    help=f"Columns in grid (default: {DEFAULT_COLS}, max: {MAX_COLS})")
    args = ap.parse_args()

    cols      = min(args.cols, MAX_COLS)
    pptx_path = Path(args.input)
    if not pptx_path.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        images = _convert_to_images(pptx_path, tmpdir)
        if not images:
            print("Could not convert slides to images. "
                  "Ensure LibreOffice and poppler-utils are installed.", file=sys.stderr)
            sys.exit(1)
        _build_grid(images, args.output_prefix, cols)


if __name__ == "__main__":
    main()
