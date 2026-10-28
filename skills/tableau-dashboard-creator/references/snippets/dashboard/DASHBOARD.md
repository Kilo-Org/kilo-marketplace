# Dashboard Reference

**Snippets**: `single-sheet-layout.twb`, `multi-sheet-layout.twb`, `action-filter.twb`, `highlight-action.twb`, `parameter-action.twb`

## Zone Hierarchy

Every dashboard is a tree of zones. The root is always `type-v2='layout-basic'` with `w=100000 h=100000`.

### Zone Types

| `type-v2` | Purpose | Key Attributes |
|-----------|---------|----------------|
| `layout-basic` | Root container | Always `x=0 y=0 w=100000 h=100000` |
| `layout-flow` | Flow container | `param='horz'` (left-to-right) or `param='vert'` (top-to-bottom) |
| *(worksheet)* | Sheet zone | `name='sheet-name'` — must match a `<worksheet name=...>` |
| `empty` | Blank spacer | No content — see Spacers section |
| `text` | Text block | `<formatted-text>` > `<run>` for styled text |
| `bitmap` | Image/logo | `param='Image/filename.svg'`, `is-scaled='1'` |
| `color` | Legend zone | `name='WorksheetName'`, `param='ColorField'` — see Legend Zones section |
| `filter` | Quick filter | `mode='checkdropdown'` (default for dimensions) |
| `dashboard-object` | Button/extension | `<button>` child for navigation or toggle |
| `paramctrl` | Parameter widget | `param='[Parameters].[Parameter N]'`, `mode='compact'` |

> **Note**: Tableau uses `type-v2` (not `type`) for zone classification. All generated zones should use `type-v2`.

### Critical Rules

> **`<zone-style>` must be the LAST child** of every `<zone>` element — after all child zones, after `<layout-cache>`, after everything.

### Default Zone-Style Reset

Tableau applies a baseline style to every zone. The skill should emit this as a default, then override with specific styling:
```xml
<zone-style>
  <format attr='border-color' value='#000000' />
  <format attr='border-style' value='none' />
  <format attr='border-width' value='0' />
  <format attr='margin' value='4' />
</zone-style>
```

### Zone Friendly Names

Every layout zone should have a `friendly-name` attribute with a human-readable label derived from the TABLEAU-IMPLEMENTATION.md container tree:
```xml
<zone id='3' param='vert' friendly-name='Main Content' type-v2='layout-flow'>
```
Requires `<ZoneFriendlyName />` in the manifest (already included in `workbook-skeleton.twb`).

### Layout Patterns

**Single sheet** (`single-sheet-layout.twb`):
```
layout-basic (root)
  └── worksheet zone (name='bar-chart')
```

**Nested containers** (`multi-sheet-layout.twb`):
```
layout-basic (root)
  └── layout-flow (horz)
        └── layout-flow (vert)
              ├── layout-flow (horz)   ← top row
              │     ├── layout-flow (vert, fixed-size=432)  ← left column
              │     │     ├── bar-chart   (show-title=false)
              │     │     └── line-chart  (show-title=false)
              │     └── map-chart         (show-title=false)
              └── empty                ← bottom spacer
```

Key attributes for layout control:
- `is-fixed='true'` + `fixed-size='432'` = fixed-width/height container (pixels)
- `show-title='false'` = suppress worksheet title in dashboard
- Without `is-fixed`, containers fill remaining space proportionally
- `layout-strategy-id='distribute-evenly'` = equal-width/height children (use for KPI card rows)

## Common Layout Archetypes

### 1. Header Bar
Fixed-height horizontal flow for branding, title, and utility elements:
```
zone (layout-flow, horz, is-fixed, fixed-size='50-70', friendly-name='Header')
  ├── zone (bitmap): logo — param='Image/logo.svg', is-scaled='1', fixed-size for width
  ├── zone (empty, fixed-size='12'): spacer
  ├── zone (text, fixed-size): title text
  ├── zone (empty): flex spacer — pushes remaining items right
  └── zone (worksheet): utility sheet (e.g., reference date)
```
Zone-style: background-color from design tokens, padding on all sides.

