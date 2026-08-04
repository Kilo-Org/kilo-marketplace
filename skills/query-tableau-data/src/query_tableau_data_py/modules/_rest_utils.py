"""Shared REST transport helpers used by catalog.py, inventory.py, and lineage.py.

Internal module — underscore prefix signals it is not part of the public API.
Do not import this from outside the modules/ package.

Extracted from catalog.py when lineage.py became the third consumer of these
helpers (three-consumer rule documented in f4z.34 review / f4z.35 design).
"""

from __future__ import annotations

import http.client
import ssl
from urllib.parse import urlparse

from query_tableau_data_py.config import SdkConfig


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


_MAX_PAGE_SIZE = 1000


def _clamp_page_size(page_size: int) -> int:
    """Clamp page_size to the API maximum."""
    return min(page_size, _MAX_PAGE_SIZE)


def _build_rest_filter(
    filter_name: str | None,
    filter_project: str | None,
) -> str | None:
    """Build the REST filter expression from caller-supplied filters.

    Format: ``field:operator:value``; multiple filters comma-separated.
    """
    parts: list[str] = []
    if filter_name is not None:
        parts.append(f"name:eq:{filter_name}")
    if filter_project is not None:
        parts.append(f"projectName:eq:{filter_project}")
    return ",".join(parts) if parts else None
