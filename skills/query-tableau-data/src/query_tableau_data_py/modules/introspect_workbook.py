"""Deep-dive workbook introspection via the Tableau Metadata API (GraphQL).

Retrieves comprehensive structure for a single workbook LUID:
- Sheets with field instances (sheetFieldInstances) and worksheet calculated fields
- Dashboards with component sheet references
- Embedded datasources with fields and upstream published datasource links
- Workbook-level parameters

There is **no REST fallback** — GraphQL is the only source for field-level
workbook detail.  Any failure raises ``CatalogUnavailableError``.

Sync transport using http.client (stdlib). No external HTTP dependencies.
Pure functional API — no temp I/O, no stdout printing.
"""

from __future__ import annotations

import http.client
import json
import logging
import socket
import ssl
from typing import Any
from urllib.parse import urlparse

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.errors import CatalogUnavailableError
from query_tableau_data_py.models import (
    DashboardDetail,
    DashboardRef,
    DatasourceRef,
    EmbeddedDatasourceDetail,
    SheetDetail,
    SheetFieldInstance,
    SheetRef,
    WorkbookSchema,
)
from query_tableau_data_py.modules.auth import AuthToken

logger = logging.getLogger(__name__)

_GRAPHQL_PATH = "/api/metadata/graphql"

_GRAPHQL_INTROSPECT_WORKBOOK_QUERY = """
query IntrospectWorkbook($luid: String!) {
  workbooks(filter: { luid: $luid }) {
    name
    luid
    description
    projectName
    owner { name }
    createdAt
    updatedAt
    sheets {
      name
      luid
      index
      sheetFieldInstances {
        name
        ... on ColumnField { dataType role }
        ... on CalculatedField { dataType role formula }
        # DatasourceField intentionally omitted — it does not implement
        # dataType/role on the Field interface; only name is available.
      }
      worksheetFields {
        name
        formula
        dataType
        role
      }
      containedInDashboards {
        name
        luid
      }
    }
    dashboards {
      name
      luid
      index
      sheets {
        name
        luid
      }
    }
    embeddedDatasources {
      name
      hasExtracts
      fields {
        name
        ... on ColumnField { dataType role }
        ... on CalculatedField { dataType role formula }
      }
      upstreamDatasources {
        luid
        name
      }
    }
    parameters {
      name
      # Parameter.dataType does not exist in the Metadata API schema —
      # inline fragments on Parameter are invalid. Only name is available.
    }
  }
}
"""


def _make_connection(config: SdkConfig) -> http.client.HTTPSConnection:
    """Create an HTTPSConnection from SDK config."""
    parsed = urlparse(config.base_url)
    host = parsed.hostname
    port = parsed.port or 443

    if config.ssl_verify:
        ssl_context = ssl.create_default_context()
    else:
        ssl_context = ssl._create_unverified_context()

    return http.client.HTTPSConnection(
        host, port, context=ssl_context, timeout=config.timeout
    )


def _get_base_path(config: SdkConfig) -> str:
    """Extract the base path from config.base_url (for subpath installs)."""
    parsed = urlparse(config.base_url)
    return parsed.path.rstrip("/")


# ── Parsing helpers ──────────────────────────────────────────────────────────


def _parse_field_instance(raw: dict[str, Any]) -> SheetFieldInstance:
    """Map a raw GraphQL field node to SheetFieldInstance.

    ``formula`` is only present on CalculatedField nodes — absent on
    ColumnField nodes, so raw.get returns None.

    For DatasourceField nodes in sheetFieldInstances, only ``name`` is
    available from the base Field interface; ``data_type`` and ``role``
    will be None because no inline fragment is requested for that type
    (requesting ``... on DatasourceField { dataType role }`` is invalid
    GraphQL against the Tableau Metadata API schema).

    For embedded datasource fields, only ColumnField and CalculatedField
    fragments are requested. Any DatasourceField entries will carry name
    only, with data_type and role as None.
    """
    return SheetFieldInstance(
        name=raw.get("name", ""),
        data_type=raw.get("dataType"),
        role=raw.get("role"),
        formula=raw.get("formula"),
    )


def _parse_sheet(raw: dict[str, Any]) -> SheetDetail:
    """Parse a raw GraphQL sheet node into SheetDetail."""
    field_instances = [
        _parse_field_instance(f) for f in (raw.get("sheetFieldInstances") or [])
    ]
    worksheet_fields = [
        _parse_field_instance(f) for f in (raw.get("worksheetFields") or [])
    ]
    contained_in_dashboards = [
        DashboardRef(luid=d.get("luid", ""), name=d.get("name", ""))
        for d in (raw.get("containedInDashboards") or [])
    ]
    return SheetDetail(
        luid=raw.get("luid", ""),
        name=raw.get("name", ""),
        index=raw.get("index"),
        field_instances=field_instances,
        worksheet_fields=worksheet_fields,
        contained_in_dashboards=contained_in_dashboards,
    )


def _parse_dashboard(raw: dict[str, Any]) -> DashboardDetail:
    """Parse a raw GraphQL dashboard node into DashboardDetail."""
    sheets = [
        SheetRef(luid=s.get("luid", ""), name=s.get("name", ""))
        for s in (raw.get("sheets") or [])
    ]
    return DashboardDetail(
        luid=raw.get("luid", ""),
        name=raw.get("name", ""),
        index=raw.get("index"),
        sheets=sheets,
    )


