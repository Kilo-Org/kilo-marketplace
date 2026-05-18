#!/usr/bin/env python3
"""
edit_docx.py — Edit an existing .docx file via direct OOXML XML manipulation.

Usage:
  python edit_docx.py INPUT OUTPUT [options]

Options:
  --replace OLD NEW              Plain text search-replace (no tracking)
  --replace-tracked OLD NEW      Tracked substitution: mark OLD as deleted,
                                 insert NEW immediately after (same paragraph)
  --insert-after MATCH TEXT      Insert a new paragraph after the first paragraph
                                 containing MATCH, wrapped in <w:ins>
  --delete MATCH                 Wrap the first run containing MATCH in <w:del>
  --comment MATCH TEXT           Add an inline comment on first occurrence of MATCH
  --author AUTHOR                Reviewer name for tracked changes and comments
  --date DATE                    ISO 8601 timestamp (default: current UTC time)

Examples:
  python edit_docx.py in.docx out.docx --replace "draft" "final"
  python edit_docx.py in.docx out.docx \\
    --replace-tracked "original wording" "revised wording" --author "Claude"
  python edit_docx.py in.docx out.docx \\
    --insert-after "Introduction" "New paragraph text." --author "Claude"
  python edit_docx.py in.docx out.docx --delete "remove this" --author "Claude"
  python edit_docx.py in.docx out.docx \\
    --comment "deadline" "Confirm date with client." --author "Claude"
"""
from __future__ import annotations

import argparse
import copy
import shutil
import sys
import zipfile
from datetime import datetime, timezone

try:
    from lxml import etree
except ImportError:
    print('Error: lxml not installed. Run: pip install lxml', file=sys.stderr)
    sys.exit(1)

# ── Namespace constants ───────────────────────────────────────────────────────

W  = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
COMMENTS_CONTENT_TYPE = (
    'application/vnd.openxmlformats-officedocument'
    '.wordprocessingml.comments+xml'
)
COMMENTS_REL_TYPE = (
    'http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships/comments'
)


def qn(local: str) -> str:
    return f'{{{W}}}{local}'


W_P          = qn('p')
W_R          = qn('r')
W_T          = qn('t')
W_RPR        = qn('rPr')
W_PPR        = qn('pPr')
W_INS        = qn('ins')
W_DEL        = qn('del')
W_DELTEXT    = qn('delText')
W_COMMENT_RS  = qn('commentRangeStart')
W_COMMENT_RE  = qn('commentRangeEnd')
W_COMMENT_REF = qn('commentReference')
W_RSTYLE      = qn('rStyle')
W_COMMENT     = qn('comment')
W_ANNOT_REF   = qn('annotationRef')


# ── DocxEditor ────────────────────────────────────────────────────────────────

