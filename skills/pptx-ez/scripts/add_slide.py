#!/usr/bin/env python3
"""
add_slide.py — Add a new slide to an unpacked PPTX directory.

Usage:
  python add_slide.py UNPACKED_DIR SOURCE

SOURCE can be:
  slide2.xml         — duplicate an existing slide
  slideLayout2.xml   — create a blank slide from a layout

Prints the <p:sldId> element to add to presentation.xml <p:sldIdLst>
at the desired position.

To see available layouts:
  ls UNPACKED_DIR/ppt/slideLayouts/

Examples:
  python scripts/add_slide.py unpacked/ slide1.xml
  python scripts/add_slide.py unpacked/ slideLayout6.xml
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path


def _next_slide_num(slides_dir: Path) -> int:
    nums = [int(m.group(1)) for f in slides_dir.glob("slide*.xml")
            if (m := re.match(r"slide(\d+)\.xml", f.name))]
    return max(nums) + 1 if nums else 1


def _add_content_type(unpacked: Path, slide_name: str) -> None:
    ct_path = unpacked / "[Content_Types].xml"
    ct      = ct_path.read_text(encoding="utf-8")
    entry   = (f'<Override PartName="/ppt/slides/{slide_name}" '
               f'ContentType="application/vnd.openxmlformats-officedocument'
               f'.presentationml.slide+xml"/>')
    if f"/ppt/slides/{slide_name}" not in ct:
        ct = ct.replace("</Types>", f"  {entry}\n</Types>")
        ct_path.write_text(ct, encoding="utf-8")


def _add_prs_rel(unpacked: Path, slide_name: str) -> str:
    rels_path = unpacked / "ppt" / "_rels" / "presentation.xml.rels"
    rels      = rels_path.read_text(encoding="utf-8")
    rids      = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels)]
    rid       = f"rId{max(rids) + 1 if rids else 1}"
    entry     = (f'<Relationship Id="{rid}" '
                 f'Type="http://schemas.openxmlformats.org/officeDocument'
                 f'/2006/relationships/slide" '
                 f'Target="slides/{slide_name}"/>')
    if f"slides/{slide_name}" not in rels:
        rels = rels.replace("</Relationships>", f"  {entry}\n</Relationships>")
        rels_path.write_text(rels, encoding="utf-8")
    return rid


def _next_slide_id(unpacked: Path) -> int:
    prs  = (unpacked / "ppt" / "presentation.xml").read_text(encoding="utf-8")
    ids  = [int(m) for m in re.findall(r'<p:sldId[^>]*\bid="(\d+)"', prs)]
    return max(ids) + 1 if ids else 256


def duplicate_slide(unpacked: Path, source: str) -> None:
    slides_dir  = unpacked / "ppt" / "slides"
    rels_dir    = slides_dir / "_rels"
    source_path = slides_dir / source
    if not source_path.exists():
        print(f"Error: {source_path} not found", file=sys.stderr)
        sys.exit(1)

    dest_name  = f"slide{_next_slide_num(slides_dir)}.xml"
    dest_path  = slides_dir / dest_name
    shutil.copy2(source_path, dest_path)

    src_rels  = rels_dir / f"{source}.rels"
    dest_rels = rels_dir / f"{dest_name}.rels"
    if src_rels.exists():
        shutil.copy2(src_rels, dest_rels)
        # Remove notesSlide relationship from the copy (prevents orphaned notes)
        rels_txt = dest_rels.read_text(encoding="utf-8")
        rels_txt = re.sub(
            r'\s*<Relationship[^>]*Type="[^"]*notesSlide"[^>]*/>\s*',
            "\n", rels_txt,
        )
        dest_rels.write_text(rels_txt, encoding="utf-8")

    _add_content_type(unpacked, dest_name)
    rid     = _add_prs_rel(unpacked, dest_name)
    sld_id  = _next_slide_id(unpacked)

    print(f"Created {dest_name} from {source}")
    print(f'Add to presentation.xml <p:sldIdLst>: '
          f'<p:sldId id="{sld_id}" r:id="{rid}"/>')


_BLANK_SLIDE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


def create_from_layout(unpacked: Path, layout_file: str) -> None:
    slides_dir   = unpacked / "ppt" / "slides"
    layouts_dir  = unpacked / "ppt" / "slideLayouts"
    rels_dir     = slides_dir / "_rels"

    if not (layouts_dir / layout_file).exists():
        print(f"Error: {layouts_dir / layout_file} not found", file=sys.stderr)
        sys.exit(1)

    dest_name = f"slide{_next_slide_num(slides_dir)}.xml"
    rels_dir.mkdir(exist_ok=True)
    (slides_dir / dest_name).write_text(_BLANK_SLIDE, encoding="utf-8")

    rels_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org'
                '/package/2006/relationships">\n'
                f'  <Relationship Id="rId1"\n'
                f'    Type="http://schemas.openxmlformats.org/officeDocument'
                f'/2006/relationships/slideLayout"\n'
                f'    Target="../slideLayouts/{layout_file}"/>\n'
                '</Relationships>')
    (rels_dir / f"{dest_name}.rels").write_text(rels_xml, encoding="utf-8")

    _add_content_type(unpacked, dest_name)
    rid    = _add_prs_rel(unpacked, dest_name)
    sld_id = _next_slide_id(unpacked)

    print(f"Created {dest_name} from {layout_file}")
    print(f'Add to presentation.xml <p:sldIdLst>: '
          f'<p:sldId id="{sld_id}" r:id="{rid}"/>')


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python add_slide.py UNPACKED_DIR SOURCE", file=sys.stderr)
        print("", file=sys.stderr)
        print("SOURCE: slide2.xml | slideLayout2.xml", file=sys.stderr)
        print("To list layouts: ls UNPACKED_DIR/ppt/slideLayouts/", file=sys.stderr)
        sys.exit(1)

    unpacked = Path(sys.argv[1])
    source   = sys.argv[2]

    if not unpacked.exists():
        print(f"Error: {unpacked} not found", file=sys.stderr)
        sys.exit(1)

    if source.startswith("slideLayout") and source.endswith(".xml"):
        create_from_layout(unpacked, source)
    else:
        duplicate_slide(unpacked, source)


if __name__ == "__main__":
    main()
