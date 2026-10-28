# Worksheets Reference

**Snippets**: `bar-chart.twb`, `line-chart.twb`, `text-table.twb`, `area-chart.twb`, `pie-chart.twb`, `scatter-plot.twb`, `dual-axis.twb`, `map-chart.twb`, `stacked-bar-chart.twb`, `combo-chart.twb`, `histogram.twb`, `bar-chart-styled.twb`, `bar-chart-filtered.twb`, `bar-chart-sorted.twb`, `custom-tooltip.twb`

## How to Use These Snippets

The snippets show the **simplest valid example** of each chart type (typically 1 dimension + 1 measure). Real dashboards will have more fields. The patterns generalize as follows:
- **Multiple dimensions**: Add more `<column>` + `<column-instance>` entries in `<datasource-dependencies>`, and append fields to `<rows>` or `<cols>` separated by ` / ` for nesting or as separate shelf entries
- **Multiple measures**: Add more `<column-instance>` entries; on shelves, combine with ` + ` for dual-axis or use `[:Measure Names]` / `[:Measure Values]` for side-by-side
- **Additional encodings**: Any chart can add `<color>`, `<size>`, `<lod>` (Detail), `<text>` (Label) encodings — these aren't limited to the chart types shown
- **Calculated fields on shelves**: Use the same column-instance pattern but with `[Calculation_ID]` as the column reference (see `FEATURES.md`)

## Chart Type Quick Reference

The snippets demonstrate the minimum configuration. Real charts often use more fields.

| Chart Type | Mark Class | Columns | Rows | Key Encodings | Panes |
|------------|-----------|---------|------|---------------|-------|
| Bar | `Automatic` | 1+ discrete dim | 1+ measure | — | 1 |
| Line | `Automatic` | 1 continuous date | 1+ measure | — | 1 |
| Text Table | `Automatic` | 1+ discrete dim | 1+ discrete dim | `<text>` = measure | 1 |
| Area | `Area` | 1 continuous date | 1+ measure | — | 1 |
| Pie | `Pie` | *empty* | *empty* | `<color>`, `<wedge-size>`, `<size>`, `<text>` | 1 |
| Scatter | `Automatic` | 1 measure | 1 measure | `<lod>` = dimension (Detail) | 1 |
| Dual Axis | `Automatic` | 1 continuous date | 2 measures (`+`) | `<color>` = `[:Measure Names]` | 3 |
| Map | `Automatic` | `[Longitude (generated)]` | `[Latitude (generated)]` | `<lod>`, `<color>`, `<geometry>` | 1 |
| Stacked Bar | `Automatic` | 1+ discrete dim | 1+ measure | `<color>` = stacking dim | 1 |
| Combo (Bar+Line) | `Bar` + `Line` (per-pane) | 1 continuous date | 2 measures (`+`) | `<color>` = `[:Measure Names]` | 3 |
| Histogram | `Automatic` | 1 bin dim (ordinal) | `CNT` or `SUM` measure | — | 1 |

## Mark Class Rules

- `Automatic`: Tableau infers the mark type from the shelf configuration. Used by bar, line, scatter, dual-axis, stacked bar, histogram, and map.
- `Area`: Must be explicitly set — Tableau would default to Line otherwise.
- `Pie`: Must be explicitly set — all data goes through encodings, not shelves.
- `Bar` + `Line` (per-pane): In combo charts, each pane overrides the mark class individually. See Combo Chart section below.

## What Makes Each Chart Type Unique

### Bar Chart
The simplest pattern. Discrete dimension on one axis, aggregated measure on the other. No encodings block needed.

### Line Chart
Same structure as bar, but the dimension is a **continuous date** with a truncation derivation (e.g., `tmn` = Month-Trunc). The continuous date on Columns triggers the line mark.

### Text Table
Both axes are **discrete dimensions**. The measure appears only as a `<text>` encoding inside `<pane>`:
```xml
<encodings>
  <text column='[datasource].[sum:revenue:qk]' />
</encodings>
```
Requires mark-level style for labels:
```xml
<style-rule element='mark'>
  <format attr='mark-labels-show' value='true' />
  <format attr='mark-labels-cull' value='true' />
</style-rule>
```

### Area Chart
Structurally identical to line chart, except `<mark class='Area' />` is explicit. The date truncation can be any level.

