#!/usr/bin/env python3
"""Lint a Sent WhatsApp template payload against Meta's category + structural rules.

Usage:
    python lint_waba_template.py <path-to-template.json>

Exits 0 with "OK" if the template passes all checks.
Exits non-zero and prints each issue with the offending field on failure.

Checks performed:
  * Required top-level keys: name, language, category, components.
  * category is one of UTILITY, MARKETING, AUTHENTICATION (Sent's three).
  * language matches BCP-47 (lowercase locale, optional uppercase region: en, en_US).
  * Exactly one BODY component is present with non-empty text
    (AUTHENTICATION templates are exempt — they use managed body content).
  * Placeholders {{1}}..{{N}} in body text are numbered 1..N sequentially with no gaps.
  * Sample value count under example.body_text matches the placeholder count.
  * For UTILITY templates:
      - Promotional phrases ("buy now", "limited time", "special offer",
        "discount", "sale", "free shipping") trigger warnings.
      - "click here to purchase" triggers a hard failure (clear cross-sell).
  * HEADER component (if present): `format` must be one of TEXT, IMAGE, VIDEO,
    DOCUMENT (Sent's allowed CreateTemplateRequest header types).
  * BUTTONS component (if present) is either <=3 QUICK_REPLY OR <=2 CTA
    (URL/PHONE_NUMBER/OTP) — never mixed. Per-button checks:
      - type must be one of QUICK_REPLY, URL, PHONE_NUMBER (Sent's button
        enum) or OTP (Cloud API authentication-only, warned).
      - URL buttons require a non-empty `url` field.
      - PHONE_NUMBER buttons require a non-empty `phone_number` field.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

VALID_CATEGORIES = {"UTILITY", "MARKETING", "AUTHENTICATION"}
LANGUAGE_RE = re.compile(r"^[a-z]{2}(_[A-Z]{2})?$")
PLACEHOLDER_RE = re.compile(r"\{\{(\d+)\}\}")

PROMO_WARN_PHRASES = (
    "buy now",
    "limited time",
    "special offer",
    "discount",
    "sale",
    "free shipping",
)
PROMO_FAIL_PHRASES = ("click here to purchase",)

CTA_BUTTON_TYPES = {"URL", "PHONE_NUMBER", "OTP"}
QUICK_REPLY_TYPE = "QUICK_REPLY"

# Sent CreateTemplateRequest enums (snapshot Template Models section).
SENT_HEADER_TYPES = {"TEXT", "IMAGE", "VIDEO", "DOCUMENT"}
SENT_BUTTON_TYPES = {"QUICK_REPLY", "URL", "PHONE_NUMBER"}


class LintResult:
    def __init__(self) -> None:
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []

    def error(self, field: str, message: str) -> None:
        self.errors.append((field, message))

    def warn(self, field: str, message: str) -> None:
        self.warnings.append((field, message))

    @property
    def failed(self) -> bool:
        return bool(self.errors)


def _components_by_type(components: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for c in components:
        t = c.get("type")
        if not isinstance(t, str):
            continue
        grouped.setdefault(t.upper(), []).append(c)
    return grouped


def _check_top_level(payload: dict[str, Any], result: LintResult) -> None:
    for key in ("name", "language", "category", "components"):
        if key not in payload:
            result.error(key, f"missing required top-level key '{key}'")

    category = payload.get("category")
    if isinstance(category, str) and category not in VALID_CATEGORIES:
        result.error(
            "category",
            f"category '{category}' must be one of {sorted(VALID_CATEGORIES)}",
        )

    language = payload.get("language")
    if isinstance(language, str) and not LANGUAGE_RE.match(language):
        result.error(
            "language",
            f"language '{language}' must match BCP-47 form (e.g. 'en' or 'en_US')",
        )

    components = payload.get("components")
    if components is not None and not isinstance(components, list):
        result.error("components", "components must be a list")


def _check_body(payload: dict[str, Any], result: LintResult) -> None:
    components = payload.get("components")
    if not isinstance(components, list):
        return
    grouped = _components_by_type(components)
    category = payload.get("category")
    body_list = grouped.get("BODY", [])

    if category == "AUTHENTICATION":
        # Authentication body uses managed content (e.g. add_security_recommendation);
        # freeform text is not required and placeholder checks do not apply.
        return

    if not body_list:
        result.error("components", "exactly one BODY component is required")
        return
    if len(body_list) > 1:
        result.error("components", "more than one BODY component is not allowed")

    body = body_list[0]
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        result.error("components[BODY].text", "BODY text must be a non-empty string")
        return

    placeholders = [int(m.group(1)) for m in PLACEHOLDER_RE.finditer(text)]
    if placeholders:
        unique_sorted = sorted(set(placeholders))
        expected = list(range(1, len(unique_sorted) + 1))
        if unique_sorted != expected:
            result.error(
                "components[BODY].text",
                f"placeholders must be sequential starting at 1, got {unique_sorted}",
            )
        first_occurrence = []
        seen: set[int] = set()
        for n in placeholders:
            if n not in seen:
                first_occurrence.append(n)
                seen.add(n)
        if first_occurrence != sorted(first_occurrence):
            result.error(
                "components[BODY].text",
                f"placeholders must first appear in numeric order, got {first_occurrence}",
            )

    example = body.get("example", {})
    body_text = example.get("body_text") if isinstance(example, dict) else None
    placeholder_count = len(set(placeholders))

    if placeholder_count == 0:
        if body_text:
            result.warn(
                "components[BODY].example.body_text",
                "body has no placeholders but example.body_text is present",
            )
        return

    if not isinstance(body_text, list) or not body_text:
        result.error(
            "components[BODY].example.body_text",
            "example.body_text must be a non-empty list of sample rows",
        )
        return
    first_row = body_text[0]
    if not isinstance(first_row, list):
        result.error(
            "components[BODY].example.body_text",
            "example.body_text must be array-of-arrays (one row per variable group)",
        )
        return
    if len(first_row) != placeholder_count:
        result.error(
            "components[BODY].example.body_text",
            f"sample count {len(first_row)} does not match placeholder count {placeholder_count}",
        )


def _check_utility_promo(payload: dict[str, Any], result: LintResult) -> None:
    if payload.get("category") != "UTILITY":
        return
    components = payload.get("components")
    if not isinstance(components, list):
        return
    body_list = _components_by_type(components).get("BODY", [])
    if not body_list:
        return
    text = body_list[0].get("text")
    if not isinstance(text, str):
        return
    lowered = text.lower()
    for phrase in PROMO_FAIL_PHRASES:
        if phrase in lowered:
            result.error(
                "components[BODY].text",
                f"UTILITY body contains banned promotional phrase '{phrase}'",
            )
    for phrase in PROMO_WARN_PHRASES:
        if phrase in lowered:
            result.warn(
                "components[BODY].text",
                f"UTILITY body contains promotional phrase '{phrase}' — Meta is likely to re-categorize as MARKETING",
            )


def _check_header(payload: dict[str, Any], result: LintResult) -> None:
    components = payload.get("components")
    if not isinstance(components, list):
        return
    headers = _components_by_type(components).get("HEADER", [])
    if not headers:
        return
    header = headers[0]
    # In the Cloud API shape used by these fixtures, HEADER type discriminator
    # is `format`; in Sent's shape it would be `type`. Accept either.
    fmt = header.get("format")
    if fmt is None:
        fmt = header.get("type")
    if not isinstance(fmt, str):
        result.error(
            "components[HEADER].format",
            "HEADER component requires a 'format' (TEXT/IMAGE/VIDEO/DOCUMENT)",
        )
        return
    if fmt.upper() not in SENT_HEADER_TYPES:
        result.error(
            "components[HEADER].format",
            f"header format '{fmt}' must be one of {sorted(SENT_HEADER_TYPES)} "
            "(Sent CreateTemplateRequest enum)",
        )


def _check_buttons(payload: dict[str, Any], result: LintResult) -> None:
    components = payload.get("components")
    if not isinstance(components, list):
        return
    button_components = _components_by_type(components).get("BUTTONS", [])
    if not button_components:
        return
    buttons = button_components[0].get("buttons")
    if not isinstance(buttons, list) or not buttons:
        result.error("components[BUTTONS].buttons", "buttons list must be non-empty")
        return
    types = []
    for i, b in enumerate(buttons):
        t = b.get("type")
        if not isinstance(t, str):
            result.error(f"components[BUTTONS].buttons[{i}].type", "button type missing")
            continue
        upper = t.upper()
        types.append(upper)

        # Sent's button type enum is QUICK_REPLY|URL|PHONE_NUMBER. Cloud-API OTP
        # buttons (auth-only) are surfaced as a warning rather than a hard fail
        # because Cloud-API-shaped fixtures use them; they are not part of the
        # Sent CreateTemplateRequest button enum.
        if upper not in SENT_BUTTON_TYPES and upper != "OTP":
            result.error(
                f"components[BUTTONS].buttons[{i}].type",
                f"button type '{t}' must be one of {sorted(SENT_BUTTON_TYPES)} "
                "(Sent CreateTemplateRequest enum)",
            )
            continue
        if upper == "OTP":
            result.warn(
                f"components[BUTTONS].buttons[{i}].type",
                "'OTP' is a Cloud-API auth-only button type; not part of Sent's "
                "button enum (QUICK_REPLY/URL/PHONE_NUMBER)",
            )

        if upper == "URL":
            url = b.get("url")
            if not isinstance(url, str) or not url.strip():
                result.error(
                    f"components[BUTTONS].buttons[{i}].url",
                    "URL buttons require a non-empty 'url' field",
                )
        if upper == "PHONE_NUMBER":
            phone = b.get("phone_number")
            if not isinstance(phone, str) or not phone.strip():
                result.error(
                    f"components[BUTTONS].buttons[{i}].phone_number",
                    "PHONE_NUMBER buttons require a non-empty 'phone_number' field",
                )

    quick = sum(1 for t in types if t == QUICK_REPLY_TYPE)
    cta = sum(1 for t in types if t in CTA_BUTTON_TYPES)
    if quick and cta:
        result.error(
            "components[BUTTONS].buttons",
            "cannot mix QUICK_REPLY and CTA buttons in the same template",
        )
        return
    if quick > 3:
        result.error(
            "components[BUTTONS].buttons",
            f"at most 3 QUICK_REPLY buttons allowed, got {quick}",
        )
    if cta > 2:
        result.error(
            "components[BUTTONS].buttons",
            f"at most 2 CTA buttons allowed, got {cta}",
        )


def lint_template(payload: Any) -> LintResult:
    result = LintResult()
    if not isinstance(payload, dict):
        result.error("<root>", "template payload must be a JSON object")
        return result
    _check_top_level(payload, result)
    _check_body(payload, result)
    _check_utility_promo(payload, result)
    _check_header(payload, result)
    _check_buttons(payload, result)
    return result


def _format(prefix: str, entries: list[tuple[str, str]]) -> str:
    return "\n".join(f"{prefix} {field}: {msg}" for field, msg in entries)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="lint_waba_template.py",
        description="Lint a Sent WhatsApp template payload against Meta's structural and category rules.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a JSON file containing a WhatsApp template payload.",
    )
    args = parser.parse_args(argv)

    try:
        raw = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"could not read {args.path}: {exc}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON in {args.path}: {exc}", file=sys.stderr)
        return 2

    result = lint_template(payload)

    if result.warnings:
        print(_format("WARN", result.warnings))
    if result.errors:
        print(_format("FAIL", result.errors))
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
