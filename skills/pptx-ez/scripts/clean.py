#!/usr/bin/env python3
"""
clean.py — Remove orphaned files from an unpacked PPTX directory.

Usage:
  python clean.py UNPACKED_DIR

Removes:
  - Slides not listed in <p:sldIdLst> and their .rels files
  - Unreferenced media, charts, diagrams, drawings, embeddings
  - Orphaned .rels files
  - Unreferenced notes slides
  - Stale Content_Types.xml overrides for deleted parts

Examples:
  python scripts/clean.py unpacked/
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import defusedxml.minidom as dxml
except ImportError:
    print("Error: defusedxml not installed. Run: pip install defusedxml", file=sys.stderr)
    sys.exit(1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse(path: Path):
    return dxml.parse(str(path))


def _get_rids(dom) -> dict[str, str]:
    """Return {rId: Target} for all Relationship elements."""
    result = {}
    for rel in dom.getElementsByTagName("Relationship"):
        rid    = rel.getAttribute("Id")
        target = rel.getAttribute("Target")
        if rid and target:
            result[rid] = target
    return result


def _slides_in_sldidlst(unpacked: Path) -> set[str]:
    """Return set of slide filenames (e.g. 'slide1.xml') listed in sldIdLst."""
    prs_path  = unpacked / "ppt" / "presentation.xml"
    rels_path = unpacked / "ppt" / "_rels" / "presentation.xml.rels"
    if not prs_path.exists() or not rels_path.exists():
        return set()

    rids = _get_rids(_parse(rels_path))
    prs  = prs_path.read_text(encoding="utf-8")
    referenced_rids = set(re.findall(r'<p:sldId[^>]*\br:id="([^"]+)"', prs))

    result = set()
    for rid in referenced_rids:
        target = rids.get(rid, "")
        if target.startswith("slides/"):
            result.add(target.replace("slides/", ""))
    return result


def _all_referenced(unpacked: Path) -> set[Path]:
    """Walk all .rels files and collect every referenced file's absolute path."""
    referenced: set[Path] = set()
    for rels_file in unpacked.rglob("*.rels"):
        dom = _parse(rels_file)
        for rel in dom.getElementsByTagName("Relationship"):
            target = rel.getAttribute("Target")
            if not target:
                continue
            resolved = (rels_file.parent.parent / target).resolve()
            try:
                referenced.add(resolved.relative_to(unpacked.resolve()))
            except ValueError:
                pass
    return referenced


# ── Removals ─────────────────────────────────────────────────────────────────

def _remove_orphaned_slides(unpacked: Path) -> list[str]:
    slides_dir  = unpacked / "ppt" / "slides"
    rels_dir    = slides_dir / "_rels"
    rels_prs    = unpacked / "ppt" / "_rels" / "presentation.xml.rels"
    if not slides_dir.exists():
        return []

    listed   = _slides_in_sldidlst(unpacked)
    removed  = []

    for slide in slides_dir.glob("slide*.xml"):
        if slide.name not in listed:
            slide.unlink()
            removed.append(str(slide.relative_to(unpacked)))
            rels = rels_dir / f"{slide.name}.rels"
            if rels.exists():
                rels.unlink()
                removed.append(str(rels.relative_to(unpacked)))

    if removed and rels_prs.exists():
        dom     = _parse(rels_prs)
        changed = False
        for rel in list(dom.getElementsByTagName("Relationship")):
            target = rel.getAttribute("Target")
            if target.startswith("slides/") and target.replace("slides/", "") not in listed:
                if rel.parentNode:
                    rel.parentNode.removeChild(rel)
                    changed = True
        if changed:
            rels_prs.write_bytes(dom.toxml(encoding="utf-8"))

    return removed


def _remove_orphaned_resources(unpacked: Path) -> list[str]:
    referenced = _all_referenced(unpacked)
    removed    = []

    resource_dirs = ["media", "embeddings", "charts", "diagrams",
                     "drawings", "tags", "ink"]
    for dname in resource_dirs:
        dpath = unpacked / "ppt" / dname
        if not dpath.exists():
            continue
        for f in dpath.glob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(unpacked)
            if rel not in referenced:
                f.unlink()
                removed.append(str(rel))

    notes_dir = unpacked / "ppt" / "notesSlides"
    if notes_dir.exists():
        for f in notes_dir.glob("*.xml"):
            rel = f.relative_to(unpacked)
            if rel not in referenced:
                f.unlink()
                removed.append(str(rel))
        rels_dir = notes_dir / "_rels"
        if rels_dir.exists():
            for f in rels_dir.glob("*.rels"):
                target = notes_dir / f.name.replace(".rels", "")
                if not target.exists():
                    f.unlink()
                    removed.append(str(f.relative_to(unpacked)))

    return removed


def _update_content_types(unpacked: Path, removed: list[str]) -> None:
    ct_path = unpacked / "[Content_Types].xml"
    if not ct_path.exists() or not removed:
        return
    dom     = _parse(ct_path)
    changed = False
    for ov in list(dom.getElementsByTagName("Override")):
        part = ov.getAttribute("PartName").lstrip("/")
        if part in removed:
            if ov.parentNode:
                ov.parentNode.removeChild(ov)
                changed = True
    if changed:
        ct_path.write_bytes(dom.toxml(encoding="utf-8"))


# ── Entry point ───────────────────────────────────────────────────────────────

def clean(unpacked_dir: str) -> list[str]:
    unpacked  = Path(unpacked_dir)
    all_removed: list[str] = []
    all_removed.extend(_remove_orphaned_slides(unpacked))
    # Iterate until no more orphans (cascading deletions)
    while True:
        batch = _remove_orphaned_resources(unpacked)
        if not batch:
            break
        all_removed.extend(batch)
    if all_removed:
        _update_content_types(unpacked, all_removed)
    return all_removed


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python clean.py UNPACKED_DIR", file=sys.stderr)
        sys.exit(1)

    removed = clean(sys.argv[1])
    if removed:
        print(f"Removed {len(removed)} orphaned file(s):")
        for f in removed:
            print(f"  {f}")
    else:
        print("No orphaned files found.")


if __name__ == "__main__":
    main()
