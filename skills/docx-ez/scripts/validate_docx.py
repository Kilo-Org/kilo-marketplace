#!/usr/bin/env python3
"""
validate_docx.py — Validate a .docx file's ZIP integrity and XML well-formedness.

Usage:
  python validate_docx.py <document.docx> [<document2.docx> ...]

Exit codes:
  0  All checks passed for all files
  1  One or more checks failed
"""
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
    'word/document.xml',
    'word/_rels/document.xml.rels',
    'word/styles.xml',
]


def validate(path: str) -> list[str]:
    errors: list[str] = []

    # 1. Valid ZIP?
    if not zipfile.is_zipfile(path):
        return [f'{path}: not a valid ZIP/docx archive']

    with zipfile.ZipFile(path, 'r') as z:
        names = set(z.namelist())

        # 2. Required parts
        for part in REQUIRED_PARTS:
            if part not in names:
                errors.append(f'Missing required part: {part}')

        # 3. All XML parts parse cleanly
        xml_names = [n for n in names if n.endswith('.xml') or n.endswith('.rels')]
        for part in xml_names:
            try:
                data = z.read(part)
                etree.fromstring(data)
            except etree.XMLSyntaxError as e:
                errors.append(f'XML parse error in {part}: {e}')

        # 4. document.xml body check
        if 'word/document.xml' in names:
            try:
                root = etree.fromstring(z.read('word/document.xml'))
                W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                body = root.find(f'{{{W}}}body')
                if body is None:
                    errors.append('word/document.xml: missing <w:body> element')
            except Exception:
                pass  # already caught above

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print(f'Usage: python {sys.argv[0]} <document.docx> [...]')
        sys.exit(1)

    any_failure = False
    for path in sys.argv[1:]:
        errors = validate(path)
        if errors:
            any_failure = True
            for e in errors:
                print(f'FAIL [{path}]: {e}', file=sys.stderr)
        else:
            print(f'OK: {path}')

    sys.exit(1 if any_failure else 0)


if __name__ == '__main__':
    main()
