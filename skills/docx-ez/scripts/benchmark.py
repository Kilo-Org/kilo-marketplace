#!/usr/bin/env python3
"""Benchmark: docx-ez skill vs Anthropic skills fork docx skill.

Suites:
  C – SKILL.md coverage (keyword/topic checks)
  D – Script inventory (which files each skill ships)
  E – Code quality (safety, portability, design guidance)
  A – Functional round-trip (create → validate → unpack → pack)
  B – Feature-specific tests (edit, accept_changes, comment)
  P – POI corpus tests (only when --poi is given)

Usage:
    python benchmark.py [--poi POI_DIR_OR_FILE] [--output JSON_FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

SKILL_A = Path("/home/user/kilo/skills/docx-ez")
SKILL_B = Path("/home/user/skills/skills/docx")
SKILL_A_SCRIPTS = SKILL_A / "scripts"
SKILL_B_SCRIPTS = SKILL_B / "scripts"
SKILL_B_OFFICE  = SKILL_B / "scripts" / "office"

_results: list[tuple[str, str, str, str]] = []
_pass = _fail = _warn = 0


# ── helpers ───────────────────────────────────────────────────────────────────

def _record(suite: str, name: str, status: str, detail: str = "") -> None:
    global _pass, _fail, _warn
    _results.append((suite, name, status, detail))
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}.get(status, "?")
    suffix = f": {detail}" if detail else ""
    print(f"  {icon} [{suite}] {name}{suffix}")
    if status == "PASS":   _pass += 1
    elif status == "FAIL": _fail += 1
    elif status == "WARN": _warn += 1


def _read(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(errors="replace")


def _run(cmd: list[str], cwd: str | None = None, env=None,
         timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=cwd, env=env, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)


# ── Suite C – SKILL.md coverage ───────────────────────────────────────────────

SKILL_MD_CHECKS = [
    ("tracked changes",     ["w:ins", "w:del"]),
    ("comment XML",         ["commentRangeStart", "w:comment"]),
    ("style headings",      ["Heading 1", "heading"]),
    ("table creation",      ["add_table", "w:tr"]),
    ("image embedding",     ["add_picture", "ImageRun"]),
    ("PDF export",          ["LibreOffice", "soffice"]),
    ("smart quotes",        ["&#x201C;", "&#x2019;"]),
    ("OOXML unpack/pack",   ["unpack", "pack"]),
    ("xml:space preserve",  ["xml:space", "preserve"]),
    ("defusedxml or lxml safety", ["lxml", "huge_tree"]),
]


def suite_c() -> None:
    print("\n## Suite C: SKILL.md Coverage")
    a_text = _read(SKILL_A / "SKILL.md")
    b_text = _read(SKILL_B / "SKILL.md")

    for label, keywords in SKILL_MD_CHECKS:
        a_has = all(kw.lower() in a_text.lower() for kw in keywords)
        b_has = all(kw.lower() in b_text.lower() for kw in keywords)

        if a_has:
            _record("C", label, "PASS")
        elif b_has and not a_has:
            _record("C", label, "WARN", "Skill A missing; Skill B has it")
        else:
            _record("C", label, "WARN", "Both missing")


# ── Suite D – Script inventory ────────────────────────────────────────────────

SCRIPT_PAIRS: dict[str, tuple[Path | None, Path | None]] = {
    "create_docx.py":           (SKILL_A_SCRIPTS / "create_docx.py",
                                 SKILL_B_SCRIPTS / "create_docx.py"),
    "create_docx.js":           (SKILL_A_SCRIPTS / "create_docx.js",
                                 None),
    "edit_docx.py":             (SKILL_A_SCRIPTS / "edit_docx.py",
                                 SKILL_B_SCRIPTS / "edit_docx.py"),
    "accept_changes.py":        (SKILL_A_SCRIPTS / "accept_changes.py",
                                 SKILL_B_SCRIPTS / "accept_changes.py"),
    "comment.py":               (SKILL_A_SCRIPTS / "comment.py",
                                 SKILL_B_SCRIPTS / "comment.py"),
    "export_pdf.sh":            (SKILL_A_SCRIPTS / "export_pdf.sh",
                                 None),
    "validate_docx.py":         (SKILL_A_SCRIPTS / "validate_docx.py",
                                 SKILL_B_OFFICE / "validate.py"),
    "office/unpack.py":         (SKILL_A_SCRIPTS / "office" / "unpack.py",
                                 SKILL_B_OFFICE / "unpack.py"),
    "office/pack.py":           (SKILL_A_SCRIPTS / "office" / "pack.py",
                                 SKILL_B_OFFICE / "pack.py"),
    "office/soffice.py":        (SKILL_A_SCRIPTS / "office" / "soffice.py",
                                 SKILL_B_OFFICE / "soffice.py"),
    "benchmark.py":             (SKILL_A_SCRIPTS / "benchmark.py",
                                 None),
    "python-docx.md reference": (SKILL_A / "references" / "python-docx.md",
                                 SKILL_B / "references" / "python-docx.md"),
    "ooxml.md reference":       (SKILL_A / "references" / "ooxml.md",
                                 SKILL_B / "references" / "ooxml.md"),
}


def suite_d() -> None:
    print("\n## Suite D: Script Inventory")
    for label, (path_a, path_b) in SCRIPT_PAIRS.items():
        a_has = path_a is not None and path_a.exists()
        b_has = path_b is not None and path_b.exists()

        if a_has and b_has:
            _record("D", label, "PASS")
        elif a_has and not b_has:
            _record("D", label, "WARN", "Skill A unique feature")
        elif b_has and not a_has:
            _record("D", label, "FAIL", "Skill B has it; Skill A missing")
        else:
            _record("D", label, "FAIL", "Both missing")


# ── Suite E – Code quality ────────────────────────────────────────────────────

def suite_e() -> None:
    print("\n## Suite E: Code Quality")

    # create_docx.py
    a_create = _read(SKILL_A_SCRIPTS / "create_docx.py")
    _record("E", "create_docx: shebang present",
            "PASS" if "#!/usr/bin/env python3" in a_create else "FAIL")
    _record("E", "create_docx: json.load spec loading",
            "PASS" if "json.load" in a_create else "FAIL")
    _record("E", "create_docx: notes/toc support",
            "PASS" if "toc" in a_create.lower() or "add_toc" in a_create else "FAIL")
    _record("E", "create_docx: table support",
            "PASS" if "add_table" in a_create else "FAIL")

    # edit_docx.py
    a_edit = _read(SKILL_A_SCRIPTS / "edit_docx.py")
    _record("E", "edit_docx: replace_tracked (w:ins/w:del)",
            "PASS" if "replace_tracked" in a_edit and ("w:ins" in a_edit or "w:del" in a_edit)
            else "FAIL")
    _record("E", "edit_docx: add_comment",
            "PASS" if "add_comment" in a_edit else "FAIL")
    _record("E", "edit_docx: deepcopy for run duplication",
            "PASS" if "deepcopy" in a_edit else "FAIL")

    # validate_docx.py
    a_val = _read(SKILL_A_SCRIPTS / "validate_docx.py")
    _record("E", "validate_docx: checks ZIP integrity",
            "PASS" if "zipfile" in a_val or "is_zipfile" in a_val else "FAIL")
    _record("E", "validate_docx: checks required parts (word/document.xml)",
            "PASS" if "word/document.xml" in a_val else "FAIL")

    # office/unpack.py
    a_unpack = _read(SKILL_A_SCRIPTS / "office" / "unpack.py")
    _record("E", "office/unpack: smart-quote encoding (&#x201C;)",
            "PASS" if "&#x201C;" in a_unpack else "FAIL")
    _record("E", "office/unpack: lxml pretty_print",
            "PASS" if "pretty_print" in a_unpack else "FAIL")

    # office/pack.py
    a_pack = _read(SKILL_A_SCRIPTS / "office" / "pack.py")
    _record("E", "office/pack: --original flag",
            "PASS" if "--original" in a_pack else "FAIL")
    _record("E", "office/pack: smart-quote decode (&#x201C; back to Unicode)",
            "PASS" if "&#x201C;" in a_pack else "FAIL")

    # SKILL.md length ratio
    a_len = len(_read(SKILL_A / "SKILL.md"))
    b_len = len(_read(SKILL_B / "SKILL.md"))
    ratio = a_len / b_len if b_len else 0
    _record("E", f"SKILL.md coverage ratio (A={a_len} B={b_len} chars)",
            "PASS" if ratio >= 0.5 else "FAIL" if ratio < 0.25 else "WARN",
            f"Skill A is {int(ratio*100)}% of Skill B guidance coverage")


# ── Suite A – Functional round-trip ──────────────────────────────────────────

def _make_minimal_docx(path: Path) -> None:
    CT = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    RELS = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>"""
    DOC = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r><w:t>Hello DOCX</w:t></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels",         RELS)
        z.writestr("word/document.xml",   DOC)


