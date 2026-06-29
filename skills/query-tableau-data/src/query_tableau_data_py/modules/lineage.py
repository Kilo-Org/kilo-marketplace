"""Targeted per-asset GraphQL lineage queries (Tier 2 discovery).

Answers "how does this specific asset connect to others?" with two functions,
each fetching one node by luid — no pagination, one HTTP request per call.

Transport pattern (POSTMORTEM_2 §8.1 Fix A):
    conn.request(...)                   # TCP handshake opens the socket here
    if conn.sock is not None:
        conn.sock.settimeout(_GRAPHQL_TIMEOUT)   # applied AFTER request()
    resp = conn.getresponse()
    resp_body = resp.read()
    # finally: restore conn.sock.settimeout(config.timeout)

No REST fallback — lineage data is Metadata API only.
On any failure (HTTP error, socket.timeout, empty node list): raise CatalogUnavailableError.

See PROTOTYPE_3.md §4 for the full specification and GraphQL queries.
"""

from __future__ import annotations

import http.client
import json
import logging
import socket
from typing import Any

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.errors import CatalogUnavailableError
from query_tableau_data_py.models import (
    DatasourceLineage,
    WorkbookLineage,
)
from query_tableau_data_py.modules._parse_utils import (
    _parse_dashboard_refs,
    _parse_datasource_refs,
    _parse_embedded_datasource_refs,
    _parse_field_previews,
    _parse_owner_name,
    _parse_sheet_refs,
    _parse_upstream_database_refs,
    _parse_upstream_table_refs,
    _parse_workbook_refs,
)
from query_tableau_data_py.modules._rest_utils import (
    _get_base_path,
    _make_connection,
)
from query_tableau_data_py.modules.auth import AuthToken

logger = logging.getLogger(__name__)

# Per-request GraphQL timeout (applied after conn.request() opens the socket).
_GRAPHQL_TIMEOUT = 15.0

# ---------------------------------------------------------------------------
# GraphQL queries (verbatim from PROTOTYPE_3.md §4.2)
# ---------------------------------------------------------------------------

_DATASOURCE_LINEAGE_QUERY = """
query DatasourceLineage($luid: String!) {
  publishedDatasources(filter: { luid: $luid }) {
    name luid description projectName
    owner { name }
    isCertified hasExtracts
    downstreamWorkbooks { luid name projectName }
    downstreamSheets    { luid name }
    downstreamDashboards { luid name }
    upstreamTables      { name database { name } }
    upstreamDatabases   { name connectionType }
    fields(first: 30) {
      name __typename
      ... on ColumnField    { dataType role }
      ... on CalculatedField { dataType role }
    }
  }
}
"""

_WORKBOOK_LINEAGE_QUERY = """
query WorkbookLineage($luid: String!) {
  workbooks(filter: { luid: $luid }) {
    name luid description projectName
    owner { name }
    createdAt updatedAt
    sheets     { luid name index }
    dashboards { luid name index }
    embeddedDatasources {
      name
      upstreamDatasources { luid name }
    }
    upstreamDatasources { luid name }
    upstreamDatabases   { name connectionType }
  }
}
"""


# ---------------------------------------------------------------------------
# Internal helper — single GraphQL POST with correct timeout ordering
# ---------------------------------------------------------------------------


