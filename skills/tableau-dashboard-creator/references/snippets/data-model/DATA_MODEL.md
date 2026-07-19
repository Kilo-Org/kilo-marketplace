# Data Model Reference

**Snippets**: `single-csv.twb`, `multi-csv-relationship.twb`, `multi-csv-join.twb`

## Decision Criteria

| Scenario | Use | Snippet |
|----------|-----|---------|
| One CSV file | Single datasource | `single-csv.twb` |
| Multiple CSVs, independent queries per table | Relationship model | `multi-csv-relationship.twb` |
| Multiple CSVs, pre-joined flat result | Join model | `multi-csv-join.twb` |

> **Rule**: Relationships and joins are a **structural fork** — you cannot mix them. The choice fundamentally changes the `<relation>`, `<object-graph>`, and `<extract>` structure.

## Single CSV Pattern

The simplest datasource. One `<relation type='table'>` pointing to one CSV:

```xml
<relation connection='textscan.HASH' name='sales_orders.csv'
          table='[sales_orders#csv]' type='table'>
  <columns>
    <column datatype='string' name='order_id' ordinal='0' />
    ...
  </columns>
</relation>
```

- Single object in `<object-graph>`
- Single capability `<metadata-record>`
- No `<cols>` mapping block needed
- No `<extract>` section

## Relationship Model (`type='collection'`)

Used when connecting multiple tables via Tableau's relationship model (new data model). The join logic lives in `<object-graph>`, NOT in the `<relation>` tree.

### Key structure:

```xml
<relation type='collection'>
  <relation type='table' ... />  <!-- table 1 -->
  <relation type='table' ... />  <!-- table 2 -->
</relation>
```

### Object graph stores the relationship:

```xml
<object-graph>
  <objects>
    <object id='table1_GUID' ...> ... </object>
    <object id='table2_GUID' ...> ... </object>
  </objects>
  <relationships>
    <relationship>
      <expression op='='>
        <expression op='[field_name]' />
        <expression op='[field_name (table2.csv)]' />
      </expression>
      <first-end-point object-id='table1_GUID' />
      <second-end-point object-id='table2_GUID' />
    </relationship>
  </relationships>
</object-graph>
```

### Characteristics:

- **Two objects** in object-graph (one per table), each with unique GUID
- **`<cols>` mapping block** required — maps logical field names to `[table].[field]`
- **Duplicate field names** get a `(tablename.csv)` suffix: `[customer_name (customer_segments.csv)]`
- **Two capability metadata-records** (one per CSV)
- **Two `__tableau_internal_object_id__` columns** (one per table)
- **Datasource caption** uses `+` suffix (e.g., `sales_orders+`)
- **Extract** (if present): preserves separate tables in hyper file as `<relation type='collection'>`

## Join Model (`type='join'`)

Used for legacy-style pre-joined flat tables. The join clause lives directly in the `<relation>` tree.

### Key structure:

```xml
<relation join='inner' type='join'>
  <clause type='join'>
    <expression op='='>
      <expression op='[sales_orders.csv].[customer_name]' />
      <expression op='[customer_segments.csv].[customer_name]' />
    </expression>
  </clause>
  <relation type='table' ... />  <!-- left table -->
  <relation type='table' ... />  <!-- right table -->
</relation>
```

### Characteristics:

- **One object** in object-graph (the joined result uses the primary table's GUID)
- **No `<relationships>` element** in object-graph
- **Join types**: `inner`, `left`, `right`, `full`
- **Join expressions** use `[tablename].[fieldname]` syntax in `op` attributes
- **One `__tableau_internal_object_id__` column** (for joined result)
- **Extract** (if present): single flat `[Extract].[Extract]` table
  - Duplicate field names get numeric suffixes in extract: `customer_name` → `customer_name1`
  - All `parent-name` values are `[Extract]`
- **Datasource caption** also uses `+` suffix

## Field Reference Format

Fields on shelves use the fully-qualified format:
```
[datasource_name].[column_instance_name]
```

Example:
```
[federated.1hckotw0bte0i51b8k3sd1ffpnqc].[sum:profit:qk]
```

### Nested dimensions on shelves

Multiple dimensions can be grouped with the `/` operator:
```xml
<rows>([datasource].[none:segment:nk] / [datasource].[none:product_category:nk])</rows>
```
Parentheses are required for nested field grouping.

## Column-Instance Naming Convention

Format: `[derivation:field_name:type_suffix]`

| Derivation | Meaning | Example |
|------------|---------|---------|
| `none` | No aggregation (dimension) | `[none:region:nk]` |
| `sum` | SUM aggregation | `[sum:profit:qk]` |
| `tmn` | Month truncation | `[tmn:order_date:qk]` |
| `twk` | Week truncation | `[twk:order_date:qk]` |
| `tyr` | Year truncation | `[tyr:order_date:qk]` |
| `tqr` | Quarter truncation | `[tqr:order_date:qk]` |
| `tdy` | Day truncation | `[tdy:order_date:qk]` |

| Type Suffix | Meaning |
|-------------|---------|
| `nk` | Nominal key (discrete dimension) |
| `qk` | Quantitative key (continuous measure) |
| `ok` | Ordinal key (ordered dimension) |

## Live Connection Only

**Always generate as live connection** — do not include `<extract>` sections. The multi-table snippet files may contain extract blocks from Tableau Desktop auto-generation; **ignore them**. The live connection pattern (no `<extract>`) is the correct baseline. See `SCAFFOLD.md` → "Live Connection vs Extract" for rationale.

## How to Use These Snippets

These snippets demonstrate the **minimum viable data model** for each pattern. Real dashboards will have:
- More columns per table — add more `<column>` entries in all 4 redundancy locations (see `SCAFFOLD.md`)
- More tables in relationships/joins — add more `<relation type='table'>` children and corresponding objects/metadata
- Different CSV filenames — replace all filename references consistently across the datasource

Use the snippets to understand the structural pattern, then generalize to the actual data.

## Gotchas

1. **Quadruple-redundancy**: Every column must appear in (1) `relation > columns`, (2) `metadata-records`, (3) `object-graph > properties > relation > columns`, AND (4) `datasource > column` direct children. All four must be in sync. See `SCAFFOLD.md` for details.
2. **ID consistency**: The named-connection `name` must be referenced exactly in every `relation connection=` attribute. Object-ID GUIDs must match across metadata-records and object-graph.
3. **`#csv` table names**: The `table` attribute replaces `.` with `#` (e.g., `[sales_orders#csv]`).
4. **Relationship vs Join is irreversible**: Once chosen, the entire datasource structure differs. Cannot convert between them without rebuilding.
5. **Multi-table metadata differences**: In relationship model, each table's columns have distinct `object-id` values. In join model, ALL columns share one `object-id`. Getting this wrong breaks the datasource silently.
