"""
TWB XML Validator — Breakage-Only Checks (v1).

Validates Tableau workbook (.twb) XML files for structural errors that would
cause Tableau Desktop to fail, render blank, or produce incorrect output.
Style preferences (hex case, attribute order, comments) are NOT checked —
Tableau normalizes those on save.

Usage:
    python validate_twb.py <path_to_twb_file>
    python validate_twb.py <path_to_twb_file> --verbose

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
    2 — file could not be parsed (fatal)
"""

import argparse
import logging
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ── Logging setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    details: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Aggregated report of all validation checks."""

    file_path: str
    results: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if every check passed."""
        return all(r.passed for r in self.results)

    @property
    def failed_count(self) -> int:
        """Number of failed checks."""
        return sum(1 for r in self.results if not r.passed)

    @property
    def passed_count(self) -> int:
        """Number of passed checks."""
        return sum(1 for r in self.results if r.passed)


# ── Validator class ──────────────────────────────────────────────────────────

class TwbValidator:
    """Validates a .twb XML file for structural breakage issues.

    Checks performed (v1 — breakage only):
        1. Well-formed XML
        2. Datasource existence (worksheet refs → top-level datasources)
        3. Column reference integrity (column-instance → column)
        4. Shelf reference integrity (rows/cols → datasource-dependencies)
        5. CDATA for field references in <run> elements
        6. Dashboard datasource declarations (when filter cards exist)
        7. Filter/slices consistency
        8. Worksheet name ↔ window name match
    """

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.raw_content: str = ""
        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self.report = ValidationReport(file_path=file_path)

    def validate(self) -> ValidationReport:
        """Run all validation checks and return the report.

        Returns:
            ValidationReport with results of all checks.
        """
        # Check 1: Well-formed XML (must pass before other checks)
        if not self._check_well_formed_xml():
            return self.report

        # Remaining checks require a parsed tree
        self._check_datasource_existence()
        self._check_column_reference_integrity()
        self._check_shelf_reference_integrity()
        self._check_cdata_field_references()
        self._check_dashboard_datasource_declarations()
        self._check_filter_slices_consistency()
        self._check_worksheet_window_match()

        return self.report

    # ── Check 1: Well-formed XML ─────────────────────────────────────────

    def _check_well_formed_xml(self) -> bool:
        """Parse the TWB file as XML. If parsing fails, nothing else can run.

        Returns:
            True if parsing succeeded.
        """
        check_name = "Well-formed XML"
        try:
            self.raw_content = Path(self.file_path).read_text(encoding="utf-8")
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
            self.report.results.append(CheckResult(name=check_name, passed=True))
            return True
        except ET.ParseError as e:
            self.report.results.append(CheckResult(
                name=check_name,
                passed=False,
                details=[f"XML parse error: {e}"],
            ))
            return False
        except Exception as e:
            self.report.results.append(CheckResult(
                name=check_name,
                passed=False,
                details=[f"File read error: {e}"],
            ))
            return False

    # ── Check 2: Datasource existence ────────────────────────────────────

    def _check_datasource_existence(self) -> None:
        """Verify that every datasource referenced in worksheets exists
        in the top-level <datasources> block.
        """
        check_name = "Datasource existence"
        errors: List[str] = []

        # Collect top-level datasource names (direct children of <workbook>)
        top_level_ds_names: Set[str] = set()
        top_ds_block = self.root.find("datasources")
        if top_ds_block is not None:
            for ds in top_ds_block.findall("datasource"):
                ds_name = ds.get("name", "")
                if ds_name:
                    top_level_ds_names.add(ds_name)

        # Check each worksheet's view > datasources references
        for ws in self.root.findall(".//worksheets/worksheet"):
            ws_name = ws.get("name", "<unnamed>")
            for ds_ref in ws.findall(".//view/datasources/datasource"):
                ref_name = ds_ref.get("name", "")
                if ref_name and ref_name not in top_level_ds_names:
                    errors.append(
                        f"Worksheet '{ws_name}' references datasource "
                        f"'{ref_name}' which does not exist in top-level "
                        f"<datasources>"
                    )

        self.report.results.append(CheckResult(
            name=check_name,
            passed=len(errors) == 0,
            details=errors,
        ))

    # ── Check 3: Column reference integrity ──────────────────────────────

    def _check_column_reference_integrity(self) -> None:
        """Verify that every column-instance's 'column' attribute resolves
        to a declared <column> in the same datasource-dependencies block
        or in the parent datasource.
        """
        check_name = "Column reference integrity"
        errors: List[str] = []

        # Build a map of columns declared at the top-level datasource
        ds_columns: Dict[str, Set[str]] = {}
        for ds in self.root.findall(".//datasources/datasource"):
            ds_name = ds.get("name", "")
            columns: Set[str] = set()
            for col in ds.findall("column"):
                col_name = col.get("name", "")
                if col_name:
                    columns.add(col_name)
            ds_columns[ds_name] = columns

        # Check each worksheet's datasource-dependencies
        for ws in self.root.findall(".//worksheets/worksheet"):
            ws_name = ws.get("name", "<unnamed>")
            for dep in ws.findall(".//datasource-dependencies"):
                dep_ds = dep.get("datasource", "")

                # Columns declared in this dependencies block
                local_columns: Set[str] = set()
                for col in dep.findall("column"):
                    col_name = col.get("name", "")
                    if col_name:
                        local_columns.add(col_name)

                # Combined: local + top-level datasource columns
                all_columns = local_columns | ds_columns.get(dep_ds, set())

                # Check each column-instance
                for ci in dep.findall("column-instance"):
                    ci_column = ci.get("column", "")
                    if not ci_column:
                        continue

                    # Skip built-in Tableau fields
                    if self._is_builtin_field(ci_column):
                        continue

                    if ci_column not in all_columns:
                        ci_name = ci.get("name", ci_column)
                        errors.append(
                            f"Worksheet '{ws_name}': column-instance "
                            f"'{ci_name}' references column '{ci_column}' "
                            f"which is not declared in datasource-dependencies "
                            f"or datasource '{dep_ds}'"
                        )

        self.report.results.append(CheckResult(
            name=check_name,
            passed=len(errors) == 0,
            details=errors,
        ))

    # ── Check 4: Shelf reference integrity ───────────────────────────────

    def _check_shelf_reference_integrity(self) -> None:
        """Verify that all field references in <rows> and <cols> match
        column-instances declared in the worksheet's datasource-dependencies.
        """
        check_name = "Shelf reference integrity"
        errors: List[str] = []

        # Pattern to extract [datasource].[column-instance] refs from shelf text
        # Matches: [datasource.name].[instance:name:suffix]
        shelf_ref_pattern = re.compile(
            r"\[([^\]]+)\]\.\[([^\]]+)\]"
        )

        for ws in self.root.findall(".//worksheets/worksheet"):
            ws_name = ws.get("name", "<unnamed>")

            # Collect all column-instance names per datasource in this worksheet
            ds_instances: Dict[str, Set[str]] = {}
            for dep in ws.findall(".//datasource-dependencies"):
                dep_ds = dep.get("datasource", "")
                instances: Set[str] = set()
                for ci in dep.findall("column-instance"):
                    ci_name = ci.get("name", "")
                    if ci_name:
                        instances.add(ci_name)
                ds_instances[dep_ds] = instances

            # Check <rows> and <cols>
            table = ws.find("table")
            if table is None:
                continue

            for shelf_tag in ("rows", "cols"):
                shelf_el = table.find(shelf_tag)
                if shelf_el is None:
                    continue

                shelf_text = shelf_el.text
                if not shelf_text or not shelf_text.strip():
                    continue  # Empty shelf (<rows /> or <cols />) is valid

                refs = shelf_ref_pattern.findall(shelf_text)
                for ds_name, instance_name in refs:
                    # Skip Tableau built-in generated fields
                    if self._is_builtin_field_name(instance_name):
                        continue

                    # Skip Measure Names / Measure Values
                    if "Measure Names" in instance_name or "Measure Values" in instance_name:
                        continue

                    known_instances = ds_instances.get(ds_name, set())
                    # Column-instance names in XML include brackets:
                    # e.g., [sum:profit:qk], but shelf text strips them
                    bracketed_name = f"[{instance_name}]"
                    if (instance_name not in known_instances
                            and bracketed_name not in known_instances):
                        errors.append(
                            f"Worksheet '{ws_name}', <{shelf_tag}>: "
                            f"references '{ds_name}.{instance_name}' but "
                            f"'{instance_name}' is not declared as a "
                            f"column-instance in datasource-dependencies"
                        )

        self.report.results.append(CheckResult(
            name=check_name,
            passed=len(errors) == 0,
            details=errors,
        ))

    # ── Check 5: CDATA for field references in <run> elements ────────────

    def _check_cdata_field_references(self) -> None:
        """Detect <run> elements that use entity-encoded field references
        (&lt;[...]&gt;) instead of CDATA wrapping. Entity-encoded refs
        cause Tableau to display literal text instead of the field value.
        """
        check_name = "CDATA for field references"
        errors: List[str] = []

        # Entity-encoded field reference pattern: &lt;[datasource].[field]&gt;
        entity_pattern = re.compile(r"&lt;\[.*?\]\.\[.*?\]&gt;")

        # Search raw content since ET strips CDATA/entities
        # Find all <run ...>content</run> segments
        run_pattern = re.compile(
            r"<run\b[^>]*>(.*?)</run>",
            re.DOTALL,
        )

        for i, line in enumerate(self.raw_content.splitlines(), start=1):
            # Check for entity-encoded field refs in <run> elements on this line
            for match in run_pattern.finditer(line):
                run_content = match.group(1)
                if entity_pattern.search(run_content):
                    # Extract a short preview
                    preview = run_content[:80].strip()
                    errors.append(
                        f"Line {i}: <run> element uses entity-encoded field "
                        f"reference instead of CDATA: '{preview}...'"
                    )

        self.report.results.append(CheckResult(
            name=check_name,
            passed=len(errors) == 0,
            details=errors,
        ))

    # ── Check 6: Dashboard datasource declarations ───────────────────────

    def _check_dashboard_datasource_declarations(self) -> None:
        """When a dashboard contains filter card zones, the <dashboard>
        element must have its own <datasources> block. Missing this causes
        filter cards to crash.
        """
        check_name = "Dashboard datasource declarations"
        errors: List[str] = []

        for dashboard in self.root.findall(".//dashboards/dashboard"):
            db_name = dashboard.get("name", "<unnamed>")

            # Look for filter card zones: zones with type='filter' attribute
            # or cards with type='filter' in the dashboard zones
            has_filter_zone = False

            # Method 1: quick filter zones in layout
            for zone in dashboard.iter("zone"):
                zone_type = zone.get("type", "")
                if zone_type == "filter":
                    has_filter_zone = True
                    break
                # Also check for 'mode' attribute which indicates a quick filter
                if zone.get("mode") in ("checkdropdown", "typeinlist",
                                         "checkdropdownsingle", "slider"):
                    has_filter_zone = True
                    break

            if not has_filter_zone:
                continue

            # Dashboard has filter zones — check for <datasources>
            db_datasources = dashboard.find("datasources")
            if db_datasources is None:
                errors.append(
                    f"Dashboard '{db_name}' has filter card zones but no "
                    f"<datasources> block inside the <dashboard> element. "
                    f"Filter cards require dashboard-level datasource "
                    f"declarations."
                )

        self.report.results.append(CheckResult(
            name=check_name,
            passed=len(errors) == 0,
            details=errors,
        ))

    # ── Check 7: Filter/slices consistency ───────────────────────────────

    def _check_filter_slices_consistency(self) -> None:
        """Every field with a <filter> element must also appear in <slices>.
        Missing slices entries cause filters to be silently ignored.
        """
        check_name = "Filter/slices consistency"
        errors: List[str] = []

        for ws in self.root.findall(".//worksheets/worksheet"):
            ws_name = ws.get("name", "<unnamed>")
            view = ws.find(".//view")
            if view is None:
                continue

            # Collect filter columns
            filter_columns: Set[str] = set()
            for filt in view.findall("filter"):
                col = filt.get("column", "")
                if col:
                    filter_columns.add(col)

            if not filter_columns:
                continue

            # Collect slices columns
            slices_columns: Set[str] = set()
            slices = view.find("slices")
            if slices is not None:
                for col_el in slices.findall("column"):
                    if col_el.text:
                        slices_columns.add(col_el.text.strip())

            # Check: every filter column should be in slices
            # Note: action filters (containing "Action" in the column name)
            # are handled specially by Tableau and DO appear in slices,
            # so we check them too
            for fc in filter_columns:
                if fc not in slices_columns:
                    # Skip quantitative filters on date ranges — these
                    # sometimes legitimately lack slices entries in some
                    # Tableau versions, but it's still best practice
                    errors.append(
                        f"Worksheet '{ws_name}': filter on '{fc}' has no "
                        f"matching entry in <slices>"
                    )

        self.report.results.append(CheckResult(
            name=check_name,
            passed=len(errors) == 0,
            details=errors,
        ))

    # ── Check 8: Worksheet name ↔ window name match ─────────────────────

    def _check_worksheet_window_match(self) -> None:
        """Every <worksheet name='X'> must have a corresponding
        <window name='X'> in <windows>. Mismatches cause sheets not
        to display.
        """
        check_name = "Worksheet-window name match"
        errors: List[str] = []

        # Collect worksheet names
        worksheet_names: Set[str] = set()
        for ws in self.root.findall(".//worksheets/worksheet"):
            name = ws.get("name", "")
            if name:
                worksheet_names.add(name)

        # Collect window names (only worksheet-class windows)
        window_names: Set[str] = set()
        for win in self.root.findall(".//windows/window"):
            win_class = win.get("class", "")
            name = win.get("name", "")
            if name and win_class == "worksheet":
                window_names.add(name)

        # Also collect dashboard window names (they don't need worksheet match)
        dashboard_names: Set[str] = set()
        for db in self.root.findall(".//dashboards/dashboard"):
            name = db.get("name", "")
            if name:
                dashboard_names.add(name)

        # Check: every worksheet should have a window
        for ws_name in worksheet_names:
            if ws_name not in window_names:
                errors.append(
                    f"Worksheet '{ws_name}' has no matching "
                    f"<window name='{ws_name}'> in <windows>"
                )

        # Check reverse: every worksheet-class window should have a worksheet
        for win_name in window_names:
            if win_name not in worksheet_names:
                errors.append(
                    f"Window '{win_name}' (class='worksheet') has no "
                    f"matching <worksheet name='{win_name}'>"
                )

        self.report.results.append(CheckResult(
            name=check_name,
            passed=len(errors) == 0,
            details=errors,
        ))

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _is_builtin_field(column_ref: str) -> bool:
        """Check if a column reference is a Tableau built-in field.

        Args:
            column_ref: The column name from a column-instance's column attr.

        Returns:
            True if this is a built-in field.
        """
        builtins = {
            "[Number of Records]",
            "[Measure Names]",
            "[Measure Values]",
            "[:Measure Names]",
            "[:Measure Values]",
        }
        return column_ref in builtins

    @staticmethod
    def _is_builtin_field_name(instance_name: str) -> bool:
        """Check if a column-instance name refers to a built-in/generated field.

        Args:
            instance_name: The instance name from shelf text.

        Returns:
            True if this is a built-in or generated field name.
        """
        # Tableau-generated geographic fields
        if "(generated)" in instance_name:
            return True
        # Measure Names / Values
        if "Measure Names" in instance_name or "Measure Values" in instance_name:
            return True
        return False


