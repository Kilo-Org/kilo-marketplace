"""Catalog discovery (datasources, workbooks, views) via Metadata API (GraphQL)
with REST fallback.

Sync transport using http.client (stdlib). No external HTTP dependencies.
Pure functional API — no temp I/O, no stdout printing.
"""

from __future__ import annotations

import http.client
import json
import logging
import socket
import time
from typing import Any
from urllib.parse import urlencode

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.errors import CatalogUnavailableError
from query_tableau_data_py.models import (
    DatasourceSummary,
    ViewSummary,
    WorkbookSummary,
)
from query_tableau_data_py.modules._parse_utils import (
    _parse_dashboard_refs,
    _parse_embedded_datasource_refs,
    _parse_field_previews,
    _parse_owner_name,
    _parse_sheet_refs,
    _parse_workbook_refs,
)
from query_tableau_data_py.modules.auth import AuthToken
from query_tableau_data_py.modules._rest_utils import (
    _make_connection,
    _get_base_path,
    _clamp_page_size,
    _build_rest_filter,
)

logger = logging.getLogger(__name__)

# GraphQL catalog queries can be slow on large sites.  Use a short per-request
# timeout so the automatic REST fallback triggers promptly.
_GRAPHQL_TIMEOUT = 15.0

# Wall-clock budget for the entire GraphQL pagination loop.  socket.settimeout()
# is a per-recv() timeout, not a total-request timeout.  On large sites each page
# may complete within _GRAPHQL_TIMEOUT while the full crawl still takes minutes.
# When this limit is exceeded the loop abandons GraphQL and returns None so the
# caller falls back to the REST API.
_GRAPHQL_TOTAL_TIMEOUT = 60.0