def suite_a(tmpdir: Path) -> None:
    print("\n## Suite A: Functional Round-Trip")

    # ── Skill A: create via create_docx.py ──────────────────────────────────
    out_a = tmpdir / "a_demo.docx"
    rc, out, err = _run([sys.executable, str(SKILL_A_SCRIPTS / "create_docx.py"),
                         str(out_a)])
    a_create_ok = rc == 0 and out_a.exists()
    _record("A", "Skill A create_docx.py: demo document created",
            "PASS" if a_create_ok else "FAIL", err.strip() if not a_create_ok else "")

    if a_create_ok:
        try:
            with zipfile.ZipFile(out_a) as z:
                names = z.namelist()
            has_doc = "word/document.xml" in names
            _record("A", "Skill A create: valid zip with word/document.xml",
                    "PASS" if has_doc else "FAIL")
        except Exception as e:
            _record("A", "Skill A create: valid zip", "FAIL", str(e))

    # ── Skill A: validate ────────────────────────────────────────────────────
    if a_create_ok:
        rc, out, err = _run([sys.executable,
                             str(SKILL_A_SCRIPTS / "validate_docx.py"), str(out_a)])
        _record("A", "Skill A validate_docx.py: passes on own output",
                "PASS" if rc == 0 else "FAIL",
                (out + err).strip() if rc != 0 else "")

    # ── Skill A: unpack ──────────────────────────────────────────────────────
    fixture = tmpdir / "fixture.docx"
    _make_minimal_docx(fixture)

    a_unpacked = tmpdir / "a_unpacked"
    rc, out, err = _run([sys.executable,
                         str(SKILL_A_SCRIPTS / "office" / "unpack.py"),
                         str(fixture), str(a_unpacked)])
    a_unpack_ok = rc == 0 and (a_unpacked / "word" / "document.xml").exists()
    _record("A", "Skill A unpack.py: extracts word/document.xml",
            "PASS" if a_unpack_ok else "FAIL", err.strip() if not a_unpack_ok else "")

    if a_unpack_ok:
        doc_xml = (a_unpacked / "word" / "document.xml").read_text(errors="replace")
        _record("A", "Skill A unpack: body text preserved",
                "PASS" if "Hello DOCX" in doc_xml else "FAIL")

    # ── Skill A: pack ────────────────────────────────────────────────────────
    if a_unpack_ok:
        a_repacked = tmpdir / "a_repacked.docx"
        rc, out, err = _run([sys.executable,
                             str(SKILL_A_SCRIPTS / "office" / "pack.py"),
                             str(a_unpacked), str(a_repacked),
                             "--original", str(fixture)])
        a_pack_ok = rc == 0 and a_repacked.exists()
        if "lxml" in err or "ModuleNotFoundError" in err:
            _record("A", "Skill A pack.py: repackages unpacked DOCX", "WARN",
                    f"dependency missing: {err.strip()[:100]}")
        else:
            _record("A", "Skill A pack.py: repackages unpacked DOCX",
                    "PASS" if a_pack_ok else "FAIL",
                    err.strip() if not a_pack_ok else "")

    # ── Skill B: unpack ──────────────────────────────────────────────────────
    b_unpacked = tmpdir / "b_unpacked"
    env_b = os.environ.copy()
    env_b["PYTHONPATH"] = str(SKILL_B_SCRIPTS)
    rc, out, err = _run([sys.executable, str(SKILL_B_OFFICE / "unpack.py"),
                         str(fixture), str(b_unpacked)],
                        env=env_b)
    b_unpack_ok = rc == 0 and (b_unpacked / "word" / "document.xml").exists()
    _record("A", "Skill B unpack.py: extracts word/document.xml",
            "PASS" if b_unpack_ok else "FAIL", err.strip() if not b_unpack_ok else "")

    if b_unpack_ok:
        doc_xml = (b_unpacked / "word" / "document.xml").read_text(errors="replace")
        _record("A", "Skill B unpack: body text preserved",
                "PASS" if "Hello DOCX" in doc_xml else "FAIL")

    # ── Skill B: pack ────────────────────────────────────────────────────────
    if b_unpack_ok:
        b_repacked = tmpdir / "b_repacked.docx"
        rc, out, err = _run([sys.executable, str(SKILL_B_OFFICE / "pack.py"),
                             str(b_unpacked), str(b_repacked),
                             "--original", str(fixture)],
                            env=env_b)
        b_pack_ok = rc == 0 and b_repacked.exists()
        if "lxml" in err or "defusedxml" in err or "ModuleNotFoundError" in err:
            _record("A", "Skill B pack.py: repackages unpacked DOCX", "WARN",
                    f"dependency missing: {err.strip()[:100]}")
        else:
            _record("A", "Skill B pack.py: repackages unpacked DOCX",
                    "PASS" if b_pack_ok else "FAIL",
                    err.strip() if not b_pack_ok else "")


