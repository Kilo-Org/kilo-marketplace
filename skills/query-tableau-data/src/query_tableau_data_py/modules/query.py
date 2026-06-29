"""VDS query execution — health check, buffered query,
``listSupportedFunctions``.

Sync transport using http.client (stdlib). No external HTTP dependencies.
Pure functional API: no temp/ I/O, no stdout printing.
Persistence is handled by ``data.py`` (f4z.14), called by the orchestrator.
"""

from __future__ import annotations

import http.client
import json
import logging
import socket
import ssl
from urllib.parse import urlparse

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.errors import (
    AuthenticationError,
    QueryExecutionError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from query_tableau_data_py.models import (
    QueryField,
    QueryRequest,
    QueryResult,
    QueryResultMetadata,
    SupportedFunction,
)
from query_tableau_data_py.modules.auth import AuthToken

logger = logging.getLogger(__name__)

_VDS_BASE = "/api/v1/vizql-data-service"


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


def build_query_payload(request: QueryRequest) -> dict:
    """Flatten a ``QueryRequest`` into the nested VDS JSON body shape."""
    payload: dict = {
        "datasource": {
            "datasourceLuid": request.datasource_luid,
        },
        "options": request.options.model_dump(
            mode="json", exclude_unset=True, by_alias=True
        ),
    }
    # returnFormat must always be present for a self-describing payload;
    # the VDS server defaults to "OBJECTS" but downstream consumers need
    # the format explicitly stated regardless of whether the user set it.
    payload["options"].setdefault("returnFormat", "OBJECTS")

    if request.connections:
        payload["datasource"]["connections"] = [
            c.model_dump(mode="json", exclude_none=True, by_alias=True)
            for c in request.connections
        ]

    query: dict = {}
    if request.fields:
        query["fields"] = [
            f.model_dump(mode="json", exclude_none=True, by_alias=True)
            for f in request.fields
        ]
    if request.filters:
        filter_list: list[dict] = []
        for f in request.filters:
            raw = f.model_dump(mode="json", exclude_none=True, by_alias=True)
            # VDS expects "field" as a nested object, not a flat "fieldCaption"
            nested: dict = {}
            if raw.get("fieldCaption"):
                nested["field"] = {"fieldCaption": raw.pop("fieldCaption")}
            if raw.get("calculation"):
                nested["field"] = {"calculation": raw.pop("calculation")}
            # fieldToMeasure also needs nesting
            ftm = raw.pop("fieldToMeasure", None)
            if ftm:
                nested["fieldToMeasure"] = {"fieldCaption": ftm}
            # function on fieldToMeasure is not currently modelled; if added later,
            # it should be included in the nested fieldToMeasure dict above.
            nested.update(raw)
            filter_list.append(nested)
        query["filters"] = filter_list
    if request.parameters:
        query["parameters"] = [
            p.model_dump(mode="json", exclude_none=True, by_alias=True)
            for p in request.parameters
        ]

    if query:
        payload["query"] = query

    return payload


def _parse_vds_error(body: dict) -> tuple[str | None, str | None]:
    """Extract Tableau error code and message from a VDS error dict."""
    code = body.get("errorCode") or body.get("tab-error-code")
    message = body.get("message")
    return (str(code) if code is not None else None, message)


def _raise_from_error_body(body: dict, status_code: int | None = None) -> None:
    """Raise the correct typed exception from a VDS error object."""
    tableau_code, tableau_message = _parse_vds_error(body)
    raise QueryExecutionError(
        status_code=status_code,
        response_body=json.dumps(body).encode(),
        tableau_error_code=tableau_code,
        tableau_error_message=tableau_message,
    )


def _handle_error_response(
    status_code: int, resp_body: bytes, resp_headers: dict[str, str]
) -> None:
    """Inspect an HTTP response and raise the matching typed exception.

    Mapping (PROTOTYPE.md §4):
    - 401/403  → AuthenticationError
    - 429      → RateLimitError (with retry_after)
    - 5xx      → ServerError
    - VDS error body (including 404934 "Unknown field") → QueryExecutionError
    """
    tableau_code: str | None = None
    tableau_message: str | None = None

    try:
        data = json.loads(resp_body.decode("utf-8"))
        if isinstance(data, dict):
            tableau_code, tableau_message = _parse_vds_error(data)
    except Exception:
        pass

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

    # Any remaining 4xx or unexpected status with a VDS error object
    if tableau_code is not None:
        raise QueryExecutionError(
            status_code=sc,
            response_body=resp_body,
            response_headers=resp_headers,
            tableau_error_code=tableau_code,
            tableau_error_message=tableau_message,
        )

    # Fallback: treat any unexpected non-2xx as ServerError
    raise ServerError(
        status_code=sc,
        response_body=resp_body,
        response_headers=resp_headers,
        tableau_error_code=tableau_code,
        tableau_error_message=tableau_message,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def health_check(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
) -> bool:
    """GET ``/api/v1/vizql-data-service/simple-request``.

    Returns ``True`` if the response body contains ``"ahoy"``.
    """
    base_path = _get_base_path(config)
    path = f"{base_path}{_VDS_BASE}/simple-request"
    headers = {"X-Tableau-Auth": token.token}
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            _handle_error_response(resp.status, resp_body, dict(resp.getheaders()))

        return "ahoy" in resp_body.decode("utf-8").lower()
    finally:
        if should_close:
            conn.close()


def query(
    config: SdkConfig,
    token: AuthToken,
    request: QueryRequest,
    conn: http.client.HTTPSConnection | None = None,
) -> QueryResult:
    """POST ``/api/v1/vizql-data-service/query-datasource`` (buffered).

    Returns a fully materialised ``QueryResult``.  Does **not** write to
    ``temp/`` or print to stdout.
    """
    base_path = _get_base_path(config)
    path = f"{base_path}{_VDS_BASE}/query-datasource"
    payload = build_query_payload(request)
    body = json.dumps(payload).encode("utf-8")
    req_headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("POST", path, body=body, headers=req_headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            _handle_error_response(resp.status, resp_body, dict(resp.getheaders()))

        try:
            parsed = json.loads(resp_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError(
                status_code=resp.status,
                response_body=resp_body,
                tableau_error_code=None,
                tableau_error_message=f"Invalid JSON in VDS response: {exc}",
            ) from exc

        # During-streaming error disguised as HTTP 200
        if isinstance(parsed, dict) and "errorCode" in parsed:
            _raise_from_error_body(parsed, status_code=resp.status)

        rows = parsed.get("data", [])
        debug_info = parsed.get("debug")

        metadata = QueryResultMetadata(
            field_captions=[f.field_caption for f in request.fields],
            row_count=len(rows),
            is_complete=True,
        )

        return QueryResult(rows=rows, metadata=metadata, debug_info=debug_info)
    finally:
        if should_close:
            conn.close()


def query_raw(
    config: SdkConfig,
    token: AuthToken,
    payload: dict,
    conn: http.client.HTTPSConnection | None = None,
) -> QueryResult:
    """POST ``/api/v1/vizql-data-service/query-datasource`` with a raw dict payload.

    This is the escape-hatch for agents that need to construct or mutate
    the JSON body directly without using the typed ``QueryRequest`` model.
    """
    base_path = _get_base_path(config)
    path = f"{base_path}{_VDS_BASE}/query-datasource"
    body = json.dumps(payload).encode("utf-8")
    req_headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("POST", path, body=body, headers=req_headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            _handle_error_response(resp.status, resp_body, dict(resp.getheaders()))

        try:
            parsed = json.loads(resp_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError(
                status_code=resp.status,
                response_body=resp_body,
                tableau_error_code=None,
                tableau_error_message=f"Invalid JSON in VDS response: {exc}",
            ) from exc

        # During-streaming error disguised as HTTP 200
        if isinstance(parsed, dict) and "errorCode" in parsed:
            _raise_from_error_body(parsed, status_code=resp.status)

        rows = parsed.get("data", [])
        debug_info = parsed.get("debug")

        # Derive field captions from the payload if available
        field_captions: list[str] = []
        query_section = payload.get("query", {})
        if isinstance(query_section, dict):
            fields = query_section.get("fields", [])
            if isinstance(fields, list):
                for f in fields:
                    if isinstance(f, dict):
                        field_captions.append(f.get("fieldCaption", ""))

        metadata = QueryResultMetadata(
            field_captions=field_captions,
            row_count=len(rows),
            is_complete=True,
        )

        return QueryResult(rows=rows, metadata=metadata, debug_info=debug_info)
    finally:
        if should_close:
            conn.close()


def list_supported_functions(
    config: SdkConfig,
    token: AuthToken,
    datasource_luid: str,
    conn: http.client.HTTPSConnection | None = None,
) -> list[SupportedFunction]:
    """POST ``/api/v1/vizql-data-service/list-supported-functions``.

    Returns the Tableau functions supported for the given datasource.
    """
    base_path = _get_base_path(config)
    path = f"{base_path}{_VDS_BASE}/list-supported-functions"
    payload = {"datasource": {"datasourceLuid": datasource_luid}}
    body = json.dumps(payload).encode("utf-8")
    req_headers = {
        "X-Tableau-Auth": token.token,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }
    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("POST", path, body=body, headers=req_headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            _handle_error_response(resp.status, resp_body, dict(resp.getheaders()))

        try:
            parsed = json.loads(resp_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError(
                status_code=resp.status,
                response_body=resp_body,
                tableau_error_code=None,
                tableau_error_message=f"Invalid JSON in VDS response: {exc}",
            ) from exc

        if isinstance(parsed, dict) and "errorCode" in parsed:
            _raise_from_error_body(parsed, status_code=resp.status)

        functions = parsed.get("data", []) if isinstance(parsed, dict) else []
        return [SupportedFunction.model_validate(f) for f in functions]
    finally:
        if should_close:
            conn.close()
