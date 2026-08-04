"""REST-based view data retrieval via ``GET /sites/{site-id}/views/{view-id}/data``.

Sync transport using http.client (stdlib). No external HTTP dependencies.
Pure functional API — no temp I/O, no stdout printing.
Persistence is handled by ``data.py``, called by the orchestrator.

## Overview

When a user's question is perfectly answered by an existing Tableau view,
``query_view_data`` retrieves that view's data directly via the REST API.
This is the "quick answer" path — faster and simpler than introspecting a
datasource and building a VDS query.

## Known Limitations

1. **First sheet only** — The endpoint renders the first (default) sheet in a
   workbook. It cannot target a specific sheet within a multi-sheet workbook.

2. **Hidden sheets** — Sheets hidden by the workbook author are not queryable.
   The caller receives an empty result with no error.

3. **Published views** — Views published independently (not as part of a
   workbook) can be queried directly by their own LUID.

4. **No filter/aggregation control** — Unlike VDS, custom fields, filters, or
   aggregations cannot be specified. The view returns its pre-configured data.
   (View-filter query parameters such as ``vf_<fieldname>`` are out of scope
   for this module; use a raw request if you need them.)

5. **CSV only** — The response is ``text/csv``. ``ViewQueryResult`` exposes
   both the parsed structure (``column_names``, ``rows``) and the raw text
   (``raw_csv``) for agents that prefer to process it themselves.
"""

from __future__ import annotations

import csv
import http.client
import io
import json
import logging
import socket
import ssl
from urllib.parse import urlparse, urlencode

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.errors import (
    AuthenticationError,
    RateLimitError,
    ServerError,
    ViewQueryError,
)
from query_tableau_data_py.models import ViewQueryResult
from query_tableau_data_py.modules.auth import AuthToken

logger = logging.getLogger(__name__)


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


def _parse_rest_error(
    status_code: int, resp_body: bytes, resp_headers: dict[str, str]
) -> tuple[str | None, str | None]:
    """Extract Tableau error code and message from a REST API error response.

    The REST API returns JSON bodies shaped as::

        {"error": {"code": "400080", "message": "..."}}

    Falls back to ``None`` if the body is not JSON or lacks the expected shape.
    """
    try:
        data = json.loads(resp_body.decode("utf-8"))
        if isinstance(data, dict):
            error = data.get("error", {})
            if isinstance(error, dict):
                code = str(error.get("code", "")) or None
                message = error.get("message") or None
                return code, message
            return None, str(error) if error else None
    except Exception:
        pass
    return None, None


def _handle_error_response(
    status_code: int, resp_body: bytes, resp_headers: dict[str, str]
) -> None:
    """Inspect a non-2xx HTTP response and raise the matching typed exception.

    Mapping:
    - 401 / 403  → :class:`AuthenticationError`
    - 429        → :class:`RateLimitError` (with ``retry_after`` when available)
    - 5xx        → :class:`ServerError`
    - Other 4xx  → :class:`ViewQueryError`
    """
    tableau_code, tableau_message = _parse_rest_error(
        status_code, resp_body, resp_headers
    )
    sc = status_code

    if sc in (401, 403):
        raise AuthenticationError(
            status_code=sc,
            response_body=resp_body,
            response_headers=resp_headers,
            tableau_error_code=tableau_code,
            tableau_error_message=tableau_message,
        )

    if sc == 429:
        retry_after: int | None = None
        raw_ra = resp_headers.get("retry-after")
        if raw_ra is not None:
            try:
                retry_after = int(raw_ra)
            except ValueError:
                pass
        raise RateLimitError(
            status_code=sc,
            response_body=resp_body,
            response_headers=resp_headers,
            tableau_error_code=tableau_code,
            tableau_error_message=tableau_message,
            retry_after=retry_after,
        )

    if sc >= 500:
        raise ServerError(
            status_code=sc,
            response_body=resp_body,
            response_headers=resp_headers,
            tableau_error_code=tableau_code,
            tableau_error_message=tableau_message,
        )

    # Remaining 4xx (400 bad view ID, 404 site not found, 405 wrong method, …)
    raise ViewQueryError(
        status_code=sc,
        response_body=resp_body,
        response_headers=resp_headers,
        tableau_error_code=tableau_code,
        tableau_error_message=tableau_message,
    )


def _parse_csv(text: str) -> ViewQueryResult:
    """Parse a CSV string into a :class:`ViewQueryResult`.

    The first row is treated as the header (column names). Each subsequent
    row becomes a ``dict[str, str]`` keyed by column name.

    An empty or whitespace-only string returns a default ``ViewQueryResult``.
    """
    if not text or not text.strip():
        return ViewQueryResult()

    reader = csv.DictReader(io.StringIO(text))
    column_names: list[str] = reader.fieldnames or []  # type: ignore[assignment]
    rows: list[dict[str, str]] = [dict(row) for row in reader]

    return ViewQueryResult(
        column_names=list(column_names),
        rows=rows,
        row_count=len(rows),
        raw_csv=text,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def query_view_data(
    config: SdkConfig,
    token: AuthToken,
    view_luid: str,
    conn: http.client.HTTPSConnection | None = None,
    *,
    max_age: int | None = None,
) -> ViewQueryResult:
    """Retrieve tabular data for a Tableau view via the REST API.

    Calls ``GET /api/{version}/sites/{site-id}/views/{view-id}/data`` and
    returns a parsed :class:`~query_tableau_data_py.models.ViewQueryResult`.

    Args:
        config: SDK configuration (server URL, API version, credentials).
        token: Valid authentication token from :func:`modules.auth.sign_in`.
        view_luid: LUID of the view to query.
        conn: Optional shared :class:`http.client.HTTPSConnection`. If ``None``,
            a temporary connection is created and closed after the request.
        max_age: Maximum age of cached data in minutes. Maps to the
            ``?maxAge=`` query parameter. ``None`` uses Tableau's default
            (60 minutes).

    Returns:
        A :class:`ViewQueryResult` with ``column_names``, ``rows``,
        ``row_count``, and ``raw_csv`` populated from the CSV response.

    Raises:
        AuthenticationError: On 401 or 403 responses.
        RateLimitError: On 429 responses (includes ``retry_after`` when
            the ``Retry-After`` header is present).
        ServerError: On 5xx responses.
        ViewQueryError: On other 4xx responses (e.g. bad view LUID,
            site not found, invalid method).
    """
    base_path = _get_base_path(config)
    url_path = (
        f"{base_path}/api/{config.api_version}"
        f"/sites/{token.site_id}/views/{view_luid}/data"
    )
    params: dict[str, int] = {}
    if max_age is not None:
        params["maxAge"] = max_age

    if params:
        url_path = f"{url_path}?{urlencode(params)}"

    headers = {"X-Tableau-Auth": token.token}

    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("GET", url_path, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            _handle_error_response(resp.status, resp_body, dict(resp.getheaders()))

        return _parse_csv(resp_body.decode("utf-8"))
    finally:
        if should_close:
            conn.close()