### Pie Chart
The most encoding-heavy chart — **Rows and Cols are empty**. Everything goes through encodings:
```xml
<encodings>
  <color column='[datasource].[none:product_category:nk]' />
  <wedge-size column='[datasource].[sum:cost:qk]' />
  <size column='[datasource].[sum:cost:qk]' />
  <text column='[datasource].[sum:cost:qk]' />
</encodings>
```
- `<wedge-size>` is pie-specific — determines each slice's angle
- Requires right-edge legend cards (color + size) in `<windows>`
- Has `<zoom type='entire-view' />` in viewpoint

### Scatter Plot
Both axes are **continuous measures** — this triggers the circle/shape mark:
```xml
<cols>[datasource].[sum:profit:qk]</cols>
<rows>[datasource].[sum:cost:qk]</rows>
```
Uses `<lod>` encoding for the Detail shelf (disaggregates marks):
```xml
<encodings>
  <lod column='[datasource].[none:product_name:nk]' />
</encodings>
```

### Dual Axis
The most structurally complex worksheet. Two measures combined with `+` on Rows:
```xml
<rows>([datasource].[sum:profit:qk] + [datasource].[sum:revenue:qk])</rows>
```

Creates **3 panes**:
- Pane 0: Shared/default — `<color column='[:Measure Names]' />`
- Pane 1: `y-axis-name='[sum:profit:qk]'` — first axis
- Pane 2: `y-axis-name='[sum:revenue:qk]'` — second axis

Axis synchronization via style rules:
```xml
<style-rule element='axis'>
  <encoding attr='space' class='0' field='[sum:revenue:qk]' synchronized='true' type='space' />
  <format attr='display' class='0' field='[sum:revenue:qk]' scope='rows' value='false' />
</style-rule>
```
- `synchronized='true'` = sync axes
- `display='false'` = hide second axis labels

Requires right-edge color legend card for `[:Measure Names]`.

### Map Chart
Uses **Tableau-generated fields** that don't appear in `<datasource-dependencies>`:
```xml
<cols>[datasource].[Longitude (generated)]</cols>
<rows>[datasource].[Latitude (generated)]</rows>
```

Encodings:
```xml
<encodings>
  <lod column='[datasource].[none:country:nk]' />
  <color column='[datasource].[sum:profit:qk]' />
  <geometry column='[datasource].[Geometry (generated)]' />
</encodings>
```

Requires:
- `<mapsources>` at **both** workbook level and inside `<view>`
- `<style-rule element='map'>` with `washout` attribute
- Geographic dimension must have `semantic-role` attribute (e.g., `[Country].[ISO3166_2]`)
- Right-edge color legend card

### Stacked Bar Chart
Same structure as a basic bar chart, but with a **`<color>` encoding** on a second dimension. The color dimension creates stacked segments within each bar:
```xml
<encodings>
  <color column='[datasource].[none:region:nk]' />
</encodings>
```
- Requires `<column>` + `<column-instance>` for the color dimension in `<datasource-dependencies>`
- Requires right-edge color legend card in `<windows>`
- Mark class stays `Automatic` — Tableau stacks automatically when color is applied to a bar chart

### Combo Chart (Bar + Line)
Combines **different mark types per pane** on a dual axis. Structurally similar to `dual-axis.twb`, but with per-pane mark class overrides:
```xml
<!-- Pane 0: shared — color encoding for Measure Names -->
<pane selection-relaxation-option='selection-relaxation-allow'>
  <mark class='Automatic' />
  <encodings>
    <color column='[:Measure Names]' />
  </encodings>
</pane>
<!-- Pane 1: Bar marks for first measure -->
<pane selection-relaxation-option='selection-relaxation-allow'
     y-axis-name='[sum:revenue:qk]'>
  <mark class='Bar' />
</pane>
<!-- Pane 2: Line marks for second measure -->
<pane selection-relaxation-option='selection-relaxation-allow'
     y-axis-name='[sum:profit:qk]'>
  <mark class='Line' />
</pane>
```
- Uses the same `([measure1] + [measure2])` shelf pattern as dual-axis
- The **critical difference** from `dual-axis.twb`: each pane explicitly sets `<mark class='Bar' />` or `<mark class='Line' />` instead of `Automatic`
- Pane 1 may also include `<mark-sizing>` for bar width control
- Requires right-edge color legend card for `[:Measure Names]`

