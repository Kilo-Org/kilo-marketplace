# Step D: Tableau Implementation Spec

Create `TABLEAU-IMPLEMENTATION.md` that serves as a technical blueprint for building the dashboard in Tableau Desktop. A Tableau developer should be able to implement the dashboard solely from this document.

## Process

1. **Review the approved mock** (`mock-version/v_N/mock.html`)
2. **Review DASHBOARD-PLAN.md** for data mappings
3. **Review DS-ARCHITECTURE.md** for field references
4. **Review design-tokens.md** for styling values and template layout
5. **Create TABLEAU-IMPLEMENTATION.md** with all sections below
6. **Save to** `mock-version/v_N/TABLEAU-IMPLEMENTATION.md`
7. **Sync root-level docs** — When the user approves the implementation spec, review whether it diverged from `DASHBOARD-PLAN.md` (e.g., added/removed sheets, changed calculated fields, new filters or actions). If it did, update `DASHBOARD-PLAN.md` to match before proceeding to Step E.

## Entry Requirements

Before Step D begins, verify:
- the mock is approved
- `DASHBOARD-PLAN.md`, `DS-ARCHITECTURE.md`, and `design-tokens.md` are the latest approved global truth
- KPI IDs, viz IDs, filter IDs, and action IDs from Step B are stable and reusable

If Step D must change the approved plan to stay Tableau-feasible, document that clearly and sync the root docs after approval.

## TABLEAU-IMPLEMENTATION.md Template

```markdown
# Tableau Implementation: [Dashboard Name]

**Template**: [Which template layout to use from design-tokens.md]
**Datasources**: [List of datasources from DS-ARCHITECTURE.md]
**Mock version**: v_N
**Derived from**: approved `design-tokens.md`, approved `DS-ARCHITECTURE.md`, approved `DASHBOARD-PLAN.md`, `mock-version/v_N/mock.html`

---

## Section 1: Container Hierarchy

[Full container tree with all properties. Use indentation to show nesting.]

### Container Tree

```
Root Container (layout-basic)
├── Content (Vertical, fixed-height: [px])
│   ├── Top Banner (Tiled, fixed-height: [px])
│   │   ├── Logo (Image, [w]x[h], padding: [values])
│   │   ├── Spacer (Blank, flex)
│   │   ├── Update Time (Sheet, [w]x[h], inner-padding: 8)
│   │   └── Info Icon (Sheet, [w]x[h], inner-padding: 8)
│   ├── Dashboard Title (Text, fixed-height: [px])
│   │   └── "[Title Text]" ([font], [size], bold, [color], bg: [color])
│   ├── Filter Bar (Horizontal, fixed-height: [px], margin-top: 11, margin-bottom: 11)
│   │   ├── "Filters" Label (Text, fixed-width: [px])
│   │   ├── [Filter 1] (Filter, type: [dropdown/slider/date])
│   │   ├── [Filter 2] (Filter, type: [type])
│   │   ├── Spacer (Blank, flex)
│   │   └── Expand Button (Button, fixed-width: [px])
│   └── Main Area (Horizontal, flex)
│       ├── Charts Area (Vertical, ~86% width)
│       │   ├── KPI Row (Horizontal, distribute-evenly, fixed-height: [px])
│       │   │   ├── KPI 1 Container (Vertical, bg: [card bg color])
│       │   │   │   ├── Accent Bar (Blank, 3px, bg: [accent color])
│       │   │   │   ├── [KPI <Descriptive Name>] (Sheet, inner-padding: 8)
│       │   │   │   └── Spacer (Blank, flex)
│       │   │   └── [... more KPIs]
│       │   ├── Chart Row 1 (Horizontal, distribute-evenly, margin-top: 11)
│       │   │   └── Chart 1 Container (Vertical, padding: 8, bg: [card bg color])
│       │   │       ├── Title Bar (Horizontal, fixed-height: 46)
│       │   │       │   ├── Icon (Image, 40x40, from branding/icons/ or generated)
│       │   │       │   ├── "[Chart Title]" (Text, [size], [color])
│       │   │       │   ├── Spacer (Blank, flex)
│       │   │       │   └── Info Icon (Sheet)
│       │   │       ├── Separator (Blank, 3px, bg: [separator color], margin: 0 10px)
│       │   │       ├── [Chart Sheet Name] (Sheet, flex, inner-padding: 8)
│       │   │       └── Spacer (Blank, flex)
│       │   └── [... more chart rows]
│       └── Hidden Filters Panel (Vertical, ~14% width, collapsible)
│           ├── [Hidden filter sheets]
│           └── Spacer (Blank, flex)
```

### Container Rules

- **Spacer (Blank, flex)**: Every `layout-flow` container must include at least one blank zone (`type='empty'`) with flexible size. This prevents Tableau from collapsing containers when sheets are hidden or empty.
- **Inner padding on sheets**: All worksheet (Sheet) zones default to `inner-padding: 8` (Tableau `padding` attribute) unless explicitly overridden. This is the space between the zone border and the sheet content — not outer margin.
- **Fixed-size rule**: Apply `fixed-size` and `is-fixed='true'` to elements that should not shrink on smaller viewports — specifically: title bars, KPI rows, filter bars, accent bars, separator lines, icon images, and logo areas. Only chart sheet areas and main content areas should use `flex` sizing.

### Container Details

| Container Name | Type | Direction | Size | Background | Padding | Margin |
|---------------|------|-----------|------|------------|---------|--------|
| [Name] | [Horizontal/Vertical/Tiled] | [H/V] | [fixed px or flex] | [color] | [values] | [values] |

---

## Section 2: Sheets

### Sheet: [Descriptive Sheet Name]

> Use an informative name — e.g., `KPI No Recent Searches` not `KPI1_Sheet`.
> Calculated fields scoped to this sheet use the pattern `<Sheet Name> — <Measure>`.

**Sheet ID**: [Use the stable ID from Step B, e.g., `viz_01_sales_trend` or `kpi_01_total_sales`]
**Container**: [Parent container name from hierarchy]
**Size**: [Width x Height or flex]
**Title**: [Visible title text, or "hidden"]

#### Marks
- **Mark type**: [Bar / Line / Circle / Square / Text / etc.]
- **Columns shelf**: [field(s)]
- **Rows shelf**: [field(s)]
- **Color**: [field or fixed color]
- **Size**: [field or fixed]
- **Label**: [field(s) and format]
- **Detail**: [field(s)]
- **Tooltip**: [custom tooltip text with field references]

#### Calculated Fields

| Field Name | Formula | Purpose |
|-----------|---------|---------|
| [<Sheet Name> — <Measure>] | `[Tableau calc syntax]` | [What it computes] |

#### Filters
| Filter | Type | Values | Scope |
|--------|------|--------|-------|
| [Field] | [Dimension/Measure/Date] | [All/specific/relative] | [This sheet / All using datasource] |

#### Formatting
- **Font**: [size, weight, color]
- **Number format**: [e.g., #,##0 / $#,##0.00 / 0.0%]
- **Axis**: [show/hide, title, range]
- **Grid lines**: [show/hide]
- **Reference lines**: [if any]

---

[Repeat "Sheet: [Name]" section for every sheet in the dashboard]

---

## Section 3: Parameters

| Parameter Name | Data Type | Default | Allowable Values | Used In |
|---------------|-----------|---------|-----------------|---------|
| [Name] | [String/Integer/Float/Date/Boolean] | [default] | [All/List/Range] | [Which calc fields or filters use it] |

[If no parameters are needed, state: "No parameters required for this dashboard."]

---

## Dashboard Actions

| Action ID | Action Name | Type | Source Sheet ID | Target Sheet ID(s) | Run On | Fields |
|-----------|-------------|------|-----------------|--------------------|--------|--------|
| [from Step B] | [Name] | [Filter/Highlight/URL/Go to Sheet] | [sheet id] | [sheet id(s)] | [Select/Hover/Menu] | [field mappings] |

---

## Cross-Dashboard Navigation (if multi-dashboard)

| Button Label | Source Dashboard | Target Dashboard | Button Location |
|-------------|-----------------|-----------------|-----------------|
| [Label] | [source] | [target] | [container name in hierarchy] |

### Shared Worksheets
[List any worksheets that appear on multiple dashboards]

---

## Notes
[Any additional implementation notes, edge cases, or considerations]

---

## Approval Checklist
- [ ] Every sheet maps back to a stable ID from `DASHBOARD-PLAN.md`
- [ ] All calculated fields and filters are explicit enough to implement without guessing
- [ ] Container sizes and hierarchy are specific enough to reproduce the approved mock
- [ ] Any Tableau-driven deviations from the mock are called out explicitly
- [ ] Root-level docs can remain the latest approved global truth after sync
```

