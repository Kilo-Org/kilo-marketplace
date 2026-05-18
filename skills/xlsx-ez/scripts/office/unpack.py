#!/usr/bin/env python3
"""
unpack.py — Extract a .xlsx file to a directory for direct XML editing.

Usage:
  python unpack.py INPUT.xlsx OUTPUT_DIR

The output directory is created (or overwritten). Each part is extracted as-is;
XML files are pretty-printed and smart quotes are replaced with XML entities so
plain-text editors don't corrupt them.

Smart-quote encoding (unpack → pack round-trip):
  " → &#x201C;   " → &#x201D;
  ' → &#x2018;   ' → &#x2019;

Examples:
  python scripts/office/unpack.py workbook.xlsx unpacked/
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    print("Error: lxml not installed. Run: pip install lxml", file=sys.stderr)
    sys.exit(1)

SMART_QUOTE_ENCODE = [
    ("“", "&#x201C;"),
    ("”", "&#x201D;"),
    ("‘", "&#x2018;"),
    ("’", "&#x2019;"),
]


def _pretty(data: bytes) -> bytes:
    try:
        tree = etree.fromstring(data)
        raw = etree.tostring(tree, pretty_print=True,
                             xml_declaration=True, encoding="UTF-8", standalone=True)
    except etree.XMLSyntaxError:
        return data
    text = raw.decode("utf-8")
    for char, entity in SMART_QUOTE_ENCODE:
        text = text.replace(char, entity)
    return text.encode("utf-8")


def unpack(src: str, dst: str) -> None:
    dst_path = Path(dst)
    if dst_path.exists():
        shutil.rmtree(dst_path)

    with zipfile.ZipFile(src, "r") as z:
        for name in z.namelist():
            out = dst_path / name
            out.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(name)
            if name.endswith(".xml") or name.endswith(".rels"):
                data = _pretty(data)
            out.write_bytes(data)

    print(f"Unpacked: {src} → {dst}")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python unpack.py INPUT.xlsx OUTPUT_DIR", file=sys.stderr)
        sys.exit(1)
    unpack(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