### Histogram
Uses a **bin-based calculated field** defined at the datasource level with `class='bin'`:
```xml
<column caption='Revenue (bin)' datatype='real'
        name='[Revenue (bin)]' role='dimension' type='ordinal'>
  <calculation class='bin' decimals='2' formula='[revenue]' peg='0' size='500' />
</column>
```
- `class='bin'` (not `class='tableau'`) — `formula` references the source measure, `size` is the bin width, `peg` is the starting value
- The bin column-instance uses **ordinal** type (`:ok` suffix), not nominal (`:nk`):
  ```xml
  <column-instance column='[Revenue (bin)]' derivation='None'
                   name='[none:Revenue (bin):ok]' pivot='key' type='ordinal' />
  ```
- Rows typically use a count aggregation (`CNT` or `SUM` of a "Number of Records" calc)
- May include `<show-full-range>` element to display all bin ranges even if empty

## KPI Worksheets

KPI cards use specialized worksheet patterns. Each KPI card in the dashboard typically consists of 2–3 separate worksheets (value + deltas).

### KPI Value Worksheet (Big Number)
- **Mark class**: `Automatic`
- **Rows/Cols**: Both empty (`<rows />` `<cols />`)
- **Tooltip**: `<tooltip-style tooltip-mode='none' />` — suppress tooltips entirely
- **Encoding**: Single `<text>` encoding with the measure
- **`customized-label`** for the big number display:
  ```xml
  <customized-label>
    <formatted-text>
      <run bold='true' fontcolor='#181d27' fontname='Tableau Medium' fontsize='22'><![CDATA[<[datasource].[sum:measure:qk]>]]></run>
    </formatted-text>
  </customized-label>
  ```
- **Pane style**: `mark-labels-show='true'`, `mark-labels-cull='true'`, `text-align` and `vertical-align` for positioning

### KPI Delta Worksheet (MoM/YoY Change)
- Same base structure as KPI Value, plus **color encoding** for directional indicators
- **Number formatting** with arrow unicode:
  ```xml
  <format attr='text-format' field='...' value='*&#9650; 0.0%;&#9660; -0.0%;&#9668; 0.0%' />
  ```
  Where: ▲ (`&#9650;`) = positive, ▼ (`&#9660;`) = negative, ◄ (`&#9668;`) = zero
- **Color palette** maps a calculated field ("Good"/"Bad"/"zero") to colors:
  ```xml
  <encoding attr='color' field='[none:ColorCalc:nk]' type='palette'>
    <map to='#079455'><bucket>&quot;Good&quot;</bucket></map>
    <map to='#717680'><bucket>&quot;zero&quot;</bucket></map>
    <map to='#d92d20'><bucket>&quot;Bad&quot;</bucket></map>
  </encoding>
  ```
- **Parenthesized label** (for secondary indicators like YoY):
  ```xml
  <customized-label>
    <formatted-text>
      <run fontname='Tableau Medium'>(</run>
      <run fontname='Tableau Medium'><![CDATA[<[datasource].[usr:Calculation_ID:qk]>]]></run>
      <run fontname='Tableau Medium'>)</run>
    </formatted-text>
  </customized-label>
  ```

### Toggle Worksheets (for DZV)
1-cell worksheets used as visual toggle buttons:
- **Mark class**: `Automatic`, empty rows/cols
- Single `<text>` encoding with a calculated field label (CDATA)
- **Background color** via `<style-rule element='table'><format attr='background-color' value='#7f56d9' /></style-rule>` (active state) or neutral color (inactive state)
- `tooltip-mode='none'`

## Number Formatting

The `<format attr='text-format' field='...' value='...' />` attribute controls number display in cells. Lives inside `<style-rule element='cell'>` in the pane `<style>` block:

| Pattern | Display | Use For |
|---------|---------|---------|
| `'*#,##0'` | 1,234 | Integers with commas |
| `'0.0%'` | 12.3% | One decimal percent |
| `'$#,##0.00'` | $1,234.56 | Currency |
| `'*&#9650; 0.0%;&#9660; -0.0%;&#9668; 0.0%'` | ▲ 5.2% / ▼ -3.1% / ◄ 0.0% | Delta indicators with arrows |

## Encoding Elements Catalog

