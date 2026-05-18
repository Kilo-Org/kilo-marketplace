#!/usr/bin/env python3
"""
pack.py — Repack an unpacked PPTX directory back into a .pptx file.

Usage:
  python pack.py UNPACKED_DIR OUTPUT.pptx [--original ORIGINAL.pptx]

Options:
  --original ORIGINAL.pptx  Copy media and parts not modified from the original.
                             Use when the unpacked dir was created from the original.

XML files are condensed (whitespace stripped between elements) and smart-quote
XML entities are re-encoded back to Unicode characters before packing.

Examples:
  python scripts/office/pack.py unpacked/ output.pptx
  python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
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
        # Write all parts from the unpacked directory
        packed: set[str] = set()
        for file in sorted(src.rglob("*")):
            if not file.is_file():
                continue
            name = str(file.relative_to(src)).replace("\\", "/")
            data = file.read_bytes()
            if name.endswith(".xml") or name.endswith(".rels"):
                data = _condense(data)
            z.writestr(name, data)
            packed.add(name)

        # Fill in any missing media from the original
        for name, data in original_parts.items():
            if name not in packed:
                z.writestr(name, data)

    print(f"Packed: {src_dir} → {dst}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("unpacked_dir", help="Unpacked PPTX directory")
    ap.add_argument("output",       help="Destination .pptx")
    ap.add_argument("--original",   default=None,
                    help="Original .pptx (fill in unmodified parts)")
    args = ap.parse_args()
    pack(args.unpacked_dir, args.output, args.original)


if __name__ == "__main__":
    main()
