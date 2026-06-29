"""Session class — reusable auth lifecycle and API delegate.

This module provides the ``Session`` context manager, the primary building
block for agent orchestrators.  It handles authentication, retries, and
exposes thin delegates to the functional API modules.

Sync transport using http.client (stdlib). No external HTTP dependencies.
"""

from __future__ import annotations

import dataclasses
import http.client
import logging
import ssl
import time
from typing import Any
from urllib.parse import urlparse

import query_tableau_data_py.modules.auth as auth
from query_tableau_data_py.modules.auth import AuthToken
import query_tableau_data_py.modules.catalog as catalog
import query_tableau_data_py.modules.inventory as inventory
import query_tableau_data_py.modules.introspect_datasource as introspect_datasource
import query_tableau_data_py.modules.introspect_workbook as introspect_workbook
import query_tableau_data_py.modules.lineage as lineage
import query_tableau_data_py.modules.query_view as query_view
from query_tableau_data_py.errors import (
    AuthenticationError,
    QueryExecutionError,
    RateLimitError,
    ServerError,
)
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.models import (
    DatasourceInventoryItem,
    DatasourceLineage,
    DatasourceSchema,
    DatasourceSummary,
    ProjectItem,
    QueryRequest,
    QueryResult,
    ServerInfo,
    SiteScope,
    SupportedFunction,
    ViewInventoryItem,
    ViewQueryResult,
    ViewSummary,
    WorkbookInventoryItem,
    WorkbookLineage,
    WorkbookSchema,
    WorkbookSummary,
)
from query_tableau_data_py.modules.query import (
    health_check,
    list_supported_functions,
    query,
    query_raw,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Session:
    """Authenticated session wrapper with transparent retry logic.

    Usage::

        with Session(config) as session:
            ds = session.list_datasources()
            result = session.query(request)
    """

    config: SdkConfig
    token: AuthToken | None = dataclasses.field(default=None, repr=False)
    server_info: ServerInfo | None = dataclasses.field(default=None, repr=False)
    _conn: http.client.HTTPSConnection | None = dataclasses.field(
        default=None, init=False, repr=False
    )
    _host: str = dataclasses.field(default="", init=False, repr=False)
    _port: int = dataclasses.field(default=443, init=False, repr=False)
    _base_path: str = dataclasses.field(default="", init=False, repr=False)
    _ssl_context: ssl.SSLContext | None = dataclasses.field(
        default=None, init=False, repr=False
    )
    _closed: bool = dataclasses.field(default=False, init=False, repr=False)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _make_connection(self) -> http.client.HTTPSConnection:
        """Create a fresh HTTPSConnection using resolved host/port/ssl."""
        return http.client.HTTPSConnection(
            self._host,
            self._port,
            context=self._ssl_context,
            timeout=self.config.timeout,
        )

    # ------------------------------------------------------------------
    # Internal retry wrapper
    # ------------------------------------------------------------------

    def _call_with_reconnect(self, fn, *args, **kwargs) -> Any:
        """Call *fn* once, retrying transparently on stale connection.

        If ``RemoteDisconnected`` is raised (server closed the keep-alive
        socket), the connection is replaced and *fn* is retried exactly once.
        A second ``RemoteDisconnected`` raises ``ServerError``.

        This method handles transport-level resilience only.  Business-logic
        retries (auth, rate-limit) are handled by ``_request_with_retry``.
        """
        try:
            return fn(*args, **kwargs)
        except http.client.RemoteDisconnected:
            logger.debug("Connection stale — reconnecting and retrying")
            self._conn.close()
            self._conn = self._make_connection()
            if "conn" in kwargs:
                kwargs["conn"] = self._conn
            try:
                return fn(*args, **kwargs)
            except http.client.RemoteDisconnected:
                raise ServerError(
                    status_code=None,
                    response_body=b"",
                    tableau_error_code=None,
                    tableau_error_message="Connection lost and reconnect failed",
                )

    def _request_with_retry(
        self,
        fn,
        *args,
        max_retries: int = 1,
        **kwargs,
    ) -> Any:
        """Execute *fn* with business-logic retries (auth refresh, rate-limit backoff).

        Stale-connection recovery (``RemoteDisconnected``) is handled by
        ``_call_with_reconnect`` and is fully orthogonal — it never consumes
        the retry budget managed here.
        """
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return self._call_with_reconnect(fn, *args, **kwargs)
            except AuthenticationError as exc:
                last_exception = exc
                if attempt < max_retries:
                    logger.warning(
                        "Authentication error (%s) on attempt %d — re-signing in",
                        exc.tableau_error_code,
                        attempt + 1,
                    )
                    self.token = auth.sign_in(self.config, self._conn)
                    if "token" in kwargs:
                        kwargs["token"] = self.token
                    continue
                raise
            except RateLimitError as exc:
                last_exception = exc
                if attempt < max_retries:
                    wait = exc.retry_after or 60
                    logger.warning(
                        "Rate limited (%s) — waiting %ds before retry",
                        exc.tableau_error_code,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                raise

        # Should never reach here, but satisfies type-checkers
        raise last_exception  # pragma: no cover

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "Session":
        # Parse URL once at entry
        parsed = urlparse(self.config.base_url)
        self._host = parsed.hostname or ""
        self._port = parsed.port or 443
        self._base_path = parsed.path.rstrip("/")

        # Build SSL context
        if self.config.ssl_verify:
            self._ssl_context = ssl.create_default_context()
        else:
            self._ssl_context = ssl._create_unverified_context()

        # Create connection
        self._conn = self._make_connection()

        # Probe server version (no auth required, same connection)
        self.server_info = auth.server_info(self.config, self._conn)

        # Auto-negotiate API version from server's reported REST API version
        self.config.api_version = self.server_info.rest_api_version

        # Authenticate
        self.token = auth.sign_in(self.config, self._conn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._closed:
            self.sign_out()
        if self._conn is not None:
            self._conn.close()
        return False

    def sign_out(self) -> None:
        """Idempotent sign-out."""
        if self._closed:
            return
        try:
            if self.token:
                auth.sign_out(self.token, self.config, conn=self._conn)
        finally:
            self._closed = True

    # ------------------------------------------------------------------
    # Thin delegates to functional API modules
    # ------------------------------------------------------------------

    def list_datasources(
        self, filter_name: str | None = None, **kw
    ) -> list[DatasourceSummary]:
        return self._request_with_retry(
            catalog.list_datasources,
            self.config,
            self.token,
            conn=self._conn,
            filter_name=filter_name,
            **kw,
        )

    def introspect(self, datasource_luid: str) -> DatasourceSchema:
        return self._request_with_retry(
            introspect_datasource.introspect,
            self.config,
            self.token,
            datasource_luid,
            conn=self._conn,
        )

    def query(self, request: QueryRequest) -> QueryResult:
        return self._request_with_retry(
            query, self.config, self.token, request, conn=self._conn
        )

    def query_raw(self, payload: dict) -> QueryResult:
        """Execute a raw VDS query payload (dict) bypassing the typed model."""
        return self._request_with_retry(
            query_raw, self.config, self.token, payload, conn=self._conn
        )

    def health_check(self) -> bool:
        return self._request_with_retry(
            health_check, self.config, self.token, conn=self._conn
        )

    def list_supported_functions(self, datasource_luid: str) -> list[SupportedFunction]:
        return self._request_with_retry(
            list_supported_functions,
            self.config,
            self.token,
            datasource_luid,
            conn=self._conn,
        )

    def list_workbooks(self, **kw) -> list[WorkbookSummary]:
        """Discover Tableau workbooks on the site.

        Delegates to ``catalog.list_workbooks``.  Accepts the same keyword
        arguments (``filter_name``, ``filter_project``, ``page_size``, ``limit``).
        """
        return self._request_with_retry(
            catalog.list_workbooks,
            self.config,
            self.token,
            conn=self._conn,
            **kw,
        )

    def list_views(self, **kw) -> list[ViewSummary]:
        """Discover Tableau views (sheets and dashboards) on the site.

        Delegates to ``catalog.list_views``.  Accepts the same keyword
        arguments (``filter_name``, ``page_size``, ``limit``).
        """
        return self._request_with_retry(
            catalog.list_views,
            self.config,
            self.token,
            conn=self._conn,
            **kw,
        )

    def introspect_workbook(self, workbook_luid: str) -> WorkbookSchema:
        """Retrieve comprehensive structure for a single Tableau workbook.

        Delegates to ``introspect_workbook.introspect_workbook``.
        """
        return self._request_with_retry(
            introspect_workbook.introspect_workbook,
            self.config,
            self.token,
            workbook_luid,
            conn=self._conn,
        )

    def query_view_data(self, view_luid: str, **kw) -> ViewQueryResult:
        """Retrieve tabular data for a Tableau view via the REST API.

        Delegates to ``query_view.query_view_data``.  Accepts the optional
        ``max_age`` keyword argument.
        """
        return self._request_with_retry(
            query_view.query_view_data,
            self.config,
            self.token,
            view_luid,
            conn=self._conn,
            **kw,
        )

    # ------------------------------------------------------------------
    # Inventory delegates (REST-only, Tier 1 discovery)
    # ------------------------------------------------------------------

    def inventory_datasources(self, **kw) -> list[DatasourceInventoryItem]:
        """Return a flat REST-only list of all published datasources on the site.

        Delegates to ``inventory.inventory_datasources``.  Accepts the same
        keyword arguments (``filter_name``, ``filter_project``, ``page_size``,
        ``limit``).  Fast, always completes, no GraphQL.
        """
        return self._request_with_retry(
            inventory.inventory_datasources,
            self.config,
            self.token,
            conn=self._conn,
            **kw,
        )

    def scope_site(self) -> SiteScope:
        """Return total asset counts and project list via fast REST probes.

        Makes 3 ``pageSize=1`` requests for counts (datasources, workbooks,
        views) plus 1 paginated request for the full project list.  Always
        completes regardless of site size — no timeout risk.

        Use this immediately after auth to gauge site scale and understand
        the project taxonomy before calling any ``inventory_*`` methods.

        Returns:
            ``SiteScope`` with asset counts and a full project list.

        Raises:
            CatalogUnavailableError: On any non-2xx REST response.
        """
        return self._request_with_retry(
            inventory.scope_site,
            self.config,
            self.token,
            conn=self._conn,
            server_info=self.server_info,
        )

    def inventory_views(self, **kw) -> list[ViewInventoryItem]:
        """Return a flat REST-only list of all views on the site.

        Always includes ``total_view_count`` (``includeUsageStatistics=true``).
        Delegates to ``inventory.inventory_views``.  Accepts the same keyword
        arguments (``filter_name``, ``page_size``, ``limit``).
        """
        return self._request_with_retry(
            inventory.inventory_views,
            self.config,
            self.token,
            conn=self._conn,
            **kw,
        )

    def inventory_workbooks(self, **kw) -> list[WorkbookInventoryItem]:
        """Return a flat REST-only list of all workbooks on the site.

        Delegates to ``inventory.inventory_workbooks``.  Accepts the same
        keyword arguments (``filter_name``, ``filter_project``, ``page_size``,
        ``limit``).  Fast, always completes, no GraphQL.
        """
        return self._request_with_retry(
            inventory.inventory_workbooks,
            self.config,
            self.token,
            conn=self._conn,
            **kw,
        )

    # ------------------------------------------------------------------
    # Lineage delegates (targeted GraphQL, Tier 2 discovery)
    # ------------------------------------------------------------------

    def datasource_lineage(self, luid: str) -> DatasourceLineage:
        """Fetch lineage for a single published datasource by luid.

        Delegates to ``lineage.datasource_lineage``.  One GraphQL request —
        no pagination.  Use after ``inventory_datasources()`` to understand
        downstream consumers and upstream tables for a candidate datasource.

        Args:
            luid: The luid of the published datasource.

        Returns:
            ``DatasourceLineage`` with downstream and upstream relationship data.

        Raises:
            CatalogUnavailableError: On HTTP error, socket.timeout, or when
                no datasource with the given luid exists.
        """
        return self._request_with_retry(
            lineage.datasource_lineage,
            self.config,
            self.token,
            conn=self._conn,
            luid=luid,
        )

    def workbook_lineage(self, luid: str) -> WorkbookLineage:
        """Fetch lineage for a single workbook by luid.

        Delegates to ``lineage.workbook_lineage``.  One GraphQL request —
        no pagination.  Use after ``inventory_workbooks()`` to understand
        which published datasources power a workbook and what sheets/dashboards
        it contains.

        Args:
            luid: The luid of the workbook.

        Returns:
            ``WorkbookLineage`` with sheets, dashboards, and datasource links.

        Raises:
            CatalogUnavailableError: On HTTP error, socket.timeout, or when
                no workbook with the given luid exists.
        """
        return self._request_with_retry(
            lineage.workbook_lineage,
            self.config,
            self.token,
            conn=self._conn,
            luid=luid,
        )
