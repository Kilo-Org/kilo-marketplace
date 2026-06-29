# Datasource Introspection

Once a data source has been identified via the [Data Catalog](./CATALOG.md), the agent must introspect it to retrieve comprehensive field metadata so it can construct valid VDS queries. This document covers **Phase 2: Datasource Introspection** in the agent's three-phase pipeline.

1. **Discovery** — Find published data sources on the Tableau site and identify which ones are relevant.
2. **Introspection** — Retrieve field metadata and datasource model.

> **Prerequisites:** You must authenticate via the Tableau REST API as described in [AUTH.md](./AUTH.md) before calling any VDS endpoint.

> **IMPORTANT:** The agent must call `readMetadata` before querying. VDS `readMetadata` is the primary source of truth for which fields are queryable. The Metadata API (GraphQL) is secondary enrichment.

> _NOTE_: VDS only works with published datasources, not those embedded inside workbooks.

---

## Datasource Introspection

Given a datasource LUID, retrieve comprehensive metadata. This phase calls **up to three APIs** and merges their results with a strict fallback chain.

### Step 2A: VDS `readMetadata`

**METHOD**: `POST /api/v1/vizql-data-service/read-metadata`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD**:

```json
{
  "datasource": {
    "datasourceLuid": "<luid>"
  }
}
```

**RESPONSE PAYLOAD**:

```json
{
  "data": [
    {
      "fieldName": "Order Date",
      "fieldCaption": "Order Date",
      "dataType": "DATETIME",
      "defaultAggregation": "NONE",
      "columnClass": "COLUMN",
      "formula": null,
      "logicalTableId": "table-1"
    },
    {
      "fieldName": "SUM(Sales)",
      "fieldCaption": "Sales",
      "dataType": "REAL",
      "defaultAggregation": "SUM",
      "columnClass": "COLUMN",
      "formula": null,
      "logicalTableId": "table-1"
    }
  ],
  "extraData": {
    "parameters": [
      {
        "parameterCaption": "Date Range",
        "parameterType": "QUANTITATIVE_DATE",
        "dataType": "DATE",
        "value": "2024-01-01",
        "minDate": "2020-01-01",
        "maxDate": "2024-12-31",
        "periodValue": 1,
        "periodType": "YEARS"
      }
    ]
  }
}
```

**Response fields (per field)**:

| Field | Description |
|-------|-------------|
| `fieldName` | Internal name |
| `fieldCaption` | Human-readable name (used in VDS queries) |
| `dataType` | `INTEGER`, `REAL`, `STRING`, `DATETIME`, `BOOLEAN`, `DATE`, `SPATIAL`, `UNKNOWN` |
| `defaultAggregation` | `SUM`, `AVG`, `MEDIAN`, `COUNT`, `COUNTD`, `MIN`, `MAX`, `STDEV`, `VAR`, `COLLECT`, `YEAR`, `QUARTER`, `MONTH`, `WEEK`, `DAY`, `TRUNC_YEAR`, `TRUNC_QUARTER`, `TRUNC_MONTH`, `TRUNC_WEEK`, `TRUNC_DAY`, `AGG`, `NONE`, `UNSPECIFIED` |
| `columnClass` | `COLUMN`, `BIN`, `GROUP`, `CALCULATION`, `TABLE_CALCULATION` |
| `formula` | Calculation formula (if applicable) |
| `logicalTableId` | Table this field belongs to |

**Parameters (in `extraData.parameters`)**:

| `parameterType` | Properties |
|-----------------|------------|
| `LIST` | `members` array |
| `QUANTITATIVE_DATE` | `minDate`, `maxDate`, `periodValue`, `periodType` |
| `QUANTITATIVE_RANGE` | `min`, `max`, `step` |
| `ANY_VALUE` | free-form |

**Role:** Primary source of truth. Only fields returned here can be used in VDS queries.

---

### Step 2B: VDS `getDatasourceModel`

**METHOD**: `POST /api/v1/vizql-data-service/get-datasource-model`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD**:

```json
{
  "datasource": {
    "datasourceLuid": "<luid>"
  }
}
```

**RESPONSE PAYLOAD**:

```json
{
  "logicalTables": [
    {
      "logicalTableId": "table-1",
      "caption": "Orders",
      "description": "Order-level sales data"
    },
    {
      "logicalTableId": "table-2",
      "caption": "Returns",
      "description": "Returned orders"
    }
  ],
  "logicalTableRelationships": [
    {
      "fromLogicalTable": { "logicalTableId": "table-1" },
      "toLogicalTable": { "logicalTableId": "table-2" },
      "expression": {
        "op": "AND",
        "relationships": [
          {
            "operator": "=",
            "fromField": "Order ID",
            "toField": "Order ID"
          }
        ]
      }
    }
  ]
}
```

**Version gating:** Only available on Tableau 2025.3+. On earlier versions, skip this call.

---

### Step 2C: Metadata API GraphQL Enrichment

**METHOD**: `POST /api/metadata/graphql`

**HEADERS**:

```
X-Tableau-Auth: <token>
Content-Type: application/json
```

**REQUEST PAYLOAD**:

```graphql
query DatasourceFieldInfo($luid: String!) {
  publishedDatasources(filter: { luid: $luid }) {
    name
    description
    owner {
      name
    }
    fields {
      name
      isHidden
      description
      descriptionInherited {
        attribute
        value
      }
      fullyQualifiedName
      __typename
      upstreamTables {
        name
      }
      ... on AnalyticsField {
        __typename
      }
      ... on ColumnField {
        dataCategory
        role
        dataType
        defaultFormat
        semanticRole
        aggregation
        aggregationParam
      }
      ... on CalculatedField {
        dataCategory
        role
        dataType
        defaultFormat
        semanticRole
        aggregation
        aggregationParam
        formula
        isAutoGenerated
        hasUserReference
      }
      ... on BinField {
        dataCategory
        role
        dataType
        formula
        binSize
      }
      ... on GroupField {
        dataCategory
        role
        dataType
        hasOther
      }
      ... on CombinedSetField {
        delimiter
        combinationType
      }
    }
  }
}
```

Send as JSON:

```json
{
  "query": "<GRAPHQL QUERY STRING FROM ABOVE>",
  "variables": {
    "luid": "<datasource-luid>"
  }
}
```

**Field type discrimination via `__typename`**:

| Type | Description |
|------|-------------|
| `ColumnField` | Raw column from database |
| `CalculatedField` | User-defined calculation |
| `BinField` | Binned measure |
| `GroupField` | Grouped dimension |
| `CombinedSetField` | Combined set |
| `AnalyticsField` | Tableau-generated analytics field |

**Enriched properties (matched by `name` from GraphQL ↔ `fieldCaption` from VDS)**:

- `description`, `descriptionInherited`
- `dataCategory`
- `role`
- `defaultFormat`
- `semanticRole`
- `aggregation`
- `formula`
- `isAutoGenerated`
- `hasUserReference`
- `binSize`

---

### Step 2D: Merge Logic (`combineFields`)

The merge follows this exact procedure:

1. **Initialize result** with:
   - `datasourceDescription` from GraphQL (or empty string if unavailable)
   - `datasourceModel` from Step 2B (if available)
   - Empty `fieldGroups` and `parameters`

2. **Base fields from `readMetadata`** — iterate over every field in the VDS `readMetadata` response. These are the **only** fields included in the final output because only they can be queried via VDS.

3. **For each VDS field, create a simplified field object:**
   - `name` = `fieldCaption`
   - `dataType` = `dataType`
   - `columnClass` = `columnClass`
   - `logicalTableId` = normalized `logicalTableId` (null if empty/undefined)
   - Optional: `defaultAggregation` (if present), `formula` (if present)

4. **Enrich from GraphQL** — for each VDS field, find the matching GraphQL field where `GraphQL.name == VDS.fieldCaption`. If found, add enriched properties.

5. **Populate parameters** from `readMetadata.extraData.parameters` with type-specific extraction.

6. **Group by `logicalTableId`** — collect fields into `fieldGroups: [{ logicalTableId, fields: [...] }]`.

7. **If `datasourceModel` is available**, include it for logical table relationships.

---

### Graceful Degradation Chain: Introspection Phase

The fallback chain is ordered by severity:

| Step | Condition | Behavior |
|------|-----------|----------|
| 1 | VDS `readMetadata` fails (404 or error) | Return error: VDS is not available |
| 2 | VDS `getDatasourceModel` fails (404 or error) | version 2025.3+ -> Return error: VDS is not available |
| 3 | Metadata API is explicitly disabled | Return simplified VDS-only result |
| 4 | Metadata API throws (any exception) | Catch error, return simplified VDS-only result |
| 5 | Metadata API returns empty fields | Return simplified VDS-only result |
| 6 | All APIs succeed | Return fully merged result |

