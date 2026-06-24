# Fallback Design Tokens (Tableau Defaults)

These are default Tableau design tokens used as a **fallback** when the user provides neither a `template.twb` nor a `branding/` directory. Step 0 generates a project-specific `design-tokens.md` that overrides these values and should explicitly disclose every fallback-driven decision.

For a structural TWB reference, see `examples/top-level-workbook-example.twb`.

## Typography

- **Font family**: Open Sans (all elements)
- **Dashboard title**: 36px, bold, `#000021`
- **Chart title**: 15px, regular, `#000021`
- **Filter/section labels**: 12px, bold, `#5f5f71`
- **Worksheet default font size**: 12px
- **Tooltip font size**: 12px

## Colors

### Backgrounds
- **Dashboard background**: `#f6f7f9`
- **Top banner / title area**: `#f5f7f9`
- **Chart card background**: `#ffffff`
- **Separator line**: `#f0f3f5`

### KPI Accent Colors (top border bar)
- Accent 1: `#4e79a7` (Tableau blue)
- Accent 2: `#f28e2b` (Tableau orange)
- Accent 3: `#e15759` (Tableau red)
- Accent 4: `#76b7b2` (Tableau teal)

### Chart Series Colors (Tableau 10 palette)
`#4e79a7`, `#f28e2b`, `#e15759`, `#76b7b2`, `#59a14f`, `#edc948`, `#b07aa1`, `#ff9da7`, `#9c755f`, `#bab0ac`

### Text
- Dark (titles): `#000021`
- Medium (labels): `#5f5f71`

### Borders
- Default border-style: `none` (border-width: 0)

## Dashboard Sizing

- **Sizing mode**: Range
- **Minimum height**: 800
- **Minimum width**: 1100
- **Maximum**: Flex (no max set)

## Standard Container Hierarchy

```
layout-basic (root, 100% x 100%)
└── Content (vertical flow, centered)
    ├── Top Banner (layout-basic, fixed-size 65)
    │   ├── Logo area (fixed-size 195, padding: 7, padding-left: 12)
    │   ├── Spacer (Blank, flex)
    │   └── Right section
    │       ├── Update Time (fixed-size 305, inner-padding: 8)
    │       └── Info icon (fixed-size 34, margin: 4)
    ├── Dashboard Title (horizontal flow, fixed-size 70)
    │   └── Text (margin: 4, margin-bottom: 1, bg: title area color)
    ├── Top Filters (horizontal flow, fixed-size 53)
    │   ├── Label (fixed-size 185, margin: 4)
    │   ├── Filter placeholder (margin: 4)
    │   ├── Spacer (Blank, flex)
    │   └── Expand/collapse button (fixed-size ~38, margin: 4)
    │   └── [margin-top: 11, margin-bottom: 11]
    └── Charts & Hidden Filters (horizontal flow, flex)
        ├── KPI & Charts (vertical flow, ~86% width)
        │   ├── Main KPI row (horizontal, distribute-evenly, fixed-size 94)
        │   ├── Chart rows (per layout)
        │   └── Spacer (Blank, flex)
        └── Hidden Filters panel (vertical flow, ~14% width, collapsible)
            └── Spacer (Blank, flex)
```

## KPI Card Pattern

```
KPI container (horizontal flow, margin-right: 16)
└── Inner wrapper (vertical flow, bg: card background)
    ├── Accent bar (3px height, margin: 0, bg: accent color)
    ├── KPI content area (sheet, inner-padding: 8)
    └── Spacer (Blank, flex)
```

## Chart Card Pattern

```
Chart wrapper (horizontal flow, margin-top: 11)
└── Chart outer (horizontal flow)
    └── Chart inner (vertical flow, padding: 8, bg: card background)
        ├── Title bar (horizontal flow, fixed-size 46)
        │   ├── Icon image (40x40, fixed-size 47, from branding/icons/)
        │   ├── Chart title text (margin: 4, margin-left: 10)
        │   ├── Spacer (Blank, flex)
        │   └── Info icon (fixed-size 38, margin: 4)
        ├── Separator line (3px, margin-lr: 10, bg: separator color)
        ├── Chart sheet area (flex, inner-padding: 8)
        └── Spacer (Blank, flex)
```

## Available Template Layouts

### Without Main KPI
- **Frame (1*1)**: 1 chart, full width
- **Frame (1*2)**: 2 rows, 1 chart each
- **Frame (1+2)**: 1 full-width row + 1 row with 2 charts
- **Frame (2*2)**: 2 rows, 2 charts each
- **Frame (2*2*1)**: 2 rows of 2 charts + 1 full-width row
- **Frame (2+3)**: 1 row of 2 charts + 1 row of 3 charts
- **Frame (3*2)**: 2 rows, 3 charts each

### With Main KPI Row
Same chart layouts prefixed with a KPI row containing 4 evenly distributed KPI cards:
- **Frame With Main KPI (1*1)** through **Frame With Main KPI (3*2)**

## Spacing Reference

| Element | Property | Value |
|---------|----------|-------|
| Content container | outer margin | ~1.25% from edges |
| Logo | padding | 7 (padding-left: 12) |
| Dashboard title | margin | 4 (margin-bottom: 1) |
| Filter bar | margin-top/bottom | 11 |
| Filter label | margin | 4 |
| KPI cards | margin-right | 16 (between cards) |
| KPI accent bar | margin | 0, height 3 |
| Chart card outer | margin-top | 11 |
| Chart card inner | padding | 8 |
| Chart title text | margin | 4 (margin-left: 10) |
| Separator line | margin-right/left | 10 |
| Sheet zone | inner padding | 8 |

## Constraints

- **No rounded corners** unless the user explicitly accepts a non-Tableau-faithful mock
- **border-style: none** on all containers
- Charts have white background, dashboard has light gray background
- Use distribute-evenly layout strategy for KPI rows and multi-chart rows
- Hidden filters panel uses collapsible toggle button (DZV pattern)
- Use `fixed-size` on structural elements (title bars, KPI rows, filter bars, accent/separator bars, icons, logo) — only chart areas and main content should flex
- Every `layout-flow` container must include at least one Spacer (Blank, flex) to prevent layout collapse
- If these fallback tokens are used in Step 0, the generated `design-tokens.md` should list them under `## Fallback Decisions`