---
name: dealmachine
description: >-
  Search and enrich US property, owner, and people data with
  DealMachine through its MCP tools or dm CLI. Use for real estate lead
  generation, property and owner lookup, contact enrichment, prospecting,
  comparable sales, market research, targeted lists or exports, and credit-aware
  DealMachine workflows.
license: MIT
metadata:
  category: business
  author: DealMachine
  version: 0.3.0
  source:
    repository: 'https://github.com/DealMachine/dealmachine-cli'
    path: skills/dealmachine
    ref: master
    commit: d7b69c8959b3002d60c769f2c902de2f8262e962
---

# DealMachine

Use DealMachine to turn a user's sales, marketing, lead generation, or real estate research request into a precise property, people, enrichment, comparable-sales, or export workflow.

## Choose the interface

1. Prefer the `dealmachine_*` MCP tools when they are available.
2. Otherwise, use the `dm` CLI if shell access is available.
3. If neither interface is connected, help the user connect the hosted MCP server at `https://mcp.dealmachine.com` or install the CLI with `npm install -g dealmachine`, then run `dm login`.

Never ask the user to paste an API key into chat.

Read [REFERENCE.md](REFERENCE.md) when you need the exact MCP Tool ID, CLI command group, or current interface coverage. The reference tracks DealMachine CLI and hosted MCP 0.3.0.

## Protect credits

- Treat filters, fields, locations, usage, identity checks, and count operations as discovery steps.
- Discover valid filter IDs and field IDs before searching. Never invent them.
- Count or estimate the matching audience before a paid search or export.
- Explain the expected result count, fields, contact audience, and credit impact before a large paid operation.
- Ask for confirmation before an export or an operation that can consume a material number of credits.
- For property-only requests, do not add owner or resident contact enrichment.
- For explicit single-record lookups, run the requested lookup and report whether credits were used.

## Plan the request

Identify:

- Entity: property, person, or list
- Location: address, city, county, ZIP code, state, coordinates, or APN
- Criteria: ownership, equity, property characteristics, demographics, or other filters
- Output: count, preview, detailed results, enrichment, comparable sales, list, or export
- Fields: only the data needed for the task
- Contact audience: owners, residents, both, or none
- Limit and format: a small preview first unless the user specifies otherwise

Ask one focused question only when a missing detail would materially change the search or credit cost.

## Use MCP tools

### Discovery

- Use `dealmachine_filters` to find valid property or people filters.
- Use `dealmachine_fields` to find valid output fields.
- Use `dealmachine_location_search` to resolve supported locations.
- Use `dealmachine_usage` before large paid operations.
- Use `dealmachine_whoami` when account context matters.

### Property workflows

- Use `dealmachine_property_count` before a broad search.
- Use `dealmachine_property_search` for a limited result set.
- Use `dealmachine_property_get` or `dealmachine_property_get_many` for known IDs.
- Use `dealmachine_property_export` only after confirming scope and credit impact.
- Use `dealmachine_comps` for comparable sales.

### People workflows

- Use `dealmachine_people_count` before a broad search.
- Use `dealmachine_people_search` for results and the matching get tools for known IDs.
- People search and lookup are available through MCP. Use the CLI for a people export.

### Enrichment

- Use the address, latitude and longitude, or APN enrichment tool for a property.
- Use the email, phone, or name enrichment tool for a person.
- Narrow name searches with a location.

## Use the CLI

Run `dm --help` or a command-specific `--help` when exact syntax is uncertain.

Common patterns:

```bash
dm filters --source-type properties --search "absentee owner" --json
dm fields --source-type properties --search "equity" --json
dm properties count --body-file search.json --json
dm properties search --body-file search.json --json
dm enrich address "123 Main St, Austin, TX" --json
dm enrich phone "5125550100" --json
dm comps PROPERTY_ID --json
dm usage --json
```

Use JSON output for automation. Store complex request bodies in a temporary JSON file instead of constructing fragile shell-escaped payloads.

The CLI also supports saved lists, exports, account activity, address validation, CRM, tasks, dialer, direct mail, and developer license management. Use `dm <command> --help` and the command map in [REFERENCE.md](REFERENCE.md) before operating those workflows.

## Present the result

- State what was searched and which filters were applied.
- Distinguish estimates, counts, previews, and complete exports.
- Report records returned and credits used when the response provides those values.
- Show the most decision-useful fields first.
- Preserve uncertainty when a field is missing or inferred.
- Offer the next logical action, such as narrowing the audience, enriching selected records, finding comps, or exporting the confirmed set.

## Boundaries

- Do not claim a phone number, email, valuation, ownership fact, or other attribute that the result does not contain.
- Do not describe a count as a completed export.
- Do not expose access tokens, API keys, or raw credentials.
- Do not bypass DealMachine authentication, plan limits, or credit controls.
