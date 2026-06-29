"""Tableau REST API authentication (no tableauserverclient).

Sync transport using http.client (stdlib). No external HTTP dependencies.
"""

import datetime
import http.client
import json
import logging
import socket
import ssl
from dataclasses import dataclass, field
from urllib.parse import urlparse

from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.errors import AuthenticationError
from query_tableau_data_py.models import ServerInfo

logger = logging.getLogger(__name__)

DEFAULT_API_VERSION = "3.21"


@dataclass(frozen=True)
class AuthToken:
    """Immutable token returned by ``sign_in``."""

    token: str
    site_id: str
    user_id: str
    estimated_ttl_minutes: int
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


def _build_pat_payload(config: SdkConfig) -> dict:
    """Build the REST API request body for PAT authentication."""
    return {
        "credentials": {
            "personalAccessTokenName": config.pat_name,
            "personalAccessTokenSecret": config.pat_secret,
            "site": {"contentUrl": config.tableau_site_name},
        }
    }


def _build_password_payload(config: SdkConfig) -> dict:
    """Build the REST API request body for username/password authentication."""
    return {
        "credentials": {
            "name": config.username,
            "password": config.password,
            "site": {"contentUrl": config.tableau_site_name},
        }
    }


def _build_jwt_payload(config: SdkConfig) -> dict:
    """Build the REST API request body for JWT authentication."""
    raise NotImplementedError("JWT authentication is not supported in this version.")


def _select_credential_payload(config: SdkConfig) -> dict:
    """Select the appropriate credential payload based on available triplets."""
    if config.pat_name is not None and config.pat_secret is not None:
        return _build_pat_payload(config)
    if config.username is not None and config.password is not None:
        return _build_password_payload(config)
    if config.jwt_client_id is not None and config.jwt_secret is not None:
        return _build_jwt_payload(config)
    raise AuthenticationError(
        status_code=None,
        response_body=b"",
        tableau_error_code=None,
        tableau_error_message="No valid credential triplet found in config.",
    )


def _parse_ttl(value: str | None) -> int:
    """Parse Tableau's estimatedTimeToExpiration string into minutes.

    Handles common formats defensively. Falls back to 240 minutes
    (Tableau's default token lifetime) with a warning if parsing fails.
    """
    if value is None:
        logger.warning("estimatedTimeToExpiration missing; defaulting to 240 minutes.")
        return 240

    cleaned = value.strip()
    if cleaned.isdigit():
        return int(cleaned)

    # Try ISO 8601 duration (e.g. "PT240M")
    if cleaned.upper().startswith("PT") and cleaned.upper().endswith("M"):
        try:
            return int(cleaned[2:-1])
        except ValueError:
            pass

    # Try HH:MM:SS (e.g. "364:03:56")
    if ":" in cleaned:
        try:
            parts = cleaned.split(":")
            if len(parts) == 3:
                hours, minutes, _seconds = map(int, parts)
                return hours * 60 + minutes
            if len(parts) == 2:
                minutes, _seconds = map(int, parts)
                return minutes
        except ValueError:
            pass

    logger.warning(
        "Could not parse estimatedTimeToExpiration '%s'; defaulting to 240 minutes.",
        value,
    )
    return 240


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


def _raise_auth_error(status_code: int, body: bytes, headers: dict[str, str]) -> None:
    """Raise AuthenticationError from raw response components."""
    tableau_code = None
    tableau_message = None

    try:
        data = json.loads(body.decode("utf-8"))
        if isinstance(data, dict):
            error = data.get("error", {})
            if isinstance(error, dict):
                tableau_code = str(error.get("code", "")) or None
                tableau_message = error.get("message") or None
            else:
                tableau_message = str(error)
    except Exception:
        pass

    raise AuthenticationError(
        status_code=status_code,
        response_body=body,
        response_headers=headers,
        tableau_error_code=tableau_code,
        tableau_error_message=tableau_message,
    )


