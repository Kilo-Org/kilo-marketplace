"""Shared GraphQL node-to-model helpers used by catalog.py and lineage.py.

Internal module — underscore prefix signals it is not part of the public API.
Do not import this from outside the modules/ package.

Every helper filters out ``None`` elements from the input list before
constructing model instances.  This guards against GraphQL responses that
contain null entries in relationship arrays (e.g., when a downstream asset
has been deleted but its dangling reference remains in the metadata graph).
"""

from __future__ import annotations

from query_tableau_data_py.models import (
    DashboardRef,
    DatasourceRef,
    EmbeddedDatasourceRef,
    FieldPreview,
    SheetRef,
    UpstreamDatabaseRef,
    UpstreamTableRef,
    WorkbookRef,
)


def _parse_workbook_refs(raw: list | None) -> list[WorkbookRef]:
    """Parse downstream workbook references from GraphQL node arrays."""
    return [
        WorkbookRef(luid=w.get("luid", ""), name=w.get("name", ""))
        for w in (raw or [])
        if w
    ]


def _parse_sheet_refs(raw: list | None) -> list[SheetRef]:
    """Parse sheet references (with optional index) from GraphQL node arrays."""
    return [
        SheetRef(
            luid=s.get("luid", ""),
            name=s.get("name", ""),
            index=s.get("index"),
        )
        for s in (raw or [])
        if s
    ]


def _parse_dashboard_refs(raw: list | None) -> list[DashboardRef]:
    """Parse dashboard references (with optional index) from GraphQL node arrays."""
    return [
        DashboardRef(
            luid=d.get("luid", ""),
            name=d.get("name", ""),
            index=d.get("index"),
        )
        for d in (raw or [])
        if d
    ]


def _parse_datasource_refs(raw: list | None) -> list[DatasourceRef]:
    """Parse published datasource references from GraphQL node arrays."""
    return [
        DatasourceRef(luid=u.get("luid", ""), name=u.get("name", ""))
        for u in (raw or [])
        if u
    ]


def _parse_embedded_datasource_refs(
    raw: list | None,
) -> list[EmbeddedDatasourceRef]:
    """Parse embedded datasource references with nested upstream links."""
    return [
        EmbeddedDatasourceRef(
            name=eds.get("name", ""),
            upstream_datasources=_parse_datasource_refs(eds.get("upstreamDatasources")),
        )
        for eds in (raw or [])
        if eds
    ]


def _parse_field_previews(
    raw: list | None, *, limit: int | None = None
) -> list[FieldPreview]:
    """Parse field preview entries from GraphQL node arrays.

    Args:
        raw: Raw list of field dicts from GraphQL response.
        limit: Optional cap on number of fields returned (e.g., 30 for lineage).
    """
    items = raw or []
    if limit is not None:
        items = items[:limit]
    return [
        FieldPreview(
            name=f.get("name", ""),
            data_type=f.get("dataType", ""),
            role=f.get("role", ""),
        )
        for f in items
        if f
    ]


def _parse_upstream_table_refs(raw: list | None) -> list[UpstreamTableRef]:
    """Parse upstream table references from GraphQL node arrays."""
    return [
        UpstreamTableRef(
            name=t.get("name", ""),
            database_name=(t.get("database") or {}).get("name"),
        )
        for t in (raw or [])
        if t
    ]


def _parse_upstream_database_refs(raw: list | None) -> list[UpstreamDatabaseRef]:
    """Parse upstream database references from GraphQL node arrays."""
    return [
        UpstreamDatabaseRef(
            name=db.get("name", ""),
            connection_type=db.get("connectionType"),
        )
        for db in (raw or [])
        if db
    ]


def _parse_owner_name(node: dict) -> str | None:
    """Extract owner name from a GraphQL node, guarding against null owner."""
    owner = node.get("owner") or {}
    return owner.get("name") if isinstance(owner, dict) else None
