# Tableau Data Catalog

The **Tableau Data Catalog** describes data sources, workbooks, and views — the full content hierarchy of a Tableau site. This enables agents to navigate from user-facing views through workbooks down to queryable published datasources.

> **Prerequisites:** You must authenticate via the Tableau REST API as described in [AUTH.md](./AUTH.md) before calling any catalog endpoint.

> **IMPORTANT**: Tableau environments can have large volumes of datasources with metadata, it is therefore a best practice to store API responses in the `temp/` folder to parse and explore according to [TEMP_DATA.md](../sdk/TEMP_DATA.md). You must delete this temporary data when you finish your work.

> _NOTE_: VDS only works with published datasources, not those embedded inside workbooks.

---

## Three-Tier Discovery Architecture

Catalog discovery is structured as three tiers with distinct responsibilities, transport choices, and cost profiles. Use the tier that matches how much you already know — you do not need to run all three.

| Module | Question answered | Transport | Cost | Always completes? |
|--------|-------------------|-----------|------|-------------------|
| `inventory.py` | "What exists on this site?" | REST only | Fast, flat | Yes — no timeout risk |
| `lineage.py` | "How does this specific asset connect?" | Targeted GraphQL (one node) | One request per asset | Yes — no pagination loop |
| `introspect_datasource.py` / `introspect_workbook.py` | "What is inside this asset?" | VDS + GraphQL enrichment | Deep, per-asset | Yes — on the chosen asset only |

