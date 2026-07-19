# Step E: TWB Workbook Generation (Experimental)

**Identity**: You are a Tableau XML engineer. Your goal is to generate a valid `.twbx` packaged workbook that can be opened directly in Tableau Desktop, fully implementing the dashboard from Step D's specification.

**Default scaffold build string**: `source-build='2025.1.10 (20251.25.1121.1650)'`. All snippets are authored against this build. The actual emitted `version` and content model depend on the user's **Target Tableau Version** (set in Step 0 — see *Tableau Version Targeting* below).

> **Experimental**: This step generates Tableau XML programmatically. The output should be a functional starting point, though minor adjustments in Tableau Desktop may be needed.

---

## Tableau Version Targeting

Read `## Target Tableau Version` from `design-tokens.md` (set in Step 0). Apply the matching emission rules below. Do **not** ask the user again — Step 0 already collected this.

| Target version | Workbook attribute | `<explain-data>` element | Notes |
|----------------|--------------------|--------------------------|-------|
| **2024.2 – 2025.x** *(default)* | `version='18.1'` | **Do NOT emit** — Tableau 2025.x rejects this element with error code `D2E8DA72` (`no declaration found for element 'explain-data'`) | Use the scaffold as-is. The 2025.x content model ends with `..., windows, thumbnails?, external?` — anything after `<thumbnails />` other than `<external>` breaks the load. |
| **2026.1+** | `version='26.1'` | **Required** — emit immediately after `<thumbnails />`:<br>`<explain-data enabled-for-viewer='false' extreme-values-enabled-for-all='false'><explanation-types /></explain-data>` | The official `twb_2026.1.0.xsd` declares `<explain-data>` as a required workbook child. |

If `design-tokens.md` does not have a `## Target Tableau Version` section, default to **2024.2 – 2025.x** and add a `MANUAL_STEPS.md` note that the user should confirm the target.

## Process

1. **Read the approved TABLEAU-IMPLEMENTATION.md** (`mock-version/v_N/TABLEAU-IMPLEMENTATION.md`)
2. **Read design-tokens.md** for all styling values
3. **Read DS-ARCHITECTURE.md** for field names and types
4. **Locate sample data CSVs** from Step A (in the project root or `sample-data/` directory)
5. **Read the relevant snippet files and companion docs** (see Assembly Workflow below)
6. **Assemble `dashboard.twb`** from validated snippet patterns
7. **Run both validators** on the assembled `.twb` (see *Validation* below) — `validate_twb.py` and `validate_twb_xsd.py`. Resolve any failures before continuing.
8. **Package as `dashboard.twbx`** — a ZIP archive bundling the `.twb` with all sample CSV data files
9. **Save to** `mock-version/v_N/` (both `.twb` and `.twbx`)

---

## Assembly Workflow

### Step 1: Start from the Scaffold

Read the **actual XML** in `snippets/scaffold/workbook-skeleton.twb` and the companion `snippets/scaffold/SCAFFOLD.md`.

> **Important**: Always read both the `.twb` file (source of truth for exact XML structure) AND the companion `.md` (explains the patterns and parameterization). The `.md` alone is not sufficient — you need the actual XML to assemble from.

This is your base template. All generated workbooks follow this structure:

```
<workbook>
  1. <document-format-change-manifest>   ← from scaffold
  2. <preferences>                        ← from scaffold
  3. <datasources>                        ← from data-model snippets
  4. <actions>                            ← from dashboard action snippets (if any)
  5. <worksheets>                         ← from worksheet snippets
  6. <dashboards>                         ← from dashboard snippets
  7. <windows>                            ← assembled from worksheets + dashboard
  8. <thumbnails>                         ← empty placeholders
</workbook>
```

**Element order is STRICT** — violating it causes Tableau to reject the file.

### Step 2: Select Data Model Pattern

Read `snippets/data-model/DATA_MODEL.md` and the relevant `.twb` snippet.