# GraphQL query used for datasource discovery.
# Offset-based pagination (first + offset) is used for simplicity and
# forward-compatibility with cursor-based paging.
_GRAPHQL_QUERY = """
query DiscoverDatasources($first: Int!, $offset: Int) {
  publishedDatasourcesConnection(first: $first, offset: $offset) {
    nodes {
      name
      luid
      description
      projectName
      owner {
        name
      }
      hasExtracts
      isCertified
      downstreamWorkbooks {
        luid
        name
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


def _build_graphql_filter(
    filter_name: str | None,
    filter_project: str | None,
) -> dict[str, str] | None:
    """Build the GraphQL filter object from caller-supplied filters."""
    filt: dict[str, str] = {}
    if filter_name is not None:
        filt["name"] = filter_name
    if filter_project is not None:
        filt["projectName"] = filter_project
    return filt if filt else None


def _parse_graphql_nodes(data: dict[str, Any]) -> list[DatasourceSummary]:
    """Normalize a GraphQL ``publishedDatasourcesConnection.nodes`` list."""
    nodes = (
        data.get("data", {}).get("publishedDatasourcesConnection", {}).get("nodes", [])
    )
    results: list[DatasourceSummary] = []
    for node in nodes:
        tags = [
            t.get("label", "") for t in node.get("tags", []) if t and t.get("label")
        ]
        results.append(
            DatasourceSummary(
                luid=node.get("luid", ""),
                name=node.get("name", ""),
                description=node.get("description"),
                project_name=node.get("projectName"),
                owner_name=_parse_owner_name(node),
                has_extracts=node.get("hasExtracts"),
                is_certified=node.get("isCertified"),
                tags=tags,
                field_preview=_parse_field_previews(node.get("fields")),
                downstream_workbooks=_parse_workbook_refs(
                    node.get("downstreamWorkbooks")
                ),
            )
        )
    return results


def _parse_rest_datasources(data: dict[str, Any]) -> list[DatasourceSummary]:
    """Normalize a REST ``datasources.datasource`` list."""
    raw = data.get("datasources", {}).get("datasource", [])
    # Handle case where REST returns a single object instead of a list
    if isinstance(raw, dict):
        raw = [raw]
    results: list[DatasourceSummary] = []
    for item in raw:
        project = item.get("project") or {}
        owner = item.get("owner") or {}
        # REST response shape: tags: { tag: [{ label: "..." }] }
        tags_raw = item.get("tags", {}) or {}
        tag_list = tags_raw.get("tag", []) if isinstance(tags_raw, dict) else []
        tags = [t.get("label", "") for t in tag_list if t.get("label")]

        # REST may return booleans as strings ("true"/"false")
        has_extracts = item.get("hasExtracts")
        if isinstance(has_extracts, str):
            has_extracts = has_extracts.lower() == "true"
        is_certified = item.get("isCertified")
        if isinstance(is_certified, str):
            is_certified = is_certified.lower() == "true"

        results.append(
            DatasourceSummary(
                luid=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description"),
                project_name=project.get("name") if isinstance(project, dict) else None,
                owner_name=owner.get("name") if isinstance(owner, dict) else None,
                has_extracts=has_extracts,
                is_certified=is_certified,
                tags=tags,
                field_preview=[],
            )
        )
    return results


def _graphql_list_datasources(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[DatasourceSummary] | None:
    """Attempt datasource discovery via the Metadata API (GraphQL).

    Returns ``None`` when the response indicates the caller should fall back
    to the REST API (403/503/timeout).

    Raises ``CatalogUnavailableError`` on unrecoverable GraphQL errors.
    """
    base_path = _get_base_path(config)
    path = f"{base_path}/api/metadata/graphql"
    headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
    }
    page_size = _clamp_page_size(page_size)
    filt = _build_graphql_filter(filter_name, filter_project)
    offset = 0
    results: list[DatasourceSummary] = []

    _wall_start = time.monotonic()

    while True:
        if time.monotonic() - _wall_start > _GRAPHQL_TOTAL_TIMEOUT:
            logger.warning(
                "GraphQL publishedDatasourcesConnection pagination exceeded %.0fs "
                "wall-clock limit; falling back to REST (%d results collected so far).",
                _GRAPHQL_TOTAL_TIMEOUT,
                len(results),
            )
            return None  # triggers REST fallback in calling function

        variables: dict[str, Any] = {"first": page_size, "offset": offset}
        if filt is not None:
            variables["filter"] = filt

        payload = {"query": _GRAPHQL_QUERY, "variables": variables}
        body = json.dumps(payload).encode("utf-8")
        req_headers = {
            **headers,
            "Content-Length": str(len(body)),
        }

        try:
            conn.request("POST", path, body=body, headers=req_headers)
            # Socket now exists — apply GraphQL-specific timeout before reading response
            if conn.sock is not None:
                conn.sock.settimeout(_GRAPHQL_TIMEOUT)
            resp = conn.getresponse()
            resp_body = resp.read()
        except socket.timeout:
            logger.warning("GraphQL Metadata API timed out; falling back to REST.")
            return None
        except (http.client.HTTPException, OSError):
            logger.warning("GraphQL Metadata API HTTP error; falling back to REST.")
            return None
        finally:
            # Restore default timeout
            if conn.sock is not None:
                conn.sock.settimeout(config.timeout)

        if resp.status in (403, 503):
            logger.warning(
                "GraphQL Metadata API returned %d; falling back to REST.",
                resp.status,
            )
            return None

        if resp.status >= 400:
            logger.warning(
                "GraphQL Metadata API returned %d; falling back to REST.",
                resp.status,
            )
            return None

        try:
            data = json.loads(resp_body.decode("utf-8"))
        except Exception:
            logger.warning(
                "GraphQL response could not be parsed; falling back to REST."
            )
            return None

        # GraphQL may return { "data": null, "errors": [...] } on failure
        top_data = data.get("data")
        if top_data is None:
            errors = data.get("errors", [])
            logger.warning(
                "GraphQL returned null data (errors=%r); falling back to REST.",
                errors,
            )
            return None

        page_results = _parse_graphql_nodes(data)
        results.extend(page_results)
        logger.debug(
            "GraphQL %s: page %d \u2014 %d items this page, %d total (%.1fs elapsed)",
            "publishedDatasourcesConnection",
            offset // page_size + 1,
            len(page_results),
            len(results),
            time.monotonic() - _wall_start,
        )

        if limit is not None and len(results) >= limit:
            results = results[:limit]
            break

        page_info = (
            data.get("data", {})
            .get("publishedDatasourcesConnection", {})
            .get("pageInfo", {})
        )
        if not page_info.get("hasNextPage", False):
            break

        offset += page_size

    return results


def _rest_list_datasources(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[DatasourceSummary]:
    """Attempt datasource discovery via the REST API.

    Raises ``CatalogUnavailableError`` on any non-2xx response.
    """
    base_path = _get_base_path(config)
    base_url_path = (
        f"{base_path}/api/{config.api_version}/sites/{token.site_id}/datasources"
    )
    headers = {
        "X-Tableau-Auth": token.token,
        "Accept": "application/json",
    }
    page_size = _clamp_page_size(page_size)
    page_number = 1
    results: list[DatasourceSummary] = []
    rest_filter = _build_rest_filter(filter_name, filter_project)

    while True:
        params: dict[str, Any] = {
            "pageSize": page_size,
            "pageNumber": page_number,
        }
        if rest_filter is not None:
            params["filter"] = rest_filter

        path = f"{base_url_path}?{urlencode(params)}"
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            message = None
            try:
                data = json.loads(resp_body.decode("utf-8"))
                if isinstance(data, dict):
                    error = data.get("error", {})
                    if isinstance(error, dict):
                        message = error.get("message")
                    else:
                        message = str(error)
            except Exception:
                # Not valid JSON — use the raw text body as the message
                message = resp_body.decode("utf-8", errors="replace") or None
            raise CatalogUnavailableError(
                status_code=resp.status,
                response_body=resp_body,
                response_headers=dict(resp.getheaders()),
                tableau_error_code=None,
                tableau_error_message=message or f"HTTP {resp.status}",
            )

        data = json.loads(resp_body.decode("utf-8"))
        page_results = _parse_rest_datasources(data)
        results.extend(page_results)

        if limit is not None and len(results) >= limit:
            results = results[:limit]
            break

        pagination = data.get("pagination", {})
        total_available = int(pagination.get("totalAvailable", 0))
        if total_available == 0:
            break
        if page_number * page_size >= total_available:
            break

        page_number += 1

    return results


def list_datasources(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[DatasourceSummary]:
    """Discover published Tableau datasources.

    Primary path uses the GraphQL Metadata API. On 403/503/timeout, it
    automatically falls back to the REST ``list-datasources`` endpoint.
    If both paths fail, raises ``CatalogUnavailableError``.

    Args:
        config: SDK configuration (server URL, API versions, etc.).
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``http.client.HTTPSConnection`` for connection reuse.
        filter_name: Optional name filter (exact match via ``eq``).
        filter_project: Optional project-name filter (exact match via ``eq``).
        page_size: Items per page (default 1,000; clamped to 1,000 max).
        limit: Maximum total items to return.

    Returns:
        List of ``DatasourceSummary`` objects. Empty list if the catalog
        contains no published datasources.

    Raises:
        CatalogUnavailableError: When both GraphQL and REST APIs fail.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        # Primary: GraphQL Metadata API
        gql_results = _graphql_list_datasources(
            config,
            token,
            conn,
            filter_name=filter_name,
            filter_project=filter_project,
            page_size=page_size,
            limit=limit,
        )

        if gql_results is not None:
            return gql_results

        # Fallback: REST API
        return _rest_list_datasources(
            config,
            token,
            conn,
            filter_name=filter_name,
            filter_project=filter_project,
            page_size=page_size,
            limit=limit,
        )
    finally:
        if should_close:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Workbook catalog discovery