### 2. Sidebar (Collapsible)
Fixed-width vertical flow for filters and navigation:
```
zone (layout-flow, vert, is-fixed, fixed-size='150-200', friendly-name='Sidebar')
  ├── zone (empty): top spacer
  ├── zone (filter, mode='checkdropdown'): filter 1
  ├── zone (filter, mode='checkdropdown'): filter 2
  └── zone (empty): bottom spacer
```
Add `hidden-by-user='true'` for collapsible sidebars (toggled by a toggle button — see Buttons section).
Zone-style: border, padding, white background.

### 3. Card Container
Vertical flow with border styling for grouped content (KPIs, chart sections):
```xml
<zone-style>
  <format attr='border-color' value='#e9eaeb' />
  <format attr='border-style' value='solid' />
  <format attr='border-width' value='1' />
  <format attr='margin' value='7' />
  <format attr='padding' value='8' />
  <format attr='background-color' value='#ffffff' />
</zone-style>
```

### 4. Spacers
Two types — use correctly:
- **Flex spacer**: `type-v2='empty'` *without* `fixed-size` or `is-fixed` — fills remaining space proportionally. Use to push elements apart (e.g., title left, button right).
- **Fixed spacer**: `type-v2='empty'` *with* `fixed-size='N'` — creates exact pixel gaps between elements.

## Title Pattern

Prefer separate `<zone type-v2='text'>` elements above each worksheet zone for titles, with `show-title='false'` on the sheet zone. This provides better control over title styling:

```
zone (layout-flow, vert, friendly-name='Chart Name')
  ├── zone (text, fixed-size='30'):
  │     <formatted-text><run bold='true' fontname='Tableau Medium' fontsize='12'>Chart Title</run></formatted-text>
  └── zone (worksheet, name='SheetName', show-title='false')
```

## Layout Cache

`<layout-cache>` is an optional element on worksheet zones that provides sizing hints to Tableau's layout engine. Place it as a child of the zone, before `<zone-style>`:

| Zone Type | Recommended `<layout-cache>` |
|-----------|------------------------------|
| KPI value | `cell-count-h='1' cell-count-w='1' type-h='cell' type-w='cell'` |
| KPI delta | `fixed-size-h='20' fixed-size-w='60' type-h='fixed' type-w='fixed'` |
| Trend chart | `minheight='163' minwidth='140' type-h='scalable' type-w='scalable'` |
| Bar/table chart | `cell-count-h='2' minwidth='180' type-h='cell' type-w='scalable'` |
| Toggle button | `cell-count-h='1' type-h='cell' type-w='cell'` |

## Legend Zones

Legends can be placed as `type-v2='color'` zones inside the dashboard layout (preferred over window-edge legend cards for positioning control). Place below the chart they describe:

```xml
<zone fixed-size='22' id='{{ZONE_ID}}' is-fixed='true'
      leg-item-layout='horz'
      name='{{WORKSHEET_NAME}}'
      pane-specification-id='{{PANE_INDEX}}'
      param='{{COLOR_FIELD_REFERENCE}}'
      show-title='false'
      type-v2='color'>
  <zone-style>
    <format attr='border-color' value='#000000' />
    <format attr='border-style' value='none' />
    <format attr='border-width' value='0' />
    <format attr='margin' value='4' />
    <format attr='padding-left' value='16' />
  </zone-style>
</zone>
```

| Attribute | Purpose |
|-----------|---------|
| `name` | The worksheet whose color encoding to display |
| `param` | The field used for color encoding (full `[datasource].[field:role]` reference) |
| `pane-specification-id` | Which pane's encoding to show (0-indexed; relevant for multi-pane charts) |
| `leg-item-layout='horz'` | Horizontal legend items (single row); omit for vertical |
| `show-title='false'` | Hides the default "Color" label |
| `fixed-size='22'` | Typical single-row height |

Legend font/sizing is controlled in the worksheet's `<style>` block — see WORKSHEETS.md § Legend Styling.

## KPI Card Assembly

KPI cards are multi-part containers with a value, optional delta indicators, and labels:

```
zone (layout-flow, vert, friendly-name='KPI Name', card styling)
  ├── zone (text): KPI title — bold, gray (#717680), fontsize='12'
  ├── zone (worksheet): KPI value — layout-cache cell-count-h='1' cell-count-w='1' type-h='cell'
  ├── zone (layout-flow, horz): delta indicators row
  │   ├── zone (worksheet): MoM delta — layout-cache fixed-size-h='20' fixed-size-w='60'
  │   └── zone (worksheet): YoY delta — layout-cache fixed-size-h='20' fixed-size-w='80'
  └── zone (text): subtitle label — light gray (#bcbec4), e.g., "MoM (YoY)"
```

The KPI row container should use `layout-strategy-id='distribute-evenly'` to space cards equally.

See WORKSHEETS.md § KPI Worksheets for the worksheet-level patterns (mark type, customized-label, number formatting, conditional coloring).

## Image Zones

For logos and icons embedded in the dashboard:
```xml
<zone fixed-size='192' id='{{ZONE_ID}}' is-fixed='true' is-scaled='1'
      param='Image/{{filename}}' type-v2='bitmap'>
  <zone-style> ... </zone-style>
</zone>
```
- Supported formats: SVG, PNG, JPG
- Images must be included in the `.twbx` ZIP under an `Image/` subdirectory
- Typically placed in header bars with `fixed-size` for width control

## Dashboard-Level Datasource Declarations

When a dashboard includes quick filters, the `<dashboard>` element must contain its own `<datasources>` and `<datasource-dependencies>` blocks:

```xml
<dashboard name='Dashboard Name'>
  <datasources>
    <datasource caption='sales_orders' name='federated.HASH' />
  </datasources>
  <datasource-dependencies datasource='federated.HASH'>
    <column-instance column='[region]' derivation='None' name='[none:region:nk]' pivot='key' type='nominal' />
    <column caption='Region' datatype='string' name='[region]' role='dimension' type='nominal' />
  </datasource-dependencies>
  <!-- ... zones ... -->
</dashboard>
```

This is **separate** from workbook-level datasources and required for filter zones to function.

## Buttons and Navigation

### Cross-Dashboard Navigation Button (`goto-sheet`)

```xml
<zone fixed-size='192' id='{{ZONE_ID}}' is-fixed='true' type-v2='dashboard-object'>
  <button action='tabdoc:goto-sheet window-id="{{TARGET_WINDOW_UUID}}"' button-type='text'>
    <button-visual-state>
      <caption>{{Button Label}}</caption>
      <button-caption-font-style fontname='Tableau Medium' fontsize='12' />
      <format attr='border-style' value='solid' />
      <format attr='border-width' value='1' />
      <format attr='border-color' value='#e9eaeb' />
    </button-visual-state>
  </button>
  <zone-style> ... </zone-style>
</zone>
```

The `window-id` references the target dashboard's `<simple-id uuid='...'>` in the `<windows>` section (see SCAFFOLD.md § Window Attributes).

### Toggle Button (Show/Hide Zones)

```xml
<zone id='{{ZONE_ID}}' type-v2='dashboard-object'>
  <button active-visual-state-index='1'>
    <toggle-action>tabdoc:toggle-button-click-action window-id="{{DASHBOARD_WINDOW_UUID}}" zone-ids=[{{TARGET_ZONE_IDS}}]</toggle-action>
    <button-visual-state />
    <button-visual-state>
      <image-path>Image/{{icon_filename}}</image-path>
    </button-visual-state>
  </button>
  <zone-style> ... </zone-style>
</zone>
```

- `active-visual-state-index` controls which visual state is active (0 or 1)
- `zone-ids` references the zone IDs of collapsible sections (e.g., a sidebar)
- Two `<button-visual-state>` elements: one empty (hidden state), one with icon (visible state)

### Toggle Button Bar (DZV Toggles)

For parameter-driven toggle systems (see FEATURES.md § DZV Toggle Workflow):
```
zone (layout-flow, horz, friendly-name='Toggle Bar', fixed-size='50')
  ├── zone (worksheet): "Option A Active" — layout-cache cell-count-h='1' type-h='cell'
  ├── zone (worksheet): "Option A InActive" — layout-cache cell-count-h='1' type-h='cell'
  ├── zone (worksheet): "Option B Active" ...
  ├── zone (worksheet): "Option B InActive" ...
  └── zone (empty): flex spacer
```

