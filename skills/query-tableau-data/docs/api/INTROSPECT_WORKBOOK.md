# Workbook Introspection

Once a workbook has been identified via the [Data Catalog](./CATALOG.md), the agent can introspect it to retrieve comprehensive structural detail: which sheets it contains, what fields each sheet uses, what calculated fields were authored directly on the sheet, how its embedded datasources map to published datasources, and how dashboards compose those sheets.

This document covers **Phase 2: Workbook Introspection** in the agent's three-phase pipeline.

1. **Discovery** — Find workbooks and views on the Tableau site to identify which ones are relevant.
2. **Introspection** — Retrieve data source and field metadata.

> **Prerequisites:** Authenticate via the Tableau REST API as described in [AUTH.md](./AUTH.md) before calling the Metadata API.

> **When to use this:** When an agent needs to understand the *visual layer* — what fields a workbook author curated, how sheets are structured, or which published datasources a workbook consumes. For datasource field introspection (VDS queries), see [INTROSPECT_DATASOURCE.md](./INTROSPECT_DATASOURCE.md).

> **IMPORTANT**: Workbook introspection uses GraphQL exclusively. There is **no REST fallback**. If the Metadata API is unavailable, `introspect_workbook()` raises `CatalogUnavailableError`.

> _NOTE_: VDS only works with published datasources, not those embedded inside workbooks.

> _NOTE_: Do not query dashboards since they are limited to only surfacing data from the "first view", which may be unrelated to your needs. Instead, see if you can find the individual "sheet" (view) used by that dashboard to query it directly. Sheets must be published in order to be queryable, so if you find an unpublished one in the workbook lineage you can use it to understand the datasource schema but not as a source of data.

---

## Overview

The agent hierarchy for understanding Tableau content is:

```
views → workbooks → embedded datasources → published datasources → fields
```

`introspect_workbook()` provides the middle layer — it reveals what a workbook author curated at the visual layer, bridging user-facing views and the underlying published datasources that can be queried via VDS.

There is **no REST fallback** for workbook introspection. GraphQL is the only source for field-level detail. If you need a REST-only catalog (e.g., the Metadata API is disabled on your site), use `catalog.list_workbooks()` with REST fallback, which provides `WorkbookSummary` without field detail.

---

## GraphQL Query

**METHOD**: `POST /api/metadata/graphql`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD**:

```graphql
query IntrospectWorkbook($luid: String!) {
  workbooks(filter: { luid: $luid }) {
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
      sheetFieldInstances {
        name
        ... on ColumnField { dataType role }
        ... on CalculatedField { dataType role formula }
      }
      worksheetFields {
        name
        formula
        dataType
        role
      }
      containedInDashboards {
        name
        luid
      }
    }
    dashboards {
      name
      luid
      index
      sheets {
        name
        luid
      }
    }
    embeddedDatasources {
      name
      hasExtracts
      fields {
        name
        ... on ColumnField { dataType role }
        ... on CalculatedField { dataType role formula }
      }
      upstreamDatasources {
        luid
        name
      }
    }
    parameters {
      name
    }
  }
}
```

Send as JSON:

```json
{
  "query": "<GRAPHQL QUERY STRING FROM ABOVE>",
  "variables": {
    "luid": "<workbook-luid>"
  }
}
```

---

## Response Structure

### Top-Level Workbook Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Workbook display name |
| `luid` | string | Unique identifier |
| `description` | string \| null | Optional description |
| `projectName` | string \| null | Project containing the workbook |
| `owner.name` | string | Owner display name |
| `createdAt` | string \| null | ISO 8601 creation timestamp |
| `updatedAt` | string \| null | ISO 8601 last-modified timestamp |
| `sheets` | array | Individual worksheets (see below) |
| `dashboards` | array | Dashboards (see below) |
| `embeddedDatasources` | array | Embedded datasources (see below) |
| `parameters` | array | Workbook-level parameters (name only) |

### Sheet Fields (`sheets[]`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Sheet display name |
| `luid` | string | Sheet identifier |
| `index` | integer \| null | Order within the workbook |
| `sheetFieldInstances` | array | Fields placed on this sheet's shelves |
| `worksheetFields` | array | Calculated fields authored directly on this sheet |
| `containedInDashboards` | array | Dashboards that embed this sheet |

### Sheet Field Instances (`sheetFieldInstances[]`)

`sheetFieldInstances` returns only the fields **actively placed** on a sheet's shelves (rows, columns, filters, marks). This is distinct from the full datasource field set — it shows exactly what the workbook author chose to visualize.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Field display name |
| `dataType` | string \| null | `STRING`, `INTEGER`, `REAL`, `DATE`, `DATETIME`, `BOOLEAN` (null for `DatasourceField` nodes) |
| `role` | string \| null | `DIMENSION` or `MEASURE` (null for `DatasourceField` nodes) |
| `formula` | string \| null | Calculation formula (non-null for `CalculatedField` only) |

**Why `DatasourceField` nodes have null `dataType`/`role`:** The Tableau Metadata API's `Field` interface only exposes `name` at the base level. `DatasourceField` does not support `dataType`/`role` inline fragments in GraphQL — only `ColumnField` and `CalculatedField` do. The implementation intentionally omits the `DatasourceField` fragment because the schema rejects it.

### Worksheet Fields (`worksheetFields[]`)

Calculated fields **created directly on the sheet** (e.g., in the Rows or Columns shelf editor). These are scoped to the sheet and may not appear in the embedded datasource's field list.

Same shape as `sheetFieldInstances[]` — `name`, `dataType`, `role`, `formula`.

### Dashboard Fields (`dashboards[]`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Dashboard display name |
| `luid` | string | Dashboard identifier |
| `index` | integer \| null | Order within the workbook |
| `sheets` | array | Component worksheets (`{luid, name}`) |

### Embedded Datasource Fields (`embeddedDatasources[]`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Embedded datasource name |
| `hasExtracts` | boolean \| null | Whether the datasource uses extracted data |
| `fields` | array | All fields in the embedded datasource (`ColumnField` and `CalculatedField` fragments) |
| `upstreamDatasources` | array | Published datasource references (`{luid, name}`) |

**Key navigation:** `upstreamDatasources[].luid` is the published datasource LUID. Pass it to `introspect_datasource.introspect()` or `query.query()` for VDS queries.
