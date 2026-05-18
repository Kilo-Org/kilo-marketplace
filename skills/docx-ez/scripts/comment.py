#!/usr/bin/env python3
"""
comment.py — Manage comments in a .docx file.

Usage:
  python comment.py INPUT list
  python comment.py INPUT OUTPUT add TEXT --author AUTHOR
                    --start PARA_IDX [--end PARA_IDX]
  python comment.py INPUT OUTPUT delete COMMENT_ID

Commands:
  list                  Print all comments to stdout; no OUTPUT argument needed.
  add TEXT              Add a new comment anchored to paragraph(s).
  delete COMMENT_ID     Remove a comment by its numeric w:id.

Options for 'add':
  --author AUTHOR       Comment author name (default: Claude)
  --date DATE           ISO 8601 timestamp (default: current UTC time)
  --start PARA_IDX      0-based index of the first paragraph to anchor (default: 0)
  --end PARA_IDX        0-based index of the last paragraph to anchor
                        (default: same as --start)

Examples:
  python comment.py report.docx list
  python comment.py report.docx out.docx add "Please clarify." --author "Alice" --start 2
  python comment.py report.docx out.docx delete 3
"""
from __future__ import annotations

import argparse
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
CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
RL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'

COMMENTS_CONTENT_TYPE = (
    'application/vnd.openxmlformats-officedocument'
    '.wordprocessingml.comments+xml'
)
COMMENTS_REL_TYPE = (
    'http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships/comments'
)

XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


def qn(local: str) -> str:
    return f'{{{W}}}{local}'


W_COMMENT     = qn('comment')
W_P           = qn('p')
W_R           = qn('r')
W_T           = qn('t')
W_RPR         = qn('rPr')
W_RSTYLE      = qn('rStyle')
W_ANNOT_REF   = qn('annotationRef')
W_COMMENT_RS  = qn('commentRangeStart')
W_COMMENT_RE  = qn('commentRangeEnd')
W_COMMENT_REF = qn('commentReference')

# ── Helpers ───────────────────────────────────────────────────────────────────


def _now_iso(date_str: str | None) -> str:
    if date_str:
        return date_str
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _to_bytes(root: etree._Element) -> bytes:
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding='UTF-8',
        standalone=True,
    )


def _scan_max_id(doc: etree._Element, cmt_root: etree._Element) -> int:
    wid = f'{{{W}}}id'
    ids: list[int] = []
    for tree in (doc, cmt_root):
        for el in tree.iter():
            val = el.get(wid, '')
            if val.lstrip('-').isdigit():
                ids.append(int(val))
    return max(ids, default=0)


def _comment_text(comment_el: etree._Element) -> str:
    """Extract plain text from a <w:comment> element."""
    return ''.join(t.text or '' for t in comment_el.iter(W_T))


# ── DocxCommentManager ────────────────────────────────────────────────────────