# ── Report printing ──────────────────────────────────────────────────────────

def print_report(report: ValidationReport, verbose: bool = False) -> None:
    """Print a formatted validation report.

    Args:
        report: The validation report to print.
        verbose: If True, print details for passed checks too.
    """
    logger.info("=" * 60)
    logger.info("TWB Validation Report")
    logger.info("=" * 60)
    logger.info("File: %s", report.file_path)
    logger.info("")

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        icon = "[+]" if result.passed else "[X]"
        logger.info("%s %s: %s", icon, result.name, status)

        if result.details and (not result.passed or verbose):
            for detail in result.details:
                logger.info("    - %s", detail)

    logger.info("")
    logger.info("-" * 60)
    total = len(report.results)
    logger.info(
        "Result: %d/%d checks passed, %d failed",
        report.passed_count, total, report.failed_count,
    )

    if report.passed:
        logger.info("Status: ALL CHECKS PASSED")
    else:
        logger.info("Status: VALIDATION FAILED")
    logger.info("=" * 60)


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point for the TWB validator.

    Parses arguments, runs validation, prints report, and exits
    with appropriate code.
    """
    parser = argparse.ArgumentParser(
        description="Validate a Tableau .twb file for structural errors.",
    )
    parser.add_argument(
        "twb_file",
        help="Path to the .twb file to validate",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show details for passed checks too",
    )
    args = parser.parse_args()

    # Validate file exists
    twb_path = Path(args.twb_file)
    if not twb_path.exists():
        logger.error("File not found: %s", args.twb_file)
        sys.exit(2)

    if not twb_path.suffix.lower() == ".twb":
        logger.warning("File does not have .twb extension: %s", args.twb_file)

    # Run validation
    validator = TwbValidator(str(twb_path))
    report = validator.validate()

    # Print report
    print_report(report, verbose=args.verbose)

    # Exit code
    if not report.results:
        sys.exit(2)  # No checks ran (fatal parse error)
    elif report.passed:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