**Critical rule:** If GraphQL fails or is disabled, the agent still gets usable VDS-only metadata. The query is never blocked by Metadata API downtime.


### Field Names vs. Captions

When building VDS queries, it is important to understand the relationship between
introspection output and query request fields:

| Introspection (`FieldMeta`) | Query Request (`QueryField`) | VDS Wire Format | Meaning |
|-----------------------------|------------------------------|-----------------|---------|
| `field.name` or `field.caption` | `field_caption` | `fieldCaption` | The **user-facing** field name shown in Tableau Desktop/Server |
| `field.data_type` | _(not on QueryField)_ | `dataType` | Field data type (`STRING`, `REAL`, `INTEGER`, `DATE`, etc.) |
| `field.default_aggregation` | `function` | `function` | Aggregation to apply (`SUM`, `AVG`, `COUNT`, etc.) |
| `field.role` (property) | _(inferred)_ | _(inferred)_ | `DIMENSION` or `MEASURE` — computed from `column_class` and `data_type` |
| _(n/a)_ | `field_alias` | `fieldAlias` | Controls the **response key name** (see below) |

> **Rule of thumb:** Use `FieldMeta.name` (or the equivalent `FieldMeta.caption` property) as the value for `QueryField.field_caption` when constructing `QueryRequest` objects.

### Response Key Naming

VDS response keys depend on whether a field has an aggregation function:

| Query Field | Response Key (default) | With `field_alias` |
|-------------|----------------------|---------------------|
| `QueryField(field_caption="Region")` | `"Region"` | _(unchanged)_ |
| `QueryField(field_caption="Sales", function="SUM")` | `"SUM(Sales)"` | `"Sales"` (if `field_alias="Sales"`) |
| `QueryField(field_caption="Profit", function="AVG")` | `"AVG(Profit)"` | `"Avg Profit"` (if `field_alias="Avg Profit"`) |

Without `field_alias`, dimensions retain their bare caption as the key, while aggregated measures use the pattern `FUNCTION(fieldCaption)`. Use `field_alias` to normalize response keys for cleaner downstream access:

```python
from query_tableau_data_py.models import QueryField, QueryRequest

# After introspection
field = schema.field_groups[0].fields[0]  # FieldMeta

# Without alias — response key will be "SUM(Sales)"
QueryField(field_caption=field.name, function="SUM")

# With alias — response key will be "Sales"
QueryField(field_caption=field.name, function="SUM", field_alias=field.name)
```

### Naming Across API Layers

The same conceptual field appears under different attribute names depending on the API layer:

| Concept | Python `FieldMeta` (introspection) | Python `QueryField` (request) | VDS Wire (JSON) | GraphQL Metadata API |
|---------|-----------------------------------|-------------------------------|-----------------|---------------------|
| User-visible name | `name` (+ `.caption` alias) | `field_caption` | `fieldCaption` | `name` |
| Response key (aggregated) | _(n/a)_ | controlled by `field_alias` | `fieldAlias` | _(n/a)_ |
| Data type | `data_type` | _(not on QueryField)_ | `dataType` | `dataType` |
| Role | `.role` property | _(inferred from function)_ | _(inferred)_ | `role` |
| Aggregation | `default_aggregation` | `function` | `function` | `aggregation` |
| Logical table | `logical_table_id` | _(not on QueryField)_ | `logicalTableId` | _(via upstreamTables)_ |

### Introspection Output Format

Introspection results are saved as **JSON** in `temp/` for local exploration (see [TEMP_DATA.md](../sdk/TEMP_DATA.md)).

A short summary is printed to stdout (first 10 datasource names) so the agent can reason in context without opening the file.

---

## Version Gating Reference

The following features affect datasource introspection workflows (see [vds/LIMITATIONS.md](../vds/LIMITATIONS.md)):

| Feature | Tableau >= 2025.3 | < 2025.3 |
|---------|-------------------|----------|
| Datasource model (`getDatasourceModel`) | Available | Unavailable |
| Metadata API GraphQL enrichment | Available | Available |

> Query row limits and functions/calculations in filters are documented in [vds/LIMITATIONS.md](../vds/LIMITATIONS.md).
