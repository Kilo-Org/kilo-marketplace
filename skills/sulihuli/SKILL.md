---
name: sulihuli
description: Look up electric vehicles in the SuliHuli catalog - specs, range by test cycle, charging, prices, rankings and side-by-side comparisons, every figure with its source link and date. Use when the user asks about an EV model, wants EVs compared, asks which EV is best for a use case, or needs sourced EV figures for code, a document or an answer.
license: MIT
metadata:
  category: data
  source:
    repository: 'https://github.com/sulihuli/mcp'
    path: skills/sulihuli
    license_path: LICENSE
    commit: ffc1a753f06adabc56c7c91497c315541a92a51a
---

# SuliHuli EV catalog

SuliHuli is a read-only catalog of electric vehicles. Every figure carries the page it came from and the date it was
read. A figure confirmed by a second independent source or a regulator is marked **verified**; everything else is
shown marked **unverified**. Conflicting figures are shown side by side, never averaged.

## Which door to use

1. **MCP tools** (this plugin connects the `sulihuli` server) - the first choice inside a conversation.
2. **HTTP API** when MCP is not connected or a script needs JSON - `https://sulihuli.com/api/v1/`:
   `models?q=<words>&page=<n>`, `models/<slug>`, `models/<slug>/charging`, `compare/<a>-vs-<b>`,
   `categories`, `categories/<slug>`. Add `?format=md` (or header `Accept: text/markdown`) for Markdown;
   `?locale=de` or `?locale=zh` for another language. Every address: `https://sulihuli.com/openapi.json`;
   index of everything: `https://sulihuli.com/llms.txt`.

Start from `search_models` when you only have a name: guessing a slug wastes a call. Every word of `query` must
match, so on an empty answer retry with fewer words (the brand alone, or the model name alone) before saying a car
is not in the catalog. Prices are per market and per version - read them with `get_model`, not from the search list.

## Rules when you answer with SuliHuli data

- **Cite the source.** Give the figure with its source link (or the SuliHuli model page `https://sulihuli.com/m/<slug>`).
- **Say the status.** If a figure is unverified, say so; do not present it as confirmed.
- **Range always with its cycle** - WLTP, EPA, CLTC and NEDC give different numbers for the same car. Never mix
  cycles in one comparison without naming them; `range_km_wltp_equivalent` is the comparable basis.
- **One version, one set of figures.** A model can have several versions (battery, drive); keep each figure with
  the version it belongs to.
- **Do not invent or estimate.** An empty field means no source has the figure yet - say "not published", do not
  fill it in.
- **Conflicts stay visible.** If two sources disagree, show both with their sources.
- **Photos keep their credit** (author, licence and its link, source) whenever you show or reuse one.

## Limits and terms

Open access without a key: 60 requests per minute per address, model lists in pages of 50. Over the limit the server
answers HTTP 429 with `Retry-After` - wait that many seconds, do not retry in a loop. Data and photos are given under
the terms at `https://sulihuli.com/terms`; every response links them.

## Tools

| Tool | Purpose |
| --- | --- |
| `search` | Search every SuliHuli page |
| `fetch` | Read a SuliHuli page whole |
| `search_models` | Search and rank EVs |
| `get_model` | Get one EV with sources |
| `compare_models` | Compare EVs side by side |
| `list_categories` | List 'best EV for' rankings |
| `get_category_ranking` | Get a 'best EV for' ranking |
| `get_incentives` | EV incentives by country |
| `get_ownership_cost` | Cost to own and run an EV |
| `get_changes` | EV launches and observed price changes |