## Structured Output Contract

This document is not free-form prose. It is a constrained markdown spec that later steps can consume reliably.

Minimum required structure:
- one top-level dashboard header
- one container hierarchy section
- one sheet section per KPI/chart/info sheet, each with a stable `Sheet ID`
- one parameters section, even if it only states that none are required
- one dashboard actions section, even if it only states that none are required
- one approval checklist

> **Multi-dashboard workbooks**: When the dashboard plan includes multiple dashboards (e.g., overview + detail), repeat the dashboard-specific parts of the spec for each dashboard: Container Hierarchy, Sheets, Parameters, Dashboard Actions, and Cross-Dashboard Navigation as needed. Each dashboard gets its own Container Tree and Sheets section.

## Guidelines

- Be explicit about every calculated field formula - a developer should not need to guess
- Use Tableau formula syntax for calculated fields (not SQL)
- Reference field names exactly as they appear in DS-ARCHITECTURE.md
- Use colors and fonts from design-tokens.md for all styling values
- Include number formats for all measures
- Specify tooltip content including field references in square brackets
- Document all dashboard actions including field mappings
- This document will be used as input for Step E (TWB generation) — keep the section order and required labels stable so later steps do not have to infer structure
- Every `layout-flow` container in the tree must include a Spacer (Blank, flex) to prevent layout collapse
- All Sheet zones must specify `inner-padding: 8` unless overridden by design tokens
- Preserve the stable IDs introduced in Step B and map them to final worksheet names here
- If a mock interaction or layout choice cannot be reproduced faithfully in Tableau, document the deviation explicitly instead of hiding it

### Naming Convention — Sheets & Calculated Fields

- **Use informative, human-readable names** for all sheets and calculated fields — never use opaque numeric suffixes like `KPI1_Sheet`, `KPI2 Count`, or `Chart3_Sheet`.
- **Sheet names** must describe what the sheet displays. If a sheet belongs to a KPI, prefix it with `KPI` followed by the metric's plain-English name (e.g., `KPI No Recent Searches`, `KPI Declining Active Users`, `KPI Churn Indicator`).
- **Calculated field names** must describe what they compute. When a field belongs to a specific sheet, use the pattern `<Sheet Name> — <Measure>` (e.g., `KPI No Recent Searches — Count`, `KPI No Recent Searches — Pct`).
- **Info / tooltip sheets** follow the same pattern with a `— Info` suffix (e.g., `KPI Declining Searches — Info`).
- This convention ensures that Tableau's sheet tabs, field lists, and dependency dialogs are self-documenting — a developer or stakeholder can identify any element without cross-referencing the spec.