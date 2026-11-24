#!/usr/bin/env python3
"""Read what an AI/ML API decision model or router accepts, from its live schema. Standard library only; no API key.

  decide.py shape <model-id>        # request shape, question types and limits, media fields
  decide.py judges [<router-id>]    # decision models a router accepts in router.decision_model

Add --json for machine-readable output. Sending a free test request: POST /v1/decisions with the header X-AIMLAPI-Sandbox: 1.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.aimlapi.com"
# A named User-Agent shows which requests come from these skills; it is not needed for access.
CLIENT = "aimlapi-skills/1.0.5 decide.py"
DECISIONS = "internal/decisions"
CHAT = "openai/chat-completions"
MEDIA_FIELDS = ("images", "assets", "videos", "audios", "media")
LIMIT_KEYS = ("minProperties", "maxProperties", "minItems", "maxItems")


def get(path: str, params: dict | None = None) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v})
    url = path if path.startswith("http") else API + path
    if query:
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": CLIENT, "x-aimlapi-client": CLIENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        sys.exit(f"GET {url} -> {err.code}: {err.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.URLError as err:
        sys.exit(f"GET {url} failed: {err.reason}")


def docs_json(model_id: str, type_: str) -> tuple[str, dict]:
    """(canonical id, OpenAPI document) of one model on one endpoint type."""
    data = get("/v1/models", {"id": model_id, "type": type_}).get("data", [])
    if not data:
        sys.exit(f"{model_id}: not listed with type {type_}. List them: curl -s '{API}/v1/models?type={type_}'")
    entry = data[0]
    doc = entry.get("info", {}).get("docsJson")
    if not doc:
        sys.exit(f"{entry['id']}: no docsJson in the catalogue")
    return entry["id"], doc if isinstance(doc, dict) else get(doc)


def request_variants(doc: dict) -> list[dict]:
    """Every request-body schema variant of the document's single operation."""
    for ops in doc.get("paths", {}).values():
        for op in ops.values():
            schema = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            return schema.get("anyOf") or schema.get("oneOf") or [schema]
    return []


def limits(spec: dict) -> dict:
    return {k: spec[k] for k in LIMIT_KEYS if k in spec}


def refused(spec: dict) -> bool:
    desc = (spec.get("description") or "").lower()
    return spec.get("maxItems") == 0 or desc.startswith("not supported")


def summarize(variant: dict) -> dict:
    """Shape, required fields, question types and media fields of one request variant."""
    props = variant.get("properties", {})
    questions = props.get("questions", {})
    if questions.get("type") == "array":
        shape, items = "openai", questions.get("items", {})
    else:
        shape, items = "system-one", questions.get("additionalProperties", {})
    types = []
    for q in items.get("oneOf") or items.get("anyOf") or []:
        qprops = q.get("properties", {})
        name = (qprops.get("type", {}).get("enum") or ["?"])[0]
        fields = {k: limits(v) for k, v in qprops.items() if k != "type"}
        types.append({"type": name, "required": [r for r in q.get("required", []) if r != "type"], "fields": fields})
    media = {}
    for field in MEDIA_FIELDS:
        if field in props:
            spec = props[field]
            media[field] = {"accepted": not refused(spec), **limits(spec), "description": (spec.get("description") or "")[:240]}
    return {
        "shape": shape,
        "content_field": "input" if shape == "openai" else "state",
        "required": variant.get("required", []),
        "questions": limits(questions),
        "types": types,
        "media": media,
        "other": sorted(k for k in props if k not in {"model", "state", "input", "questions", *MEDIA_FIELDS}),
    }


def judges(doc: dict) -> list[str]:
    """Values of router.decision_model in a router's schema, in the order published."""
    found: list[str] = []
    for variant in request_variants(doc):
        router = variant.get("properties", {}).get("router", {})
        for value in router.get("properties", {}).get("decision_model", {}).get("enum", []):
            if value not in found:
                found.append(value)
    return found


def fmt_limits(lim: dict) -> str:
    lo = lim.get("minProperties", lim.get("minItems"))
    hi = lim.get("maxProperties", lim.get("maxItems"))
    if lo is None and hi is None:
        return ""
    return f"{'' if lo is None else lo}..{'' if hi is None else hi}"


def cmd_shape(a) -> None:
    model_id, doc = docs_json(a.model, DECISIONS)
    variants = request_variants(doc)
    if not variants:
        sys.exit(f"{model_id}: the schema has no request body")
    out = {"id": model_id, **summarize(variants[0])}
    if a.json:
        print(json.dumps(out, indent=2))
        return
    label = "OpenAI Decisions: input + questions array" if out["shape"] == "openai" else "System One: state + questions object"
    print(f"{model_id}  shape: {out['shape']} ({label})")
    print(f"  required: {', '.join(out['required'])}")
    print(f"  questions: {fmt_limits(out['questions']) or 'no stated limit'}")
    for t in out["types"]:
        extra = " ".join(f"{k} {fmt_limits(v)}" for k, v in t["fields"].items() if fmt_limits(v))
        optional = [k for k in t["fields"] if k not in t["required"]]
        line = f"    {t['type']:<10} needs {', '.join(t['required']) or '-'}"
        line += f"; optional {', '.join(optional)}" if optional else ""
        print(line + (f"  ({extra})" if extra else ""))
    for field, m in out["media"].items():
        state = f"accepted {fmt_limits(m)}".rstrip() if m["accepted"] else "refused"
        print(f"  {field:<8} {state}: {m['description']}")
    if out["other"]:
        print(f"  other fields: {', '.join(out['other'])}")
    if len(variants) > 1:
        print(f"  note: {len(variants)} schema variants; this is the first. Read the full schema for the others.")


def cmd_judges(a) -> None:
    router_id, doc = docs_json(a.router, CHAT)
    found = judges(doc)
    if a.json:
        print(json.dumps({"router": router_id, "decision_models": found}, indent=2))
        return
    if not found:
        sys.exit(f"{router_id}: no router.decision_model in its schema; is it a router?")
    print(f"{router_id} accepts router.decision_model:")
    for value in found:
        print(f"  {value}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shape", help="request shape and limits of a decision model")
    s.add_argument("model")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_shape)
    j = sub.add_parser("judges", help="decision models a router accepts")
    j.add_argument("router", nargs="?", default="aimlapi/dynamic-router")
    j.add_argument("--json", action="store_true")
    j.set_defaults(func=cmd_judges)
    a = p.parse_args(argv)
    a.func(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
