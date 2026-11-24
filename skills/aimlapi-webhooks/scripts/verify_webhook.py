"""Verify an AI/ML API webhook (Standard Webhooks). Standard library only.

    from verify_webhook import verify, WebhookVerificationError
    event = verify(raw_body_bytes, request_headers, os.environ["AIMLAPI_WEBHOOK_SECRET"])

`raw_body` must be the exact bytes received, before any JSON parsing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Mapping

TOLERANCE_SECONDS = 300


class WebhookVerificationError(Exception):
    pass


def _header(headers: Mapping[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name:
            return value
    raise WebhookVerificationError(f"missing {name} header")


def sign(secret: str, msg_id: str, timestamp: int | str, body: bytes) -> str:
    """The `v1,<base64>` signature for one message; used by verify() and by tests."""
    try:
        key = base64.b64decode((secret or "").removeprefix("whsec_"), validate=True)
    except ValueError as err:
        raise WebhookVerificationError("the webhook secret is not valid base64") from err
    if len(key) < 16:
        # An empty or truncated secret would let anyone forge a signature.
        raise WebhookVerificationError("the webhook secret is empty or too short; load the whsec_... value")
    signed = f"{msg_id}.{timestamp}.".encode() + body
    digest = hmac.new(key, signed, hashlib.sha256).digest()
    return "v1," + base64.b64encode(digest).decode()


def verify(raw_body: bytes, headers: Mapping[str, str], secret: str, *, now: float | None = None) -> Any:
    """Return the parsed event, or raise WebhookVerificationError."""
    if isinstance(raw_body, str):
        raw_body = raw_body.encode()
    msg_id = _header(headers, "webhook-id")
    timestamp = _header(headers, "webhook-timestamp")
    signatures = _header(headers, "webhook-signature")

    try:
        ts = int(timestamp)
    except ValueError as err:
        raise WebhookVerificationError("bad webhook-timestamp") from err
    current = time.time() if now is None else now
    if abs(current - ts) > TOLERANCE_SECONDS:
        raise WebhookVerificationError("webhook-timestamp outside the tolerance window")

    expected = sign(secret, msg_id, timestamp, raw_body).split(",", 1)[1].encode()
    # During a secret rotation the header carries several space-separated signatures.
    for candidate in signatures.split(" "):
        version, _, value = candidate.partition(",")
        if version == "v1" and hmac.compare_digest(value.encode(), expected):
            return json.loads(raw_body)
    raise WebhookVerificationError("no matching signature")
