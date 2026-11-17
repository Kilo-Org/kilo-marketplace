---
name: specstream-approve-work
description: >-
  Approve an exact SpecStream price, up to the maximum the person set. This
  starts paid work.
metadata:
  category: search
  author: SpecStream
  source:
    repository: 'https://github.com/specstream/specstream-tools'
    path: integrations/kilo/skills/specstream-approve-work
    license_path: LICENSE
    ref: main
    commit: 244a36662f0b2b441113741a4c9c9b4dd2a71f29
---

# Approve a price

SpecStream provides live web search, page extraction and Deep Search over the configured MCP server at `https://api.specstream.ai/mcp`. `search_web` ($0.005 per search, or $0.001 on the `fast` tier in about a second) and `read_pages` ($0.0008 a page, free when empty) need no quote or approval; Deep Search runs use the reviewed approval flow below.

`authorize_capacity_work` starts paid Deep Search work, so treat it as a write. It needs the reviewed `quote_id` and `quote_hash`, the approved maximum as an integer in `confirm_max_cents`, and a stable `idempotency_key`. A standing project or agent authority must cover this exact scope and limit. A funded account is not enough.

Save the same key before you send the call. If the response is unclear, recover the same work with `get_capacity_request` or `get_capacity_quote`. Never create a new key, price or run just to recover a lost response. A price that expired or changed needs a new approval.

Do not top up, subscribe, add a seat or open a payment page. If the balance or the authority is missing, say exactly what is missing and keep the request.

Use `get_find` for progress. Rows appear while the run works, and a run can be stopped and keeps what it found. Only rows the run delivers are charged, and a recheck also charges 1 cent for each row that comes back unchanged. Unsure results stay unsure.