# ─────────────────────────────────────────────────────────────────────────────

_GRAPHQL_WORKBOOKS_QUERY = """
query DiscoverWorkbooks($first: Int!, $offset: Int, $filter: Workbook_Filter) {
  workbooksConnection(first: $first, offset: $offset, filter: $filter) {
    nodes {
      name
      luid
      description
      projectName
      owner {
        name
      }
      createdAt
      updatedAt
      sheets {
        name
        luid
        index
      }
      dashboards {
        name
        luid
        index
      }
      embeddedDatasources {
        name
        upstreamDatasources {
          luid
          name
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


def _parse_graphql_workbook_nodes(data: dict[str, Any]) -> list[WorkbookSummary]:
    """Normalise a GraphQL ``workbooksConnection.nodes`` list."""
    nodes = data.get("data", {}).get("workbooksConnection", {}).get("nodes", [])
    results: list[WorkbookSummary] = []
    for node in nodes:
        results.append(
            WorkbookSummary(
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
            )
        )
    return results


def _parse_rest_workbooks(data: dict[str, Any]) -> list[WorkbookSummary]:
    """Normalise a REST ``workbooks.workbook`` list."""
    raw = data.get("workbooks", {}).get("workbook", [])
    if isinstance(raw, dict):
        raw = [raw]
    results: list[WorkbookSummary] = []
    for item in raw:
        project = item.get("project") or {}
        owner = item.get("owner") or {}
        results.append(
            WorkbookSummary(
                luid=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description"),
                project_name=project.get("name") if isinstance(project, dict) else None,
                owner_name=owner.get("name") if isinstance(owner, dict) else None,
                created_at=item.get("createdAt"),
                updated_at=item.get("updatedAt"),
                # REST does not provide nested detail
                sheets=[],
                dashboards=[],
                embedded_datasources=[],
            )
        )
    return results


def _graphql_list_workbooks(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[WorkbookSummary] | None:
    """Attempt workbook discovery via the Metadata API (GraphQL).

    Returns ``None`` when the response signals a REST fallback is needed
    (403/503/timeout).
    """
    base_path = _get_base_path(config)
    path = f"{base_path}/api/metadata/graphql"
    headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
    }
    page_size = _clamp_page_size(page_size)
    filt = _build_graphql_filter(filter_name, filter_project)
    offset = 0
    results: list[WorkbookSummary] = []

    _wall_start = time.monotonic()

    while True:
        if time.monotonic() - _wall_start > _GRAPHQL_TOTAL_TIMEOUT:
            logger.warning(
                "GraphQL workbooksConnection pagination exceeded %.0fs "
                "wall-clock limit; falling back to REST (%d results collected so far).",
                _GRAPHQL_TOTAL_TIMEOUT,
                len(results),
            )
            return None  # triggers REST fallback in calling function

        variables: dict[str, Any] = {"first": page_size, "offset": offset}
        if filt is not None:
            variables["filter"] = filt

        payload = {"query": _GRAPHQL_WORKBOOKS_QUERY, "variables": variables}
        body = json.dumps(payload).encode("utf-8")
        req_headers = {
            **headers,
            "Content-Length": str(len(body)),
        }

        try:
            conn.request("POST", path, body=body, headers=req_headers)
            # Socket now exists — apply GraphQL-specific timeout before reading response
            if conn.sock is not None:
                conn.sock.settimeout(_GRAPHQL_TIMEOUT)
            resp = conn.getresponse()
            resp_body = resp.read()
        except socket.timeout:
            logger.warning("GraphQL workbooks timed out; falling back to REST.")
            return None
        except (http.client.HTTPException, OSError):
            logger.warning("GraphQL workbooks HTTP error; falling back to REST.")
            return None
        finally:
            if conn.sock is not None:
                conn.sock.settimeout(config.timeout)

        if resp.status in (403, 503):
            logger.warning(
                "GraphQL workbooks returned %d; falling back to REST.",
                resp.status,
            )
            return None

        if resp.status >= 400:
            logger.warning(
                "GraphQL workbooks returned %d; falling back to REST.",
                resp.status,
            )
            return None

        try:
            data = json.loads(resp_body.decode("utf-8"))
        except Exception:
            logger.warning(
                "GraphQL workbooks response unparseable; falling back to REST."
            )
            return None

        top_data = data.get("data")
        if top_data is None:
            errors = data.get("errors", [])
            logger.warning(
                "GraphQL workbooks returned null data (errors=%r); falling back to REST.",
                errors,
            )
            return None

        page_results = _parse_graphql_workbook_nodes(data)
        results.extend(page_results)
        logger.debug(
            "GraphQL %s: page %d \u2014 %d items this page, %d total (%.1fs elapsed)",
            "workbooksConnection",
            offset // page_size + 1,
            len(page_results),
            len(results),
            time.monotonic() - _wall_start,
        )

        if limit is not None and len(results) >= limit:
            results = results[:limit]
            break

        page_info = (
            data.get("data", {}).get("workbooksConnection", {}).get("pageInfo", {})
        )
        if not page_info.get("hasNextPage", False):
            break

        offset += page_size

    return results


def _rest_list_workbooks(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[WorkbookSummary]:
    """Attempt workbook discovery via the REST API.

    Raises ``CatalogUnavailableError`` on any non-2xx response.
    """
    base_path = _get_base_path(config)
    base_url_path = (
        f"{base_path}/api/{config.api_version}/sites/{token.site_id}/workbooks"
    )
    headers = {
        "X-Tableau-Auth": token.token,
        "Accept": "application/json",
    }
    page_size = _clamp_page_size(page_size)
    page_number = 1
    results: list[WorkbookSummary] = []
    rest_filter = _build_rest_filter(filter_name, filter_project)

    while True:
        params: dict[str, Any] = {
            "pageSize": page_size,
            "pageNumber": page_number,
        }
        if rest_filter is not None:
            params["filter"] = rest_filter

        path = f"{base_url_path}?{urlencode(params)}"
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            message = None
            try:
                resp_data = json.loads(resp_body.decode("utf-8"))
                if isinstance(resp_data, dict):
                    error = resp_data.get("error", {})
                    message = (
                        error.get("message") if isinstance(error, dict) else str(error)
                    )
            except Exception:
                message = resp_body.decode("utf-8", errors="replace") or None
            raise CatalogUnavailableError(
                status_code=resp.status,
                response_body=resp_body,
                response_headers=dict(resp.getheaders()),
                tableau_error_code=None,
                tableau_error_message=message or f"HTTP {resp.status}",
            )

        data = json.loads(resp_body.decode("utf-8"))
        page_results = _parse_rest_workbooks(data)
        results.extend(page_results)

        if limit is not None and len(results) >= limit:
            results = results[:limit]
            break

        pagination = data.get("pagination", {})
        total_available = int(pagination.get("totalAvailable", 0))
        if total_available == 0:
            break
        if page_number * page_size >= total_available:
            break

        page_number += 1

    return results


def list_workbooks(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[WorkbookSummary]:
    """Discover Tableau workbooks on a site.

    Primary path uses the GraphQL Metadata API (``workbooksConnection``),
    which returns rich nested detail: sheets, dashboards, and embedded
    datasource references.  On 403/503/timeout, falls back to the REST
    ``Query Workbooks for Site`` endpoint.  REST results have empty
    ``sheets``, ``dashboards``, and ``embedded_datasources`` lists.

    Args:
        config: SDK configuration (server URL, API versions, etc.).
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``http.client.HTTPSConnection`` for connection reuse.
        filter_name: Optional name filter (exact match).
        filter_project: Optional project-name filter (exact match).
        page_size: Items per page (default 1,000; clamped to 1,000 max).
        limit: Maximum total items to return.

    Returns:
        List of ``WorkbookSummary`` objects.

    Raises:
        CatalogUnavailableError: When both GraphQL and REST APIs fail.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        gql_results = _graphql_list_workbooks(
            config,
            token,
            conn,
            filter_name=filter_name,
            filter_project=filter_project,
            page_size=page_size,
            limit=limit,
        )

        if gql_results is not None:
            return gql_results

        return _rest_list_workbooks(
            config,
            token,
            conn,
            filter_name=filter_name,
            filter_project=filter_project,
            page_size=page_size,
            limit=limit,
        )
    finally:
        if should_close:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# View catalog discovery  (sheets + dashboards)
