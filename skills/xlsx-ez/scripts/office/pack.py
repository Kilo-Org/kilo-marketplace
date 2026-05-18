#!/usr/bin/env python3
"""
pack.py — Repack an unpacked XLSX directory back into a .xlsx file.

Usage:
  python pack.py UNPACKED_DIR OUTPUT.xlsx [--original ORIGINAL.xlsx]

Options:
  --original ORIGINAL.xlsx  Copy media and parts not modified from the original.
                             Use when the unpacked dir was created from the original.

XML files are condensed (whitespace stripped between elements) and smart-quote
XML entities are re-encoded back to Unicode characters before packing.

The output uses ZIP_DEFLATED compression and the correct MIME type:
  application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

Examples:
  python scripts/office/pack.py unpacked/ output.xlsx
  python scripts/office/pack.py unpacked/ output.xlsx --original template.xlsx
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    print("Error: lxml not installed. Run: pip install lxml", file=sys.stderr)
    sys.exit(1)

MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

SMART_QUOTE_DECODE = [
    ("&#x201C;", "“"),
    ("&#x201D;", "”"),
    ("&#x2018;", "‘"),
    ("&#x2019;", "’"),
    ("&#x201c;", "“"),
    ("&#x201d;", "”"),
    ("&#x2018;", "‘"),
    ("&#x2019;", "’"),
]


def _condense(data: bytes) -> bytes:
    """Parse XML, re-encode smart-quote entities, return condensed bytes."""
    text = data.decode("utf-8", errors="replace")
    for entity, char in SMART_QUOTE_DECODE:
        text = text.replace(entity, char)
    try:
        tree = etree.fromstring(text.encode("utf-8"))
        return etree.tostring(tree, xml_declaration=True,
                              encoding="UTF-8", standalone=True)
    except etree.XMLSyntaxError:
        return text.encode("utf-8")


def pack(src_dir: str, dst: str, original: str | None = None) -> None:
    src = Path(src_dir)
    if not src.is_dir():
        print(f"Error: {src_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    original_parts: dict[str, bytes] = {}
    if original:
        with zipfile.ZipFile(original, "r") as z:
            for n in z.namelist():
                original_parts[n] = z.read(n)

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        # Write [Content_Types].xml first — required by the OOXML spec so that
        # consumers can identify part types before reading any other entry.
        packed: set[str] = set()
        content_types_name = "[Content_Types].xml"
        content_types_file = src / content_types_name
        if content_types_file.exists():
            data = content_types_file.read_bytes()
            data = _condense(data)
            z.writestr(content_types_name, data)
            packed.add(content_types_name)

        # Write all remaining parts from the unpacked directory
        for file in sorted(src.rglob("*")):
            if not file.is_file():
                continue
            name = str(file.relative_to(src)).replace("\\", "/")
            if name in packed:
                continue
            data = file.read_bytes()
            if name.endswith(".xml") or name.endswith(".rels"):
                data = _condense(data)
            z.writestr(name, data)
            packed.add(name)

        # Fill in any missing parts (e.g. media, fonts) from the original
        for name, data in original_parts.items():
            if name not in packed:
                z.writestr(name, data)

    print(f"Packed: {src_dir} → {dst}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("unpacked_dir", help="Unpacked XLSX directory")
    ap.add_argument("output",       help="Destination .xlsx")
    ap.add_argument("--original",   default=None,
                    help="Original .xlsx (fill in unmodified parts)")
    args = ap.parse_args()
    pack(args.unpacked_dir, args.output, args.original)


if __name__ == "__main__":
    main()
