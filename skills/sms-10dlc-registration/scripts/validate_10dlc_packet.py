#!/usr/bin/env python3
"""Validate a Sent 10DLC compliance packet before it is filed with TCR.

Usage:
    python validate_10dlc_packet.py <path-to-packet.json>

The packet is a JSON object representing the answers a tenant submitted on
Sent's compliance form. Field names match the verified Sent compliance form
in the dashboard (see references/10dlc-evidence-checklist.md). The validator
checks the mechanical things that are cheap to catch locally and expensive
to discover after TCR or a carrier rejects the submission. Semantic checks
(use-case match, content policy) are out of scope.

Expected shape:

    {
      "legal_business_name": "Example Corp LLC",
      "business_registration_number": "IL-12345678",
      "business_type": "PRIVATE_PROFIT",
      "industry_category": "RETAIL",
      "ein": "12-3456789",
      "business_address": "123 Main St, Springfield, IL 62701, US",
      "business_phone": "+12175550101",
      "contact_email": "compliance@example.com",
      "website": "https://example.com",
      "privacy_policy_url": "https://example.com/privacy",
      "opt_in_mechanism_url": "https://example.com/signup",
      "opt_keywords": {
        "stop": ["STOP"],
        "start": ["START"],
        "help": ["HELP"]
      },
      "use_cases": [
        {
          "selection": "Notifications",
          "description": "Shipping and delivery updates for orders.",
          "sample_messages": [
            "Example: Your order #1029 has shipped. Reply STOP to opt out."
          ]
        }
      ]
    }

Exits 0 with `OK` on success. On failure, prints one issue per line in the
form `<path>: <field>: <reason>` and exits 1.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

# Required top-level keys on the packet. Match the verified Sent compliance
# form field names — business identity, US-required URLs, opt keywords, and
# use cases.
REQUIRED_TOP_LEVEL = (
    "legal_business_name",
    "business_registration_number",
    "business_type",
    "industry_category",
    "ein",
    "business_address",
    "business_phone",
    "contact_email",
    "website",
    "privacy_policy_url",
    "opt_in_mechanism_url",
    "opt_keywords",
    "use_cases",
)

# Required keys on each use case.
REQUIRED_USE_CASE = (
    "selection",
    "description",
    "sample_messages",
)

# Verified use-case selection values from the Sent compliance form.
VALID_USE_CASE_SELECTIONS = (
    "Authentication",
    "Notifications",
    "Marketing",
    "Customer Service",
    "High Volume",
)

URL_FIELDS = ("website", "privacy_policy_url", "opt_in_mechanism_url")

# Permissive URL regex: scheme + host + optional path. Catches obvious junk
# (no scheme, internal whitespace, missing host) without trying to be a full
# RFC 3986 validator.
URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

# EIN: 9 digits, optionally hyphenated after the first two.
EIN_RE = re.compile(r"^\d{2}-?\d{7}$")

# E.164 phone number: leading +, then 1-15 digits.
PHONE_RE = re.compile(r"^\+\d{1,15}$")

# Permissive email regex — local@domain.tld.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Minimum length of a sample message before reviewers flag it as too generic.
MIN_SAMPLE_LEN = 20


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate(packet: dict[str, Any], path: str) -> list[str]:
    """Return a list of issue strings. Empty list means the packet is valid."""
    issues: list[str] = []

    def issue(field: str, reason: str) -> None:
        issues.append(f"{path}: {field}: {reason}")

    if not isinstance(packet, dict):
        issue("<root>", "packet must be a JSON object")
        return issues

    # Top-level required keys.
    for key in REQUIRED_TOP_LEVEL:
        if key not in packet:
            issue(key, "missing required field")
        elif key == "use_cases":
            if not isinstance(packet[key], list) or len(packet[key]) == 0:
                issue(key, "must be a non-empty list")
        elif key == "opt_keywords":
            if not isinstance(packet[key], dict):
                issue(key, "must be a JSON object with stop/start/help keys")
        elif not _is_nonempty_string(packet[key]):
            issue(key, "must be a non-empty string")

    # URL fields.
    for key in URL_FIELDS:
        value = packet.get(key)
        if _is_nonempty_string(value) and not URL_RE.match(value):
            issue(key, f"not a valid URL: {value!r}")

    # EIN format.
    ein = packet.get("ein")
    if _is_nonempty_string(ein) and not EIN_RE.match(ein):
        issue("ein", f"must match ^\\d{{2}}-?\\d{{7}}$ (got {ein!r})")

    # Business phone format (E.164).
    phone = packet.get("business_phone")
    if _is_nonempty_string(phone) and not PHONE_RE.match(phone):
        issue(
            "business_phone",
            f"must be E.164 (+CCNNNNNNNNNN, got {phone!r})",
        )

    # Contact email format.
    email = packet.get("contact_email")
    if _is_nonempty_string(email) and not EMAIL_RE.match(email):
        issue("contact_email", f"not a valid email address: {email!r}")

    # Opt keywords — at minimum STOP must be configured.
    opt_keywords = packet.get("opt_keywords")
    if isinstance(opt_keywords, dict):
        stop = opt_keywords.get("stop")
        if not isinstance(stop, list) or not any(
            _is_nonempty_string(kw) and kw.strip().upper() == "STOP"
            for kw in stop
        ):
            issue(
                "opt_keywords.stop",
                "must include 'STOP' as an opt-out keyword (configured in "
                "the Compliance → Opt Keywords dashboard tab)",
            )

    # Use cases.
    use_cases = packet.get("use_cases")
    if isinstance(use_cases, list):
        for i, uc in enumerate(use_cases):
            prefix = f"use_cases[{i}]"
            if not isinstance(uc, dict):
                issue(prefix, "must be a JSON object")
                continue

            for key in REQUIRED_USE_CASE:
                if key not in uc:
                    issue(f"{prefix}.{key}", "missing required field")

            selection = uc.get("selection")
            description = uc.get("description")
            if "selection" in uc:
                if not _is_nonempty_string(selection):
                    issue(f"{prefix}.selection", "must be a non-empty string")
                elif selection not in VALID_USE_CASE_SELECTIONS:
                    issue(
                        f"{prefix}.selection",
                        f"must be one of {VALID_USE_CASE_SELECTIONS} "
                        f"(got {selection!r})",
                    )
            if "description" in uc and not _is_nonempty_string(description):
                issue(f"{prefix}.description", "must be a non-empty string")

            samples = uc.get("sample_messages")
            if "sample_messages" in uc:
                if not isinstance(samples, list) or len(samples) == 0:
                    issue(
                        f"{prefix}.sample_messages",
                        "must be a non-empty list (>=1 sample per use case)",
                    )
                else:
                    for j, sample in enumerate(samples):
                        sprefix = f"{prefix}.sample_messages[{j}]"
                        if not _is_nonempty_string(sample):
                            issue(sprefix, "must be a non-empty string")
                        elif len(sample.strip()) < MIN_SAMPLE_LEN:
                            issue(
                                sprefix,
                                f"sample is {len(sample.strip())} chars; "
                                f"reviewers flag samples under {MIN_SAMPLE_LEN} as too generic",
                            )

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_10dlc_packet.py",
        description=(
            "Validate a Sent 10DLC compliance packet (JSON) before filing "
            "with The Campaign Registry. Checks required fields, URL / EIN "
            "/ phone / email format, use-case selection, sample-message "
            "length, and opt-out keyword configuration. See "
            "references/10dlc-evidence-checklist.md for the field-by-field "
            "rationale."
        ),
    )
    parser.add_argument("packet", help="Path to the packet JSON file")
    args = parser.parse_args(argv)

    path = args.packet

    try:
        with open(path, encoding="utf-8") as f:
            packet = json.load(f)
    except FileNotFoundError:
        print(f"{path}: <file>: not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"{path}: <file>: invalid JSON ({e})", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"{path}: <file>: could not read ({e})", file=sys.stderr)
        return 1

    issues = validate(packet, path)
    if issues:
        for line in issues:
            print(line, file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
