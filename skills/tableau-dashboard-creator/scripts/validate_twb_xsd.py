"""TWB XSD Validator — Structural Checks Against Official Tableau Schema.

Validates a Tableau workbook (.twb) file against the official 2026.1 XSD
published by Tableau (`tableau/tableau-document-schemas` on GitHub).

This is complementary to `validate_twb.py`:
    - `validate_twb.py` checks cross-section semantic integrity (datasource
      references, column-instance refs, filter-slices consistency) — the
      content the XSD marks as `processContents="skip"`.
    - This script checks everything outside those skip-zones: element
      nesting, required attributes, attribute value enums, child ordering.

The XSD targets Tableau 2026.1. When validating a workbook authored for an
older Tableau version (e.g., 2025.x), expect a small set of known
"version-shifted" errors that are safe to ignore. See
`references/step-e-twb-generation.md § XSD Validation` for the
interpretation guide.

Usage:
    python validate_twb_xsd.py <path_to_twb_file>

Exit codes:
    0 — XSD validation passed (with no errors)
    1 — XSD validation failed (one or more errors)
    2 — file could not be parsed or schema could not be loaded (fatal)
"""

import argparse
import logging
import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    print("ERROR: lxml is required. Install with: pip install lxml",
          file=sys.stderr)
    sys.exit(2)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Schema location — sibling `references/xsd/` directory.
# Script lives at: <skill-root>/scripts/validate_twb_xsd.py
# XSD lives at:    <skill-root>/references/xsd/twb_2026.1.0.xsd
SCRIPT_DIR = Path(__file__).resolve().parent
XSD_PATH = SCRIPT_DIR.parent / "references" / "xsd" / "twb_2026.1.0.xsd"


def load_schema(xsd_path: Path) -> etree.XMLSchema:
    """Parse and compile the XSD into a usable schema validator.

    Args:
        xsd_path: Path to the root XSD file. The XSD imports `user.xsd`
            and `xml.xsd` from the same directory.

    Returns:
        Compiled XMLSchema validator.

    Raises:
        FileNotFoundError: If the XSD file does not exist.
        etree.XMLSchemaParseError: If the XSD itself is malformed or has
            unresolved imports.
    """
    if not xsd_path.exists():
        raise FileNotFoundError(f"XSD not found at expected path: {xsd_path}")
    schema_doc = etree.parse(str(xsd_path))
    return etree.XMLSchema(schema_doc)


def validate(twb_path: Path, schema: etree.XMLSchema) -> tuple[bool, list]:
    """Run the schema against a TWB file.

    Args:
        twb_path: Path to the .twb file to validate.
        schema: Compiled XMLSchema validator from `load_schema`.

    Returns:
        Tuple of (passed, errors). `errors` is a list of
        lxml `_LogEntry` objects; empty when `passed` is True.
    """
    doc = etree.parse(str(twb_path))
    passed = schema.validate(doc)
    return passed, list(schema.error_log)


def print_report(twb_path: Path, passed: bool, errors: list) -> None:
    """Print a human-readable validation report.

    Args:
        twb_path: Path of the file that was validated (for display).
        passed: True if validation succeeded.
        errors: List of lxml `_LogEntry` validation errors (may be empty).
    """
    logger.info("=" * 60)
    logger.info("TWB XSD Validation Report")
    logger.info("=" * 60)
    logger.info("File:   %s", twb_path)
    logger.info("Schema: twb_2026.1.0.xsd (Tableau official, version 26.1)")
    logger.info("")

    if passed:
        logger.info("[+] XSD validation: PASS")
        logger.info("Status: ALL CHECKS PASSED")
        logger.info("=" * 60)
        return

    logger.info("[X] XSD validation: FAIL (%d errors)", len(errors))
    logger.info("")
    for err in errors:
        logger.info("    Line %d: %s", err.line, err.message)
    logger.info("")
    logger.info("-" * 60)
    logger.info(
        "Note: when targeting Tableau 2025.x or earlier, a small set of "
        "errors is expected (e.g., 'missing explain-data', "
        "'dim-percentage not allowed'). See step-e-twb-generation.md "
        "§ XSD Validation for the interpretation guide."
    )
    logger.info("=" * 60)


def main() -> None:
    """CLI entry point.

    Parses args, loads the schema, validates the workbook, prints the
    report, and exits with the appropriate code.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Tableau .twb file against the official 2026.1 XSD."
        ),
    )
    parser.add_argument(
        "twb_file",
        help="Path to the .twb file to validate",
    )
    args = parser.parse_args()

    twb_path = Path(args.twb_file)
    if not twb_path.exists():
        logger.error("File not found: %s", twb_path)
        sys.exit(2)
    if twb_path.suffix.lower() != ".twb":
        logger.warning("File does not have .twb extension: %s", twb_path)

    try:
        schema = load_schema(XSD_PATH)
    except FileNotFoundError as e:
        logger.error("%s", e)
        sys.exit(2)
    except etree.XMLSchemaParseError as e:
        logger.error("Failed to compile XSD: %s", e)
        sys.exit(2)

    try:
        passed, errors = validate(twb_path, schema)
    except etree.XMLSyntaxError as e:
        logger.error("File is not well-formed XML: %s", e)
        sys.exit(2)

    print_report(twb_path, passed, errors)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