class DocxEditor:
    """Open a .docx, apply edits, and save to a new path."""

    def __init__(self, src_path: str) -> None:
        with zipfile.ZipFile(src_path, 'r') as z:
            self._names = z.namelist()
            self._parts: dict[str, bytes] = {n: z.read(n) for n in self._names}

        self._doc     = etree.fromstring(self._parts['word/document.xml'])
        self._cmt_xml = self._load_comments()
        self._next_id = self._scan_max_id() + 1

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _load_comments(self) -> etree._Element:
        if 'word/comments.xml' in self._parts:
            return etree.fromstring(self._parts['word/comments.xml'])
        root = etree.Element(qn('comments'), nsmap={'w': W})
        return root

    def _scan_max_id(self) -> int:
        wid = f'{{{W}}}id'
        ids = [
            int(el.get(wid))
            for el in self._doc.iter()
            if el.get(wid, '').isdigit()
        ]
        return max(ids, default=0)

    def _alloc_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    @staticmethod
    def _now_iso(date_str: str | None) -> str:
        if date_str:
            return date_str
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def _paragraphs(self) -> list[etree._Element]:
        return self._doc.findall(f'.//{W_P}')

    @staticmethod
    def _para_text(para: etree._Element) -> str:
        return ''.join(
            t.text or ''
            for t in para.iter(W_T)
        )

    def _find_run(self, match: str) -> tuple[
        etree._Element | None,
        etree._Element | None,
        int,
    ]:
        """Return (paragraph, run, run-index) for first run containing match."""
        for para in self._paragraphs():
            children = list(para)
            for i, child in enumerate(children):
                if child.tag != W_R:
                    continue
                if match in ''.join(t.text or '' for t in child.findall(W_T)):
                    return para, child, i
        return None, None, -1

    # ── Operations ─────────────────────────────────────────────────────────────

    def replace(self, old: str, new: str) -> None:
        """Plain text search-replace across all runs."""
        for t in self._doc.iter(W_T):
            if t.text and old in t.text:
                t.text = t.text.replace(old, new)
                t.set(XML_SPACE, 'preserve')

    def insert_after(self, match: str, text: str, author: str,
                     date: str | None = None) -> None:
        """Insert a new paragraph after the paragraph containing match.
        The new paragraph's run is wrapped in <w:ins>."""
        date = self._now_iso(date)
        for para in self._paragraphs():
            if match in self._para_text(para):
                t_el = etree.Element(W_T)
                t_el.text = text
                t_el.set(XML_SPACE, 'preserve')

                new_run = etree.Element(W_R)
                new_run.append(t_el)

                ins = etree.Element(W_INS)
                ins.set(qn('id'),     str(self._alloc_id()))
                ins.set(qn('author'), author)
                ins.set(qn('date'),   date)
                ins.append(new_run)

                new_para = etree.Element(W_P)
                new_para.append(ins)

                parent = para.getparent()
                parent.insert(list(parent).index(para) + 1, new_para)
                return
        raise ValueError(f'Paragraph containing {match!r} not found')

    def delete(self, match: str, author: str, date: str | None = None) -> None:
        """Wrap the first run containing match in <w:del>."""
        date = self._now_iso(date)
        para, run, idx = self._find_run(match)
        if run is None:
            raise ValueError(f'Run containing {match!r} not found')

        del_run = copy.deepcopy(run)
        for t in del_run.findall(W_T):
            t.tag = W_DELTEXT

        del_el = etree.Element(W_DEL)
        del_el.set(qn('id'),     str(self._alloc_id()))
        del_el.set(qn('author'), author)
        del_el.set(qn('date'),   date)
        del_el.append(del_run)

        para.remove(run)
        para.insert(idx, del_el)

    def replace_tracked(self, old: str, new: str, author: str,
                        date: str | None = None) -> None:
        """Tracked substitution: wrap old text in <w:del> and insert new as <w:ins>."""
        date = self._now_iso(date)
        para, run, idx = self._find_run(old)
        if run is None:
            raise ValueError(f'Run containing {old!r} not found')

        del_run = copy.deepcopy(run)
        for t in del_run.findall(W_T):
            t.tag = W_DELTEXT

        del_el = etree.Element(W_DEL)
        del_el.set(qn('id'),     str(self._alloc_id()))
        del_el.set(qn('author'), author)
        del_el.set(qn('date'),   date)
        del_el.append(del_run)

        t_el = etree.Element(W_T)
        t_el.text = new
        t_el.set(XML_SPACE, 'preserve')
        new_run = etree.Element(W_R)
        new_run.append(t_el)

        ins_el = etree.Element(W_INS)
        ins_el.set(qn('id'),     str(self._alloc_id()))
        ins_el.set(qn('author'), author)
        ins_el.set(qn('date'),   date)
        ins_el.append(new_run)

        para.remove(run)
        para.insert(idx, ins_el)
        para.insert(idx, del_el)

    def add_comment(self, match: str, comment_text: str, author: str,
                    date: str | None = None) -> None:
        """Attach an inline comment to the first occurrence of match."""
        date = self._now_iso(date)
        cid  = self._alloc_id()

        # Register in word/comments.xml
        c_el = etree.SubElement(self._cmt_xml, W_COMMENT)
        c_el.set(qn('id'),       str(cid))
        c_el.set(qn('author'),   author)
        c_el.set(qn('date'),     date)
        c_el.set(qn('initials'), author[:1].upper())
        c_para  = etree.SubElement(c_el, W_P)
        c_run   = etree.SubElement(c_para, W_R)
        c_t     = etree.SubElement(c_run, W_T)
        c_t.text = comment_text

        # Anchor in document.xml
        para, run, idx = self._find_run(match)
        if run is None:
            raise ValueError(f'Run containing {match!r} not found')

        crs = etree.Element(W_COMMENT_RS)
        crs.set(qn('id'), str(cid))

        cre = etree.Element(W_COMMENT_RE)
        cre.set(qn('id'), str(cid))

        ref_run = etree.Element(W_R)
        ref_rpr = etree.SubElement(ref_run, W_RPR)
        rs_el   = etree.SubElement(ref_rpr, W_RSTYLE)
        rs_el.set(qn('val'), 'CommentReference')
        ref_ref = etree.SubElement(ref_run, W_COMMENT_REF)
        ref_ref.set(qn('id'), str(cid))

        para.insert(idx,     crs)
        para.insert(idx + 2, cre)
        para.insert(idx + 3, ref_run)

    # ── Serialisation ──────────────────────────────────────────────────────────

    def _to_bytes(self, root: etree._Element) -> bytes:
        return etree.tostring(
            root,
            xml_declaration=True,
            encoding='UTF-8',
            standalone=True,
        )

    def _ensure_comments_registered(self) -> None:
        """Register word/comments.xml in [Content_Types].xml and rels."""
        CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
        RL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'

        # [Content_Types].xml
        ct = etree.fromstring(self._parts['[Content_Types].xml'])
        have = {el.get('PartName') for el in ct.findall(f'{{{CT_NS}}}Override')}
        if '/word/comments.xml' not in have:
            ov = etree.SubElement(ct, f'{{{CT_NS}}}Override')
            ov.set('PartName',    '/word/comments.xml')
            ov.set('ContentType', COMMENTS_CONTENT_TYPE)
            self._parts['[Content_Types].xml'] = self._to_bytes(ct)

        # word/_rels/document.xml.rels
        rels_key = 'word/_rels/document.xml.rels'
        if rels_key not in self._parts:
            return
        rels = etree.fromstring(self._parts[rels_key])
        have_types = {
            el.get('Type')
            for el in rels.findall(f'{{{RL_NS}}}Relationship')
        }
        if COMMENTS_REL_TYPE not in have_types:
            rel = etree.SubElement(rels, f'{{{RL_NS}}}Relationship')
            rel.set('Id',     f'rId{self._alloc_id()}')
            rel.set('Type',   COMMENTS_REL_TYPE)
            rel.set('Target', 'comments.xml')
            self._parts[rels_key] = self._to_bytes(rels)

    def save(self, dst_path: str) -> None:
        """Write edited document to dst_path."""
        has_comments = len(self._cmt_xml) > 0
        if has_comments:
            self._ensure_comments_registered()

        self._parts['word/document.xml'] = self._to_bytes(self._doc)
        if has_comments:
            self._parts['word/comments.xml'] = self._to_bytes(self._cmt_xml)

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
    ap.add_argument('input',  help='Source .docx')
    ap.add_argument('output', help='Destination .docx')
    ap.add_argument('--replace',
                    nargs=2, metavar=('OLD', 'NEW'),
                    action='append', default=[])
    ap.add_argument('--replace-tracked',
                    nargs=2, metavar=('OLD', 'NEW'),
                    action='append', default=[], dest='replace_tracked')
    ap.add_argument('--insert-after',
                    nargs=2, metavar=('MATCH', 'TEXT'),
                    action='append', default=[], dest='insert_after')
    ap.add_argument('--delete',
                    nargs=1, metavar='MATCH',
                    action='append', default=[])
    ap.add_argument('--comment',
                    nargs=2, metavar=('MATCH', 'TEXT'),
                    action='append', default=[])
    ap.add_argument('--author', default='Claude',
                    help='Author name for tracked changes and comments')
    ap.add_argument('--date',   default=None,
                    help='ISO 8601 timestamp (default: now)')
    args = ap.parse_args()

    editor = DocxEditor(args.input)

    for old, new in args.replace:
        editor.replace(old, new)

    for old, new in args.replace_tracked:
        editor.replace_tracked(old, new, args.author, args.date)

    for match, text in args.insert_after:
        editor.insert_after(match, text, args.author, args.date)

    for (match,) in args.delete:
        editor.delete(match, args.author, args.date)

    for match, text in args.comment:
        editor.add_comment(match, text, args.author, args.date)

    editor.save(args.output)


if __name__ == '__main__':
    main()
