# Tableau API Reference

This directory documents the HTTP API interactions used by this skill — authentication, catalog discovery, schema introspection, and query execution against Tableau Cloud and Tableau Server.

The APIs here follow a three-phase pipeline: **Discover** assets in the catalog, **Introspect** their schemas to understand queryable fields, then **Execute** queries to retrieve data.

## Contents

| File | When to Use | Description |
| --- | --- | --- |
| [AUTH.md](./AUTH.md) | Setting up credentials for the first time, debugging 401/403 errors, or understanding token lifecycle | Authentication methods (PAT, JWT, username/password), credential management, token lifecycle, permission requirements, and the sign-in/sign-out HTTP contract |
| [CATALOG.md](./CATALOG.md) | Discovering what datasources, workbooks, and views exist on a Tableau site before introspecting or querying them | Data Catalog discovery via the GraphQL Metadata API with automatic REST fallback — covers datasource, workbook, and view discovery with filtering, pagination, and quality signals (certification, freshness) |
| [INTROSPECT_DATASOURCE.md](./INTROSPECT_DATASOURCE.md) | Understanding a datasource's queryable fields, parameters, and logical table structure before building a VDS query | Datasource schema introspection via VDS `readMetadata` and GraphQL enrichment — field metadata, parameters, logical table relationships, and the merge strategy for building a complete queryable schema |
| [INTROSPECT_WORKBOOK.md](./INTROSPECT_WORKBOOK.md) | Understanding how a workbook is structured — which sheets use which fields, what calculations exist, and how to trace back to published datasources | Workbook structural introspection via GraphQL — sheets, dashboards, field instances, authored calculations, embedded datasource lineage, and upstream published datasource resolution |
| [QUERY_DATASOURCE.md](./QUERY_DATASOURCE.md) | Looking up the exact HTTP endpoint, request body shape, query options, or error response format for VDS query execution | VDS query execution endpoint — request/response shapes, query options (`returnFormat`, `rowLimit`, streaming), connection credentials, error handling, and the `list-supported-functions` endpoint |
| [QUERY_VIEW.md](./QUERY_VIEW.md) | Quickly retrieving pre-configured view data via REST when a custom VDS query is unnecessary | REST-based view data retrieval — the "quick answer" path for pre-configured views, CSV parsing, filter parameters, and limitations compared to full VDS queries |

---

### See Also

- [VDS Reference](../vds/VDS.md) — query construction primitives (fields, filters, parameters, calculations)
- [SDK Reference](../sdk/SDK.md) — Python package that wraps these APIs into a `Session` abstraction
- [REPL.md](../REPL.md) — complete REPL exploration session from credentials to queried data