| DS-ARCHITECTURE says... | Use snippet | Key |
|------------------------|-------------|-----|
| 1 CSV file | `data-model/single-csv.twb` | Single `<relation type='table'>` |
| Multiple CSVs, independent tables | `data-model/multi-csv-relationship.twb` | `<relation type='collection'>` + `<relationships>` in object-graph |
| Multiple CSVs, pre-joined | `data-model/multi-csv-join.twb` | `<relation type='join'>` with `<clause>` |

**Always generate as live connection** — do NOT include `<extract>` sections. If the snippet contains an extract block, ignore it.

Parameterize: datasource name (new hash), named-connection name (new hash), object-ID GUIDs, CSV filenames, all column definitions (4-way redundancy — see SCAFFOLD.md).

### Step 3: Build Worksheets

Read `snippets/worksheets/WORKSHEETS.md` and the relevant chart-type `.twb` snippets.

#### Snippet Lookup Table

When TABLEAU-IMPLEMENTATION.md specifies a chart type or feature, use this table to find the correct snippet:

| Implementation Spec Term | Snippet File(s) | Notes |
|--------------------------|------------------|-------|
| "bar chart" | `worksheets/bar-chart.twb` | Add `-sorted`/`-styled`/`-filtered` as needed |
| "stacked bar" / "stacked chart" | `worksheets/stacked-bar-chart.twb` | Color encoding on stacking dimension |
| "line chart" / "trend" | `worksheets/line-chart.twb` | Continuous date on Columns |
| "area chart" | `worksheets/area-chart.twb` | Explicit `mark class='Area'` |
| "combo chart" / "bar and line" | `worksheets/combo-chart.twb` | Per-pane mark class overrides (Bar + Line) |
| "dual axis" | `worksheets/dual-axis.twb` | Same mark type on both axes |
| "pie chart" / "donut" | `worksheets/pie-chart.twb` | All data through encodings, empty shelves |
| "scatter plot" | `worksheets/scatter-plot.twb` | Measures on both axes |
| "text table" / "crosstab" | `worksheets/text-table.twb` | Dimensions on both axes, measure as `<text>` |
| "KPI card" / "big number" | `worksheets/text-table.twb` | Single-measure, centered; see WORKSHEETS.md § KPI |
| "histogram" / "distribution" | `worksheets/histogram.twb` | Bin calculation (`class='bin'`), count aggregation |
| "map" / "geographic" | `worksheets/map-chart.twb` | Generated lat/lon fields, `<mapsources>` |
| "custom tooltip" | `worksheets/custom-tooltip.twb` | Three-part chain pattern |
| "calculated field" | `features/calculated-field.twb` | Datasource-level `<column>` + `<calculation>` |
| "LOD expression" | `features/lod-expression.twb` | `{FIXED/INCLUDE/EXCLUDE}` formula syntax |
| "table calculation" / "running total" / "percent of total" | `features/tablea-calculation.twb` | `<table-calc>` nested inside `<column-instance>` |
| "reference line" / "average line" / "benchmark" | `features/reference-line.twb` | `<reference-line>` in `<view>`, styling via `<style-rule element='refline'>` |
| "parameter" | `features/parameter-control.twb` | `<datasource name='Parameters'>` pseudo-datasource |
| "filter action" | `dashboard/action-filter.twb` | `tsc:tsl-filter` command pattern |
| "highlight action" | `dashboard/highlight-action.twb` | Highlight on select |
| "parameter action" | `dashboard/parameter-action.twb` | `<edit-parameter-action>` pattern |
| "single-sheet dashboard" | `dashboard/single-sheet-layout.twb` | Minimal zone hierarchy |
| "multi-sheet dashboard" | `dashboard/multi-sheet-layout.twb` | Nested container pattern |
| "single CSV" | `data-model/single-csv.twb` | Single `<relation type='table'>` |
| "multiple CSVs" (join) | `data-model/multi-csv-join.twb` | `<relation type='join'>` with `<clause>` |
| "multiple CSVs" (relationship) | `data-model/multi-csv-relationship.twb` | `<relation type='collection'>` + `<relationships>` |

