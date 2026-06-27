# Scaffold Reference

**Snippet**: `workbook-skeleton.twb`
**Version**: `source-build='2025.1.10 (20251.25.1121.1650)'`

## Purpose

The minimal valid `.twb` that Tableau Desktop opens without errors. Use as the starting skeleton for all generated workbooks — add datasources, worksheets, dashboards, and windows into this structure.

## Top-Level Element Order (STRICT)

Elements **must** appear in this exact order inside `<workbook>`:

```
1. <document-format-change-manifest>
2. <preferences>
3. <datasources>
4. <actions>              ← optional, only if dashboard actions exist
5. <worksheets>
6. <dashboards>
7. <windows>
8. <thumbnails>
```

Violating this order causes Tableau to reject the file.

## Document Format Change Manifest

The manifest contains empty self-closing tags that act as **feature flags**. The skeleton includes:

```xml
<document-format-change-manifest>
  <AccessibleZoneTabOrder />
  <AnimationOnByDefault />
  <AutoCreateAndUpdateDSDPhoneLayouts />
  <MarkAnimation />
  <ObjectModelEncapsulateLegacy />
  <ObjectModelTableType />
  <SchemaViewerObjectModel />
  <SetMembershipControl />
  <SheetIdentifierTracking />
  <WindowsPersistSimpleIdentifiers />
  <ZoneFriendlyName />
</document-format-change-manifest>
```

> **Gotcha**: Adding or removing tags here changes Tableau behavior. When in doubt, keep the skeleton's set as-is.
> `<ZoneFriendlyName />` enables `friendly-name` attributes on dashboard layout zones — always include it.

## Internal ID Patterns

| ID Type | Format | Example |
|---------|--------|---------|
| Datasource name | `federated.` + 32-char hash | `federated.1hckotw0bte0i51b8k3sd1ffpnqc` |
| Named connection | `textscan.` + 32-char hash | `textscan.16xkalt18d1a7p1cjzge51xf66r6` |
| Object ID | `{filename}_{32-hex-GUID}` | `sales_orders.csv_09EB5EA8C4E1488681646EA8C7C1C3B0` |
| Simple ID (UUID) | `{GUID}` with braces | `{8ED4AD55-A43F-4C33-B8C1-A6484D0F1985}` |
| Zone IDs | Sequential integers | `3`, `4`, `5` |

> **Rule**: Every ID must be unique within the workbook. Generate new GUIDs/hashes — never reuse from snippets.

## Column Definition Redundancy

Every column in a datasource is defined in **four places** that must stay in sync. This applies to **all datasource types** (single CSV, relationship, join):