| Element | Purpose | Used By |
|---------|---------|---------|
| `<color>` | Color shelf — dimension creates discrete colors, measure creates gradient | Pie, Dual Axis, Map, Stacked Bar, Combo |
| `<text>` | Label/Text shelf — displayed value on marks | Text Table, Pie |
| `<size>` | Size shelf — scales mark size by measure | Pie |
| `<lod>` | Detail shelf — disaggregates marks without visual encoding | Scatter, Map |
| `<wedge-size>` | Pie-specific — determines slice angle | Pie only |
| `<geometry>` | Map-specific — geographic geometry for polygons | Map only |

## Datasource-Dependencies Block

Every worksheet declares which fields it uses via `<datasource-dependencies>`:
```xml
<datasource-dependencies datasource='federated.HASH'>
  <column caption='Profit' datatype='real' name='[profit]' role='measure' type='quantitative' />
  <column-instance column='[profit]' derivation='Sum' name='[sum:profit:qk]' pivot='key' type='quantitative' />
</datasource-dependencies>
```

- `<column>`: field definition (name, datatype, role, type)
- `<column-instance>`: aggregated/derived reference used on shelves and encodings

## Windows Right-Edge Legends

Charts with color/size encodings need legend cards in the `<window>` section:
```xml
<edge name='right'>
  <strip size='160'>
    <card type='color' />
    <card type='size' />
  </strip>
</edge>
```

Required for: Pie, Dual Axis, Map, and any chart using `<color>` or `<size>` encodings.

## Date Truncation Prefixes

| Prefix | Truncation | Example Instance Name |
|--------|-----------|----------------------|
| `tyr` | Year | `[tyr:order_date:qk]` |
| `tqr` | Quarter | `[tqr:order_date:qk]` |
| `tmn` | Month | `[tmn:order_date:qk]` |
| `twk` | Week | `[twk:order_date:qk]` |
| `tdy` | Day | `[tdy:order_date:qk]` |

The derivation attribute matches: `Year-Trunc`, `Quarter-Trunc`, `Month-Trunc`, `Week-Trunc`, `Day-Trunc`.

## Scaling to Multiple Fields

### Multiple Dimensions on One Axis

Add each dimension as a separate `<column>` + `<column-instance>` in `<datasource-dependencies>`, then list them on the shelf separated by ` / ` for hierarchical nesting:
```xml
<rows>([datasource].[none:region:nk] / [datasource].[none:product_category:nk])</rows>
```
Parentheses are required. Each dimension needs its own entry in `<datasource-dependencies>`.

### Multiple Measures (Non-Dual-Axis)

For side-by-side measures (e.g., grouped bar chart), use the built-in `[:Measure Names]` and `[:Measure Values]` fields:
```xml
<cols>([datasource].[none:region:nk] / [datasource].[none::Measure Names:])</cols>
<rows>[datasource].[sum::Measure Values:]</rows>
```
Each measure still needs its own `<column-instance>` in `<datasource-dependencies>`.

### Color by Dimension

Any chart type can add a color encoding — just add the dimension to `<datasource-dependencies>` and reference it:
```xml
<encodings>
  <color column='[datasource].[none:segment:nk]' />
</encodings>
```
This creates a stacked bar, multi-line chart, etc. depending on the chart type. Remember to add a right-edge color legend card in `<windows>`.

### Tooltip Customization

See the "Custom Tooltips" section below for the full `<customized-tooltip>` pattern. For default tooltips, fields on `<lod>` (Detail) shelf are available without affecting the visual encoding.

## Legend Styling

Legend font/sizing is controlled by `<style-rule element='legend'>` in the worksheet's `<style>` block:
```xml
<style-rule element='legend'>
  <format attr='col-width' field='{{COLOR_FIELD}}' value='70' />
  <format attr='font-size' value='12' />
  <format attr='font-family' value='Tableau Medium' />
</style-rule>
```

This controls the appearance of dashboard-level legend zones (see DASHBOARD.md § Legend Zones).

## Style Rule Ordering

Style rules inside `<style>` blocks **must be ordered alphabetically** by `element` attribute. Tableau Desktop enforces this order:

```xml
<style>
  <style-rule element='axis'> ... </style-rule>
  <style-rule element='cell'> ... </style-rule>
  <style-rule element='gridline'> ... </style-rule>
  <style-rule element='legend'> ... </style-rule>
  <style-rule element='mark'> ... </style-rule>
  <style-rule element='table'> ... </style-rule>
  <style-rule element='worksheet'> ... </style-rule>
</style>
```

