#!/usr/bin/env python3
"""Query the AI/ML API model catalogue. Standard library only; no API key needed.

  models.py search <text> [--type T] [--limit N]
  models.py list [--type T] [--tag T] [--output M] [--input M] [--capability C] [--sort newest|name] [--limit N]
  models.py params <model-id> [--type T]
  models.py price <model-id> [--type T] [--tokens N] [--batch]
  models.py speed <model-id> [<model-id> ...]
  models.py status <model-id>

Add --json to any command for machine-readable output.
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
CLIENT = "aimlapi-skills/1.0.5 models.py"


def get(path: str, params: dict | None = None) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v}, doseq=True)
    url = f"{path}?{query}" if query else path
    if not url.startswith("http"):
        url = API + url
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": CLIENT, "x-aimlapi-client": CLIENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")[:500]
        sys.exit(f"GET {url} -> {err.code}: {body}")
    except urllib.error.URLError as err:
        sys.exit(f"GET {url} failed: {err.reason}")


def catalogue(**filters) -> list[dict]:
    return get("/v1/models", filters).get("data", [])


def one(model_id: str, type_: str | None) -> dict:
    data = catalogue(id=model_id, type=type_, include="all")
    if not data:
        sys.exit(f"{model_id}: not in the catalogue. Run `models.py status {model_id}` to see whether it was retired.")
    # Prefer the endpoint a caller most likely means: batch types last.
    data.sort(key=lambda m: ("batches" in m["type"], m["type"] != "openai/chat-completions"))
    if len(data) > 1 and not type_:
        types = ", ".join(m["type"] for m in data)
        print(f"note: {model_id} is served through several endpoint types ({types}); showing {data[0]['type']}. Pass --type to choose.", file=sys.stderr)
    return data[0]


def group(data: list) -> list:
    """One row per model id: the catalogue lists a model once per endpoint type."""
    merged: dict[str, dict] = {}
    for m in data:
        if m["id"] in merged:
            merged[m["id"]]["types"].append(m["type"])
        else:
            merged[m["id"]] = {**m, "types": [m["type"]]}
    for m in merged.values():
        m["types"].sort(key=lambda t: ("batches" in t, t != "openai/chat-completions", t))
        m["type"] = m["types"][0]
    return list(merged.values())


def row(m: dict) -> str:
    info = m.get("info", {})
    ctx = info.get("contextLength")
    extra = f" ctx={ctx}" if ctx else ""
    types = m.get("types") or [m["type"]]
    shown = types[0] + (f" +{len(types) - 1}" if len(types) > 1 else "")
    return f"{m['id']:<55} {shown:<40} {info.get('releasedAt', ''):<10}{extra}"


def cmd_search(a) -> None:
    text = a.text.lower()
    hits = [
        m
        for m in catalogue(type=a.type)
        if text in m["id"].lower()
        or any(text in alias.lower() for alias in m.get("aliases", []))
        or text in m.get("info", {}).get("name", "").lower()
        or text in m.get("info", {}).get("description", "").lower()
    ]
    # Newest first, so the current version of a family comes before its older snapshots.
    hits = group(hits)
    hits.sort(key=lambda m: m["id"])
    hits.sort(key=lambda m: m.get("info", {}).get("releasedAt") or "", reverse=True)
    hits.sort(key=lambda m: text not in m["id"].lower())
    emit(a, hits[: a.limit], lambda: [print(row(m)) for m in hits[: a.limit]])


def cmd_list(a) -> None:
    data = catalogue(
        type=a.type,
        tags=a.tag,
        output_modalities=a.output,
        input_modalities=a.input,
        capabilities=a.capability,
    )
    data = group(data)
    if a.sort == "newest":
        data.sort(key=lambda m: m.get("info", {}).get("releasedAt") or "", reverse=True)
    else:
        data.sort(key=lambda m: m["id"])
    emit(a, data[: a.limit], lambda: [print(row(m)) for m in data[: a.limit]])


def request_schema(doc: dict) -> dict:
    for path_item in doc.get("paths", {}).values():
        for op in path_item.values():
            schema = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
            if schema:
                return schema
    return {}


def flatten(schema: dict) -> tuple[dict, set]:
    """Merge alternatives into one parameter list. A field is required only if every alternative requires it."""
    props, required = dict(schema.get("properties", {})), set(schema.get("required", []))
    for sub in schema.get("allOf", []):
        p, r = flatten(sub)
        for name, spec in p.items():
            props.setdefault(name, spec)
        required |= r
    for key in ("anyOf", "oneOf"):
        alternatives = [flatten(sub) for sub in schema.get(key, [])]
        for p, _ in alternatives:
            for name, spec in p.items():
                props.setdefault(name, spec)
        if alternatives:
            required |= set.intersection(*(r for _, r in alternatives))
    return props, required


def describe(spec: dict) -> str:
    alternatives = spec.get("anyOf") or spec.get("oneOf")
    if alternatives and "type" not in spec:
        text = " | ".join(describe(alt) for alt in alternatives)
        return text + (f" default {json.dumps(spec['default'])}" if "default" in spec else "")
    parts = [spec.get("type", "object")]
    if spec.get("type") == "object" and spec.get("properties"):
        parts = ["{" + ", ".join(spec["properties"]) + "}"]
    if "enum" in spec:
        values = spec["enum"]
        shown = ", ".join(json.dumps(v) for v in values[:12])
        parts.append(f"one of [{shown}{', …' if len(values) > 12 else ''}]")
    for bound, label in (("minimum", ">="), ("maximum", "<=")):
        if bound in spec:
            parts.append(f"{label}{spec[bound]}")
    if "default" in spec:
        parts.append(f"default {json.dumps(spec['default'])}")
    return " ".join(parts)


def cmd_params(a) -> None:
    m = one(a.model, a.type)
    url = m.get("info", {}).get("docsJson")
    if not url:
        sys.exit(f"{m['id']}: no docsJson in the catalogue; read its docs page instead: {m.get('info', {}).get('docsUrl', 'n/a')}")
    props, required = flatten(request_schema(get(url)))
    if a.json:
        print(json.dumps({"id": m["id"], "type": m["type"], "required": sorted(required), "properties": props}, indent=2))
        return
    print(f"{m['id']}  ({m['type']})")
    for name, spec in props.items():
        flag = "required" if name in required else "optional"
        print(f"  {name:<28} {flag:<9} {describe(spec)}")


def unit_line(u: dict) -> str:
    per = u.get("per", 1) or 1
    tag = (u.get("tag") or {}).get("name")
    label = f"{u.get('name', '')} {u.get('origin', '')} by {u.get('author', '')}{f' ({tag})' if tag else ''}"
    return f"{label:<36} {u.get('price')} per {per}  (= {u.get('price', 0) / per:.10g} per {u.get('name', 'unit')})"


def bands(pricing: dict) -> list[tuple[int, list]]:
    """Context-size bands as (from_tokens, units), lowest first. One band when the price does not change."""
    found = sorted(((int(t.get("from", 0)), t.get("units") or []) for t in pricing.get("thresholds") or []), key=lambda b: b[0])
    return found if len(found) > 1 else [(0, pricing.get("units") or [])]


def band_for(found: list[tuple[int, list]], tokens: int) -> tuple[int, list]:
    """The band a request of `tokens` falls in: the highest `from` not above it."""
    chosen = found[0]
    for start, units in found:
        if start <= tokens:
            chosen = (start, units)
    return chosen


def unit_key(u: dict) -> tuple:
    return (u.get("name"), u.get("origin"), u.get("author"), (u.get("tag") or {}).get("name"))


def print_fixed(pricing: dict, tokens: int | None, indent: str = "  ") -> None:
    found = bands(pricing)
    in_bands = {unit_key(u) for _, units in found for u in units}
    every = [u for u in pricing.get("units") or [] if unit_key(u) not in in_bands] if len(found) > 1 else []
    if tokens is not None:
        start, units = band_for(found, tokens)
        print(f"{indent}band for {tokens} tokens: from {start}")
        for u in units:
            print(f"{indent}  {unit_line(u)}")
        nxt = [b for b, _ in found if b > tokens]
        if nxt and nxt[0] - tokens < max(tokens // 10, 1):
            print(f"{indent}  note: the next band starts at {nxt[0]} tokens; a slightly longer request costs more")
        for u in every:
            print(f"{indent}  {unit_line(u)}")
        return
    if len(found) > 1:
        print(f"{indent}the whole request is priced at one band, chosen by its size in tokens; pass --tokens N to pick one")
    for start, units in found:
        if len(found) > 1:
            print(f"{indent}from {start} tokens:")
        for u in units:
            print(f"{indent}  {unit_line(u)}")
    if every:
        print(f"{indent}the same in every band:")
        for u in every:
            print(f"{indent}  {unit_line(u)}")


def cmd_price(a) -> None:
    m = one(a.model, a.type)
    pricing = m.get("pricing")
    if a.json:
        print(json.dumps({"id": m["id"], "type": m["type"], "pricing": pricing}, indent=2))
        return
    if not pricing:
        sys.exit(f"{m['id']}: no pricing in the catalogue.")
    if a.batch:
        if not pricing.get("batch"):
            sys.exit(f"{m['id']}: no batch price; it cannot run in a batch.")
        pricing = {**pricing["batch"], "kind": "fixed", "currency": pricing.get("currency")}
    kind = pricing.get("kind")
    print(f"{m['id']}  ({m['type']})  kind={kind}  currency={pricing.get('currency')}{'  batch price' if a.batch else ''}")
    if kind == "fixed":
        print_fixed(pricing, a.tokens)
    elif kind == "variants":
        print(f"  depends on: {', '.join(pricing.get('dimensions', []))}")
        for v in pricing.get("variants", []):
            per = v.get("per", 1) or 1
            print(f"  {json.dumps(v.get('when', {}))}: {v.get('price')} per {per} {v.get('unit', '')}")
    else:
        print("  cannot be quoted before the request; read the cost of the call afterwards (x-aimlapi-usd-spent, meta.usage).")


def cmd_status(a) -> None:
    live = catalogue(id=a.model)
    feed = [
        e
        for e in get("/v1/models/deprecations").get("data", [])
        if e["id"] == a.model or a.model in e.get("aliases", [])
    ]
    result = {
        "model": a.model,
        "in_catalogue": [{"id": m["id"], "type": m["type"]} for m in live],
        "deprecation": feed[0] if feed else None,
    }
    if a.json:
        print(json.dumps(result, indent=2))
        return
    if live:
        serving = ", ".join("{} ({})".format(m["id"], m["type"]) for m in live)
        print(f"{a.model}: serving as {serving}")
    if feed:
        e = feed[0]
        print(f"{a.model}: {e['status']}; deprecated_at={e['deprecated_at']} shutdown_at={e['shutdown_at']} replaced_by={e['replaced_by']}")
    if not live and not feed:
        print(f"{a.model}: not in the catalogue and not in the deprecation feed; it probably never existed. Try `models.py search`.")


def cmd_speed(a) -> None:
    """Live latency over the last few minutes, from GET /models/metrics (no key)."""
    answer = get("/models/metrics", {"aliases": a.models})
    rows = answer.get("models", [])
    if a.json:
        print(json.dumps(answer, indent=2))
        return
    window = answer.get("window_seconds")
    print(f"window: last {window} s, successful requests only (generated {answer.get('generated_at')})")
    for name in a.models:
        found = [r for r in rows if r.get("alias") == name]
        if not found:
            print(f"{name}: no data in the window (no successful requests, or not this exact id or alias)")
        for r in found:
            m = r.get("metrics", {})
            parts = []
            for key, label in (("ttft_ms", "first token ms"), ("duration_ms", "duration ms"), ("tps", "tokens/s")):
                if key in m:
                    parts.append(f"{label} p50 {m[key]['p50']:g} / p90 {m[key]['p90']:g}")
            print(f"{name}  ({r.get('endpoint')}): " + ("; ".join(parts) or "no metrics"))


def emit(a, data, text) -> None:
    if a.json:
        print(json.dumps(data, indent=2))
    elif not data:
        print("no models match", file=sys.stderr)
    else:
        text()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("text")
    s.add_argument("--type")
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("list")
    for flag in ("--type", "--tag", "--output", "--input", "--capability"):
        s.add_argument(flag)
    s.add_argument("--sort", choices=("newest", "name"), default="name")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("params")
    s.add_argument("model")
    s.add_argument("--type")
    s.set_defaults(fn=cmd_params)

    s = sub.add_parser("price")
    s.add_argument("model")
    s.add_argument("--type")
    s.add_argument("--tokens", type=int, help="request size in tokens (prompt plus max output) to pick the price band")
    s.add_argument("--batch", action="store_true", help="show the batch price instead")
    s.set_defaults(fn=cmd_price)

    s = sub.add_parser("speed", help="live latency and throughput of one or more models")
    s.add_argument("models", nargs="+")
    s.set_defaults(fn=cmd_speed)

    s = sub.add_parser("status")
    s.add_argument("model")
    s.set_defaults(fn=cmd_status)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
