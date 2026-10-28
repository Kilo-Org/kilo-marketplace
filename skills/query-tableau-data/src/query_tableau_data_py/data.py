"""Persistence helpers for serializing SDK output to ``temp/``.

Pure utility module — no HTTP calls, no auth imports.  Accepts typed data
and writes JSON, CSV, and Markdown files following the patterns defined in
``docs/TEMP_DATA.md``.

This module is called by the orchestrator (``main.py``) or directly by
agents in Pattern B/C workflows.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from query_tableau_data_py.models import (
    DatasourceSchema,
    DatasourceSummary,
    FieldMeta,
    QueryResult,
    ViewQueryResult,
    ViewSummary,
    WorkbookSchema,
    WorkbookSummary,
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _default_output_dir() -> Path:
    """Return the skill's default ``temp/`` directory at the skill root."""
    return Path(__file__).resolve().parent.parent.parent / "temp"


def _sanitize_filename(name: str) -> str:
    """Replace filesystem-unsafe characters with underscores."""
    return re.sub(r"[^\w\-]", "_", name)


def generate_timestamp() -> str:
    """Return a filesystem-safe timestamp in ``YYYYMMDD_HHMMSS_microseconds`` format.

    Microsecond precision eliminates same-second collisions when multiple
    write calls occur in rapid succession (e.g. orchestrator writing
    OBJECTS then ARRAYS results for the same datasource).
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


# Keys that must never appear in persisted output, even if a caller
# accidentally passes a structure that embeds credentials.
_CREDENTIAL_KEYS = frozenset(
    {
        "auth_token",
        "pat_secret",
        "pat_name",
        "jwt_secret",
        "jwt_client_id",
        "password",
        "connection_password",
    }
)


def _strip_credentials(obj: Any) -> Any:
    """Recursively remove known credential keys from dicts/lists.

    This is a **belt-and-suspenders** defensive guard.  The primary
    protection is that ``data.py`` only accepts typed models that do
    not contain credential fields.  If a caller accidentally passes the
    wrong structure (e.g. an ``SdkConfig`` or ``AuthToken``), this
    function scrubs it before it reaches disk.
    """
    if isinstance(obj, dict):
        return {
            k: _strip_credentials(v)
            for k, v in obj.items()
            if k.lower() not in _CREDENTIAL_KEYS
        }
    if isinstance(obj, list):
        return [_strip_credentials(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_catalog(
    datasources: list[DatasourceSummary],
    output_dir: Path | None = None,
) -> Path:
    """Write a list of ``DatasourceSummary`` objects to a JSON file.

    File pattern: ``data_catalog_{timestamp}.json``

    Args:
        datasources: The catalog entries to persist.
        output_dir: Directory to write the file into. Defaults to the skill's
            ``temp/`` directory.

    Returns:
        The path to the written JSON file.
    """
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generate_timestamp()
    file_path = output_dir / f"data_catalog_{timestamp}.json"

    data = [ds.model_dump(mode="json", exclude_none=True) for ds in datasources]
    data = _strip_credentials(data)

    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return file_path


def write_schema(
    schema: DatasourceSchema,
    output_dir: Path | None = None,
) -> list[Path]:
    """Write a ``DatasourceSchema`` to JSON and Markdown files.

    File patterns:
      - JSON: ``datasource_{name}_{luid}_{timestamp}.json``
      - Markdown: ``inspect_{luid}_{timestamp}.md``

    The Markdown report contains a human-readable table of field groups,
    field names, data types, descriptions, and parameters.

    Args:
        schema: The merged datasource metadata to persist.
        output_dir: Directory to write files into. Defaults to the skill's
            ``temp/`` directory.

    Returns:
        A list containing the JSON path and the Markdown path.
    """
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generate_timestamp()
    safe_name = _sanitize_filename(schema.name or "unknown")
    luid = schema.luid

    json_path = output_dir / f"datasource_{safe_name}_{luid}_{timestamp}.json"
    md_path = output_dir / f"inspect_{luid}_{timestamp}.md"

    # --- JSON ---
    data = schema.model_dump(mode="json", exclude_none=True)
    data = _strip_credentials(data)

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # --- Markdown ---
    lines: list[str] = []
    lines.append(f"# Datasource Schema: {schema.name or 'Unknown'}\n")
    lines.append(f"- **LUID:** `{luid}`\n")
    if schema.description:
        lines.append(f"- **Description:** {schema.description}\n")
    lines.append("\n")

    # Field groups table
    lines.append("## Field Groups\n")
    if schema.field_groups:
        lines.append("| Group | Field | Data Type | Description |\n")
        lines.append("|-------|-------|-----------|-------------|\n")
        for group in schema.field_groups:
            group_caption = group.logical_table_caption or (
                group.logical_table_id or "Ungrouped"
            )
            if group.fields:
                for field in group.fields:
                    desc = field.description or ""
                    lines.append(
                        f"| {group_caption} | {field.name} | {field.data_type} | {desc} |\n"
                    )
            else:
                lines.append(f"| {group_caption} | — | — | No fields |\n")
        lines.append("\n")
    else:
        lines.append("_No field groups available._\n\n")

    # Parameters
    lines.append("## Parameters\n")
    if schema.parameters:
        lines.append("| Caption | Type | Data Type | Value |\n")
        lines.append("|---------|------|-----------|-------|\n")
        for param in schema.parameters:
            # Parameters are discriminated union models; dump to dict for safe access
            param_dict = (
                param.model_dump(mode="json", exclude_none=True)
                if hasattr(param, "model_dump")
                else dict(param)
            )
            caption = param_dict.get("parameter_caption", "")
            ptype = param_dict.get("parameter_type", "")
            dtype = param_dict.get("data_type", "")
            value = param_dict.get("value", "")
            lines.append(f"| {caption} | {ptype} | {dtype} | {value} |\n")
        lines.append("\n")
    else:
        lines.append("_No parameters available._\n\n")

    with md_path.open("w", encoding="utf-8") as fh:
        fh.writelines(lines)

    return [json_path, md_path]


def write_query_result(
    result: QueryResult,
    output_dir: Path | None = None,
    datasource_name: str = "unknown",
    datasource_luid: str = "unknown",
) -> list[Path]:
    """Write a ``QueryResult`` to JSON and CSV files.

    File patterns:
      - JSON: ``query_{name}_{luid}_{timestamp}.json``
      - CSV:  ``query_{name}_{luid}_{timestamp}.csv``

    CSV output adapts to the result format:
      - ``OBJECTS`` (list of dicts) → ``csv.DictWriter``
      - ``ARRAYS``  (list of lists)  → ``csv.writer`` with header row

    Args:
        result: The buffered query result to persist.
        output_dir: Directory to write files into. Defaults to the skill's
            ``temp/`` directory.
        datasource_name: Name of the queried datasource, used in the filename.
        datasource_luid: LUID of the queried datasource, used in the filename.

    Returns:
        A list containing the JSON path and the CSV path.
    """
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generate_timestamp()
    safe_name = _sanitize_filename(datasource_name)
    luid = datasource_luid

    json_path = output_dir / f"query_{safe_name}_{luid}_{timestamp}.json"
    csv_path = output_dir / f"query_{safe_name}_{luid}_{timestamp}.csv"

    # --- JSON ---
    data = result.model_dump(mode="json", exclude_none=True)
    data = _strip_credentials(data)

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # --- CSV ---
    headers = result.metadata.field_captions if result.metadata else []
    rows = result.rows

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        if rows and isinstance(rows[0], dict):
            # OBJECTS format
            # Defensive: infer fieldnames from row keys if metadata headers are empty
            fieldnames = headers if headers else list(rows[0].keys())
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        else:
            # ARRAYS format (or empty)
            writer = csv.writer(fh)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)

    return [json_path, csv_path]


def write_workbook_catalog(
    workbooks: list[WorkbookSummary],
    output_dir: Path | None = None,
) -> Path:
    """Write a list of ``WorkbookSummary`` objects to a JSON file.

    File pattern: ``workbook_catalog_{timestamp}.json``

    Args:
        workbooks: The workbook catalog entries to persist.
        output_dir: Directory to write the file into. Defaults to the skill's
            ``temp/`` directory.

    Returns:
        The path to the written JSON file.
    """
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generate_timestamp()
    file_path = output_dir / f"workbook_catalog_{timestamp}.json"

    data = [wb.model_dump(mode="json", exclude_none=True) for wb in workbooks]
    data = _strip_credentials(data)

    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return file_path


def write_view_catalog(
    views: list[ViewSummary],
    output_dir: Path | None = None,
) -> Path:
    """Write a list of ``ViewSummary`` objects to a JSON file.

    File pattern: ``view_catalog_{timestamp}.json``

    Args:
        views: The view catalog entries to persist.
        output_dir: Directory to write the file into. Defaults to the skill's
            ``temp/`` directory.

    Returns:
        The path to the written JSON file.
    """
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generate_timestamp()
    file_path = output_dir / f"view_catalog_{timestamp}.json"

    data = [v.model_dump(mode="json", exclude_none=True) for v in views]
    data = _strip_credentials(data)

    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return file_path


def write_workbook_schema(
    schema: WorkbookSchema,
    output_dir: Path | None = None,
) -> list[Path]:
    """Write a ``WorkbookSchema`` to JSON and Markdown files.

    File patterns:
      - JSON:     ``workbook_{name}_{luid}_{timestamp}.json``
      - Markdown: ``workbook_inspect_{luid}_{timestamp}.md``

    The Markdown report contains a human-readable summary of the workbook's
    sheets (with field instance counts), dashboards, and embedded datasources.

    Args:
        schema: The workbook introspection result to persist.
        output_dir: Directory to write files into. Defaults to the skill's
            ``temp/`` directory.

    Returns:
        A list containing the JSON path and the Markdown path.
    """
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generate_timestamp()
    safe_name = _sanitize_filename(schema.name or "unknown")
    luid = schema.luid

    json_path = output_dir / f"workbook_{safe_name}_{luid}_{timestamp}.json"
    md_path = output_dir / f"workbook_inspect_{luid}_{timestamp}.md"

    # --- JSON ---
    data = schema.model_dump(mode="json", exclude_none=True)
    data = _strip_credentials(data)

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # --- Markdown ---
    lines: list[str] = []
    lines.append(f"# Workbook Schema: {schema.name or 'Unknown'}\n")
    lines.append(f"- **LUID:** `{luid}`\n")
    if schema.project_name:
        lines.append(f"- **Project:** {schema.project_name}\n")
    if schema.owner_name:
        lines.append(f"- **Owner:** {schema.owner_name}\n")
    if schema.description:
        lines.append(f"- **Description:** {schema.description}\n")
    lines.append("\n")

    # Sheets table
    lines.append("## Sheets\n")
    if schema.sheets:
        lines.append("| Sheet | Fields | Worksheet Calcs | Dashboards |\n")
        lines.append("|-------|--------|-----------------|------------|\n")
        for sheet in schema.sheets:
            dash_names = ", ".join(d.name for d in sheet.contained_in_dashboards) or "—"
            lines.append(
                f"| {sheet.name} | {len(sheet.field_instances)}"
                f" | {len(sheet.worksheet_fields)}"
                f" | {dash_names} |\n"
            )
        lines.append("\n")
    else:
        lines.append("_No sheets available._\n\n")

    # Dashboards table
    lines.append("## Dashboards\n")
    if schema.dashboards:
        lines.append("| Dashboard | Component Sheets |\n")
        lines.append("|-----------|------------------|\n")
        for dash in schema.dashboards:
            sheet_names = ", ".join(s.name for s in dash.sheets) or "—"
            lines.append(f"| {dash.name} | {sheet_names} |\n")
        lines.append("\n")
    else:
        lines.append("_No dashboards available._\n\n")

    # Embedded datasources table
    lines.append("## Embedded Datasources\n")
    if schema.embedded_datasources:
        lines.append("| Datasource | Fields | Upstream Published Datasources |\n")
        lines.append("|------------|--------|--------------------------------|\n")
        for eds in schema.embedded_datasources:
            upstream = ", ".join(u.name for u in eds.upstream_datasources) or "—"
            lines.append(f"| {eds.name} | {len(eds.fields)} | {upstream} |\n")
        lines.append("\n")
    else:
        lines.append("_No embedded datasources available._\n\n")

    with md_path.open("w", encoding="utf-8") as fh:
        fh.writelines(lines)

    return [json_path, md_path]


def write_view_query_result(
    result: ViewQueryResult,
    view_name: str,
    output_dir: Path | None = None,
) -> list[Path]:
    """Write a ``ViewQueryResult`` to JSON and CSV files.

    File patterns:
      - JSON: ``view_query_{name}_{timestamp}.json``
      - CSV:  ``view_query_{name}_{timestamp}.csv``

    The CSV file contains the ``raw_csv`` text verbatim — the original
    response body from the Tableau REST API.

    Args:
        result: The view query result to persist.
        view_name: Name of the queried view, used in the filename.
        output_dir: Directory to write files into. Defaults to the skill's
            ``temp/`` directory.

    Returns:
        A list containing the JSON path and the CSV path.
    """
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generate_timestamp()
    safe_name = _sanitize_filename(view_name)

    json_path = output_dir / f"view_query_{safe_name}_{timestamp}.json"
    csv_path = output_dir / f"view_query_{safe_name}_{timestamp}.csv"

    # --- JSON ---
    data = result.model_dump(mode="json", exclude_none=True)
    data = _strip_credentials(data)

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # --- CSV --- write raw_csv verbatim
    with csv_path.open("w", encoding="utf-8") as fh:
        fh.write(result.raw_csv)

    return [json_path, csv_path]
