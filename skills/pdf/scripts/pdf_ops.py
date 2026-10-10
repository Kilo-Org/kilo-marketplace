#!/usr/bin/env python3
"""PDF file operations CLI for AI coding assistants.

Provides subcommands for reading, extracting, and manipulating PDF files.

Requires: pypdf (pip install pypdf), pdfplumber (pip install pdfplumber)
Optional: pypdfium2 (pip install pypdfium2) — for PDF-to-image conversion
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print(
        "ERROR: pypdf is not installed.\n"
        "Install it with: pip install pypdf",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print(
        "ERROR: pdfplumber is not installed.\n"
        "Install it with: pip install pdfplumber",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_page_spec(spec: str, total_pages: int) -> list[int]:
    """Parse a page specification string into a sorted list of 0-based indices.

    Accepts comma-separated values and ranges (1-based):
      "1"       -> [0]
      "1,3,5"   -> [0, 2, 4]
      "1-5"     -> [0, 1, 2, 3, 4]
      "2,5-8"   -> [1, 4, 5, 6, 7]
    """
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            if start < 1 or end > total_pages or start > end:
                print(
                    f"ERROR: Invalid page range '{part}'. "
                    f"Document has {total_pages} pages.",
                    file=sys.stderr,
                )
                sys.exit(2)
            pages.update(range(start - 1, end))
        else:
            page_num = int(part)
            if page_num < 1 or page_num > total_pages:
                print(
                    f"ERROR: Page {page_num} out of range. "
                    f"Document has {total_pages} pages.",
                    file=sys.stderr,
                )
                sys.exit(2)
            pages.add(page_num - 1)
    return sorted(pages)


def _load_reader(path: str) -> PdfReader:
    """Load a PdfReader, handling common errors."""
    p = Path(path)
    if not p.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)
    if p.suffix.lower() != ".pdf":
        print(f"ERROR: Not a PDF file: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        return PdfReader(str(p))
    except Exception as exc:
        print(f"ERROR: Cannot read PDF: {exc}", file=sys.stderr)
        sys.exit(2)
        raise  # unreachable, satisfies type checker


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _resolve_pages(
    args: argparse.Namespace, total_pages: int
) -> list[int]:
    """Resolve --pages argument to 0-based page indices, or all pages."""
    if args.pages:
        return _parse_page_spec(args.pages, total_pages)
    return list(range(total_pages))


def _write_pdf(writer: PdfWriter, output_path: str) -> None:
    """Write a PdfWriter to disk."""
    try:
        with open(output_path, "wb") as f:
            writer.write(f)
    except Exception as exc:
        print(f"ERROR: Failed to write PDF: {exc}", file=sys.stderr)
        sys.exit(3)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_info(args: argparse.Namespace) -> None:
    """Show PDF metadata and structure."""
    reader = _load_reader(args.file)
    p = Path(args.file)
    meta = reader.metadata

    print(f"# PDF Info: {p.name}\n")
    print(f"- **Pages**: {len(reader.pages)}")
    print(f"- **File size**: {_format_size(p.stat().st_size)}")
    print(f"- **Encrypted**: {'Yes' if reader.is_encrypted else 'No'}")

    if meta:
        if meta.title:
            print(f"- **Title**: {meta.title}")
        if meta.author:
            print(f"- **Author**: {meta.author}")
        if meta.subject:
            print(f"- **Subject**: {meta.subject}")
        if meta.creator:
            print(f"- **Creator**: {meta.creator}")
        if meta.producer:
            print(f"- **Producer**: {meta.producer}")
        if meta.creation_date:
            print(f"- **Created**: {meta.creation_date}")
        if meta.modification_date:
            print(f"- **Modified**: {meta.modification_date}")

    for i, page in enumerate(reader.pages):
        box = page.mediabox
        w = float(box.width)
        h = float(box.height)
        w_in = w / 72
        h_in = h / 72
        print(
            f"- **Page {i + 1}**: {w:.0f} x {h:.0f} pt "
            f"({w_in:.1f} x {h_in:.1f} in)"
        )


def cmd_text(args: argparse.Namespace) -> None:
    """Extract text from PDF pages."""
    with pdfplumber.open(args.file) as pdf:
        total = len(pdf.pages)
        page_indices = _resolve_pages(args, total)

        for idx in page_indices:
            page = pdf.pages[idx]
            if args.layout:
                text = page.extract_text(
                    layout=True, keep_blank_chars=True
                )
            else:
                text = page.extract_text()

            if text:
                print(f"--- Page {idx + 1} ---")
                print(text)
                print()
            else:
                print(f"--- Page {idx + 1} ---")
                print("(no extractable text)")
                print()


def cmd_tables(args: argparse.Namespace) -> None:
    """Extract tables from PDF pages."""
    with pdfplumber.open(args.file) as pdf:
        total = len(pdf.pages)
        page_indices = _resolve_pages(args, total)

        all_tables: list[dict[str, Any]] = []
        table_num = 0

        for idx in page_indices:
            page = pdf.pages[idx]
            tables = page.extract_tables()
            if not tables:
                continue
            for table_data in tables:
                if not table_data or not any(table_data):
                    continue
                table_num += 1
                all_tables.append(
                    {
                        "page": idx + 1,
                        "table_number": table_num,
                        "rows": table_data,
                    }
                )

        if not all_tables:
            print("No tables found in the specified pages.")
            return

        fmt = args.format

        if fmt == "json":
            print(json.dumps(all_tables, indent=2, ensure_ascii=False))

        elif fmt == "csv":
            output_dir = Path(args.output_dir) if args.output_dir else Path(".")
            output_dir.mkdir(parents=True, exist_ok=True)
            stem = Path(args.file).stem
            for tbl in all_tables:
                csv_path = (
                    output_dir
                    / f"{stem}_p{tbl['page']}_t{tbl['table_number']}.csv"
                )
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for row in tbl["rows"]:
                        writer.writerow(
                            [cell if cell is not None else "" for cell in row]
                        )
                print(f"Saved: {csv_path}")

        else:
            for tbl in all_tables:
                print(
                    f"## Table {tbl['table_number']} "
                    f"(Page {tbl['page']})\n"
                )
                rows = tbl["rows"]
                if not rows:
                    continue
                clean_rows = [
                    [
                        str(cell).replace("|", "\\|") if cell is not None else ""
                        for cell in row
                    ]
                    for row in rows
                ]
                header = clean_rows[0]
                print("| " + " | ".join(header) + " |")
                print(
                    "| " + " | ".join("---" for _ in header) + " |"
                )
                for row in clean_rows[1:]:
                    while len(row) < len(header):
                        row.append("")
                    print("| " + " | ".join(row[: len(header)]) + " |")
                print()


def cmd_to_images(args: argparse.Namespace) -> None:
    """Convert PDF pages to PNG images."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        print(
            "ERROR: pypdfium2 is not installed.\n"
            "Install it with: pip install pypdfium2\n"
            "Or: pip install mythril-agent-skills[pdf-images]",
            file=sys.stderr,
        )
        sys.exit(1)

    p = Path(args.file)
    if not p.exists():
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    pdf = pdfium.PdfDocument(str(p))
    try:
        total = len(pdf)
        page_indices = _resolve_pages(args, total)

        output_dir = Path(args.output_dir) if args.output_dir else p.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        scale = args.scale if args.scale else 2.0

        for idx in page_indices:
            page = pdf[idx]
            bitmap = page.render(scale=scale)
            img = bitmap.to_pil()

            out_path = output_dir / f"{p.stem}_page_{idx + 1}.png"
            img.save(str(out_path), "PNG")
            print(f"Saved: {out_path} ({img.width}x{img.height})")
    finally:
        pdf.close()


