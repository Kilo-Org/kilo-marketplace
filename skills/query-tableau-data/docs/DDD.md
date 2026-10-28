# Domain-Driven Design

This file defines the **ubiquitous language** for the `query-tableau-data` skill following Domain-Driven Design (DDD) principles. It is a **C1 foundational document** — every agent operating on this skill should read it before writing or modifying any code to ensure consistent terminology and correct placement of domain concepts.


---


# Ubiquitous Language

This glossary defines the canonical terms for the skill domain. **All agents must use these exact terms** when writing code, docs, issues, and task descriptions. Inconsistent terminology creates ambiguity that compounds across documents.

When adding a term, include: the term itself, a concise definition, the bounded context(s) where it applies, and an example if the term is easily confused.


## Bounded Context: Tableau Platform

Terms from the **Tableau** platform — the external system this skill integrates with. These terms describe Tableau's native concepts, not our skill's workflow.

| Term | Definition | Example / Note |
|------|------------|----------------|
| **Datasource** | A published Tableau data source (not embedded in a workbook). The unit of queryable data in VDS. Identified by a **LUID**. | `Superstore Sales` |
| **LUID** | Locally Unique Identifier. The primary key for datasources, projects, and other Tableau objects within a site. | `12ab34cd-56ef-78ab-90cd-12ef34ab56cd` |
| **VDS** (VizQL Data Service) | The HTTP execution layer for querying published Tableau data sources. Endpoints live under `/api/v1/vizql-data-service/`. | `query-datasource`, `read-metadata` |
| **Field** | A queryable column or calculation within a datasource. Has an internal `fieldName`, a human-readable `fieldCaption`, a `dataType`, and an optional `defaultAggregation`. | `Order Date`, `SUM(Sales)` |
| **FieldCaption** | The human-readable name of a field (e.g., "Order Date"). Used in VDS queries. Not always unique. | `Order Date` |
| **FieldName** | The internal/system name of a field (e.g., "federated.0123.abc"). Stable but opaque. | `federated.0123.abc` |
| **Logical Table** | A conceptual table within a datasource model. Fields belong to a logical table via `logicalTableId`. | `Orders` |
| **Logical Table Relationship** | A join-like connection between two logical tables, expressed as a predicate over fields. | `Orders.Order ID = Returns.Order ID` |
| **Datasource Model** | The output of VDS `getDatasourceModel`: logical tables and their relationships. Only available on Tableau 2025.3+. | — |
| **ColumnClass** | The origin of a field: `COLUMN`, `BIN`, `GROUP`, `CALCULATION`, `TABLE_CALCULATION`. | `CALCULATION` for user-defined formulas |
| **Parameter** | A user-configurable value in a datasource (e.g., a date range). Exposed in `readMetadata` under `extraData.parameters`. | `Date Range` parameter |
| **Connection** | A database credential object for datasources that require additional database authentication beyond Tableau site auth. | `connectionUsername`, `connectionPassword` |
| **SSE** (Server-Sent Events) | A streaming protocol VDS supports for large result sets. Enabled via `returnServerSentEvents: true` (Tableau 2026.1+). | `text/event-stream` |
| **Streaming** | Consuming VDS query results incrementally via SSE, processing chunks without buffering the full response in memory. See [STREAMING.md](vds/STREAMING.md#implementing-sse-with-httpclient-advanced) for the http.client escape hatch. | `for line in resp.makefile("r")` |
| **Site** | A Tableau Server/Cloud site. Identified by `contentUrl`. Sign-in is site-scoped; tokens are only valid within the signed-in site. | `https://server/t/sales` |
| **Auth Token** | The `X-Tableau-Auth` header value returned by REST API `signin`. Valid for ~240 minutes. Required by VDS and Metadata API. | `12ab34cd56ef78ab90cd12ef34ab56cd` |
| **PAT** (Personal Access Token) | The preferred authentication method. A named token/secret pair obtained from a Tableau user account page. | `my-token-name` + secret |
| **JWT** (Connected Apps) | An authentication method for server-to-server or embedded scenarios. Requires site admin access to configure. | Signed token with `sub` claim |
| **Metadata API** (GraphQL) | Tableau's GraphQL endpoint at `/api/metadata/graphql`. Used for catalog discovery and field enrichment. | `publishedDatasources { fields { ... } }` |
| **REST API** | Tableau's XML/JSON REST endpoints at `/api/{api-version}/`. Used for sign-in, sign-out, and datasource listing fallback. | `/api/3.21/auth/signin` |
| **API Version** | The Tableau REST API version string, e.g., `3.21`. Included in REST URLs. Separate from the VDS API version. | `3.21` |
| **Embedded Data Source** | A data source contained within a workbook. Unlike a Published Data Source, it is not independently accessible via VDS. It may reference (layer on top of) a Published Data Source, adding workbook-specific field renames, calculations, and filters. | `EmbeddedDatasource` in the Metadata API |
| **Sheet (Metadata API)** | A single worksheet (visualization) contained in a workbook. In the Metadata API, sheets implement the `View` interface and represent individual charts, tables, or maps. Hidden sheets have blank LUIDs and cannot be queried via REST. | `Sheet` type in GraphQL schema |
| **View (REST API)** | A generic term for any sheet or dashboard visible in the REST API. Views have LUIDs and can be listed via `Query Views for Site`. Published views can be queried for data via `query_view_data`. | `GET /sites/{site-id}/views` |
| **query_view_data** | REST API operation for retrieving tabular data from a view as CSV. Limited to the first (default) sheet; cannot target specific sheets in multi-sheet workbooks; cannot access hidden sheets. No filter or aggregation control. | `GET /sites/{site-id}/views/{view-id}/data` |
| **Downstream Workbook** | A workbook that consumes a published data source. The Metadata API exposes this relationship via `PublishedDatasource.downstreamWorkbooks`. | Navigating datasource → workbook |
| **Upstream Data Source** | A published data source referenced by an embedded data source within a workbook. The Metadata API exposes this via `EmbeddedDatasource.upstreamDatasources`. | Navigating workbook → datasource |
| **Sheet Field Instance** | A field used directly by a specific sheet. The Metadata API's `sheetFieldInstances` query returns only the fields actively placed on the sheet's shelves (rows, columns, filters, marks). | Distinct from the full datasource field set |
| **Worksheet Field** | A calculated field created directly on a sheet (e.g., in the rows or columns shelves). These calculations are scoped to the sheet and may not appear in the embedded datasource's field list. | `worksheetFields` in GraphQL |


## Bounded Context: Agent Pipeline

Terms describing the **skill's multi-phase workflow** for discovering, understanding, and querying Tableau data sources autonomously. These are not Tableau-native concepts; they are our skill's domain language.

| Term | Definition | Example / Note |
|------|------------|----------------|
| **Discovery** | Phase 1 of the agent pipeline: find relevant published datasources, workbooks, or views without knowing LUIDs in advance. | `catalog.list_datasources()`, `catalog.list_workbooks()`, `catalog.list_views()` |
| **Introspection** | Phase 2 of the agent pipeline. For datasources: retrieve and merge field metadata into a unified `DatasourceSchema`. For workbooks: retrieve sheet field instances, worksheet calcs, and embedded datasource lineage into `WorkbookSchema`. | `introspect_datasource.introspect(luid)`, `introspect_workbook.introspect_workbook(luid)` |
| **Query Execution** | Phase 3 of the agent pipeline: construct and submit a VDS `query-datasource` request, or retrieve pre-configured view data via REST. | `query.query(request)`, `query_view.query_view_data(view_luid)` |
| **Quick Answer Path** | The agent workflow path where the user's question is answered by querying an existing Tableau view directly, without VDS introspection or custom query construction. Faster and simpler when the view's pre-configured data is sufficient. | `list_views()` → `query_view_data()` |
| **Shared Reality** | The aligned understanding between agent and user about which datasource, fields, and strategy to use. Established by asking clarifying questions after introspection. | "Do you mean total Sales or average Sales?" |
| **Data Strategy** | The plan for answering a user's question: which datasource, fields, filters, and aggregations to use. | "Use Superstore, filter to 2024, aggregate Sales by Region" |
| **Catalog / Data Catalog** | The discovery layer for finding datasources, workbooks, and views. GraphQL Metadata API primary, REST API fallback. | `catalog.py` module |
| **Temp Data** | Exploration output persisted to `temp/` (JSON, CSV, Markdown) so the agent can inspect results with shell tools. Must be deleted when work is complete. | `temp/query_123.json` |
| **Sign In / Sign Out** | REST API operations to obtain and invalidate an auth token. Implemented directly via `http.client` (stdlib), not TSC. | `auth.sign_in()` / `auth.sign_out()` |


## Bounded Context: SDK Architecture

Terms describing our **local SDK design** — the architectural decisions and patterns that distinguish our implementation from the official SDK.

| Term | Definition | Example / Note |
|------|------------|----------------|
| **SDK** | The local `query_tableau_data_py` Python package that replaces the official `tableauserverclient`-dependent VDS SDK. | `query_tableau_data_py` |
| **query_tableau_data_js** | The planned JavaScript/TypeScript library for querying Tableau data, following the same naming convention as the Python package under the same skill folder. | Planned — not yet implemented |
| **TSC** | `tableauserverclient`, the official Tableau Python library. Explicitly excluded from this SDK. | — |
| **Seam** | A place where behaviour can be altered without editing in place. The SDK defines seams at HTTP transport, auth mechanism, and output formatting. | Injected `http.client.HTTPSConnection` |
| **Adapter** | A concrete implementation satisfying an interface at a seam. E.g., `HttpxTransportAdapter`, `PatAuthAdapter`. | `MockTransport` for tests |
| **Module** | A unit of code with an interface and an implementation. In this skill: `auth.py`, `catalog.py`, `introspect_datasource.py`, `introspect_workbook.py`, `query.py`, `query_view.py`, `main.py`. | `catalog.py` owns all discovery |
| **Interface Contract** | The function signatures, types, invariants, error modes, and ordering constraints that define a module's surface. | `def list_datasources(...) -> list[DatasourceSummary]` |
| **Depth** | Leverage at the interface — the amount of behaviour a caller can exercise per unit of interface they have to learn. Our modules are designed to be deep (small interface, large implementation). | `introspect(luid)` hides 3 API calls + merge |
| **Shallow** | A module whose interface is nearly as complex as its implementation. The official SDK's four-function-per-endpoint pattern is shallow. | `sync`, `sync_detailed`, `asyncio_detailed` |