### Zone IDs

Zone IDs are **sequential integers**, unique within the workbook. They're cross-referenced by:
- `<window> > <active id='N'>` — the currently selected zone
- Phone device layout zones reuse the same IDs for worksheet references

## Actions

Actions live inside `<workbook> > <actions>` (between `</datasources>` and `<worksheets>`, NOT inside `<dashboard>`). Three distinct types:

### Filter Action (`action-filter.twb`)

```xml
<action caption='action-filter-example'
        name='[Action1_GUID]'>
  <activation auto-clear='true' type='on-select' />
  <source dashboard='Dashboard Name' type='sheet' worksheet='source-sheet' />
  <command command='tsc:tsl-filter'>
    <param name='exclude' value='source-sheet' />
    <param name='special-fields' value='all' />
    <param name='target' value='Dashboard Name' />
  </command>
</action>
```

| Element | Purpose |
|---------|---------|
| `activation type` | `on-select` (click) or `on-hover` |
| `auto-clear` | `true` = clear filter on deselect |
| `source worksheet` | Sheet that triggers the action |
| `exclude` | Sheet to EXCLUDE from being filtered (usually the source) |
| `special-fields` | `all` = pass all fields as filter criteria |
| `target` | Target dashboard (filters all non-excluded sheets in it) |

**Side effect**: The target worksheet gets an auto-generated filter column:
```xml
<filter class='categorical' column='[datasource].[Action (Field Name)]'>
  <groupfilter ... user:ui-action-filter='[Action1_GUID]' />
</filter>
```

### Highlight Action (`highlight-action.twb`)

```xml
<action caption='highlight-action-example'
        name='[Action1_GUID]'>
  <activation auto-clear='true' type='on-hover' />
  <source dashboard='Dashboard Name' type='sheet' worksheet='source-sheet' />
  <command command='tsc:brush'>
    <param name='exclude' value='source-sheet' />
    <param name='field-captions' value='WEEK(Order Date)' />
    <param name='target' value='Dashboard Name' />
  </command>
</action>
```

Key differences from filter:
- `command='tsc:brush'` instead of `tsc:tsl-filter`
- Typically `type='on-hover'`
- `field-captions` specifies the matching field(s) — can be a specific field name OR `all` to match on all shared fields (the snippet demonstrates a specific field)
- **No auto-generated filter** on the target worksheet

### Parameter Action (`parameter-action.twb`)

Uses a **different XML tag** entirely:

```xml
<edit-parameter-action caption='change-parameter-action-example'
                       name='[Action1_GUID]'>
  <activation type='on-select' />
  <source dashboard='Dashboard Name' type='sheet' worksheet='source-sheet' />
  <agg-type type='attr' />
  <clear-option type='do-nothing' value='s:LROOT:' />
  <params>
    <param name='source-field' value='[datasource].[none:Calculation_ID:nk]' />
    <param name='target-parameter' value='[Parameters].[Parameter 1]' />
  </params>
</edit-parameter-action>
```

| Element | Purpose |
|---------|---------|
| `<edit-parameter-action>` | Different tag from `<action>` |
| `agg-type` | How to handle multi-select (`attr` = single value) |
| `clear-option` | What happens on deselect (`do-nothing` = keep current value) |
| `source-field` | Which field's value to read from the clicked mark |
| `target-parameter` | Which parameter to set (`[Parameters].[Parameter N]`) |

**Requires**: The parameter must be defined in `<datasource name='Parameters'>` AND the dashboard must declare a `<datasource-dependencies datasource='Parameters'>` block.

### Action Name Format

Internal action names follow the pattern: `[Action1_<32-char-hex-GUID>]`

## Parameter Control Zone

To show a parameter widget in the dashboard, add a `paramctrl` zone:

```xml
<zone id='25' mode='compact'
      param='[Parameters].[Parameter 1]'
      type-v2='paramctrl' w='9323' x='90209' y='893' h='5804'>
  <zone-style> ... </zone-style>
</zone>
```

