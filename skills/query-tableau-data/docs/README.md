# Documentation for Querying Tableau Data Sources

## Documentation Index

| Topic | Entry Point | When to Use | Description |
|-------|-------------|-------------|-------------|
| REPL Exploration | [REPL.md](REPL.md) | **Start here** — first-time setup and end-to-end REPL session | A complete REPL exploration session demonstrating authentication, catalog discovery, workbook and datasource introspection, and query execution — ending with retrieved data you can analyze or export. |
| SDK Reference | [sdk/SDK.md](sdk/SDK.md) | REPL exploration, writing scripts, and orchestrating the discover → introspect → query pipeline programmatically | Python package reference for `query_tableau_data_py`. Documents the `Session` abstraction, REPL exploration patterns, module map, import patterns, file-based persistence to `temp/`, and troubleshooting. Start here when writing scripts or adapting the skill's code for custom workflows. |
| VDS Reference | [vds/VDS.md](vds/VDS.md) | Constructing correct queries and mining new insights via calculations, filters, and table calculations | Query construction reference for the VizQL Data Service. Covers all primitives needed to build valid queries: field specifications, filter types and schemas, parameter overrides, calculation syntax (LOD expressions, table calculations, functions), streaming modes, error codes, and version-specific limitations. |
| API Reference | [api/API.md](api/API.md) | Fallback reference for raw HTTP contracts — request/response shapes, headers, status codes, and endpoint URIs | HTTP API interactions with Tableau Cloud and Server. Covers authentication (PAT, JWT), catalog discovery via GraphQL with REST fallback, datasource and workbook schema introspection, VDS query execution, and REST-based view data retrieval. |
| Integration Patterns | [sdk/INTEGRATION.md](sdk/INTEGRATION.md) | Integrating VDS queries into async applications | Concrete patterns for wrapping the sync-only Session in async apps (Streamlit, FastAPI), correct test mocking, thread safety, and common pitfalls. |