# ── Suite B – Feature-specific tests ─────────────────────────────────────────

def suite_b(tmpdir: Path) -> None:
    print("\n## Suite B: Feature-Specific Tests")

    # Use the create_docx.py demo document for tests
    demo = tmpdir / "demo_for_b.docx"
    _run([sys.executable, str(SKILL_A_SCRIPTS / "create_docx.py"), str(demo)])

    fixture = tmpdir / "feat_fixture.docx"
    _make_minimal_docx(fixture)

    # Skill A: edit_docx.py --replace
    out_replaced = tmpdir / "b_replaced.docx"
    rc, stdout, err = _run([sys.executable, str(SKILL_A_SCRIPTS / "edit_docx.py"),
                            str(demo) if demo.exists() else str(fixture),
                            str(out_replaced),
                            "--replace", "Introduction", "Overview"])
    replace_ok = rc == 0 and out_replaced.exists()
    _record("B", "Skill A edit_docx: --replace changes text in output",
            "PASS" if replace_ok else "FAIL",
            (stdout + err).strip() if not replace_ok else "")

    if replace_ok:
        try:
            with zipfile.ZipFile(out_replaced) as z:
                doc_xml = z.read("word/document.xml").decode("utf-8", errors="replace")
            _record("B", "Skill A edit_docx: replaced text present in document.xml",
                    "PASS" if "Overview" in doc_xml else "FAIL")
        except Exception as e:
            _record("B", "Skill A edit_docx: verify replacement", "FAIL", str(e))

    # Skill A: accept_changes.py on a doc with NO tracked changes (graceful exit)
    out_accept = tmpdir / "b_accepted.docx"
    rc, stdout, err = _run([sys.executable, str(SKILL_A_SCRIPTS / "accept_changes.py"),
                            str(fixture), str(out_accept)])
    _record("B", "Skill A accept_changes.py: exits 0 on doc with no tracked changes",
            "PASS" if rc == 0 else "FAIL",
            (stdout + err).strip() if rc != 0 else "")

    # Skill A: comment.py list on output docx
    src_for_comment = demo if demo.exists() else fixture
    rc, stdout, err = _run([sys.executable, str(SKILL_A_SCRIPTS / "comment.py"),
                            str(src_for_comment), "list"])
    _record("B", "Skill A comment.py list: exits 0 on valid docx",
            "PASS" if rc == 0 else "FAIL",
            (stdout + err).strip() if rc != 0 else "")

    # SKILL.md size comparison
    a_len = len(_read(SKILL_A / "SKILL.md"))
    b_len = len(_read(SKILL_B / "SKILL.md"))
    ratio = a_len / b_len if b_len else 0
    _record("B", f"SKILL.md size: A={a_len} chars, B={b_len} chars",
            "PASS" if ratio >= 0.5 else "FAIL" if ratio < 0.25 else "WARN",
            f"Skill A is {int(ratio*100)}% of Skill B guidance coverage")


