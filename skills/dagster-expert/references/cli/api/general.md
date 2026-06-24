---
title: "dg api: General"
triggers:
  - "always read before using any dg api subcommand"
---

All `dg api` subcommands support `--json`, `--response-schema`, `--deployment`, `--organization`, `--api-token`, and `--view-graphql`.

- `--response-schema` — prints the JSON schema for the command's response and exits. Run this before writing any parsing logic to get exact field names, types, and valid enum values.
- `--view-graphql` — prints GraphQL queries and responses to stderr, useful for debugging.

## Tips

For complex debugging/analysis workflows, ALWAYS use `--json` to get machine-readable output. Pipe into `jq` (recommended) or other tools for further processing.

Flags like `--deployment`/`--organization`/`--api-token` are typically not needed when authenticated via `dg plus login`.
