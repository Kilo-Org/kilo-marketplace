---
name: specstream-review-work
description: Get the real SpecStream price for a Deep Search request. Nothing runs.
metadata:
  category: search
  author: SpecStream
  source:
    repository: 'https://github.com/specstream/specstream-tools'
    path: integrations/kilo/skills/specstream-review-work
    license_path: LICENSE
    ref: main
    commit: 244a36662f0b2b441113741a4c9c9b4dd2a71f29
---

# See the price

SpecStream provides live web search, page extraction and Deep Search over the configured MCP server at `https://api.specstream.ai/mcp`. `search_web` ($0.005 per search, or $0.001 on the `fast` tier in about a second) and `read_pages` ($0.0008 a page, free when empty) run directly without a quote; Deep Search runs require a reviewed quote first.

Call `quote_capacity_work` with the `ast_hash` from `compile`, the operation, the number of results wanted, the useful minimum, and the original `parent_find_id`, `project_id` or `revision_id` when one applies. Asking for more uses `extend`, adding facts uses `add_facts` and rechecking uses `refresh`.

Say the scope, the conditions, the maximum price and the expiry in text. Deep Search results cost 5 cents, 15 cents or $1 each, plus 5 cents for a person's email and 15 cents for a phone, and nothing when nothing matches on a new find. A price lasts 30 minutes. The price does not spend any balance and does not start a job.

Use `get_capacity_balance` to read the balance. A balance is not permission to spend. Do not copy the maximum into an approval unless the person said to, or an existing bounded task already allows it. Plans and top-ups live in the person's account, not in chat.