def sign_in(
    config: SdkConfig,
    conn: http.client.HTTPSConnection | None = None,
) -> AuthToken:
    """Authenticate with Tableau and return an ``AuthToken``.

    Supports PAT and username/password. JWT is not implemented.

    Args:
        config: The SDK configuration containing credentials and server URL.
        conn: Optional ``http.client.HTTPSConnection`` for transport.
            If not provided, a temporary connection is created and closed.

    Returns:
        An ``AuthToken`` containing the session token, site ID, user ID,
        estimated TTL, and creation timestamp.

    Raises:
        AuthenticationError: If the server returns 401, 403, 500, or any
            non-2xx status code.
    """
    payload = _select_credential_payload(config)
    base_path = _get_base_path(config)
    path = f"{base_path}/api/{config.api_version}/auth/signin"
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }

    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("POST", path, body=body, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            _raise_auth_error(resp.status, resp_body, dict(resp.getheaders()))

        data = json.loads(resp_body.decode("utf-8"))
        creds = data["credentials"]
        ttl_str = creds.get("estimatedTimeToExpiration")
        ttl = _parse_ttl(ttl_str)

        return AuthToken(
            token=creds["token"],
            site_id=creds["site"]["id"],
            user_id=creds["user"]["id"],
            estimated_ttl_minutes=ttl,
        )
    finally:
        if should_close:
            conn.close()


def sign_out(
    token: AuthToken,
    config: SdkConfig,
    conn: http.client.HTTPSConnection | None = None,
) -> None:
    """Invalidate an authentication token.

    Args:
        token: The ``AuthToken`` to invalidate.
        config: The SDK configuration.
        conn: Optional ``http.client.HTTPSConnection`` for transport.

    Raises:
        AuthenticationError: On non-2xx responses other than 401
            (token already expired/invalid, which is treated as success).
    """
    base_path = _get_base_path(config)
    path = f"{base_path}/api/{config.api_version}/auth/signout"
    headers = {
        "X-Tableau-Auth": token.token,
        "Accept": "application/json",
    }

    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("POST", path, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status == 401:
            # Token already invalid — idempotent success
            return
        if resp.status >= 400:
            _raise_auth_error(resp.status, resp_body, dict(resp.getheaders()))
    finally:
        if should_close:
            conn.close()


def is_near_expiry(token: AuthToken, threshold_minutes: int = 10) -> bool:
    """Check if a token is within *threshold_minutes* of expiration.

    Args:
        token: The ``AuthToken`` to check.
        threshold_minutes: Minutes before expiration to consider "near".

    Returns:
        ``True`` if the token is within the threshold of expiration
        (or already expired), ``False`` otherwise.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    expiry = token.created_at + datetime.timedelta(minutes=token.estimated_ttl_minutes)
    warning_time = expiry - datetime.timedelta(minutes=threshold_minutes)
    return now >= warning_time


# ---------------------------------------------------------------------------
# Server info (pre-auth probe)
# ---------------------------------------------------------------------------


def _derive_vds_tier(product_version: str) -> tuple[bool, str]:
    """Parse product version and return (vds_available, tier).

    Tier boundaries:
        < 2025.1  → (False, "none")
        >= 2025.1 → (True, "2025.1")
        >= 2025.2 → (True, "2025.2")
        >= 2025.3 → (True, "2025.3")
        >= 2026.1 → (True, "2026.1")

    If product_version cannot be parsed (e.g. empty string, non-numeric),
    returns (False, "none").
    """
    try:
        parts = product_version.split(".")
        major, minor = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return False, "none"

    if (major, minor) >= (2026, 1):
        return True, "2026.1"
    elif (major, minor) >= (2025, 3):
        return True, "2025.3"
    elif (major, minor) >= (2025, 2):
        return True, "2025.2"
    elif (major, minor) >= (2025, 1):
        return True, "2025.1"
    else:
        return False, "none"


def server_info(
    config: SdkConfig,
    conn: http.client.HTTPSConnection | None = None,
) -> ServerInfo:
    """Fetch server version (no auth required). Single GET request.

    Call before sign_in() to determine VDS availability and feature tier.
    Uses the same connection that will be reused for sign_in().

    Args:
        config: The SDK configuration containing the server URL.
        conn: Optional ``http.client.HTTPSConnection`` for transport.
            If not provided, a temporary connection is created and closed.

    Returns:
        A ``ServerInfo`` with product version, build number, REST API version,
        VDS availability flag, and VDS feature tier.

    Raises:
        AuthenticationError: On non-2xx response (server unreachable,
            bad URL, etc.).
    """
    base_path = _get_base_path(config)
    path = f"{base_path}/api/{config.api_version}/serverinfo"
    headers = {"Accept": "application/json"}

    should_close = conn is None
    conn = conn or _make_connection(config)

    try:
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()

        if resp.status >= 400:
            _raise_auth_error(resp.status, resp_body, dict(resp.getheaders()))

        data = json.loads(resp_body.decode("utf-8"))
        si = data["serverInfo"]
        pv = si["productVersion"]
        product_version = pv["value"]
        build_number = pv["build"]
        rest_api_version = si["restApiVersion"]
        vds_available, vds_tier = _derive_vds_tier(product_version)

        return ServerInfo(
            product_version=product_version,
            build_number=build_number,
            rest_api_version=rest_api_version,
            vds_available=vds_available,
            vds_feature_tier=vds_tier,
        )
    finally:
        if should_close:
            conn.close()
