# VizQL Data Service (VDS)

This directory contains full reference documentation for the VizQL Data Service (VDS) API — Tableau's HTTP API for querying published data sources programmatically. These docs cover everything needed to construct valid queries: how to specify fields, apply filters, override parameters, write calculations, handle errors, and work within known limitations. Use this as the authoritative reference when building or debugging VDS integrations.

## Contents

| File | When to Use | Min Version | Description |
| --- | --- | --- | --- |
| [FIELDS.md](./FIELDS.md) | Defining which columns to return, applying aggregations, adding bins, or attaching table calculations to a field | 2025.1 | How to define the `fields` array in a query — field references, aliases, table calculations, and the rules governing what must be included |
| [FILTERS.md](./FILTERS.md) | Narrowing result sets with categorical, numeric, date, or top-N filters | 2025.1 | All filter types supported by VDS — categorical, quantitative, date, and context filters — with request payload examples |
| [PARAMETERS.md](./PARAMETERS.md) | Overriding a datasource parameter at query time to change thresholds, date ranges, or toggle logic | 2025.1 | How to override published data source parameter values at query time |
| [STREAMING.md](./STREAMING.md) | Handling large result sets or consuming rows incrementally via SSE | **2026.1+** | Streaming result support — JSON and SSE modes, chunked responses, and in-stream error checking |
| [ERRORS.md](./ERRORS.md) | Debugging failed queries — mapping HTTP status codes and Tableau error codes to root causes | 2025.1 | HTTP status codes and Tableau-specific error codes returned by VDS, with conditions and details |
| [LIMITATIONS.md](./LIMITATIONS.md) | Checking whether a feature is supported on your Tableau version, or understanding why a query failed | 2025.1 | Known constraints on data source support, query features, and API behavior; version gating reference |
| [calculations/CALCULATIONS.md](./calculations/CALCULATIONS.md) | Writing ad-hoc calculations, LOD expressions, or table calculations to derive new insights from existing fields | 2025.1 (table calcs: **2025.3+**) | Full reference for calculations in VDS — syntax, data types, LOD expressions, table calculations, functions, and best practices |

> **Important**: `Fields`, `Filters`, `Parameters` and `Calculations` are your most powerful primitives for analysis. In particular, `Calculations` allow you to offload complex operations to the Tableau backend to obtain new insights.

---

### See Also

- [QUERY_DATASOURCE.md](../api/QUERY_DATASOURCE.md) — the HTTP endpoint for executing VDS queries
- [INTROSPECT_DATASOURCE.md](../api/INTROSPECT_DATASOURCE.md) — retrieving field metadata before querying
- [REPL.md](../REPL.md) — complete REPL exploration session from credentials to queried data