> **If the implementation spec uses a term not in this table**, check snippet companion docs (`WORKSHEETS.md`, `DASHBOARD.md`, `FEATURES.md`) for the closest match. If no snippet covers the feature, follow the Feature Resolution Strategy below (Tier 3 → Tier 4).

For each sheet in TABLEAU-IMPLEMENTATION.md:

1. **Identify chart type** → select the matching snippet from the table above
2. **Read the snippet** to understand the mark class, shelf configuration, and required encodings
3. **Parameterize**: worksheet name, datasource reference, field names on shelves, column-instances in datasource-dependencies
4. **Apply styling** from `bar-chart-styled.twb` pattern:
   - Worksheet title: `<layout-options>` > `<title>` > `<formatted-text>` > `<run>`
   - Body font: `<style-rule element='worksheet'>` > `<format attr='font-family'>`
   - Axis titles: `<style-rule element='axis'>` > `<format attr='title'>`
5. **Add filters** if specified — use `bar-chart-filtered.twb` pattern
6. **Add sorting** if specified — use `bar-chart-sorted.twb` pattern
7. **Add custom tooltip** if specified — use `custom-tooltip.twb` pattern

### Step 4: Build Dashboard(s)

Read `snippets/dashboard/DASHBOARD.md` and the relevant layout/action `.twb` snippets.

For **each dashboard** in TABLEAU-IMPLEMENTATION.md (workbooks can contain multiple dashboards):

1. **Zone hierarchy**: Match the Container Tree from TABLEAU-IMPLEMENTATION.md
   - Use `multi-sheet-layout.twb` for nested container patterns
   - Apply `is-fixed` + `fixed-size` for fixed containers, proportional fill otherwise
   - `<zone-style>` must be the **LAST child** of every zone
   - Add `friendly-name` attribute to every layout zone (see DASHBOARD.md § Zone Friendly Names)
   - **Title pattern**: Prefer separate `<zone type-v2='text'>` elements above each worksheet zone for titles, with `show-title='false'` on the sheet zone (see DASHBOARD.md § Title Pattern)
   - **Legend zones**: When a chart uses color encoding, add a `type-v2='color'` legend zone below the chart (see DASHBOARD.md § Legend Zones). Prefer dashboard legend zones over window-edge legend cards for better positioning control.
   - **Dashboard-level datasource declarations**: When the dashboard includes quick filters, the `<dashboard>` element must contain its own `<datasources>` and `<datasource-dependencies>` blocks declaring the filtered fields (separate from workbook-level datasources)
2. **Actions**: Add `<action>` or `<edit-parameter-action>` elements inside `<actions>` at workbook level (between `</datasources>` and `<worksheets>`)
   - Filter: `action-filter.twb` pattern
   - Highlight: `highlight-action.twb` pattern
   - Parameter: `parameter-action.twb` pattern
   - Navigation: `navigation-button.twb` pattern (for cross-dashboard goto-sheet buttons)
3. **Parameter controls**: Add `paramctrl` zones if parameters are shown on the dashboard
4. **Multiple dashboards** share the same `<datasources>` and `<actions>` sections at workbook level

### Step 5: Add Features

Read `snippets/features/FEATURES.md` and the relevant `.twb` snippets.

- **Calculated fields**: Define at datasource level + reference in worksheet datasource-dependencies
- **Parameters**: Define in `<datasource name='Parameters'>` pseudo-datasource
- **LOD expressions**: Same pattern as calculated fields, formula uses `{FIXED/INCLUDE/EXCLUDE}` syntax
- **Context filters**: Add `context='true'` to filters that must execute before FIXED LODs
- **Dynamic Zone Visibility**: Use `parameter-control.twb` — boolean calc referencing a parameter + `hidden-by-user='true'` on zones + `<dashboard-zone-visibility-node>` elements in windows

### Step 6: Assemble Windows

For each worksheet and dashboard, create a `<window>` element:

- Worksheet windows: `class='worksheet'`, with standard card layout (left: pages/filters/marks, top: columns/rows/title). Add `hidden='true'` for worksheets that only appear on dashboards (not standalone).
- Dashboard windows: `class='dashboard'`, with viewpoints for each sheet. Set `maximized='true'` on the primary (first) dashboard.
- **All viewpoints must include `<zoom type='entire-view' />`** — never use the default `'standard'` option. `entire-view` ensures sheets fill their allocated space correctly across all sheet types.
- Every `<window>` must include `<simple-id uuid='{GUID}' />` — these UUIDs are referenced by navigation buttons for cross-dashboard links.
- Add right-edge legend cards for any chart using `<color>` or `<size>` encodings (only when not using dashboard-level legend zones)

### Step 7: Generate IDs

All IDs must be **unique** within the workbook:

- **Datasource names**: `federated.` + new 32-char lowercase alphanumeric hash
- **Named connections**: `textscan.` + new 32-char lowercase alphanumeric hash
- **Object IDs**: `{filename}_{32-hex-GUID}` (uppercase hex, no dashes)
- **Simple IDs**: `{GUID}` in standard UUID format with braces — mandatory on every `<window>` element, referenced by navigation buttons
- **Zone IDs**: Sequential integers starting from 1
- **Action names**: `[Action1_{32-hex-GUID}]`
- **Calculation names**: `[Calculation_{18-digit-numeric-id}]`

**Never reuse IDs from the snippet files.**

---

## Sample Data as Datasource

- If `sample-data/` contains the CSVs → use those files
- If Step A generated CSVs during query execution → use those
- CSV column headers must match field names in DS-ARCHITECTURE.md exactly
- **Inside the `.twb` XML, always use `directory='.'`** — never use subdirectory paths

## Packaging as .twbx

After generating the `.twb`, **always** package it as a `.twbx`. A `.twbx` is a standard ZIP archive:

```
dashboard.twbx (ZIP)
├── dashboard.twb          ← the workbook XML
├── sales_orders.csv       ← sample data files (flat, at root)
├── customer_segments.csv
├── monthly_targets.csv
└── Image/                 ← optional, only if dashboard includes logos/icons
    └── company_logo.svg
```

### Packaging Script (Python)

```python
import zipfile
import os

def create_twbx(twb_path: str, csv_paths: list[str], twbx_path: str,
                image_paths: list[str] | None = None) -> None:
    """
    Package a .twb and its datasources into a .twbx archive.

    Args:
        twb_path: Path to the generated .twb file
        csv_paths: List of paths to CSV data files
        twbx_path: Output path for the .twbx file
        image_paths: Optional list of image files (logos, icons) to include
    """
    with zipfile.ZipFile(twbx_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(twb_path, os.path.basename(twb_path))
        for csv_path in csv_paths:
            zf.write(csv_path, os.path.basename(csv_path))
        for img_path in (image_paths or []):
            zf.write(img_path, f'Image/{os.path.basename(img_path)}')
```

---

## CRITICAL RULES — Common Pitfalls to Avoid

These rules are derived from real Tableau Desktop validation failures.