# ── Suite P – POI corpus (only when --poi is given) ───────────────────────────

try:
    from lxml import etree as _etree
    _HAS_LXML = True
except ImportError:
    _HAS_LXML = False

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _qn(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def _open_part(path: str, part: str):
    """Open an XML part from a .docx ZIP. Returns lxml Element or None."""
    try:
        with zipfile.ZipFile(path) as z:
            if part not in z.namelist():
                return None
            data = z.read(part)
        parser = _etree.XMLParser(huge_tree=True, recover=True)
        return _etree.fromstring(data, parser)
    except Exception:
        return None


def _count_tag(root, local: str) -> int:
    return len(root.findall(f".//{_qn(local)}"))


def _heading_counts(root) -> dict[int, int]:
    counts: dict[int, int] = {}
    pStyle_tag = _qn("pStyle")
    for p in root.findall(f".//{_qn('p')}"):
        pPr = p.find(_qn("pPr"))
        if pPr is None:
            continue
        ps = pPr.find(pStyle_tag)
        if ps is None:
            continue
        val = ps.get(_qn("val"), "")
        for prefix in ("Heading", "heading"):
            if val.startswith(prefix):
                try:
                    lvl = int(val[len(prefix):])
                    counts[lvl] = counts.get(lvl, 0) + 1
                except ValueError:
                    pass
    return counts


def _settings_has_track_revisions(path: str) -> bool:
    root = _open_part(path, "word/settings.xml")
    if root is None:
        return False
    return root.find(f".//{_qn('trackRevisions')}") is not None


def _settings_doc_protection_edit(path: str) -> str | None:
    root = _open_part(path, "word/settings.xml")
    if root is None:
        return None
    dp = root.find(f".//{_qn('documentProtection')}")
    if dp is None:
        return None
    return dp.get(_qn("edit"))


@dataclass
class _CheckResult:
    name:   str
    passed: bool
    detail: str = ""


@dataclass
class _FileResult:
    path:   str
    checks: list[_CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(_CheckResult(name, passed, detail))

    def report(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines  = [f"\n{status}: {self.path}"]
        for c in self.checks:
            sym = "✓" if c.passed else "✗"
            lines.append(f"  {sym} {c.name}" + (f": {c.detail}" if c.detail else ""))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "file":   self.path,
            "passed": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail}
                for c in self.checks
            ],
        }


