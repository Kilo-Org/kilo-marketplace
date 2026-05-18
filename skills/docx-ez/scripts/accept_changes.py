#!/usr/bin/env python3
"""
accept_changes.py — Accept or reject all tracked changes in a .docx file.

Usage:
  python accept_changes.py INPUT.docx OUTPUT.docx [--reject]

Options:
  --reject    Reject changes instead of accepting them.
              Accepting (default): keep <w:ins> content, discard <w:del> content.
              Rejecting:           discard <w:ins> content, keep <w:del> content.

Also removes format-change markup (<w:rPrChange>, <w:pPrChange>,
<w:sectPrChange>) keeping the current (post-change) formatting in place.

Examples:
  python accept_changes.py draft.docx final.docx
  python accept_changes.py draft.docx reverted.docx --reject
"""
from __future__ import annotations

import argparse
import sys
import zipfile

try:
    from lxml import etree
except ImportError:
    print('Error: lxml not installed. Run: pip install lxml', file=sys.stderr)
    sys.exit(1)

# ── Namespace constants ───────────────────────────────────────────────────────

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def qn(local: str) -> str:
    return f'{{{W}}}{local}'


W_INS         = qn('ins')
W_DEL         = qn('del')
W_T           = qn('t')
W_DELTEXT     = qn('delText')
W_RPR_CHANGE  = qn('rPrChange')
W_PPR_CHANGE  = qn('pPrChange')
W_SECT_CHANGE = qn('sectPrChange')

XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'

# ── Core logic ────────────────────────────────────────────────────────────────


def _unwrap(parent: etree._Element, elem: etree._Element) -> None:
    """Replace *elem* in *parent* with elem's children (in order)."""
    idx = list(parent).index(elem)
    for i, child in enumerate(list(elem)):
        elem.remove(child)
        parent.insert(idx + i, child)
    parent.remove(elem)


def _deltext_to_t(run: etree._Element) -> None:
    """Convert all <w:delText> elements inside *run* to <w:t>."""
    for dt in run.iter(W_DELTEXT):
        dt.tag = W_T
        if dt.get(XML_SPACE) is None and (dt.text or '').startswith(' ') or (dt.text or '').endswith(' '):
            dt.set(XML_SPACE, 'preserve')


def process_document(doc: etree._Element, reject: bool) -> tuple[int, int]:
    """
    Walk *doc*, resolving all tracked changes.

    Returns (n_ins, n_del) counts of elements processed.
    """
    n_ins = 0
    n_del = 0

    # We iterate until no more tracked-change elements remain, because
    # nested revisions (rare but valid) may be exposed after one pass.
    while True:
        changed = False

        for elem in list(doc.iter(W_INS)):
            parent = elem.getparent()
            if parent is None:
                continue
            changed = True
            n_ins += 1
            if reject:
                # Discard the entire insertion
                parent.remove(elem)
            else:
                # Keep the insertion's child runs, drop the wrapper
                _unwrap(parent, elem)

        for elem in list(doc.iter(W_DEL)):
            parent = elem.getparent()
            if parent is None:
                continue
            changed = True
            n_del += 1
            if reject:
                # Keep the deleted content — convert <w:delText> back to <w:t>
                for run in list(elem):
                    _deltext_to_t(run)
                _unwrap(parent, elem)
            else:
                # Discard the deleted content entirely
                parent.remove(elem)

        if not changed:
            break

    # Remove format-change markers (keep current / post-change formatting)
    for tag in (W_RPR_CHANGE, W_PPR_CHANGE, W_SECT_CHANGE):
        for elem in list(doc.iter(tag)):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

    return n_ins, n_del


# ── DocxChangesProcessor ──────────────────────────────────────────────────────


class DocxChangesProcessor:
    """Load a .docx, resolve tracked changes, and save to a new path."""

    def __init__(self, src_path: str) -> None:
        with zipfile.ZipFile(src_path, 'r') as z:
            self._names: list[str] = z.namelist()
            self._parts: dict[str, bytes] = {n: z.read(n) for n in self._names}

        self._doc = etree.fromstring(self._parts['word/document.xml'])

    def process(self, reject: bool) -> tuple[int, int]:
        return process_document(self._doc, reject)

    def save(self, dst_path: str) -> None:
        self._parts['word/document.xml'] = etree.tostring(
            self._doc,
            xml_declaration=True,
            encoding='UTF-8',
            standalone=True,
        )
        with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in self._parts.items():
                z.writestr(name, data)
        print(f'Saved: {dst_path}')


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('input',  help='Source .docx file')
    ap.add_argument('output', help='Destination .docx file')
    ap.add_argument(
        '--reject',
        action='store_true',
        default=False,
        help='Reject changes instead of accepting them',
    )
    args = ap.parse_args()

    processor = DocxChangesProcessor(args.input)
    n_ins, n_del = processor.process(reject=args.reject)

    if n_ins == 0 and n_del == 0:
        print('No tracked changes found.')
    else:
        verb = 'Rejected' if args.reject else 'Accepted'
        print(f'{verb} {n_ins} insertion(s), {n_del} deletion(s).')

    processor.save(args.output)


if __name__ == '__main__':
    main()