class DocxCommentManager:
    """Open a .docx, manage comments, and optionally save to a new path."""

    def __init__(self, src_path: str) -> None:
        with zipfile.ZipFile(src_path, 'r') as z:
            self._names: list[str] = z.namelist()
            self._parts: dict[str, bytes] = {n: z.read(n) for n in self._names}

        self._doc      = etree.fromstring(self._parts['word/document.xml'])
        self._cmt_root = self._load_comments()
        self._next_id  = _scan_max_id(self._doc, self._cmt_root) + 1

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _load_comments(self) -> etree._Element:
        if 'word/comments.xml' in self._parts:
            return etree.fromstring(self._parts['word/comments.xml'])
        # Build a minimal comments root; will be registered on save if needed
        root = etree.Element(qn('comments'), nsmap={'w': W})
        return root

    def _alloc_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    def _paragraphs(self) -> list[etree._Element]:
        return self._doc.findall(f'.//{W_P}')

    # ── Operations ─────────────────────────────────────────────────────────────

    def list_comments(self) -> None:
        """Print all comments to stdout."""
        comments = self._cmt_root.findall(W_COMMENT)
        if not comments:
            print('(no comments)')
            return
        for c in comments:
            cid    = c.get(qn('id'),     '?')
            author = c.get(qn('author'), '')
            date   = c.get(qn('date'),   '')
            text   = _comment_text(c)
            print(f'id={cid} author={author} date={date}: {text}')

    def add_comment(
        self,
        text: str,
        author: str,
        start_idx: int,
        end_idx: int,
        date: str | None = None,
    ) -> int:
        """
        Add a comment anchored to paragraphs [start_idx, end_idx].

        Returns the allocated comment id.
        """
        date = _now_iso(date)
        cid  = self._alloc_id()

        # ── 1. Add <w:comment> to comments.xml ──────────────────────────────
        c_el = etree.SubElement(self._cmt_root, W_COMMENT)
        c_el.set(qn('id'),       str(cid))
        c_el.set(qn('author'),   author)
        c_el.set(qn('date'),     date)
        c_el.set(qn('initials'), author[:1].upper() if author else 'C')

        # Inner paragraph with annotationRef + text run
        c_para = etree.SubElement(c_el, W_P)
        ref_run = etree.SubElement(c_para, W_R)
        etree.SubElement(ref_run, W_ANNOT_REF)
        txt_run = etree.SubElement(c_para, W_R)
        t_el = etree.SubElement(txt_run, W_T)
        t_el.text = text
        t_el.set(XML_SPACE, 'preserve')

        # ── 2. Anchor in document.xml ────────────────────────────────────────
        paras = self._paragraphs()

        def _clamp(idx: int) -> int:
            return max(0, min(idx, len(paras) - 1))

        start_idx = _clamp(start_idx)
        end_idx   = _clamp(end_idx)

        start_para = paras[start_idx]
        end_para   = paras[end_idx]

        # <w:commentRangeStart> — insert before the first child of start_para
        crs = etree.Element(W_COMMENT_RS)
        crs.set(qn('id'), str(cid))
        start_para.insert(0, crs)

        # <w:commentRangeEnd> — append as last child of end_para
        cre = etree.Element(W_COMMENT_RE)
        cre.set(qn('id'), str(cid))
        end_para.append(cre)

        # <w:r><w:commentReference/></w:r> — append after commentRangeEnd
        ref_r   = etree.Element(W_R)
        ref_rpr = etree.SubElement(ref_r, W_RPR)
        rs_el   = etree.SubElement(ref_rpr, W_RSTYLE)
        rs_el.set(qn('val'), 'CommentReference')
        cref = etree.SubElement(ref_r, W_COMMENT_REF)
        cref.set(qn('id'), str(cid))
        end_para.append(ref_r)

        return cid

    def delete_comment(self, comment_id: int) -> bool:
        """
        Remove comment *comment_id* from comments.xml and all its anchors
        from document.xml.

        Returns True if the comment was found and removed, False otherwise.
        """
        sid = str(comment_id)
        wid = qn('id')

        # Remove from comments.xml
        found = False
        for c in list(self._cmt_root):
            if c.get(wid) == sid:
                self._cmt_root.remove(c)
                found = True
                break

        if not found:
            return False

        # Remove anchors from document.xml
        for tag in (W_COMMENT_RS, W_COMMENT_RE):
            for el in list(self._doc.iter(tag)):
                if el.get(wid) == sid:
                    parent = el.getparent()
                    if parent is not None:
                        parent.remove(el)

        # Remove runs that contain only a commentReference with this id
        for ref in list(self._doc.iter(W_COMMENT_REF)):
            if ref.get(wid) == sid:
                run = ref.getparent()
                if run is not None and run.tag == W_R:
                    parent = run.getparent()
                    if parent is not None:
                        parent.remove(run)

        return True

    # ── Serialisation ──────────────────────────────────────────────────────────

    def _ensure_comments_registered(self) -> None:
        """Register word/comments.xml in [Content_Types].xml and rels if needed."""
        # [Content_Types].xml
        ct = etree.fromstring(self._parts['[Content_Types].xml'])
        have = {el.get('PartName') for el in ct.findall(f'{{{CT_NS}}}Override')}
        if '/word/comments.xml' not in have:
            ov = etree.SubElement(ct, f'{{{CT_NS}}}Override')
            ov.set('PartName',    '/word/comments.xml')
            ov.set('ContentType', COMMENTS_CONTENT_TYPE)
            self._parts['[Content_Types].xml'] = _to_bytes(ct)

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
            self._parts[rels_key] = _to_bytes(rels)

    def save(self, dst_path: str) -> None:
        """Write the (modified) document to *dst_path*."""
        has_comments = len(self._cmt_root) > 0
        had_comments = 'word/comments.xml' in self._parts

        if has_comments:
            self._ensure_comments_registered()

        self._parts['word/document.xml'] = _to_bytes(self._doc)

        if has_comments:
            # Write updated comments.xml (may have had comments before, or be new)
            self._parts['word/comments.xml'] = _to_bytes(self._cmt_root)
        elif had_comments:
            # All comments were deleted — write an empty comments root so the
            # part is valid; Word will ignore an empty <w:comments/> element.
            self._parts['word/comments.xml'] = _to_bytes(self._cmt_root)

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

    # Positional arguments parsed manually so that OUTPUT is optional for 'list'
    ap.add_argument('input', help='Source .docx file')

    sub = ap.add_subparsers(dest='command')

    # ── list ──────────────────────────────────────────────────────────────────
    sub.add_parser('list', help='Print all comments to stdout')

    # ── add ───────────────────────────────────────────────────────────────────
    add_p = sub.add_parser('add', help='Add a comment anchored to paragraph(s)')
    add_p.add_argument('output', help='Destination .docx file')
    add_p.add_argument('text',   help='Comment text')
    add_p.add_argument('--author', default='Claude',
                       help='Comment author (default: Claude)')
    add_p.add_argument('--date', default=None,
                       help='ISO 8601 timestamp (default: now)')
    add_p.add_argument('--start', type=int, default=0, metavar='PARA_IDX',
                       help='0-based index of first anchored paragraph (default: 0)')
    add_p.add_argument('--end', type=int, default=None, metavar='PARA_IDX',
                       help='0-based index of last anchored paragraph (default: --start)')

    # ── delete ────────────────────────────────────────────────────────────────
    del_p = sub.add_parser('delete', help='Remove a comment by its w:id')
    del_p.add_argument('output',     help='Destination .docx file')
    del_p.add_argument('comment_id', type=int, metavar='COMMENT_ID',
                       help='Numeric comment id (w:id attribute)')

    args = ap.parse_args()

    if args.command is None:
        ap.print_help()
        sys.exit(1)

    mgr = DocxCommentManager(args.input)

    if args.command == 'list':
        mgr.list_comments()

    elif args.command == 'add':
        end_idx = args.end if args.end is not None else args.start
        cid = mgr.add_comment(
            text=args.text,
            author=args.author,
            start_idx=args.start,
            end_idx=end_idx,
            date=args.date,
        )
        print(f'Added comment id={cid}.')
        mgr.save(args.output)

    elif args.command == 'delete':
        removed = mgr.delete_comment(args.comment_id)
        if not removed:
            print(f'Error: comment id={args.comment_id} not found.', file=sys.stderr)
            sys.exit(1)
        print(f'Deleted comment id={args.comment_id}.')
        mgr.save(args.output)


if __name__ == '__main__':
    main()