For KPI/text worksheets, include cell alignment:
```xml
<style-rule element='cell'>
  <format attr='text-align' value='center' />
  <format attr='vertical-align' value='center' />
</style-rule>
```

## Styling & Design Tokens (`bar-chart-styled.twb`)

### Worksheet Title

Defined inside `<worksheet>` > `<layout-options>` > `<title>` (placed BEFORE `<table>`):
```xml
<layout-options>
  <title>
    <formatted-text>
      <run fontcolor='#7f56d9' fontname='Microsoft Sans Serif' fontsize='14'>&lt;Sheet Name&gt;</run>
    </formatted-text>
  </title>
</layout-options>
```
- `&lt;Sheet Name&gt;` is Tableau's placeholder that auto-resolves to the worksheet name
- `fontcolor`, `fontname`, `fontsize` are inline attributes on the `<run>` element

### Worksheet-Wide Font

Set via `<style-rule element='worksheet'>` inside `<table>` > `<style>`:
```xml
<style-rule element='worksheet'>
  <format attr='font-family' value='Open Sans' />
</style-rule>
```
This cascades to all text in the worksheet (axis labels, tick marks, tooltips) unless overridden by a more specific rule.

### Custom Axis Titles

Set via `<style-rule element='axis'>`:
```xml
<style-rule element='axis'>
  <format attr='title' class='0' field='[datasource].[sum:profit:qk]' scope='rows' value='Profit per region' />
</style-rule>
```
- `scope='rows'` targets the Y-axis; `scope='cols'` targets the X-axis
- `field` identifies which axis to customize (the measure or dimension on that shelf)

### Design Token Application Pattern

To apply a full design token set to a worksheet:

| Token | XML Location | Attribute |
|-------|-------------|-----------|
| Title font/color/size | `layout-options > title > formatted-text > run` | `fontname`, `fontcolor`, `fontsize` |
| Body font | `style > style-rule element='worksheet' > format` | `attr='font-family'` |
| Axis title text | `style > style-rule element='axis' > format` | `attr='title'`, `scope`, `field` |
| Mark colors | `pane > encodings > color` | `column` (dimension for discrete, measure for gradient) |

## Filters (`bar-chart-filtered.twb`)

Filters live inside `<worksheet>` > `<table>` > `<view>`, placed AFTER `<datasource-dependencies>` and BEFORE `<slices>`.

### Categorical Filter (Dimension)

```xml
<filter class='categorical' column='[datasource].[none:region:nk]'>
  <groupfilter function='member' level='[none:region:nk]' member='&quot;Europe&quot;'
               user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />
</filter>
```

For **multiple values**, wrap in `function='union'`:
```xml
<filter class='categorical' column='[datasource].[none:region:nk]'>
  <groupfilter function='union' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate'>
    <groupfilter function='member' level='[none:region:nk]' member='&quot;Europe&quot;' />
    <groupfilter function='member' level='[none:region:nk]' member='&quot;Asia&quot;' />
  </groupfilter>
</filter>
```

### Quantitative Filter (Date Range)

```xml
<filter class='quantitative' column='[datasource].[none:order_date:qk]' included-values='in-range'>
  <min>#2025-03-03#</min>
  <max>#2025-04-22#</max>
</filter>
```
- Date literals use `#` delimiters: `#2025-03-03#`
- `included-values='in-range'` specifies a between-min-and-max range

### Context Filters

Add `context='true'` to any filter to make it a context filter:
```xml
<filter class='categorical' column='[datasource].[none:region:nk]' context='true'>
  ...
</filter>
```
Context filters execute **before** FIXED LOD calculations and all other filters. See `FEATURES.md` → "Context Filters and FIXED LOD" for the full order of operations.

### The `<slices>` Element

After all filters, add a `<slices>` block listing every filtered column:
```xml
<slices>
  <column>[datasource].[none:region:nk]</column>
  <column>[datasource].[none:order_date:qk]</column>
</slices>
```
Every field that has a `<filter>` must also appear in `<slices>`.

### Showing Filter Cards on Dashboard

By default, filters are applied but not visible. To show a filter control card, add to the `<window>` > `<cards>`:
```xml
<card column='[datasource].[none:region:nk]' type='filter' />
```