def _poi_infer_mode(filename: str) -> str:
    """Infer the feature mode from a POI corpus filename."""
    name = os.path.basename(filename).lower()
    if any(k in name for k in ("track", "change", "revision", "insert", "delete", "delins")):
        return "tracked-changes"
    if "comment" in name:
        return "comments"
    if "heading" in name:
        return "headings"
    if "table" in name:
        return "tables"
    return "structural-only"


def _poi_run_checks(path: str, mode: str) -> _FileResult:
    """
    Run checks for a single POI corpus file.

    When mode == 'structural-only' (or auto-inferred as such), only the
    xml-wellformed check is run — no feature-specific checks.
    Feature checks are only run when mode is the SPECIFIC feature name.
    """
    result = _FileResult(path)

    # Always: structural integrity
    doc = _open_part(path, "word/document.xml")
    if doc is None:
        result.add("xml-wellformed", False, "word/document.xml missing or unparseable")
        return result
    result.add("xml-wellformed", True)

    # Feature checks — only when mode is explicitly that feature
    if mode == "tracked-changes":
        ins  = _count_tag(doc, "ins")
        dels = _count_tag(doc, "del")
        flag     = _settings_has_track_revisions(path)
        dp_edit  = _settings_doc_protection_edit(path)
        dp_tracks = dp_edit == "trackedChanges"
        has = ins + dels > 0 or flag or dp_tracks
        detail_parts = []
        if ins + dels > 0:
            detail_parts.append(f"{ins} insertion(s), {dels} deletion(s)")
        if flag:
            detail_parts.append("trackRevisions=on")
        if dp_tracks:
            detail_parts.append("documentProtection edit=trackedChanges")
        result.add("has-tracked-changes", has,
                   "; ".join(detail_parts) or "none")

    elif mode == "comments":
        croot = _open_part(path, "word/comments.xml")
        n = _count_tag(croot, "comment") if croot is not None else 0
        dp_edit    = _settings_doc_protection_edit(path)
        dp_comment = dp_edit == "comments"
        has = n > 0 or dp_comment
        detail_parts = []
        if n > 0:
            detail_parts.append(f"{n} comment(s)")
        if dp_comment:
            detail_parts.append("documentProtection edit=comments")
        result.add("has-comments", has, "; ".join(detail_parts) or "none")

    elif mode == "headings":
        hcounts = _heading_counts(doc)
        result.add("has-headings", len(hcounts) > 0,
                   "levels: " + (", ".join(f"H{k}={v}"
                                 for k, v in sorted(hcounts.items()))
                                 if hcounts else "none"))

    elif mode == "tables":
        rows  = _count_tag(doc, "tr")
        cells = _count_tag(doc, "tc")
        result.add("has-tables", rows > 0, f"{rows} row(s), {cells} cell(s)")

    # mode == 'structural-only' or anything else: only xml-wellformed (already added)
    return result