The legacy `catalog.py` (all-in-one GraphQL-first path) is preserved for backward compatibility. See [Legacy Path](#legacy-path) below.

---

## Agent Decision Tree

```
Agent is assigned a task requiring Tableau data
  │
  ├─ Always start: inventory_datasources() + inventory_views()
  │    Fast, REST-only, gives full site picture with usage signals
  │
  ├─ Need to understand how views/workbooks relate to datasources?
  │    YES → workbook_lineage(luid) for top workbooks
  │           datasource_lineage(luid) for candidate datasources
  │
  ├─ Ready to query a specific datasource via VDS?
  │    YES → introspect(luid) → query()
  │
  └─ Need to understand a workbook's field-level structure?
       YES → introspect_workbook(luid)
```

For deeper introspection after discovery:
- **Datasource fields** → [INTROSPECT_DATASOURCE.md](./INTROSPECT_DATASOURCE.md)
- **Workbook field detail** → [INTROSPECT_WORKBOOK.md](./INTROSPECT_WORKBOOK.md)

---

## Tier 1: Inventory (`inventory.py`)

Answers "what exists on this site?" with flat, paginated REST calls. No GraphQL. No nested relationship data. Always completes regardless of site size.

### Functions

#### `inventory_datasources()`

```python
def inventory_datasources(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,     # exact-match on datasource name
    filter_project: str | None = None,  # exact-match on project name
    page_size: int = 1000,              # items per page, clamped to 1,000
    limit: int | None = None,           # max total items to return
) -> list[DatasourceInventoryItem]: ...
```

**Endpoint:** `GET /api/{v}/sites/{id}/datasources`

**When to use:** First step on any task — get a flat list of all published datasources with certification and tag signals. Use `filter_name` or `filter_project` to narrow large sites before iterating.

**Session delegate:** `session.inventory_datasources(**kw)`

#### `inventory_views()`

```python
def inventory_views(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[ViewInventoryItem]: ...
```

**Endpoint:** `GET /api/{v}/sites/{id}/views?includeUsageStatistics=true`

**When to use:** Get all views with popularity signals. `total_view_count` is always populated — this is the canonical path for ranking views by usage. The legacy `list_views()` returns `total_view_count=None` on the GraphQL path.

**Session delegate:** `session.inventory_views(**kw)`

#### `inventory_workbooks()`

```python
def inventory_workbooks(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    filter_name: str | None = None,
    filter_project: str | None = None,
    page_size: int = 1000,
    limit: int | None = None,
) -> list[WorkbookInventoryItem]: ...
```

**Endpoint:** `GET /api/{v}/sites/{id}/workbooks`

**When to use:** Get a flat workbook list for initial orientation. Does not include sheets, dashboards, or datasource links — use `workbook_lineage()` for those.

**Session delegate:** `session.inventory_workbooks(**kw)`

### Models

#### `DatasourceInventoryItem`

```python
class DatasourceInventoryItem(TableauModel):
    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_id: str | None = None       # REST returns owner.id, not owner.name
    has_extracts: bool | None = None
    is_certified: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    content_url: str | None = None
    tags: list[str] = []
```

> **Note:** `owner_id` is the owner's LUID, not their display name. Name resolution requires a separate users call.

#### `ViewInventoryItem`

```python
class ViewInventoryItem(TableauModel):
    luid: str
    name: str
    content_url: str | None = None
    workbook_luid: str | None = None  # join key; workbook_name not available from REST /views
    owner_id: str | None = None
    total_view_count: int | None = None
```

> **Note:** Resolve workbook names by joining with `inventory_workbooks()` on `workbook_luid`.

#### `WorkbookInventoryItem`

```python
class WorkbookInventoryItem(TableauModel):
    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_id: str | None = None
    content_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    tags: list[str] = []
```

### Usage Example

```python
with Session(SdkConfig()) as session:
    datasources = session.inventory_datasources()
    views       = session.inventory_views()
    workbooks   = session.inventory_workbooks()

    print(f"{len(datasources)} datasources, {len(views)} views, {len(workbooks)} workbooks")

    # Quality signals
    certified = [ds for ds in datasources if ds.is_certified]
    tagged    = [ds for ds in datasources if "finance" in ds.tags]

    # Popularity signals (total_view_count is always populated)
    top_views = sorted(views, key=lambda v: v.total_view_count or 0, reverse=True)
    print([(v.name, v.total_view_count) for v in top_views[:5]])

    # Resolve workbook names for top views
    wb_map = {wb.luid: wb.name for wb in workbooks}
    for v in top_views[:5]:
        print(v.name, v.total_view_count, wb_map.get(v.workbook_luid, "unknown"))
```

### Graceful Degradation

| Condition | Behavior |
|-----------|----------|
| HTTP 2xx | Returns list of inventory items |
| HTTP 4xx / 5xx | Raises `CatalogUnavailableError` with status code and message |
| No items found | Returns empty list |

---

## Tier 2: Lineage (`lineage.py`)

Answers "how does this specific asset connect to others?" with targeted, per-asset GraphQL queries. Each function fetches one node by `luid` — no pagination, one HTTP request. Applies the corrected socket timeout ordering from POSTMORTEM_2 §8.1.

No REST fallback — lineage data is Metadata API only. On timeout or missing node: raises `CatalogUnavailableError`.

### Functions

#### `datasource_lineage(luid)`

```python
def datasource_lineage(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    luid: str,   # luid of the published datasource
) -> DatasourceLineage: ...
```

**GraphQL query:** `publishedDatasources(filter: { luid: $luid })` — singular filter, one node, no pagination.

**Returns:** Downstream workbooks/sheets/dashboards, upstream tables/databases, and a 30-field preview.

**When to use:** After `inventory_datasources()` — to understand what consumers depend on a datasource and what physical data it reads from, before committing to a full `introspect()` call.

**Session delegate:** `session.datasource_lineage(luid)`

#### `workbook_lineage(luid)`

```python
def workbook_lineage(
    config: SdkConfig,
    token: AuthToken,
    conn: http.client.HTTPSConnection | None = None,
    *,
    luid: str,   # luid of the workbook
) -> WorkbookLineage: ...
```

**GraphQL query:** `workbooks(filter: { luid: $luid })` — singular filter, one node, no pagination.

**Returns:** Sheets, dashboards, embedded datasources, and direct upstream published datasources.

**When to use:** After `inventory_views()` — to discover which published datasources power the most-viewed workbooks. This is the bridge from "which views are popular?" to "which datasource do I query via VDS?".

**Session delegate:** `session.workbook_lineage(luid)`

### Models

#### `DatasourceLineage`

```python
class DatasourceLineage(TableauModel):
    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_name: str | None = None       # GraphQL returns name directly (unlike REST)
    is_certified: bool | None = None
    has_extracts: bool | None = None
    downstream_workbooks: list[WorkbookRef] = []
    downstream_sheets: list[SheetRef] = []
    downstream_dashboards: list[DashboardRef] = []
    upstream_tables: list[UpstreamTableRef] = []
    upstream_databases: list[UpstreamDatabaseRef] = []
    field_preview: list[FieldPreview] = []   # first 30 fields
```

#### `WorkbookLineage`

```python
class WorkbookLineage(TableauModel):
    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    sheets: list[SheetRef] = []
    dashboards: list[DashboardRef] = []
    embedded_datasources: list[EmbeddedDatasourceRef] = []
    upstream_datasources: list[DatasourceRef] = []
    upstream_databases: list[UpstreamDatabaseRef] = []
```

#### Supporting Reference Types

```python
class UpstreamTableRef(TableauModel):
    name: str
    database_name: str | None = None

class UpstreamDatabaseRef(TableauModel):
    name: str
    connection_type: str | None = None

class FieldPreview(TableauModel):
    name: str
    data_type: str
    role: str   # "DIMENSION" | "MEASURE"
```

### Usage Example

```python
with Session(SdkConfig()) as session:
    datasources = session.inventory_datasources()
    certified = [ds for ds in datasources if ds.is_certified]

    # Datasource lineage — what consumes it, what powers it, field preview
    for ds in certified[:2]:
        lin = session.datasource_lineage(ds.luid)
        print(f"{lin.name}")
        print(f"  downstream workbooks: {[w.name for w in lin.downstream_workbooks]}")
        print(f"  upstream tables:      {[t.name for t in lin.upstream_tables]}")
        print(f"  upstream databases:   {[db.name for db in lin.upstream_databases]}")
        dims = [f for f in lin.field_preview if f.role == "DIMENSION"]
        print(f"  field preview:        {len(dims)} dims / {len(lin.field_preview) - len(dims)} measures")

    # Workbook lineage — discover which datasources power the top-viewed workbooks
    views = session.inventory_views()
    top_wb_luids = {v.workbook_luid for v in
                    sorted(views, key=lambda v: v.total_view_count or 0, reverse=True)[:5]
                    if v.workbook_luid}
    for luid in list(top_wb_luids)[:3]:
        wl = session.workbook_lineage(luid)
        print(f"{wl.name}: upstream={[d.name for d in wl.upstream_datasources]}")
```

### Error Handling

| Condition | Behavior |
|-----------|----------|
| Metadata API returns HTTP 4xx/5xx | Raises `CatalogUnavailableError` |
| `socket.timeout` | Raises `CatalogUnavailableError` |
| `luid` not found (empty node list) | Raises `CatalogUnavailableError` with "datasource not found: {luid}" |
| No REST fallback | Lineage data is Metadata API only — if GraphQL is unavailable, raise |

---

## Legacy Path

> **These functions are preserved for backward compatibility.** Prefer the three-tier workflow above for new work.
>
> The legacy `catalog.py` functions follow a GraphQL-first pattern with automatic REST fallback. On large sites (>500 datasources) the GraphQL call can take 60–120 seconds with no output — a confirmed failure mode documented in POSTMORTEM_2 §1.3.

### Legacy Datasource Discovery

#### Primary Path: GraphQL Metadata API

The Metadata API provides richer discovery data than the REST API, including a lightweight field preview per datasource.

**METHOD**: `POST /api/metadata/graphql`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD**:

```graphql
query DiscoverDatasources($first: Int!, $offset: Int) {
  publishedDatasourcesConnection(first: $first, offset: $offset) {
    nodes {
      name
      luid
      description
      projectName
      owner {
        name
      }
      hasExtracts
      isCertified
      tags {
        label
      }
      fields(first: 30) {
        name
        __typename
        dataType
        role
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Send as JSON:

```json
{
  "query": "<GRAPHQL QUERY STRING FROM ABOVE>",
  "variables": {
    "first": 100,
    "offset": 0
  }
}
```

**Column selection rationale:**

| Field | Purpose |
|-------|---------|
| `name`, `luid`, `description`, `projectName`, `owner` | Identify the datasource |
| `hasExtracts`, `isCertified`, `tags` | Quality signals for relevance ranking |
| `fields(first: 30)` | Rich field preview so the agent can gauge datasource relevance and identify key dimensions/measures without a full inspection call |

**RESPONSE PAYLOAD**:

```json
{
  "data": {
    "publishedDatasourcesConnection": {
      "nodes": [
        {
          "name": "Superstore",
          "luid": "datasource-luid-123",
          "description": "Sales data for the Superstore",
          "projectName": "Sales",
          "owner": { "name": "Jane Doe" },
          "hasExtracts": true,
          "isCertified": true,
          "tags": [{ "label": "sales" }, { "label": "finance" }],
          "fields": [
            { "name": "Order Date", "__typename": "ColumnField", "dataType": "DATETIME", "role": "DIMENSION" },
            { "name": "Sales", "__typename": "ColumnField", "dataType": "REAL", "role": "MEASURE" }
          ]
        }
      ],
      "pageInfo": {
        "hasNextPage": true,
        "endCursor": "cursor-value"
      }
    }
  }
}
```

**Pagination:**

- Uses `first` / `offset` (or `after` cursor from `pageInfo.endCursor`)
- Max page size: 1,000 items
- Loop while `pageInfo.hasNextPage == true`

**Filtering (optional):**

You can add a `filter` argument to `publishedDatasourcesConnection`:

```graphql
publishedDatasourcesConnection(filter: { name: "Superstore" }, first: 100)
publishedDatasourcesConnection(filter: { nameWithin: ["Sales", "Marketing"] }, first: 100)
publishedDatasourcesConnection(filter: { projectName: "Finance" }, first: 100)
```

---

### Legacy Fallback Path: REST API `list-datasources`

If the Metadata API is unavailable (returns 403, 503, timeout, or `feature-disabled`), automatically fall back to the REST API.

**METHOD**: `GET /api/{api-version}/sites/{site-id}/datasources`

**HEADERS**:

```
X-Tableau-Auth: <token>
```

**QUERY PARAMETERS**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `pageSize` | integer | Items per page (1–1000, default 100) |
| `pageNumber` | integer | Page offset (default 1) |
| `filter` | string | Filter string in format `field:operator:value` |

**Pagination logic**:

```
while (totalAvailable > result.length && (!limit || limit > result.length)) {
    fetch next page with pageNumber += 1
    if (page returns empty data) throw Error
}
if (limit && limit < result.length) result.length = limit
```

**Filter format**: `field:operator:value`. Multiple filters are comma-separated.

_Example_:

```bash
curl "https://{my-server}/api/{api-version}/sites/{site-id}/datasources?filter=name:eq:Superstore&pageSize=100&pageNumber=1" \
  -H "X-Tableau-Auth: <token>"
```

**Supported filter fields and operators**:

| Field | Operators |
|-------|-----------|
| `authenticationType` | eq, in |
| `connectedWorkbookType` | eq, gt, gte, lt, lte |
| `connectionTo` | eq, in |
| `connectionType` | eq, in |
| `contentUrl` | eq, in |
| `createdAt` | eq, gt, gte, lt, lte |
| `databaseName` | eq, in |
| `databaseUserName` | eq, in |
| `description` | eq, in |
| `favoritesTotal` | eq, gt, gte, lt, lte |
| `hasAlert` | eq |
| `hasEmbeddedPassword` | eq |
| `hasExtracts` | eq |
| `isCertified` | eq |
| `isConnectable` | eq |
| `isDefaultPort` | eq |
| `isHierarchical` | eq |
| `isPublished` | eq |
| `name` | eq, in |
| `ownerDomain` | eq, in |
| `ownerEmail` | eq |
| `ownerName` | eq, in |
| `projectName` | eq, in |
| `serverName` | eq, in |
| `serverPort` | eq |
| `size` | eq, gt, gte, lt, lte |
| `tableName` | eq, in |
| `tags` | eq, in |
| `type` | eq |
| `updatedAt` | eq, gt, gte, lt, lte |

**RESPONSE PAYLOAD**:

```json
{
  "pagination": {
    "pageNumber": "1",
    "pageSize": "100",
    "totalAvailable": "42"
  },
  "datasources": {
    "datasource": [
      {
        "id": "datasource-id-123",
        "name": "Superstore",
        "description": "Sales data for the Superstore",
        "project": {
          "id": "project-id-456",
          "name": "Sales"
        },
        "tags": {
          "tag": [
            { "label": "sales" }
          ]
        }
      }
    ]
  }
}
```

---

### Legacy Graceful Degradation: Datasource Discovery

| Condition | Behavior |
|-----------|----------|
| GraphQL returns valid data | Use GraphQL results with field previews |
| GraphQL returns 403/503/timeout | Fall back to REST API `list-datasources` |
| REST API also fails | Return error to agent with original HTTP status and message |
| No datasources found | Return explicit empty-state message |

---

### Downstream Workbook References on `DatasourceSummary`

The datasource GraphQL query includes `downstreamWorkbooks { luid name }` on each published datasource. This populates `DatasourceSummary.downstream_workbooks` — a list of `WorkbookRef` objects (luid + name).

This provides direct navigation from datasource → workbook without a separate join:

```python
for ds in datasources:
    if ds.downstream_workbooks:
        print(f"{ds.name} is used by:")
        for wb in ds.downstream_workbooks:
            print(f"  - {wb.name} ({wb.luid})")
```

On the REST fallback path, `downstream_workbooks` is always an empty list — the REST `list-datasources` endpoint does not expose this relationship.

---

### Legacy Workbook Discovery

#### Primary Path: GraphQL Metadata API

**METHOD**: `POST /api/metadata/graphql`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD**:

```graphql
query DiscoverWorkbooks($first: Int!, $offset: Int) {
  workbooksConnection(first: $first, offset: $offset) {
    nodes {
      name
      luid
      description
      projectName
      owner { name }
      createdAt
      updatedAt
      sheets {
        name
        luid
        index
      }
      dashboards {
        name
        luid
        index
      }
      embeddedDatasources {
        name
        upstreamDatasources {
          luid
          name
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Send as JSON:

```json
{
  "query": "<GRAPHQL QUERY STRING FROM ABOVE>",
  "variables": {
    "first": 100,
    "offset": 0
  }
}
```

**Column selection rationale:**

| Field | Purpose |
|-------|---------|
| `name`, `luid`, `description`, `projectName`, `owner` | Identify the workbook |
| `sheets`, `dashboards` | Structural navigation (names, LUIDs, order) |
| `embeddedDatasources.upstreamDatasources` | Link embedded datasources to published datasource LUIDs for VDS queries |
| `createdAt`, `updatedAt` | Recency signals |

**RESPONSE PAYLOAD**:

```json
{
  "data": {
    "workbooksConnection": {
      "nodes": [
        {
          "name": "Sales Overview",
          "luid": "workbook-luid-123",
          "description": "Executive sales dashboard",
          "projectName": "Sales",
          "owner": { "name": "Jane Doe" },
          "createdAt": "2024-01-15T10:00:00Z",
          "updatedAt": "2024-06-01T14:30:00Z",
          "sheets": [
            { "name": "Revenue Trend", "luid": "sheet-luid-1", "index": 0 },
            { "name": "Regional Breakdown", "luid": "sheet-luid-2", "index": 1 }
          ],
          "dashboards": [
            { "name": "Executive View", "luid": "dash-luid-1", "index": 2 }
          ],
          "embeddedDatasources": [
            {
              "name": "Superstore (embedded)",
              "upstreamDatasources": [
                { "luid": "ds-luid-abc", "name": "Superstore" }
              ]
            }
          ]
        }
      ],
      "pageInfo": {
        "hasNextPage": false,
        "endCursor": null
      }
    }
  }
}
```

**Pagination:** Uses `first` / `offset`. Max page size: 1,000 items. Loop while `pageInfo.hasNextPage == true`.

**Filtering (optional):**

```graphql
workbooksConnection(filter: { name: "Sales Overview" }, first: 100)
workbooksConnection(filter: { projectName: "Finance" }, first: 100)
```

---

#### Legacy Fallback Path: REST API `Query Workbooks for Site`

If the Metadata API is unavailable (returns 403, 503, timeout, or `feature-disabled`), automatically falls back to the REST API.

**METHOD**: `GET /api/{api-version}/sites/{site-id}/workbooks`

**QUERY PARAMETERS**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `pageSize` | integer | Items per page (default 100) |
| `pageNumber` | integer | Page offset (default 1) |
| `filter` | string | Filter string in format `field:operator:value` |

**Supported filter fields**: `name:eq:{value}`, `projectName:eq:{value}`

**REST limitation:** The REST path populates only top-level workbook metadata (`luid`, `name`, `description`, `project_name`, `owner_name`, `created_at`, `updated_at`, `tags`). The `sheets`, `dashboards`, and `embedded_datasources` lists are empty on the REST path. Use `introspect_workbook()` for field-level detail after discovery.

---

#### Legacy Graceful Degradation: Workbook Discovery

| Condition | Behavior |
|-----------|----------|
| GraphQL returns valid data | Use GraphQL results with sheets, dashboards, embedded datasource links |
| GraphQL returns 403/503/timeout | Fall back to REST API `Query Workbooks for Site` |
| REST API also fails | Raise exception with original HTTP status and message |
| No workbooks found | Return empty list |

---

### Legacy View Discovery

Views are individual visualizations within a workbook — worksheets (sheets) and dashboards. Discovering views is the first step toward retrieving pre-configured data via `query_view_data()`.

#### Primary Path: GraphQL Metadata API

**METHOD**: `POST /api/metadata/graphql`

View discovery uses two separate GraphQL queries — one for sheets and one for dashboards — then merges the results.

#### Sheets Query

```graphql
query DiscoverSheets($first: Int!, $offset: Int) {
  sheetsConnection(first: $first, offset: $offset) {
    nodes {
      name
      luid
      index
      path
      createdAt
      updatedAt
      workbook {
        luid
        name
      }
      containedInDashboards {
        name
        luid
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

#### Dashboards Query

```graphql
query DiscoverDashboards($first: Int!, $offset: Int) {
  dashboardsConnection(first: $first, offset: $offset) {
    nodes {
      name
      luid
      index
      path
      createdAt
      updatedAt
      workbook {
        luid
        name
      }
      sheets {
        name
        luid
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**RESPONSE PAYLOAD (sheets)**:

```json
{
  "data": {
    "sheetsConnection": {
      "nodes": [
        {
          "name": "Revenue Trend",
          "luid": "sheet-luid-1",
          "index": 0,
          "path": "salesoverview/sheets/Revenue%20Trend",
          "createdAt": "2024-01-15T10:00:00Z",
          "updatedAt": "2024-06-01T14:30:00Z",
          "workbook": { "luid": "workbook-luid-123", "name": "Sales Overview" },
          "containedInDashboards": [
            { "name": "Executive View", "luid": "dash-luid-1" }
          ]
        }
      ],
      "pageInfo": { "hasNextPage": false, "endCursor": null }
    }
  }
}
```

---

#### Legacy Fallback Path: REST API `Query Views for Site`

**METHOD**: `GET /api/{api-version}/sites/{site-id}/views`

**QUERY PARAMETERS**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `pageSize` | integer | Items per page (default 100) |
| `pageNumber` | integer | Page offset (default 1) |
| `filter` | string | `name:eq:{value}` |

**REST limitation:** The REST `/views` endpoint returns `workbook.id` (the workbook LUID) as the join key. `workbook_name` is `None` on the REST path. `contained_in_dashboards` is always empty on the REST path.

---

#### Legacy Graceful Degradation: View Discovery

| Condition | Behavior |
|-----------|----------|
| GraphQL returns valid data | Use GraphQL results with workbook name and dashboard containment |
| GraphQL returns 403/503/timeout | Fall back to REST `Query Views for Site` |
| REST API also fails | Raise exception with original HTTP status and message |
| No views found | Return empty list |