## Sorting (`bar-chart-sorted.twb`)

### Computed Sort (by Measure)

Place `<computed-sort>` inside `<view>`, after `<datasource-dependencies>` and before `<aggregation>`:
```xml
<computed-sort column='[datasource].[none:product_category:nk]' direction='DESC'
               using='[datasource].[sum:profit:qk]' />
```
- `column` = the dimension being sorted
- `direction` = `DESC` (highest first) or `ASC` (lowest first)
- `using` = the measure that determines sort order

### Manual Sort (Explicit Order)

For custom ordering, use `<sort>` with a `<dictionary>`:
```xml
<sort column='[datasource].[none:product_category:nk]' direction='ASC'>
  <dictionary>
    <bucket>&quot;Electronics&quot;</bucket>
    <bucket>&quot;Furniture&quot;</bucket>
    <bucket>&quot;Office Supplies&quot;</bucket>
  </dictionary>
</sort>
```

### Manifest Addition

Sorted workbooks include `<SortTagCleanup />` in `<document-format-change-manifest>`.

## Custom Tooltips (`custom-tooltip.twb`)

Custom tooltips require a **three-part chain** — all must be in sync:

1. `<datasource-dependencies>` > `<column-instance>` — declares the field
2. `<pane>` > `<encodings>` > `<tooltip column='...' />` — registers the field for tooltip use
3. `<pane>` > `<customized-tooltip>` > `<formatted-text>` — the visual template

### Tooltip Template Structure

```xml
<customized-tooltip>
  <formatted-text>
    <!-- Label (gray, bold) -->
    <run bold='true' fontcolor='#757575' fontname='Open Sans' fontsize='12'>Product Category:</run>
    <!-- Line break -->
    <run fontcolor='#757575' fontname='Open Sans' fontsize='12'>&#198;&#9;</run>
    <!-- Value (bold, default color, field reference in CDATA) -->
    <run bold='true' fontname='Open Sans' fontsize='12'><![CDATA[<[datasource].[none:product_category:nk]>]]></run>
  </formatted-text>
</customized-tooltip>
```

### Field References in `<run>` Elements

Fields are embedded using **CDATA with angle brackets** — this applies to tooltips, customized-labels, KPI values, and any `<run>` element containing a field reference:
```xml
<run><![CDATA[<[datasource_name].[column_instance_name]>]]></run>
```
The `< >` around the field reference is Tableau's substitution syntax. The CDATA wrapper prevents XML parsing issues.

> **Critical**: Never use XML entity encoding (`&lt;...&gt;`) for field references — Tableau will display them as literal text instead of resolving the value. Always use CDATA.

### Line Breaks

Use `&#198;&#9;` (AE ligature + tab) — Tableau's internal line break encoding. **Do not** use `\n` or `<br/>`.

### `<run>` Style Attributes

| Attribute | Values | Notes |
|-----------|--------|-------|
| `bold` | `'true'` | Omit entirely for non-bold (no `bold='false'`) |
| `fontcolor` | `'#hex'` | Omit for default black |
| `fontname` | Font family string | e.g., `'Open Sans'` |
| `fontsize` | Point size | e.g., `'12'` |

### Tooltip Encoding Registration

Every field used in the tooltip template must also be registered in `<encodings>`:
```xml
<encodings>
  <tooltip column='[datasource].[sum:profit:qk]' />
  <tooltip column='[datasource].[attr:product_category:nk]' />
</encodings>
```

## Element Order Inside `<view>` (Canonical)

Based on all snippets, the strict order inside `<worksheet>` > `<table>` > `<view>`:

```
1. <datasources>
2. <datasource-dependencies>
3. <reference-line> elements (zero or more — see FEATURES.md)
4. <filter> elements (zero or more)
5. <computed-sort> / <sort> elements (zero or more)
6. <slices> (only if filters exist)
7. <aggregation value='true' />
```

And the full `<worksheet>` structure:
```
1. <layout-options>  (optional — title styling)
2. <table>
   ├── <view>        (fields, filters, sorts, aggregation)
   ├── <style>       (style-rules for axis, worksheet, marks)
   ├── <panes>       (mark type, encodings, customized-tooltip)
   ├── <rows>        (shelf assignments)
   └── <cols>        (shelf assignments)
3. <simple-id>
```