### Version & Manifest
1. **Use `source-build='2025.1.10 (20251.25.1121.1650)'`** — use the version from the scaffold snippet
2. **Manifest flags**: Copy from `workbook-skeleton.twb` as the baseline. Add `<SortTagCleanup />` if using sorting, `<ObjectModelExtractV2 />` only if extract is needed (it shouldn't be)
3. **Never use FCP-prefixed names** like `<_.fcp.AnimationOnByDefault.true...>` — causes "Unrecognized Format Changes" errors

### Datasource Structure
4. **`<relation>` must be plain** — never wrap with FCP wrappers
5. **`<layout>` percentages — omit them.** Do NOT include `dim-percentage` / `measure-percentage` attributes on `<layout>`. Tableau 2025.x loads fine without them; the 2026.1 XSD renamed them to `dim-percentage-v2` / `measure-percentage-v2` and rejects the un-suffixed names. Emit only `dim-ordering`, `measure-ordering`, `show-structure`. *(This rule changed — older guidance said these were required. They are not.)*
6. **`directory='.'` always** — never use subdirectory paths in connections
7. **Generate as live connection only** — no `<extract>` sections
8. **4-way column redundancy** — every column must be defined in: `relation > columns`, `metadata-records`, `object-graph > properties > relation > columns`, AND `datasource > column` direct children (see SCAFFOLD.md)

### Column & Formatting
9. **Calculated field formatting uses `default-format` attribute** — never nest `<format>` inside `<column>`
10. **Valid `<run>` attributes**: `bold`, `fontcolor`, `fontname`, `fontsize`, `italic`, `underline` only. Never use `fontstyle`
11. **Tooltip line breaks**: Use `&#198;&#9;` (AE ligature + tab). Never `\n` or `<br/>`

### Worksheet Structure
12. **Color encoding goes in `<pane><encodings>`** — never as direct child of `<table>`
13. **Sorting uses `<computed-sort>`** inside `<view>` — for computed sorts by measure
14. **Measure Names reference**: `[:Measure Names]` with brackets and colon prefix
15. **Element order inside `<view>`**: `<datasources>` → `<datasource-dependencies>` → `<reference-line>` (if any) → `<filter>` → `<computed-sort>` → `<slices>` → `<aggregation>`

### Dashboard Structure
16. **`<zone-style>` must be the LAST child** of any zone
17. **`<actions>` go at `<workbook>` level** — between `</datasources>` and `<worksheets>`, NOT inside `<dashboard>` (verified in all action snippets)
18. **Flow direction**: Controlled by `param='vert'` or `param='horz'` on the zone, not via format attributes

### XML Formatting Conventions
19. **CDATA for field references in `<run>` elements**: Field reference expressions (e.g., KPI values, tooltips) must use CDATA wrapping: `<![CDATA[<[datasource].[field:qk]>]]>`. Never use XML entity encoding (`&lt;...&gt;`) — Tableau will display them as literal text instead of resolving the value.
20. **Lowercase hex colors**: Always write `#2e86c1`, never `#2E86C1`. Tableau Desktop normalizes to lowercase.
21. **Alphabetical attribute ordering**: Attributes on XML elements should be written in alphabetical order (e.g., `bold`, `fontcolor`, `fontname`, `fontsize` on `<run>` elements). Tableau Desktop sorts attributes alphabetically when saving.
22. **No XML comments**: Never emit `<!-- ... -->` comments in the generated `.twb`. Tableau Desktop strips all comments on save.
23. **Default dimension filter mode**: For dimension filters on dashboards, use `mode='checkdropdown'` as the default (standard Tableau UX). Only use `typeinlist` when the dimension has many values (100+). Measure filters use different modes (range sliders, etc.).
24. **Style rules alphabetical order**: Style rules inside `<style>` blocks must be ordered alphabetically by `element` attribute (e.g., `cell` < `mark` < `worksheet`). Tableau Desktop enforces this order.

---

## Validation

**Always run BOTH validators on every generated `.twb` before packaging the `.twbx`.** They are complementary, not redundant — the XSD covers structural correctness (element nesting, attribute names, value enums, child ordering), and `validate_twb.py` covers cross-section semantic integrity (datasource refs, column-instance refs, filter↔slices, worksheet↔window) that the XSD explicitly skips via `processContents="skip"`.

### Commands

From the project root (replace `v_N` with the actual version dir):

```bash
# Semantic validation
python <skill-root>/scripts/validate_twb.py mock-version/v_N/dashboard.twb

# Structural validation against official Tableau XSD
python <skill-root>/scripts/validate_twb_xsd.py mock-version/v_N/dashboard.twb
```

`<skill-root>` is `skill/tableau-dashboard-creator/` inside the installed skill. The XSD validator requires `lxml` (in `requirements.txt`).

### Interpreting XSD output

The XSD is the official 2026.1 schema (`references/xsd/twb_2026.1.0.xsd`). When the target is **2024.2 – 2025.x**, expect a small set of version-shifted false positives. Bucket every error you see:

| Bucket | Examples | What to do |
|---|---|---|
| **1. Real structural bug** *(most errors fall here)* | Misspelled element, wrong nesting order, missing required attribute, invalid enum value (e.g., `param='vertical'` instead of `'vert'`/`'horz'`), `<zone-style>` not last child of zone, attribute on wrong element | **Fix the workbook.** These would break 2025.x too. |
| **2. Known 2026.1-only requirement** *(safe to ignore for 2025.x target)* | `Element 'workbook': Missing child element(s). Expected is one of ( external, referenced-extensions, explain-data )` <br><br> `Element 'layout', attribute 'dim-percentage': The attribute 'dim-percentage' is not allowed.` <br><br> `Element 'layout', attribute 'measure-percentage': The attribute 'measure-percentage' is not allowed.` | **Ignore — these are the documented 2026.1 deltas.** A clean 2025.x-targeted workbook will produce exactly **one** such error: the missing `explain-data`/`referenced-extensions`/`external` child. The `dim-percentage` errors should not appear in your output because rule #5 (Datasource Structure) tells you not to emit them. |
| **3. Unknown 2026.1-only difference** | Anything not in bucket 2 that you suspect is version-related | Investigate: confirm the element/attribute exists in the 2026.1 XSD definition. If the schema has it as required-only-in-26.1 and your target is 2025.x, treat as bucket 2 (ignore, but **add it to bucket 2 in this doc** so future runs don't re-investigate). Otherwise treat as bucket 1. |

> **Pass criterion**: `validate_twb.py` must report **all checks passed**. `validate_twb_xsd.py` may report at most the **single known 2025.x bucket-2 error** above; any additional XSD errors must be resolved or escalated to bucket 3 before approval.

---

## Validation Checklist

Before saving the `.twb`, verify:

- [ ] `validate_twb.py` reports all checks passed
- [ ] `validate_twb_xsd.py` reports only the known bucket-2 error (or PASS for a 2026.1+ target)
- [ ] XML is well-formed (all tags properly closed)
- [ ] `source-build` is `2025.1.10 (20251.25.1121.1650)`
- [ ] Manifest tags copied from scaffold (simple names, no FCP prefixes)
- [ ] All datasource connections use `directory='.'`
- [ ] All columns defined in all 4 redundancy locations
- [ ] `<layout>` elements do NOT contain `dim-percentage` / `measure-percentage` (see Datasource Structure rule #5)
- [ ] Workbook `version` attribute and `<explain-data>` emission match the *Tableau Version Targeting* table
- [ ] All `<relation>` elements are plain (no FCP wrappers)
- [ ] No `<extract>` sections present
- [ ] All field names match DS-ARCHITECTURE.md
- [ ] All calculated field formatting uses `default-format` attribute
- [ ] All `<run>` elements use only valid attributes
- [ ] Color encodings are inside `<pane><encodings>`
- [ ] All `<zone-style>` elements are the last child of their parent zone
- [ ] Dashboard actions are at `<workbook>` level
- [ ] All IDs are unique (no reuse from snippets)
- [ ] Tooltip field references exist in both `<encodings>` and `<datasource-dependencies>`
- [ ] `<slices>` lists every filtered column
- [ ] Dashboard zone hierarchy matches TABLEAU-IMPLEMENTATION.md container tree
- [ ] All zones have `friendly-name` attributes
- [ ] Design tokens (colors, fonts, spacing) applied throughout
- [ ] All hex colors are lowercase
- [ ] No XML comments in generated output
- [ ] All `<run>` field references use CDATA wrapping (not entity encoding)
- [ ] All viewpoints include `<zoom type='entire-view' />`
- [ ] All `<window>` elements include `<simple-id uuid='...' />`
- [ ] Utility worksheets have `hidden='true'` on their windows
- [ ] Style rules ordered alphabetically by `element` attribute
- [ ] Dimension filters use `mode='checkdropdown'` by default
- [ ] Dashboard-level `<datasources>` and `<datasource-dependencies>` present when filters are used
- [ ] The `.twbx` archive contains the `.twb`, all referenced CSV files, and any images under `Image/`

---

## Feature Resolution Strategy

When implementing a feature, resolve it using this priority order:

1. **Tier 1 — Snippet library** (primary source): Check `snippets/` for a matching `.twb` file + companion `.md`. This covers the vast majority of generation work — core chart types, layout patterns, data models, actions, and features. Snippets and their companion docs are the **single source of truth** for XML structure.

2. **Tier 2 — Pattern blocks** (companion docs): Check companion `.md` files for documented XML pattern blocks. These cover reusable fragments that don't need a full `.twb` file — legend zones, KPI formatting, button elements, number formatting, etc. Still part of `snippets/`.

3. **Tier 3 — Example extraction** (last resort before asking): If no snippet or pattern block covers the requested feature, search `examples/*.twb` for a real-world implementation. These are large, complex production workbooks — **do not read them in full**. Grep for the relevant XML section only, adapt it, and flag the output as `⚠️ ADAPTED FROM EXAMPLE`. This tier should be rare.

4. **Tier 4 — Ask the user**: If none of the above apply, stop and offer:
   - **Provide a reference `.twb`** — build a minimal example in Tableau Desktop, provide the path, and the agent extracts the pattern
   - **Skip and document** — generate everything else correctly and write `MANUAL_STEPS.md` listing what the user needs to add manually

## Snippets as Baseline, Not Templates

The `snippets/` directory is the **primary baseline** for all XML generation. Snippets and their companion `.md` docs encode the XML mechanics — element structure, nesting rules, required attributes, style patterns, action wiring.

**What to learn from snippets**: XML structure, element nesting, attribute names, required child elements, zone-style patterns — the *mechanics* of how Tableau represents a feature.

**What NOT to copy from snippets**: Specific field names, datasource references, color schemes, layout dimensions, number of worksheets, zone IDs — anything tied to the snippet's example content.

**When user requirements differ from snippet patterns**: Adapt the learned XML mechanics to the user's needs:
- Snippet shows 2 KPI cards → user wants 6 → replicate the KPI card XML pattern with different fields
- Snippet uses a horizontal legend → user wants vertical → change `leg-item-layout` attribute
- Snippet has 1 dashboard → user wants 3 → add `<dashboard>` elements following the same structural rules
- Snippet uses example colors → user has different design tokens → substitute from `design-tokens.md`

**Principle**: Understand the *pattern* from snippets, then apply it to the user's context. Snippets teach "how Tableau represents X in XML"; the dashboard plan (TABLEAU-IMPLEMENTATION.md) defines "what X should be."

The `examples/` directory contains complex production workbooks (`.twb` XML files). These are **not** the primary reference — `snippets/` is. Only grep into `examples/*.twb` as a Tier 3 fallback when no snippet or pattern block covers the requested feature. Never read example files in full.

---

## Output

Save both files to `mock-version/v_N/`:
- `dashboard.twb` — the raw XML workbook (for reference/debugging)
- `dashboard.twbx` — the packaged workbook with embedded CSV data (**primary deliverable**)

Present to the user with these instructions:
1. Open **`dashboard.twbx`** in Tableau Desktop (packaged file with data included)
2. The workbook uses sample CSV data from Step A — no path configuration needed
3. Go to **Data → Replace Data Source** to connect to your live database
4. Review and adjust any formatting or layout details as needed
5. The raw `dashboard.twb` is also available for manual inspection or debugging

---

## Limitations

- Complex features without validated snippets may require manual adjustment (see "Handling Unknown Features")
- Custom shapes, map layers, and image-based marks are not generated
- Datasource connection credentials are NOT embedded — user must configure after replacing datasources
- Dynamic Zone Visibility (DZV) is supported — use `snippets/features/parameter-control.twb` as the reference pattern

> **This is an iterative process.** The generated `.twbx` is unlikely to be perfect on the first attempt. Tableau's XML is complex and strict — minor issues are expected. The user should open in Tableau Desktop, identify issues, and report back. Each iteration improves fidelity.
