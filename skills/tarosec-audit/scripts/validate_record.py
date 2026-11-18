#!/usr/bin/env python3
"""Validate a Tarosec JSON record against a Tarosec schema (stdlib only).

Supports the JSON Schema subset used by the bundled Tarosec schemas.

Usage: validate_record.py SCHEMA.json RECORD.json
Exit: 0 valid, 1 invalid, 2 usage/IO error.

Canonical copy: scripts/validate_record.py (synced into each skill by
scripts/sync_shared.py).
"""
from __future__ import annotations

import json
import math
import re
import sys
from typing import Any

ANNOTATIONS = {"$schema", "$id", "title", "description"}
SUPPORTED = ANNOTATIONS | {
    "type", "const", "enum", "required", "properties", "additionalProperties",
    "items", "minItems", "minLength", "minimum", "pattern", "uniqueItems",
}
TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "integer": int, "number": (int, float),
}


def _type_ok(value: Any, name: str) -> bool:
    if name in ("integer", "number") and isinstance(value, bool):
        return False
    return isinstance(value, TYPES[name])


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON object key")
        obj[key] = value
    return obj


def _invalid_constant(_: str) -> None:
    raise ValueError("non-finite JSON number")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        _invalid_constant(value)
    return number


def load_json(file) -> Any:
    return json.load(file, object_pairs_hook=_unique_object, parse_constant=_invalid_constant,
                     parse_float=_finite_float)


def validate(value: Any, schema: dict, path: str = "$") -> list[str]:
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object"]
    unknown = set(schema) - SUPPORTED
    if unknown:
        return [f"{path}: schema uses unsupported keyword(s) {sorted(unknown)}"]
    errors: list[str] = []
    if "type" in schema and not _type_ok(value, schema["type"]):
        return [f"{path}: expected {schema['type']}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value outside allowed choices")
    if _type_ok(value, "number") and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: below minimum {schema['minimum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errors.append(f"{path}: items not unique")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required '{key}'")
        props = schema.get("properties", {})
        for key, sub in value.items():
            if key in props:
                errors += validate(sub, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: validate_record.py SCHEMA.json RECORD.json", file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as f:
            schema = load_json(f)
        with open(argv[2], encoding="utf-8") as f:
            record = load_json(f)
        errors = validate(record, schema)
    except (OSError, ValueError, TypeError, KeyError, re.error, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for e in errors:
        print(e)
    print("VALID" if not errors else f"INVALID ({len(errors)} error(s))")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