def _graphql_request(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """Send one GraphQL POST and return the parsed JSON body.

    Applies conn.sock.settimeout(_GRAPHQL_TIMEOUT) AFTER conn.request()
    (Fix A from POSTMORTEM_2 §8.3) and restores config.timeout in finally.

    Raises CatalogUnavailableError on HTTP error, socket.timeout, or parse failure.
    """
    base_path = _get_base_path(config)
    path = f"{base_path}/api/metadata/graphql"
    payload = {"query": query, "variables": variables}
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }

    try:
        conn.request("POST", path, body=body, headers=headers)
        # Socket now exists — apply GraphQL-specific timeout before reading response
        if conn.sock is not None:
            conn.sock.settimeout(_GRAPHQL_TIMEOUT)
        resp = conn.getresponse()
        resp_body = resp.read()
    except socket.timeout as exc:
        raise CatalogUnavailableError(
            tableau_error_message=f"GraphQL metadata request timed out: {exc}",
        ) from exc
    except (http.client.HTTPException, OSError) as exc:
        raise CatalogUnavailableError(
            tableau_error_message=f"GraphQL metadata request failed: {exc}",
        ) from exc
    finally:
        if conn.sock is not None:
            conn.sock.settimeout(config.timeout)

    if resp.status >= 400:
        raise CatalogUnavailableError(
            status_code=resp.status,
            response_body=resp_body,
            tableau_error_message=f"GraphQL metadata API returned HTTP {resp.status}",
        )

    try:
        return json.loads(resp_body.decode("utf-8"))
    except Exception as exc:
        raise CatalogUnavailableError(
            tableau_error_message=f"GraphQL metadata response could not be parsed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def datasource_lineage(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    luid: str,
) -> DatasourceLineage:
    """Fetch lineage for a single published datasource by luid.

    Sends one POST to the Metadata API GraphQL endpoint using the singular
    ``publishedDatasources(filter: { luid: $luid })`` form (not
    ``publishedDatasourcesConnection`` — no pagination needed).

    Args:
        config: SDK configuration.
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``HTTPSConnection`` for connection reuse.
        luid: The luid of the published datasource to look up.

    Returns:
        ``DatasourceLineage`` with downstream and upstream relationship data.

    Raises:
        CatalogUnavailableError: On HTTP error, socket.timeout, or when no
            datasource with the given luid exists.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        data = _graphql_request(
            config, token, conn, _DATASOURCE_LINEAGE_QUERY, {"luid": luid}
        )
    finally:
        if should_close:
            conn.close()

    nodes = data.get("data", {}).get("publishedDatasources", []) or []
    if not nodes:
        raise CatalogUnavailableError(
            tableau_error_message=f"datasource not found: {luid}",
        )

    node = nodes[0]

    return DatasourceLineage(
        luid=node.get("luid", ""),
        name=node.get("name", ""),
        description=node.get("description"),
        project_name=node.get("projectName"),
        owner_name=_parse_owner_name(node),
        is_certified=node.get("isCertified"),
        has_extracts=node.get("hasExtracts"),
        downstream_workbooks=_parse_workbook_refs(node.get("downstreamWorkbooks")),
        downstream_sheets=_parse_sheet_refs(node.get("downstreamSheets")),
        downstream_dashboards=_parse_dashboard_refs(node.get("downstreamDashboards")),
        upstream_tables=_parse_upstream_table_refs(node.get("upstreamTables")),
        upstream_databases=_parse_upstream_database_refs(node.get("upstreamDatabases")),
        field_preview=_parse_field_previews(node.get("fields"), limit=30),
    )


def workbook_lineage(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    luid: str,
) -> WorkbookLineage:
    """Fetch lineage for a single workbook by luid.

    Sends one POST to the Metadata API GraphQL endpoint using the singular
    ``workbooks(filter: { luid: $luid })`` form (not ``workbooksConnection``
    — no pagination needed).

    Args:
        config: SDK configuration.
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``HTTPSConnection`` for connection reuse.
        luid: The luid of the workbook to look up.

    Returns:
        ``WorkbookLineage`` with sheets, dashboards, embedded and upstream datasource data.

    Raises:
        CatalogUnavailableError: On HTTP error, socket.timeout, or when no
            workbook with the given luid exists.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        data = _graphql_request(
            config, token, conn, _WORKBOOK_LINEAGE_QUERY, {"luid": luid}
        )
    finally:
        if should_close:
            conn.close()

    nodes = data.get("data", {}).get("workbooks", []) or []
    if not nodes:
        raise CatalogUnavailableError(
            tableau_error_message=f"workbook not found: {luid}",
        )

    node = nodes[0]

    return WorkbookLineage(
        luid=node.get("luid", ""),
        name=node.get("name", ""),
        description=node.get("description"),
        project_name=node.get("projectName"),
        owner_name=_parse_owner_name(node),
        created_at=node.get("createdAt"),
        updated_at=node.get("updatedAt"),
        sheets=_parse_sheet_refs(node.get("sheets")),
        dashboards=_parse_dashboard_refs(node.get("dashboards")),
        embedded_datasources=_parse_embedded_datasource_refs(
            node.get("embeddedDatasources")
        ),
        upstream_datasources=_parse_datasource_refs(node.get("upstreamDatasources")),
        upstream_databases=_parse_upstream_database_refs(node.get("upstreamDatabases")),
    )
