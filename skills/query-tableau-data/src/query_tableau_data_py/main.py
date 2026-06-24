"""Demo orchestrator for the query-tableau-data skill.

This module contains ``demo()`` and ``main()``, a hard-coded demo pipeline
that agents can execute to verify connectivity and explore available
datasources.

For real workflows, write your own script importing
:class:`~query_tableau_data_py.session.Session`. See
``docs/REPL.md`` for a step-by-step guide.

Usage::

    uv run python -m query_tableau_data_py.main
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.data import (
    write_catalog,
    write_query_result,
    write_schema,
)

TEMP_DIR = Path("temp")
from query_tableau_data_py.errors import TableauError
from query_tableau_data_py.models import (
    DatasourceSchema,
    DatasourceSummary,
    ExplorationResult,
    QueryField,
    QueryOptions,
    QueryRequest,
)
from query_tableau_data_py.session import Session

logger = logging.getLogger(__name__)

__all__ = ["demo", "main"]


# ---------------------------------------------------------------------------
# Demo helpers
# ---------------------------------------------------------------------------


def _keyword_filter(
    datasources: list[DatasourceSummary], intent: str
) -> list[DatasourceSummary]:
    keywords = intent.lower().split()
    return [
        ds
        for ds in datasources
        if any(
            kw in ds.name.lower() or kw in (ds.description or "").lower()
            for kw in keywords
        )
    ]


def _build_demo_query(schema: DatasourceSchema) -> QueryRequest:
    """Build a minimal demo query: first 3 dims + first 2 measures."""
    dims = [
        f.name
        for fg in schema.field_groups
        for f in fg.fields
        if f.column_class == "DIMENSION"
    ]
    measures = [
        f.name
        for fg in schema.field_groups
        for f in fg.fields
        if f.column_class == "MEASURE"
    ]

    fields = [QueryField(field_caption=c) for c in dims[:3]]
    fields += [QueryField(field_caption=c, function="SUM") for c in measures[:2]]

    return QueryRequest(
        datasource_luid=schema.luid,
        fields=fields,
        options=QueryOptions(return_format="OBJECTS"),
    )


# ---------------------------------------------------------------------------
# Demo orchestrator
# ---------------------------------------------------------------------------


def demo(config: SdkConfig, intent: str) -> ExplorationResult:
    """Run the full connectivity-check / demo pipeline.

    Steps:
    1. Authenticate.
    2. List datasources.
    3. Pick the first datasource matching *intent*.
    4. Introspect its schema.
    5. Run a minimal demo query.
    6. Persist results to ``temp/``.
    7. Print a concise summary to stdout.

    This is a **demo** — not a reusable orchestrator. For real workflows,
    write your own script using ``Session``. See ``docs/REPL.md``.
    """
    os.makedirs(TEMP_DIR, exist_ok=True)

    with Session(config) as session:
        # Step 1 — list datasources
        all_datasources = session.list_datasources()
        logger.info("Found %d datasource(s)", len(all_datasources))

        # Step 2 — keyword filter
        matching = _keyword_filter(all_datasources, intent)
        if not matching:
            matching = all_datasources

        selected = matching[0]
        logger.info("Selected datasource: %s", selected.name)

        # Step 3 — introspect
        schema = session.introspect(selected.luid)
        logger.info("Introspected %d field group(s)", len(schema.field_groups))

        # Step 4 — build and execute demo query
        query_request = _build_demo_query(schema)
        query_result = session.query(query_request)
        logger.info(
            "Query returned %d row(s) — complete=%s",
            query_result.metadata.row_count,
            query_result.metadata.is_complete,
        )

        # Step 5 — persist
        temp_files: list[Path] = []
        temp_files.append(write_catalog(all_datasources))
        temp_files.extend(write_schema(schema))
        temp_files.extend(
            write_query_result(
                query_result,
                datasource_name=schema.name,
                datasource_luid=schema.luid,
            )
        )

        # Step 6 — stdout summary
        dim_fields = [
            f.name
            for fg in schema.field_groups
            for f in fg.fields
            if f.column_class == "DIMENSION"
        ]
        measure_fields = [
            f.name
            for fg in schema.field_groups
            for f in fg.fields
            if f.column_class == "MEASURE"
        ]
        print(f"\n=== Exploration Summary ===")
        print(f"Datasources found: {len(all_datasources)}")
        print(f"Selected:          {selected.name}")
        print(f"Dimensions:        {', '.join(dim_fields[:3])}")
        print(f"Measures:          {', '.join(measure_fields[:2])}")
        print(f"Rows returned:     {query_result.metadata.row_count}")
        print(f"Complete:          {query_result.metadata.is_complete}")
        print(f"Temp files:        {len(temp_files)}")
        print("===========================\n")

        return ExplorationResult(
            selected_datasource=selected,
            datasource_schema=schema,
            query_result=query_result,
            temp_files=[str(p) for p in temp_files],
        )


def main():
    parser = argparse.ArgumentParser(
        description="Tableau datasource demo / connectivity check"
    )
    parser.add_argument(
        "--intent",
        default="explore tableau datasource",
        help="Keyword(s) to filter datasources (default: explore tableau datasource)",
    )
    args = parser.parse_args()

    config = SdkConfig()
    demo(config, args.intent)


if __name__ == "__main__":
    main()