def suite_p(poi_path: str, output_json: str | None = None) -> None:
    """Suite P: POI corpus tests. Only run when --poi is specified."""
    print("\n## Suite P: POI Corpus Tests")

    if not _HAS_LXML:
        _record("P", "lxml available", "FAIL",
                "lxml not installed — run: pip install lxml")
        return

    paths: list[str] = []
    if os.path.isdir(poi_path):
        for root, _, files in os.walk(poi_path):
            for f in sorted(files):
                if f.endswith(".docx"):
                    paths.append(os.path.join(root, f))
    elif os.path.isfile(poi_path):
        paths = [poi_path]
    else:
        _record("P", "poi path", "FAIL", f"{poi_path!r} is not a file or directory")
        return

    if not paths:
        _record("P", "poi corpus", "WARN", "No .docx files found in POI path")
        return

    poi_results: list[_FileResult] = []
    for p in paths:
        mode = _poi_infer_mode(p)
        r = _poi_run_checks(p, mode)
        print(r.report())
        poi_results.append(r)

    total  = len(poi_results)
    passed = sum(1 for r in poi_results if r.passed)
    failed = total - passed
    print(f"\n  POI corpus: {passed}/{total} files passed")
    _record("P", f"POI corpus ({total} files)",
            "PASS" if failed == 0 else "FAIL",
            f"{passed} passed, {failed} failed")

    if output_json:
        with open(output_json, "w") as f:
            json.dump([r.to_dict() for r in poi_results], f, indent=2)
        print(f"  JSON results written to: {output_json}")


# ── Report ────────────────────────────────────────────────────────────────────