# ─────────────────────────────────────────────────────────────────────────────

_GRAPHQL_SHEETS_QUERY = """
query DiscoverSheets($first: Int!, $offset: Int, $filter: Sheet_Filter) {
  sheetsConnection(first: $first, offset: $offset, filter: $filter) {
    nodes {
      name
      luid
      index
      path
      createdAt
      updatedAt
      workbook {
        luid
        name
      }
      containedInDashboards {
        name
        luid
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

_GRAPHQL_DASHBOARDS_QUERY = """
query DiscoverDashboards($first: Int!, $offset: Int, $filter: Dashboard_Filter) {
  dashboardsConnection(first: $first, offset: $offset, filter: $filter) {
    nodes {
      name
      luid
      index
      path
      createdAt
      updatedAt
      workbook {
        luid
        name
      }
      sheets {
        name
        luid
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


def _build_view_graphql_filter(filter_name: str | None) -> dict[str, str] | None:
    """Build a GraphQL filter dict for views (name only)."""
    if filter_name is not None:
        return {"name": filter_name}
    return None


def _build_view_rest_filter(filter_name: str | None) -> str | None:
    """Build a REST filter expression for views (name only)."""
    if filter_name is not None:
        return f"name:eq:{filter_name}"
    return None


def _parse_graphql_sheet_nodes(data: dict[str, Any]) -> list[ViewSummary]:
    """Normalise a GraphQL ``sheetsConnection.nodes`` list into ViewSummary (type=sheet)."""
    nodes = data.get("data", {}).get("sheetsConnection", {}).get("nodes", [])
    results: list[ViewSummary] = []
    for node in nodes:
        workbook = node.get("workbook") or {}
        contained = _parse_dashboard_refs(node.get("containedInDashboards"))
        results.append(
            ViewSummary(
                luid=node.get("luid", ""),
                name=node.get("name", ""),
                view_type="sheet",
                content_url=node.get("path"),
                workbook_luid=workbook.get("luid")
                if isinstance(workbook, dict)
                else None,
                workbook_name=workbook.get("name")
                if isinstance(workbook, dict)
                else None,
                index=node.get("index"),
                created_at=node.get("createdAt"),
                updated_at=node.get("updatedAt"),
                contained_in_dashboards=contained,
                sheets_in_dashboard=[],
            )
        )
    return results


def _parse_graphql_dashboard_nodes(data: dict[str, Any]) -> list[ViewSummary]:
    """Normalise a GraphQL ``dashboardsConnection.nodes`` list into ViewSummary (type=dashboard)."""
    nodes = data.get("data", {}).get("dashboardsConnection", {}).get("nodes", [])
    results: list[ViewSummary] = []
    for node in nodes:
        workbook = node.get("workbook") or {}
        component_sheets = _parse_sheet_refs(node.get("sheets"))
        results.append(
            ViewSummary(
                luid=node.get("luid", ""),
                name=node.get("name", ""),
                view_type="dashboard",
                content_url=node.get("path"),
                workbook_luid=workbook.get("luid")
                if isinstance(workbook, dict)
                else None,
                workbook_name=workbook.get("name")
                if isinstance(workbook, dict)
                else None,
                index=node.get("index"),
                created_at=node.get("createdAt"),
                updated_at=node.get("updatedAt"),
                contained_in_dashboards=[],
                sheets_in_dashboard=component_sheets,
            )
        )
    return results


def _parse_rest_views(data: dict[str, Any]) -> list[ViewSummary]:
    """Normalise a REST ``views.view`` list into ViewSummary objects."""
    raw = data.get("views", {}).get("view", [])
    if isinstance(raw, dict):
        raw = [raw]
    results: list[ViewSummary] = []
    for item in raw:
        workbook = item.get("workbook") or {}
        usage = item.get("usage") or {}
        total_view_count = None
        if "totalViewCount" in usage:
            try:
                total_view_count = int(usage["totalViewCount"])
            except (ValueError, TypeError):
                pass
        results.append(
            ViewSummary(
                luid=item.get("id", ""),
                name=item.get("name", ""),
                view_type="sheet",  # REST /views returns both, but we can't distinguish
                content_url=item.get("contentUrl"),
                workbook_luid=workbook.get("id")
                if isinstance(workbook, dict)
                else None,
                workbook_name=None,  # REST doesn't provide workbook name
                total_view_count=total_view_count,
                contained_in_dashboards=[],
                sheets_in_dashboard=[],
            )
        )
    return results


def _graphql_paginate_connection(
    conn: http.client.HTTPSConnection,
    config: SdkConfig,
    path: str,
    headers: dict[str, str],
    query: str,
    connection_key: str,
    parser: Any,
    *,
    filter_dict: dict[str, str] | None,
    page_size: int,
    limit: int | None,
    current_count: int = 0,
) -> tuple[list[ViewSummary], bool]:
    """Paginate a single GraphQL connection and return (results, should_fallback).

    ``should_fallback=True`` means the first request failed in a way that
    warrants a REST fallback (403/503/timeout).  After the first page succeeds,
    subsequent failures are treated as partial success.
    """
    offset = 0
    results: list[ViewSummary] = []
    first_request = True

    _wall_start = time.monotonic()

    while True:
        if time.monotonic() - _wall_start > _GRAPHQL_TOTAL_TIMEOUT:
            logger.warning(
                "GraphQL %s pagination exceeded %.0fs wall-clock limit; "
                "falling back to REST (discarding %d partial results).",
                connection_key,
                _GRAPHQL_TOTAL_TIMEOUT,
                len(results),
            )
            return [], True  # ([], True) signals REST fallback to caller

        variables: dict[str, Any] = {"first": page_size, "offset": offset}
        if filter_dict is not None:
            variables["filter"] = filter_dict

        payload = {"query": query, "variables": variables}
        body = json.dumps(payload).encode("utf-8")
        req_headers = {
            **headers,
            "Content-Length": str(len(body)),
        }

        try:
            conn.request("POST", path, body=body, headers=req_headers)
            # Socket now exists — apply GraphQL-specific timeout before reading response
            if conn.sock is not None:
                conn.sock.settimeout(_GRAPHQL_TIMEOUT)
            resp = conn.getresponse()
            resp_body = resp.read()
        except socket.timeout:
            if first_request:
                logger.warning("GraphQL %s timed out.", connection_key)
                return [], True
            logger.warning(
                "GraphQL %s timed out on page %d; stopping.", connection_key, offset
            )
            break
        except (http.client.HTTPException, OSError):
            if first_request:
                return [], True
            break
        finally:
            if conn.sock is not None:
                conn.sock.settimeout(config.timeout)

        if resp.status in (403, 503) and first_request:
            logger.warning("GraphQL %s returned %d.", connection_key, resp.status)
            return [], True

        if resp.status >= 400:
            if first_request:
                return [], True
            logger.warning(
                "GraphQL %s returned %d on page %d; stopping.",
                connection_key,
                resp.status,
                offset,
            )
            break

        try:
            data = json.loads(resp_body.decode("utf-8"))
        except Exception:
            if first_request:
                return [], True
            break

        top_data = data.get("data")
        if top_data is None and first_request:
            return [], True

        first_request = False
        page_results = parser(data)
        results.extend(page_results)
        logger.debug(
            "GraphQL %s: page %d \u2014 %d items this page, %d total (%.1fs elapsed)",
            connection_key,
            offset // page_size + 1,
            len(page_results),
            current_count + len(results),
            time.monotonic() - _wall_start,
        )

        effective_total = current_count + len(results)
        if limit is not None and effective_total >= limit:
            trim = limit - current_count
            results = results[:trim]
            return results, False

        page_info = data.get("data", {}).get(connection_key, {}).get("pageInfo", {})
        if not page_info.get("hasNextPage", False):
            break

        offset += page_size

    return results, False


def _graphql_list_views(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection,
    *,
    filter_name: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[ViewSummary] | None:
    """Attempt view discovery via the Metadata API (GraphQL).

    Runs two sequential paginated queries: ``sheetsConnection`` then
    ``dashboardsConnection``.  Returns ``None`` if the sheets query fails
    in a way that warrants a REST fallback.  If sheets succeed but dashboards
    fail, logs a warning and returns the sheets-only result.
    """
    base_path = _get_base_path(config)
    path = f"{base_path}/api/metadata/graphql"
    headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
    }
    page_size = _clamp_page_size(page_size)
    filt = _build_view_graphql_filter(filter_name)

    # --- sheets ---
    sheet_results, fallback = _graphql_paginate_connection(
        conn,
        config,
        path,
        headers,
        _GRAPHQL_SHEETS_QUERY,
        "sheetsConnection",
        _parse_graphql_sheet_nodes,
        filter_dict=filt,
        page_size=page_size,
        limit=limit,
        current_count=0,
    )

    if fallback:
        return None  # trigger REST fallback

    # Check if limit already reached
    if limit is not None and len(sheet_results) >= limit:
        return sheet_results[:limit]

    # --- dashboards ---
    dashboard_results, _ = _graphql_paginate_connection(
        conn,
        config,
        path,
        headers,
        _GRAPHQL_DASHBOARDS_QUERY,
        "dashboardsConnection",
        _parse_graphql_dashboard_nodes,
        filter_dict=filt,
        page_size=page_size,
        limit=limit,
        current_count=len(sheet_results),
    )

    combined = sheet_results + dashboard_results
    if limit is not None:
        combined = combined[:limit]
    return combined


def _rest_list_views(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection,
    *,
    filter_name: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[ViewSummary]:
    """Attempt view discovery via the REST API.

    Raises ``CatalogUnavailableError`` on any non-2xx response.
    """
    base_path = _get_base_path(config)
    base_url_path = f"{base_path}/api/{config.api_version}/sites/{token.site_id}/views"
    headers = {
        "X-Tableau-Auth": token.token,
        "Accept": "application/json",
    }
    page_size = _clamp_page_size(page_size)
    page_number = 1
    results: list[ViewSummary] = []
    rest_filter = _build_view_rest_filter(filter_name)

    while True:
        params: dict[str, Any] = {
            "pageSize": page_size,
            "pageNumber": page_number,
            "includeUsageStatistics": "true",
        }
        if rest_filter is not None:
            params["filter"] = rest_filter

        path = f"{base_url_path}?{urlencode(params)}"
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            message = None
            try:
                resp_data = json.loads(resp_body.decode("utf-8"))
                if isinstance(resp_data, dict):
                    error = resp_data.get("error", {})
                    message = (
                        error.get("message") if isinstance(error, dict) else str(error)
                    )
            except Exception:
                message = resp_body.decode("utf-8", errors="replace") or None
            raise CatalogUnavailableError(
                status_code=resp.status,
                response_body=resp_body,
                response_headers=dict(resp.getheaders()),
                tableau_error_code=None,
                tableau_error_message=message or f"HTTP {resp.status}",
            )

        data = json.loads(resp_body.decode("utf-8"))
        page_results = _parse_rest_views(data)
        results.extend(page_results)

        if limit is not None and len(results) >= limit:
            results = results[:limit]
            break

        pagination = data.get("pagination", {})
        total_available = int(pagination.get("totalAvailable", 0))
        if total_available == 0:
            break
        if page_number * page_size >= total_available:
            break

        page_number += 1

    return results


def list_views(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[ViewSummary]:
    """Discover Tableau views (sheets and dashboards) on a site.

    Primary path uses two sequential GraphQL queries:
    ``sheetsConnection`` (individual worksheets) followed by
    ``dashboardsConnection`` (dashboards).  Results are combined into a
    single list with ``view_type`` set to ``"sheet"`` or ``"dashboard"``.

    Each sheet entry carries ``contained_in_dashboards`` — the list of
    dashboards this sheet appears in.  Each dashboard entry carries
    ``sheets_in_dashboard`` — the sheets that compose it.

    On 403/503/timeout from the sheets query, falls back to the REST
    ``Query Views for Site`` endpoint, which returns both sheets and
    dashboards but cannot populate ``workbook_name`` or the nested
    containment lists.

    If the sheets query succeeds but the dashboards query fails, the
    sheets-only result is returned (partial success — no REST fallback).

    Args:
        config: SDK configuration (server URL, API versions, etc.).
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``http.client.HTTPSConnection`` for connection reuse.
        filter_name: Optional name filter applied to both sheets and dashboards.
        page_size: Items per page (default 1,000; clamped to 1,000 max).
        limit: Maximum total items to return (across sheets + dashboards).

    Returns:
        List of ``ViewSummary`` objects.  Sheets appear before dashboards
        when using the GraphQL path.

    Raises:
        CatalogUnavailableError: When both GraphQL and REST APIs fail.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        gql_results = _graphql_list_views(
            config,
            token,
            conn,
            filter_name=filter_name,
            page_size=page_size,
            limit=limit,
        )

        if gql_results is not None:
            return gql_results

        return _rest_list_views(
            config,
            token,
            conn,
            filter_name=filter_name,
            page_size=page_size,
            limit=limit,
        )
    finally:
        if should_close:
            conn.close()