def cmd_merge(args: argparse.Namespace) -> None:
    """Merge multiple PDFs into one."""
    if len(args.files) < 2:
        print("ERROR: At least 2 PDF files required for merge.", file=sys.stderr)
        sys.exit(2)

    writer = PdfWriter()
    for pdf_path in args.files:
        reader = _load_reader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
        print(f"Added: {pdf_path} ({len(reader.pages)} pages)")

    _write_pdf(writer, args.output)
    print(f"\nMerged {len(args.files)} files -> {args.output}")


def cmd_split(args: argparse.Namespace) -> None:
    """Split a PDF by extracting specific pages."""
    reader = _load_reader(args.file)
    total = len(reader.pages)

    if args.each:
        output_dir = Path(args.output_dir) if args.output_dir else Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(args.file).stem
        page_indices = _resolve_pages(args, total)
        for idx in page_indices:
            w = PdfWriter()
            w.add_page(reader.pages[idx])
            out = output_dir / f"{stem}_page_{idx + 1}.pdf"
            _write_pdf(w, str(out))
            print(f"Saved: {out}")
        return

    if not args.pages:
        print(
            "ERROR: Specify --pages or --each for split.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not args.output:
        print("ERROR: -o/--output is required for split.", file=sys.stderr)
        sys.exit(2)

    page_indices = _parse_page_spec(args.pages, total)
    writer = PdfWriter()
    for idx in page_indices:
        writer.add_page(reader.pages[idx])

    _write_pdf(writer, args.output)
    print(f"Split {len(page_indices)} pages -> {args.output}")


def cmd_rotate(args: argparse.Namespace) -> None:
    """Rotate pages in a PDF."""
    reader = _load_reader(args.file)
    total = len(reader.pages)

    angle = args.angle
    if angle not in (90, 180, 270):
        print("ERROR: Angle must be 90, 180, or 270.", file=sys.stderr)
        sys.exit(2)

    if not args.output:
        print("ERROR: -o/--output is required for rotate.", file=sys.stderr)
        sys.exit(2)

    page_indices = set(_resolve_pages(args, total))

    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if i in page_indices:
            page.rotate(angle)
        writer.add_page(page)

    _write_pdf(writer, args.output)
    rotated_desc = "all pages" if len(page_indices) == total else f"{len(page_indices)} pages"
    print(f"Rotated {rotated_desc} by {angle}° -> {args.output}")


def cmd_extract_images(args: argparse.Namespace) -> None:
    """Extract embedded images from a PDF."""
    reader = _load_reader(args.file)
    total = len(reader.pages)
    page_indices = _resolve_pages(args, total)

    output_dir = Path(args.output_dir) if args.output_dir else Path(".")
    output_dir.mkdir(parents=True, exist_ok=True)

    img_count = 0
    stem = Path(args.file).stem

    for idx in page_indices:
        page = reader.pages[idx]
        if "/XObject" not in page.get("/Resources", {}):
            continue
        x_objects = page["/Resources"]["/XObject"].get_object()
        for obj_name in x_objects:
            obj = x_objects[obj_name].get_object()
            if obj.get("/Subtype") != "/Image":
                continue
            img_count += 1

            width = obj.get("/Width", 0)
            height = obj.get("/Height", 0)

            data = obj.get_data()
            filt = obj.get("/Filter", "")

            if filt == "/DCTDecode":
                ext = "jpg"
            elif filt == "/JPXDecode":
                ext = "jp2"
            elif filt == "/FlateDecode":
                ext = "png"
            elif filt == "/CCITTFaxDecode":
                ext = "tiff"
            else:
                ext = "bin"

            out_path = output_dir / f"{stem}_p{idx + 1}_img{img_count}.{ext}"

            if ext == "png":
                try:
                    from PIL import Image

                    if "/SMask" in obj:
                        has_alpha = True
                    else:
                        has_alpha = False

                    cs = obj.get("/ColorSpace", "")
                    if isinstance(cs, list):
                        cs = str(cs[0])

                    if cs in ("/DeviceRGB", "/CalRGB") or "RGB" in str(cs):
                        mode = "RGBA" if has_alpha else "RGB"
                        channels = 4 if has_alpha else 3
                    elif cs in ("/DeviceGray", "/CalGray") or "Gray" in str(cs):
                        mode = "LA" if has_alpha else "L"
                        channels = 2 if has_alpha else 1
                    elif cs in ("/DeviceCMYK",) or "CMYK" in str(cs):
                        mode = "CMYK"
                        channels = 4
                    else:
                        mode = "RGB"
                        channels = 3

                    expected = int(width) * int(height) * channels
                    if len(data) >= expected:
                        img = Image.frombytes(mode, (int(width), int(height)), data)
                        if mode == "CMYK":
                            img = img.convert("RGB")
                        img.save(str(out_path), "PNG")
                    else:
                        out_path = out_path.with_suffix(".bin")
                        with open(out_path, "wb") as f:
                            f.write(data)
                except ImportError:
                    out_path = out_path.with_suffix(".bin")
                    with open(out_path, "wb") as f:
                        f.write(data)
            else:
                with open(out_path, "wb") as f:
                    f.write(data)

            print(
                f"Extracted: {out_path} "
                f"({width}x{height}, {ext})"
            )

    if img_count == 0:
        print("No embedded images found in the specified pages.")
    else:
        print(f"\nExtracted {img_count} image(s).")


def cmd_decrypt(args: argparse.Namespace) -> None:
    """Decrypt a password-protected PDF."""
    if not args.output:
        print("ERROR: -o/--output is required for decrypt.", file=sys.stderr)
        sys.exit(2)

    reader = _load_reader(args.file)

    if not reader.is_encrypted:
        print("This PDF is not encrypted.")
        return

    try:
        reader.decrypt(args.password)
    except Exception as exc:
        print(f"ERROR: Failed to decrypt: {exc}", file=sys.stderr)
        sys.exit(2)

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    _write_pdf(writer, args.output)
    print(f"Decrypted -> {args.output}")


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="pdf_ops.py",
        description="PDF file operations for AI coding assistants.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # info
    p_info = sub.add_parser("info", help="Show PDF metadata and structure")
    p_info.add_argument("file", help="PDF file path")

    # text
    p_text = sub.add_parser("text", help="Extract text from PDF")
    p_text.add_argument("file", help="PDF file path")
    p_text.add_argument("--pages", help="Page spec: 1,3,5-8")
    p_text.add_argument(
        "--layout", action="store_true", help="Preserve spatial layout"
    )

    # tables
    p_tables = sub.add_parser("tables", help="Extract tables from PDF")
    p_tables.add_argument("file", help="PDF file path")
    p_tables.add_argument("--pages", help="Page spec: 1,3,5-8")
    p_tables.add_argument(
        "--format",
        choices=["markdown", "json", "csv"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    p_tables.add_argument(
        "--output-dir", help="Output directory for CSV files"
    )

    # to-images
    p_imgs = sub.add_parser("to-images", help="Convert PDF pages to PNG")
    p_imgs.add_argument("file", help="PDF file path")
    p_imgs.add_argument("--pages", help="Page spec: 1,3,5-8")
    p_imgs.add_argument("--output-dir", help="Output directory for images")
    p_imgs.add_argument(
        "--scale", type=float, default=2.0, help="Render scale (default: 2.0)"
    )

    # merge
    p_merge = sub.add_parser("merge", help="Merge multiple PDFs")
    p_merge.add_argument("files", nargs="+", help="PDF files to merge")
    p_merge.add_argument("-o", "--output", required=True, help="Output file")

    # split
    p_split = sub.add_parser("split", help="Split PDF by pages")
    p_split.add_argument("file", help="PDF file path")
    p_split.add_argument("--pages", help="Page spec: 1,3,5-8")
    p_split.add_argument(
        "--each",
        action="store_true",
        help="Split into individual page files",
    )
    p_split.add_argument("-o", "--output", help="Output file (for page range)")
    p_split.add_argument(
        "--output-dir", help="Output directory (for --each)"
    )

    # rotate
    p_rotate = sub.add_parser("rotate", help="Rotate PDF pages")
    p_rotate.add_argument("file", help="PDF file path")
    p_rotate.add_argument("angle", type=int, help="Rotation angle: 90, 180, 270")
    p_rotate.add_argument("--pages", help="Page spec: 1,3,5-8 (default: all)")
    p_rotate.add_argument("-o", "--output", help="Output file")

    # extract-images
    p_eimg = sub.add_parser(
        "extract-images", help="Extract embedded images from PDF"
    )
    p_eimg.add_argument("file", help="PDF file path")
    p_eimg.add_argument("--pages", help="Page spec: 1,3,5-8")
    p_eimg.add_argument("--output-dir", help="Output directory for images")

    # decrypt
    p_dec = sub.add_parser("decrypt", help="Decrypt a password-protected PDF")
    p_dec.add_argument("file", help="PDF file path")
    p_dec.add_argument("--password", required=True, help="PDF password")
    p_dec.add_argument("-o", "--output", help="Output file")

    return parser


COMMAND_DISPATCH: dict[str, Any] = {
    "info": cmd_info,
    "text": cmd_text,
    "tables": cmd_tables,
    "to-images": cmd_to_images,
    "merge": cmd_merge,
    "split": cmd_split,
    "rotate": cmd_rotate,
    "extract-images": cmd_extract_images,
    "decrypt": cmd_decrypt,
}


def main() -> None:
    """Entry point."""
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_DISPATCH.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
