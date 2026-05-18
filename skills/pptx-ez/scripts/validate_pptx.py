#!/usr/bin/env python3
"""
validate_pptx.py — Validate a .pptx file's OPC/ZIP structure.

Usage:
  python validate_pptx.py FILE.pptx

Exit 0 on success, 1 on failure.
"""
from __future__ import annotations

import sys
import zipfile

try:
    from lxml import etree
except ImportError:
    print('Error: lxml not installed. Run: pip install lxml', file=sys.stderr)
    sys.exit(1)

REQUIRED_PARTS = [
    '[Content_Types].xml',
    '_rels/.rels',
    'ppt/presentation.xml',
    'ppt/_rels/presentation.xml.rels',
]


def validate(path: str) -> list[str]:
    errors: list[str] = []

    try:
        with zipfile.ZipFile(path, 'r') as z:
            names = set(z.namelist())

            for part in REQUIRED_PARTS:
                if part not in names:
                    errors.append(f'Missing required part: {part}')

            for name in names:
                if not name.endswith('.xml') and not name.endswith('.rels'):
                    continue
                try:
                    data = z.read(name)
                    etree.fromstring(data)
                except etree.XMLSyntaxError as e:
                    errors.append(f'XML parse error in {name}: {e}')

            if 'ppt/_rels/presentation.xml.rels' in names:
                from xml.etree import ElementTree as ET
                rels_data = z.read('ppt/_rels/presentation.xml.rels')
                rels = ET.fromstring(rels_data)
                ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
                slide_rel_type = (
                    'http://schemas.openxmlformats.org/officeDocument'
                    '/2006/relationships/slide'
                )
                for rel in rels.findall(f'{{{ns}}}Relationship'):
                    if rel.get('Type') == slide_rel_type:
                        target = rel.get('Target', '').lstrip('/')
                        if not target.startswith('ppt/'):
                            target = f'ppt/{target}'
                        if target not in names:
                            errors.append(f'Slide part referenced but missing: {target}')

    except zipfile.BadZipFile:
        errors.append('Not a valid ZIP/PPTX archive')

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print('Usage: python validate_pptx.py FILE.pptx', file=sys.stderr)
        sys.exit(1)

    path   = sys.argv[1]
    errors = validate(path)

    if errors:
        print(f'FAIL  {path}')
        for e in errors:
            print(f'  • {e}')
        sys.exit(1)

    print(f'OK    {path}')


if __name__ == '__main__':
    main()
