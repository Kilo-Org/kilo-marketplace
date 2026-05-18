#!/usr/bin/env python3
"""
validate_xlsx.py — Validate the structural integrity of an .xlsx file.

Checks:
  1. ZIP archive is readable
  2. Required OOXML parts are present
  3. All XML parts are well-formed (parseable)
  4. workbook.xml references valid sheet files
  5. Each sheet XML contains at least a <sheetData> element

Usage:
    python validate_xlsx.py <file.xlsx>

Exit code 0 if all checks pass, 1 otherwise.
"""
from __future__ import annotations

import sys
import zipfile
from dataclasses import dataclass, field
from typing import Optional

try:
    from lxml import etree
except ImportError:
    print("Error: lxml not installed. Run: pip install lxml", file=sys.stderr)
    sys.exit(1)

# Namespace shortcuts
NS_WB  = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

REQUIRED_PARTS = [
    "[Content_Types].xml",
    "_rels/.rels",
    "xl/workbook.xml",
    "xl/_rels/workbook.xml.rels",
    "xl/styles.xml",
]


@dataclass
class CheckResult:
    name:   str
    passed: bool
    detail: str = ""


@dataclass
class ValidationResult:
    path:   str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, passed, detail))

    def report(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines  = [f"\n{status}: {self.path}"]
        for c in self.checks:
            sym = "✓" if c.passed else "✗"
            lines.append(f"  {sym} {c.name}" + (f": {c.detail}" if c.detail else ""))
        return "\n".join(lines)


def _read_part(zf: zipfile.ZipFile, part: str) -> Optional[bytes]:
    try:
        return zf.read(part)
    except KeyError:
        return None


def _parse_xml(data: bytes) -> Optional[etree._Element]:
    try:
        parser = etree.XMLParser(recover=True)
        return etree.fromstring(data, parser)
    except Exception:
        return None


def _list_sheet_parts(zf: zipfile.ZipFile) -> list[str]:
    """Extract sheet target paths from xl/_rels/workbook.xml.rels."""
    data = _read_part(zf, "xl/_rels/workbook.xml.rels")
    if data is None:
        return []
    root = _parse_xml(data)
    if root is None:
        return []
    sheet_parts = []
    for rel in root.iter(f"{{{NS_REL}}}Relationship"):
        rtype = rel.get("Type", "")
        if "worksheet" in rtype.lower():
            target = rel.get("Target", "")
            if target:
                if target.startswith("/"):
                    # Absolute OPC path — strip leading slash, keep as-is
                    target = target.lstrip("/")
                elif not target.startswith("xl/"):
                    # Relative to xl/ directory
                    target = f"xl/{target}"
                sheet_parts.append(target)
    return sheet_parts


def validate(path: str) -> ValidationResult:
    result = ValidationResult(path)

    # 1. ZIP readability
    try:
        zf = zipfile.ZipFile(path)
        names = set(zf.namelist())
        result.add("zip-readable", True)
    except Exception as exc:
        result.add("zip-readable", False, str(exc))
        return result

    with zf:
        # 2. Required parts present
        missing = [p for p in REQUIRED_PARTS if p not in names]
        result.add(
            "required-parts",
            len(missing) == 0,
            f"missing: {', '.join(missing)}" if missing else "",
        )

        # 3. All XML parts well-formed
        bad_xml: list[str] = []
        for name in names:
            if name.endswith(".xml") or name.endswith(".rels"):
                data = _read_part(zf, name)
                if data and _parse_xml(data) is None:
                    bad_xml.append(name)
        result.add(
            "xml-wellformed",
            len(bad_xml) == 0,
            f"unparseable: {', '.join(bad_xml)}" if bad_xml else "",
        )

        # 4. Sheet parts referenced from workbook.xml.rels exist
        sheet_parts = _list_sheet_parts(zf)
        missing_sheets = [p for p in sheet_parts if p not in names]
        result.add(
            "sheet-parts-exist",
            len(missing_sheets) == 0,
            f"missing: {', '.join(missing_sheets)}" if missing_sheets else f"{len(sheet_parts)} sheet(s)",
        )

        # 5. Each sheet has <sheetData>
        sheets_without_data: list[str] = []
        for sp in sheet_parts:
            data = _read_part(zf, sp)
            if data is None:
                continue
            root = _parse_xml(data)
            if root is None:
                continue
            tag = f"{{{NS_WB}}}sheetData"
            if root.find(f".//{tag}") is None:
                sheets_without_data.append(sp)
        result.add(
            "sheet-data-present",
            len(sheets_without_data) == 0,
            f"missing sheetData: {', '.join(sheets_without_data)}" if sheets_without_data else "",
        )

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    paths: list[str] = sys.argv[1:]
    results = [validate(p) for p in paths]

    for r in results:
        print(r.report())

    total  = len(results)
    passed = sum(1 for r in results if r.passed)
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