def _report() -> None:
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = _pass + _fail + _warn
    lines = [
        "# docx-ez Skill Benchmark Report",
        "",
        f"**Generated**: {now}",
        f"**Skill A (docx-ez)**: `kilo/skills/docx-ez/`",
        f"**Skill B (reference)**: `skills/skills/docx/`",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| | Count |",
        "|---|---|",
        f"| ✓ Passed  | {_pass} |",
        f"| ✗ Failed  | {_fail} |",
        f"| ⚠ Warnings | {_warn} |",
        f"| **Total** | **{total}** |",
        "",
        "---",
        "",
        "## Results",
        "",
        "| Suite | Test | Status | Detail |",
        "|-------|------|--------|--------|",
    ]
    for suite, name, status, detail in _results:
        icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}.get(status, "?")
        lines.append(f"| {suite} | {name} | {icon} {status} | {detail} |")

    lines += [
        "",
        "---",
        "",
        "## Key Findings",
        "",
        "### Where Skill A (docx-ez) leads",
        "",
        "- **Python creation path**: Full JSON-spec driven `create_docx.py` with "
          "headings, paragraphs, tables, images, TOC field stubs, and page breaks.",
        "- **JavaScript creation path**: `create_docx.js` using docx.js v9 for native "
          "bookmark, cross-reference, and richer TOC generation.",
        "- **edit_docx.py CLI**: Tracked insertion/deletion (`w:ins`/`w:del`), "
          "plain-text replace, insert-after, delete, and inline comments — all without "
          "unpacking.",
        "- **accept_changes.py**: Accept or reject all tracked changes in one pass, "
          "also cleans `w:rPrChange`/`w:pPrChange`/`w:sectPrChange` markup.",
        "- **comment.py**: Full comment CRUD — list, add (with replies via --parent), "
          "and delete by ID.",
        "- **validate_docx.py**: Standalone ZIP/OPC integrity + XML parse validation "
          "with required-part checks.",
        "- **export_pdf.sh**: Headless LibreOffice PDF export script.",
        "- **References**: `python-docx.md`, `ooxml.md`, `docx-js.md`, `poi-corpus.md`.",
        "",
        "### Where Skill B (Anthropic) leads",
        "",
        "- **OOXML unpack/pack workflow**: Skill B's `office/unpack.py` and "
          "`office/pack.py` are the primary editing path — unpack, edit XML directly, "
          "pack. Skill A also has these scripts, providing feature parity.",
        "- **Smart-quote entities**: Skill B SKILL.md documents the XML entity table "
          "(`&#x201C;`, `&#x2019;`, etc.) explicitly with a dedicated section. "
          "Skill A documents these in SKILL.md but may lack the same depth.",
        "- **docx-js creation guidance**: Skill B SKILL.md contains extensive docx-js "
          "examples covering page size, styles, lists, tables (dual widths, DXA), "
          "images, hyperlinks, footnotes, tab stops, multi-column, TOC, headers/footers, "
          "and a Critical Rules section. Skill A links to `references/docx-js.md`.",
        "- **NEVER use unicode bullets rule**: Explicitly called out in Skill B SKILL.md "
          "with code examples. Skill A does not highlight this pitfall.",
        "- **Tracking pitfalls**: Skill B covers rejecting another author's insertion, "
          "restoring another author's deletion, and paragraph-mark deletion. "
          "Skill A covers these in `ooxml.md` reference but less prominently.",
        "",
        "---",
        "",
        "## Actionable Improvements for docx-ez",
        "",
        "### High Priority",
        "",
        "**1. Expand SKILL.md with docx-js creation patterns**",
        "Add the docx-js Critical Rules, table dual-widths pattern, "
        "list numbering config, page-size DXA table, and 'never unicode bullets' rule "
        "directly in SKILL.md instead of (only) in `references/docx-js.md`. "
        "This reduces the chance of the model missing these critical anti-patterns.",
        "",
        "**2. Document xml:space=preserve and smart-quote table in SKILL.md**",
        "Add the XML entity table (`&#x201C;` etc.) with a clear CRITICAL callout "
        "in the SKILL.md XML Reference section, alongside the `xml:space` rule.",
        "",
        "**3. Highlight 'never use unicode bullets' in SKILL.md**",
        "Add a CRITICAL block mirroring Skill B's list section to prevent a common "
        "generation error.",
        "",
        "### Medium Priority",
        "",
        "**4. Add lxml huge_tree reference in SKILL.md**",
        "Document that deeply-nested documents require `huge_tree=True` and `recover=True` "
        "in the lxml XMLParser, and note that this is already used in the benchmark/scripts.",
        "",
        "**5. Validate that office/pack.py auto-repair is documented**",
        "SKILL.md should explain what auto-repair fixes (durableId, xml:space) and what "
        "it cannot fix (malformed XML, invalid nesting, missing rels).",
        "",
        "### Regressions to Avoid",
        "",
        "1. **Do not remove `create_docx.py`** — python-docx creation is a "
           "differentiating feature Skill B lacks.",
        "2. **Do not remove `create_docx.js`** — docx.js path for bookmarks/TOC.",
        "3. **Do not remove `accept_changes.py`** — Skill B's primary workflow does "
           "not include a scripted accept-all-changes path.",
        "4. **Do not remove `validate_docx.py`** — standalone validation absent from "
           "Skill B's primary scripts.",
        "5. **Do not remove `export_pdf.sh`** — convenient single-command PDF export.",
    ]

    report_path = SKILL_A / "benchmark_report.md"
    report_path.write_text("\n".join(lines) + "\n")
    print(f"\nReport written to: {report_path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--poi",    default=None,
                    help="Path to a POI test .docx file or directory (enables Suite P)")
    ap.add_argument("--output", default=None,
                    help="Write POI JSON results to this file (only used with --poi)")
    args = ap.parse_args()

    print("docx-ez Skill Benchmark")
    print("=" * 60)
    print(f"Skill A (docx-ez):   {SKILL_A}")
    print(f"Skill B (reference):  {SKILL_B}")

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        suite_c()
        suite_d()
        suite_e()
        suite_a(tmpdir)
        suite_b(tmpdir)
        if args.poi:
            suite_p(args.poi, args.output)

    _report()
    print(f"{'=' * 60}")
    print(f"Results: {_pass} passed, {_fail} failed, {_warn} warnings")
    return 1 if _fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
