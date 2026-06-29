"""Flat, fast, REST-only catalog inventory functions.

Answers "what exists on this site?" with three paginated REST calls.
No GraphQL. No nested relationship data. Always completes regardless of
site size (no timeout-prone Metadata API calls).

This is Tier 1 of the three-tier discovery design (PROTOTYPE_3.md §3).
Use ``lineage.py`` (Tier 2) for per-asset relationship queries, and
``introspect_datasource`` / ``introspect_workbook`` (Tier 3) for full
field-level schema.

Sync transport using http.client (stdlib). No external HTTP dependencies.
Pure functional API — no temp I/O, no stdout printing.
"""

from __future__ import annotations

import http.client
import json
import logging
from typing import Any
from urllib.parse import urlencode

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.errors import CatalogUnavailableError
from query_tableau_data_py.models import (
    DatasourceInventoryItem,
    ProjectItem,
    ServerInfo,
    SiteScope,
    ViewInventoryItem,
    WorkbookInventoryItem,
)
from query_tableau_data_py.modules.auth import AuthToken
from query_tableau_data_py.modules._rest_utils import (
    _build_rest_filter,
    _clamp_page_size,
    _get_base_path,
    _make_connection,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _raise_catalog_error(resp: http.client.HTTPResponse, resp_body: bytes) -> None:
    """Parse a non-2xx response and raise CatalogUnavailableError."""
    message: str | None = None
    try:
        data = json.loads(resp_body.decode("utf-8"))
        if isinstance(data, dict):
            error = data.get("error", {})
            if isinstance(error, dict):
                message = error.get("message")
            else:
                message = str(error)
    except Exception:
        message = resp_body.decode("utf-8", errors="replace") or None
    raise CatalogUnavailableError(
        status_code=resp.status,
        response_body=resp_body,
        response_headers=dict(resp.getheaders()),
        tableau_error_code=None,
        tableau_error_message=message or f"HTTP {resp.status}",
    )


def _parse_tags(raw_tags: dict | list | None) -> list[str]:
    """Parse REST tags shape: ``{ "tag": [{ "label": "..." }] }``."""
    if not raw_tags:
        return []
    if isinstance(raw_tags, dict):
        tag_list = raw_tags.get("tag", [])
    else:
        tag_list = raw_tags
    return [
        t.get("label", "") for t in tag_list if isinstance(t, dict) and t.get("label")
    ]


def _parse_bool(value: Any) -> bool | None:
    """Coerce REST bool values that may arrive as strings."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


# ---------------------------------------------------------------------------
# inventory_datasources
# ---------------------------------------------------------------------------


def _parse_rest_inventory_datasources(
    data: dict[str, Any],
) -> list[DatasourceInventoryItem]:
    """Normalise a REST ``datasources.datasource`` list into DatasourceInventoryItem."""
    raw = data.get("datasources", {}).get("datasource", [])
    if isinstance(raw, dict):
        raw = [raw]
    results: list[DatasourceInventoryItem] = []
    for item in raw:
        project = item.get("project") or {}
        owner = item.get("owner") or {}
        tags = _parse_tags(item.get("tags"))
        results.append(
            DatasourceInventoryItem(
                luid=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description"),
                project_name=project.get("name") if isinstance(project, dict) else None,
                owner_id=owner.get("id") if isinstance(owner, dict) else None,
                has_extracts=_parse_bool(item.get("hasExtracts")),
                is_certified=_parse_bool(item.get("isCertified")),
                created_at=item.get("createdAt"),
                updated_at=item.get("updatedAt"),
                content_url=item.get("contentUrl"),
                tags=tags,
            )
        )
    return results


def inventory_datasources(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[DatasourceInventoryItem]:
    """Return a flat list of all published datasources on the site (REST only).

    No GraphQL. No nested relationship data. Paginates via
    ``pagination.totalAvailable`` until all items are fetched.

    Args:
        config: SDK configuration.
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``HTTPSConnection`` for connection reuse.
        filter_name: Exact-match name filter (``name:eq:VALUE``).
        filter_project: Exact-match project filter (``projectName:eq:VALUE``).
        page_size: Items per page (default 1,000; clamped to 1,000).
        limit: Maximum total items to return.

    Returns:
        List of ``DatasourceInventoryItem`` objects.

    Raises:
        CatalogUnavailableError: On any non-2xx REST response.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
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
        results: list[DatasourceInventoryItem] = []
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
                _raise_catalog_error(resp, resp_body)

            data = json.loads(resp_body.decode("utf-8"))
            page_results = _parse_rest_inventory_datasources(data)
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
    finally:
        if should_close:
            conn.close()


# ---------------------------------------------------------------------------
# inventory_views
# ---------------------------------------------------------------------------


def _parse_rest_inventory_views(data: dict[str, Any]) -> list[ViewInventoryItem]:
    """Normalise a REST ``views.view`` list into ViewInventoryItem."""
    raw = data.get("views", {}).get("view", [])
    if isinstance(raw, dict):
        raw = [raw]
    results: list[ViewInventoryItem] = []
    for item in raw:
        workbook = item.get("workbook") or {}
        owner = item.get("owner") or {}
        usage = item.get("usage") or {}
        total_view_count: int | None = None
        if "totalViewCount" in usage:
            try:
                total_view_count = int(usage["totalViewCount"])
            except (ValueError, TypeError):
                pass
        results.append(
            ViewInventoryItem(
                luid=item.get("id", ""),
                name=item.get("name", ""),
                content_url=item.get("contentUrl"),
                workbook_luid=workbook.get("id")
                if isinstance(workbook, dict)
                else None,
                owner_id=owner.get("id") if isinstance(owner, dict) else None,
                total_view_count=total_view_count,
            )
        )
    return results


def inventory_views(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[ViewInventoryItem]:
    """Return a flat list of all views on the site (REST only).

    Always sets ``includeUsageStatistics=true`` — the only REST path that
    returns ``total_view_count``.  Use this as the canonical source of
    popularity signals; no separate call is needed.

    Note: ``workbook_luid`` is populated but ``workbook_name`` is not
    available from the REST ``/views`` endpoint.  Resolve workbook names
    by calling ``inventory_workbooks()`` and joining on ``workbook_luid``.

    Args:
        config: SDK configuration.
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``HTTPSConnection`` for connection reuse.
        filter_name: Exact-match name filter (``name:eq:VALUE``).
        page_size: Items per page (default 1,000; clamped to 1,000).
        limit: Maximum total items to return.

    Returns:
        List of ``ViewInventoryItem`` objects (always includes ``total_view_count``).

    Raises:
        CatalogUnavailableError: On any non-2xx REST response.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        base_path = _get_base_path(config)
        base_url_path = (
            f"{base_path}/api/{config.api_version}/sites/{token.site_id}/views"
        )
        headers = {
            "X-Tableau-Auth": token.token,
            "Accept": "application/json",
        }
        page_size = _clamp_page_size(page_size)
        page_number = 1
        results: list[ViewInventoryItem] = []
        rest_filter = filter_name and f"name:eq:{filter_name}"

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
                _raise_catalog_error(resp, resp_body)

            data = json.loads(resp_body.decode("utf-8"))
            page_results = _parse_rest_inventory_views(data)
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
    finally:
        if should_close:
            conn.close()


# ---------------------------------------------------------------------------
# inventory_workbooks
# ---------------------------------------------------------------------------


def _parse_rest_inventory_workbooks(
    data: dict[str, Any],
) -> list[WorkbookInventoryItem]:
    """Normalise a REST ``workbooks.workbook`` list into WorkbookInventoryItem."""
    raw = data.get("workbooks", {}).get("workbook", [])
    if isinstance(raw, dict):
        raw = [raw]
    results: list[WorkbookInventoryItem] = []
    for item in raw:
        project = item.get("project") or {}
        owner = item.get("owner") or {}
        tags = _parse_tags(item.get("tags"))
        results.append(
            WorkbookInventoryItem(
                luid=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description"),
                project_name=project.get("name") if isinstance(project, dict) else None,
                owner_id=owner.get("id") if isinstance(owner, dict) else None,
                content_url=item.get("contentUrl"),
                created_at=item.get("createdAt"),
                updated_at=item.get("updatedAt"),
                tags=tags,
            )
        )
    return results


def inventory_workbooks(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[WorkbookInventoryItem]:
    """Return a flat list of all workbooks on the site (REST only).

    No GraphQL. No sheets, dashboards, or embedded datasource data.
    Use ``workbook_lineage()`` for relationship data.

    Args:
        config: SDK configuration.
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``HTTPSConnection`` for connection reuse.
        filter_name: Exact-match name filter (``name:eq:VALUE``).
        filter_project: Exact-match project filter (``projectName:eq:VALUE``).
        page_size: Items per page (default 1,000; clamped to 1,000).
        limit: Maximum total items to return.

    Returns:
        List of ``WorkbookInventoryItem`` objects.

    Raises:
        CatalogUnavailableError: On any non-2xx REST response.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
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
        results: list[WorkbookInventoryItem] = []
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
                _raise_catalog_error(resp, resp_body)

            data = json.loads(resp_body.decode("utf-8"))
            page_results = _parse_rest_inventory_workbooks(data)
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
    finally:
        if should_close:
            conn.close()


# ---------------------------------------------------------------------------
# scope_site
# ---------------------------------------------------------------------------


def _probe_count(
    conn: http.client.HTTPSConnection,
    url_path: str,
    headers: dict[str, str],
) -> int:
    """Make one pageSize=1 REST probe and return totalAvailable."""
    conn.request("GET", url_path, headers=headers)
    resp = conn.getresponse()
    resp_body = resp.read()
    if resp.status >= 400:
        _raise_catalog_error(resp, resp_body)
    data = json.loads(resp_body.decode("utf-8"))
    pagination = data.get("pagination", {})
    return int(pagination.get("totalAvailable", 0))


def _parse_rest_projects(data: dict[str, Any]) -> list[ProjectItem]:
    """Normalise a REST ``projects.project`` list into ProjectItem objects."""
    raw = data.get("projects", {}).get("project", [])
    if isinstance(raw, dict):
        raw = [raw]
    results: list[ProjectItem] = []
    for item in raw:
        results.append(
            ProjectItem(
                luid=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description") or None,
                parent_project_id=item.get("parentProjectId") or None,
                content_permissions=item.get("contentPermissions") or None,
            )
        )
    return results


def scope_site(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    server_info: ServerInfo | None = None,
) -> SiteScope:
    """Return total asset counts and project list via fast REST probes.

    Makes 3 ``pageSize=1`` requests for counts (datasources, workbooks, views)
    plus 1 paginated request for the full project list.  Always completes
    regardless of site size — no timeout risk.

    The single item returned by each count probe is discarded; only
    ``pagination.totalAvailable`` is read.

    Cost: 4+ HTTP requests (~300 bytes each for counts, ~1–5 KB for projects).

    Args:
        config: SDK configuration.
        token: Active ``AuthToken`` from ``auth.sign_in``.
        conn: Optional ``HTTPSConnection`` for connection reuse.

    Returns:
        ``SiteScope`` with datasource, workbook, and view counts plus the
        full project list.

    Raises:
        CatalogUnavailableError: On any non-2xx REST response.
    """
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        base_path = _get_base_path(config)
        site_base = f"{base_path}/api/{config.api_version}/sites/{token.site_id}"
        headers = {
            "X-Tableau-Auth": token.token,
            "Accept": "application/json",
        }

        # -- 3 count probes (pageSize=1, discard item payload) ---------------
        ds_count = _probe_count(
            conn,
            f"{site_base}/datasources?pageSize=1&pageNumber=1",
            headers,
        )
        wb_count = _probe_count(
            conn,
            f"{site_base}/workbooks?pageSize=1&pageNumber=1",
            headers,
        )
        view_count = _probe_count(
            conn,
            f"{site_base}/views?pageSize=1&pageNumber=1",
            headers,
        )

        # -- 1 paginated project list (pageSize=1000, usually 1 page) --------
        projects: list[ProjectItem] = []
        page_number = 1
        project_page_size = 1000

        while True:
            path = (
                f"{site_base}/projects?"
                f"{urlencode({'pageSize': project_page_size, 'pageNumber': page_number})}"
            )
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read()

            if resp.status >= 400:
                _raise_catalog_error(resp, resp_body)

            data = json.loads(resp_body.decode("utf-8"))
            projects.extend(_parse_rest_projects(data))

            pagination = data.get("pagination", {})
            total_available = int(pagination.get("totalAvailable", 0))
            if total_available == 0 or len(projects) >= total_available:
                break

            page_number += 1

        return SiteScope(
            datasource_count=ds_count,
            workbook_count=wb_count,
            view_count=view_count,
            projects=projects,
            server_info=server_info,
        )
    finally:
        if should_close:
            conn.close()
