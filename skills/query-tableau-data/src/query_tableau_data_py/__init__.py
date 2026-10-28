# Query Tableau Datasource

from pathlib import Path

from query_tableau_data_py.models import ExplorationResult
from query_tableau_data_py.session import Session

__all__ = ["get_doc", "Session", "ExplorationResult"]

# Skill root docs/ directory (shared across Python and JS implementations).
# Resolved relative to this file: src/python/__init__.py → ../../docs/
_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"


def get_doc(name: str) -> str:
    """
    Load a documentation file by name from the skill root docs directory.

    Args:
        name: Short name of the doc, e.g. 'REPL', 'AUTH', 'CATALOG',
            'INTROSPECT_DATASOURCE', 'INTROSPECT_WORKBOOK', 'QUERY_DATASOURCE',
            'QUERY_VIEW', 'TEMP_DATA', 'CALCULATIONS', 'ERRORS', 'FIELDS',
            'FILTERS', 'LIMITATIONS', 'PARAMETERS', 'STREAMING'.

    Returns:
        The markdown content as a string.

    Raises:
        ValueError: If the requested doc name is unknown.
    """
    mapping = {
        "REPL": "REPL.md",
        "DDD": "DDD.md",
        "SDK": "sdk/SDK.md",
        "ADVANCED": "sdk/ADVANCED.md",
        "TEMP_DATA": "sdk/TEMP_DATA.md",
        "AUTH": "api/AUTH.md",
        "CATALOG": "api/CATALOG.md",
        "INTROSPECT_DATASOURCE": "api/INTROSPECT_DATASOURCE.md",
        "INTROSPECT_WORKBOOK": "api/INTROSPECT_WORKBOOK.md",
        "QUERY_DATASOURCE": "api/QUERY_DATASOURCE.md",
        "QUERY_VIEW": "api/QUERY_VIEW.md",
        "CALCULATIONS": "vds/CALCULATIONS.md",
        "ERRORS": "vds/ERRORS.md",
        "FIELDS": "vds/FIELDS.md",
        "FILTERS": "vds/FILTERS.md",
        "LIMITATIONS": "vds/LIMITATIONS.md",
        "PARAMETERS": "vds/PARAMETERS.md",
        "STREAMING": "vds/STREAMING.md",
    }

    filename = mapping.get(name.upper())
    if not filename:
        available = ", ".join(sorted(mapping.keys()))
        raise ValueError(f"Unknown doc '{name}'. Available: {available}")

    doc_path = _DOCS_DIR / filename
    return doc_path.read_text(encoding="utf-8")