| # | Location | What It Stores | Notes |
|---|----------|---------------|-------|
| 1 | `connection > relation > columns > column` | Physical schema (datatype, name, ordinal) | For multi-table: each `<relation type='table'>` has its own `<columns>` |
| 2 | `metadata-records > metadata-record` | Rich metadata (remote-type, local-type, aggregation, object-id) | Relationship model: object-id differs per table. Join model: all share one object-id |
| 3 | `object-graph > object > properties > relation > columns > column` | Physical schema (duplicate of #1) | Relationship: N objects. Join: 1 object containing the full join relation |
| 4 | `datasource > column` (direct children) | UI metadata (caption, role, type, semantic-role) | Same structure across all models |

Missing any one causes silent corruption or load failures. Locations 1 and 3 must be byte-for-byte identical (per table).

## Remote-Type Codes (ODBC)

| Code | Type | Default Aggregation | Notes |
|------|------|---------------------|-------|
| `129` | string | Count | Has `width=1073741823` and `collation` |
| `133` | date | Year | — |
| `20` | integer | Sum | — |
| `5` | real/float | Sum | — |

## Table Name Convention

CSV filenames in the `table` attribute replace `.` with `#`:
- `sales_orders.csv` → `[sales_orders#csv]`

## Dashboard Coordinate System

Zones use a **100,000 × 100,000** virtual coordinate space:
- Root zone: `x=0 y=0 w=100000 h=100000`
- Inner zones offset by margins (e.g., `x=800 y=1000 w=98400 h=98000` = 800px margins)

## Semantic Values

Tableau auto-detects locale and stores it:
```xml
<semantic-value key='[Country].[Name]' value='&quot;Israel&quot;' />
```
This is system-locale dependent — parameterize if targeting different regions.

## Window Card Structure

The `<cards>` element in `<window>` follows a rigid layout:
- **Left edge**: pages → filters → marks
- **Top edge**: columns → rows → title

Always in this order.

## Window Attributes

Every `<window>` element must include:

- **`<simple-id uuid='{GUID}' />`** — mandatory on every window. These UUIDs are the cross-reference target for navigation buttons (`tabdoc:goto-sheet window-id="..."`). Format: `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` (standard UUID with braces).
- **`hidden='true'`** — add to worksheet windows that only appear embedded in dashboards (not standalone). Hides them from the sheet tab bar.
- **`maximized='true'`** — add to the primary (first) dashboard window. Only one window should be maximized.

### Viewpoints

All viewpoints inside dashboard `<window>` elements must include `<zoom type='entire-view' />`:
```xml
<viewpoint name='SheetName'>
  <zoom type='entire-view' />
</viewpoint>
```
Never use self-closing `<viewpoint name='...' />` without the zoom child — the default `'standard'` mode causes sheets to not fill their allocated space.

## Multi-Dashboard Workbooks

A workbook can contain multiple `<dashboard>` elements and multiple dashboard `<window>` elements. The structure:

```
<workbook>
  <dashboards>
    <dashboard name='Overview' ...> ... </dashboard>
    <dashboard name='Detail' ...> ... </dashboard>
  </dashboards>
  <windows>
    <window class='dashboard' maximized='true' name='Overview'>
      <viewpoints> ... </viewpoints>
      <simple-id uuid='{...}' />
    </window>
    <window class='dashboard' name='Detail'>
      <viewpoints> ... </viewpoints>
      <simple-id uuid='{...}' />
    </window>
    <window class='worksheet' hidden='true' name='KPI Sheet'>
      ...
      <simple-id uuid='{...}' />
    </window>
  </windows>
</workbook>
```

Cross-dashboard navigation buttons reference target windows by their `simple-id uuid`.

## Live Connection vs Extract

**Always generate as live connection** (no `<extract>` section). Reasons:
- Extract doubles the XML complexity (duplicate metadata-records, cols mappings, hyper file paths, refresh events)
- The `.twbx` packaging with embedded CSVs already provides portability
- Users do `Data → Replace Data Source` to connect live databases anyway
- Extract can be created later in Tableau Desktop with one click (`Data → Extract Data`)

The snippet `.twb` files in `scaffold/` and `data-model/` use live connections as the reference pattern. If a snippet contains an `<extract>` section, **ignore it** — do not reproduce it in generated output.

## How to Use These Snippets

These snippets are **baselines, not templates**. The actual dashboard you generate will have different field names, more fields, different chart combinations, and more complex layouts. Use the snippets to understand:
- The correct XML structure and element ordering
- Which attributes are required vs optional
- How internal IDs cross-reference each other
- The structural differences between patterns (e.g., relationship vs join)

Then **generalize** from these patterns to the specific dashboard requirements.

## Phone Device Layout

Auto-generated phone layouts use `sizing-mode='vscroll'` and `is-fixed='true'` zones. These are created automatically by Tableau when `AutoCreateAndUpdateDSDPhoneLayouts` is in the manifest.

## Examples Directory

The `examples/` directory contains additional workbook references. These are **not** the primary reference — `snippets/` is. Only search the existing example workbooks in `examples/*.twb` as a Tier 3 fallback when no snippet or pattern block covers the requested feature. Do not treat them as canonical templates; extract only the specific XML patterns you need.