The dashboard must also declare the Parameters datasource:
```xml
<datasources><datasource name='Parameters' /></datasources>
<datasource-dependencies datasource='Parameters'>
  <column ... name='[Parameter 1]' ... />
</datasource-dependencies>
```

## Complex Layouts — Production Example

For dashboards requiring **3+ levels of nesting**, refer to the production workbook in `examples/top-level-workbook-example.twb`. This is a real 2-dashboard workbook with:

- **10 levels of zone nesting** (238 zones in the primary dashboard)
- `friendly-name` attributes on all structural containers (e.g., `V-Outer`, `H-Header`, `H-Body`, `V-Sidebar`, `V-Main`, `H-KPIs`)
- `layout-strategy-id='distribute-evenly'` on KPI rows
- Header bar + sidebar + main content area + KPI cards + toggle bar + chart sections
- DZV (Dynamic Zone Visibility) toggle pattern with Active/InActive worksheet pairs
- Cross-dashboard navigation (second dashboard: country detail drill-down)

**Naming convention for friendly-names**: The example uses a prefix convention — `V-` for vertical containers, `H-` for horizontal containers, then a descriptive label (e.g., `H-KPI-DELTAS-1`, `V-CHART-TRENDS`). This makes the zone hierarchy readable when debugging.

**Zone hierarchy pattern** (simplified from the example):
```
V-Outer (vert)
├── H-Header (horz, is-fixed) — logo, title, utility sheet
├── H-Body (horz)
│   ├── V-Sidebar (vert, is-fixed) — filters, navigation
│   └── V-Main (vert)
│       ├── H-KPIs (horz, distribute-evenly) — KPI value + delta pairs
│       ├── H-TOGGLE-BAR (horz, is-fixed) — DZV toggle buttons
│       ├── V-CHART-TRENDS (vert) — trend chart with title text zone
│       └── V-CHART-SUBSCRIBERS (vert) — detail chart with title text zone
```

> **Usage**: Do NOT read this file in full — it's a large production workbook (~500KB XML). Grep for specific zone patterns (e.g., `friendly-name`, `layout-strategy-id`, `hidden-by-user`) to learn the nesting structure.

> **When to use**: Only reference this example when `multi-sheet-layout.twb` (2 levels) is insufficient for the requested layout complexity. Most dashboards work fine with 2-3 levels.

## How to Use These Snippets

These snippets show the **minimum viable example** of each pattern. Real dashboards will combine multiple patterns:
- A dashboard with 5 sheets, nested containers, 2 filter actions, and a parameter control
- Multiple actions on the same dashboard — just add more `<action>` / `<edit-parameter-action>` elements inside `<actions>`
- Zones can be nested to any depth — use `layout-flow` containers to create complex grid layouts
- Any action type can use `on-select` or `on-hover` activation

Use the snippets to understand the XML structure for each feature, then compose them together based on the dashboard requirements.

## Filter Zone Modes

For filter zones in the dashboard, use the appropriate mode:

| Field Type | Default Mode | Alternative | When to Use Alternative |
|-----------|-------------|-------------|------------------------|
| Dimension | `checkdropdown` | `typeinlist` | When the dimension has 100+ distinct values |
| Date | `daterange` | — | — |
| Measure | `range` | — | — |

## Cross-Reference Checklist

When assembling a dashboard, verify these references match:

1. **Zone `name=`** ↔ **`<worksheet name=...>`** — exact string match
2. **Action `source worksheet=`** ↔ **worksheet name** — exact match
3. **Action `target dashboard=`** ↔ **`<dashboard name=...>`** — exact match
4. **Action `exclude value=`** ↔ **source worksheet name** — exact match
5. **`<window> > <viewpoint name=...>`** ↔ **worksheet name** — for each sheet in the dashboard
6. **`<window> > <active id=...>`** ↔ **zone ID** — the default selected zone
7. **Parameter action `target-parameter`** ↔ **`<column name=...>` in Parameters datasource**
8. **`paramctrl` zone `param=`** ↔ **`[Parameters].[Parameter N]`** — exact match