def _parse_embedded_datasource(raw: dict[str, Any]) -> EmbeddedDatasourceDetail:
    """Parse a raw GraphQL embeddedDatasource node into EmbeddedDatasourceDetail."""
    fields = [_parse_field_instance(f) for f in (raw.get("fields") or [])]
    upstream = [
        DatasourceRef(luid=u.get("luid", ""), name=u.get("name", ""))
        for u in (raw.get("upstreamDatasources") or [])
    ]
    return EmbeddedDatasourceDetail(
        name=raw.get("name", ""),
        has_extracts=raw.get("hasExtracts"),
        fields=fields,
        upstream_datasources=upstream,
    )


def _parse_workbook_node(node: dict[str, Any]) -> WorkbookSchema:
    """Parse a single workbook node from the GraphQL response into WorkbookSchema."""
    owner = node.get("owner") or {}
    sheets = [_parse_sheet(s) for s in (node.get("sheets") or [])]
    dashboards = [_parse_dashboard(d) for d in (node.get("dashboards") or [])]
    embedded = [
        _parse_embedded_datasource(e) for e in (node.get("embeddedDatasources") or [])
    ]
    parameters = [
        dict(p) for p in (node.get("parameters") or []) if isinstance(p, dict)
    ]
    return WorkbookSchema(
        luid=node.get("luid", ""),
        name=node.get("name", ""),
        description=node.get("description"),
        project_name=node.get("projectName"),
        owner_name=owner.get("name") if isinstance(owner, dict) else None,
        created_at=node.get("createdAt"),
        updated_at=node.get("updatedAt"),
        sheets=sheets,
        dashboards=dashboards,
        embedded_datasources=embedded,
        parameters=parameters,
    )


# ── Public API ───────────────────────────────────────────────────────────────


def introspect_workbook(
    config: SdkConfig,
    token: AuthToken,
    workbook_luid: str,
    conn: http.client.HTTPSConnection | None = None,
) -> WorkbookSchema:
    """Retrieve comprehensive structure for a single Tableau workbook.

    Uses the Metadata API GraphQL ``workbooks`` query with inline fragments
    to fetch sheet field instances, worksheet calculated fields, dashboard
    composition, embedded datasource details, and workbook-level parameters.

    There is **no REST fallback**.  Any GraphQL failure raises
    ``CatalogUnavailableError``.

    Args:
        config: SDK configuration (server URL, API versions, etc.).
        token: Active ``AuthToken`` from ``auth.sign_in``.
        workbook_luid: LUID of the workbook to introspect.
        conn: Optional ``http.client.HTTPSConnection`` for connection reuse.

    Returns:
        ``WorkbookSchema`` with sheets, dashboards, embedded datasources,
        and parameters.

    Raises:
        CatalogUnavailableError: When the GraphQL Metadata API is
            unavailable, returns an error, or the workbook is not found.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    base_path = _get_base_path(config)
    path = f"{base_path}{_GRAPHQL_PATH}"
    payload = {
        "query": _GRAPHQL_INTROSPECT_WORKBOOK_QUERY,
        "variables": {"luid": workbook_luid},
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }

    try:
        try:
            conn.request("POST", path, body=body, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read()
        except socket.timeout as exc:
            raise CatalogUnavailableError(
                status_code=None,
                response_body=b"",
                tableau_error_code=None,
                tableau_error_message=(f"GraphQL introspect_workbook timed out: {exc}"),
            ) from exc
        except (http.client.HTTPException, OSError) as exc:
            raise CatalogUnavailableError(
                status_code=None,
                response_body=b"",
                tableau_error_code=None,
                tableau_error_message=(
                    f"GraphQL introspect_workbook transport error: {exc}"
                ),
            ) from exc

        if resp.status >= 400:
            raise CatalogUnavailableError(
                status_code=resp.status,
                response_body=resp_body,
                response_headers=dict(resp.getheaders()),
                tableau_error_code=None,
                tableau_error_message=(
                    f"GraphQL introspect_workbook returned HTTP {resp.status}"
                ),
            )

        try:
            data = json.loads(resp_body.decode("utf-8"))
        except Exception as exc:
            raise CatalogUnavailableError(
                status_code=resp.status,
                response_body=resp_body,
                tableau_error_code=None,
                tableau_error_message=(
                    f"GraphQL introspect_workbook response was not valid JSON: {exc}"
                ),
            ) from exc

        top_data = data.get("data")
        if top_data is None:
            errors = data.get("errors", [])
            raise CatalogUnavailableError(
                status_code=None,
                response_body=b"",
                tableau_error_code=None,
                tableau_error_message=(
                    f"GraphQL introspect_workbook returned null data "
                    f"(errors={errors!r})"
                ),
            )

        workbooks = top_data.get("workbooks", [])
        if not workbooks:
            raise CatalogUnavailableError(
                status_code=None,
                response_body=b"",
                tableau_error_code=None,
                tableau_error_message=(
                    f"Workbook with luid={workbook_luid!r} not found in Metadata API"
                ),
            )

        return _parse_workbook_node(workbooks[0])

    finally:
        if should_close:
            conn.close()
