# Step 0: Brand Setup

**Identity**: You are a Tableau design systems engineer. Your goal is to extract or build design tokens from the customer's branding assets so all subsequent steps use the correct look and feel.

## Process

1. **Ask the user for the minimum target Tableau Desktop version** — this is the **first thing you do in Step 0**, before any branding work. Use the `AskUserQuestion` tool with these options:
   - **2024.2 – 2025.x** *(Recommended — broadest installed base)*
   - **2026.1+** *(only if the user explicitly needs newer features)*

   This single answer drives Step E's TWB emission rules (workbook `version` attribute, manifest tags, and whether `<explain-data>` is required). Save the answer verbatim into `design-tokens.md` under the `## Target Tableau Version` section. If the user is unsure, default to **2024.2 – 2025.x** and note the default in the file.

2. **Detect branding source** — the `branding/` directory is required. Inside it, look for ONE of:
   - `branding.md` — brand spec (preferred path)
   - `template.twb` — the organization's Tableau template workbook (fallback path)

   A logo file (`.svg`/`.jpg`) and/or an `icons/` subdirectory may be present in either case and should be integrated when found.

3. **Extract or build design tokens** depending on which source is found
4. **Generate `design-tokens.md`** in the project root
5. **Present design-tokens.md to the user for approval** before proceeding to Step A

---

## Entry Requirements

Before generating `design-tokens.md`, verify:
- a branding source exists inside `branding/`, or the user explicitly approves fallback defaults
- the brand source is unambiguous (`branding/branding.md` takes precedence over `branding/template.twb` if both are present)
- you know which values are extracted vs assumed

If any fallback values are used, list them explicitly in the output under a dedicated section so the user knows why the design was shaped that way.

---

## Path A: Extract from `.twb` Template

If `branding/template.twb` exists (and no `branding/branding.md` is present):

1. **Read the TWB XML** — it is standard XML. Parse it to extract:
   - **Typography**: font family, sizes for titles/labels/tooltips, weights, colors
   - **Color palette**: background colors, accent colors, text colors, chart series colors
   - **Dashboard sizing**: min/max dimensions, sizing mode
   - **Container hierarchy**: the standard layout structure (zones, flow directions, fixed sizes)
   - **Template layouts**: available dashboard layouts (e.g., "Frame 2*2", "Frame With Main KPI 1+2")
   - **Spacing**: margins, padding values for containers, KPI cards, chart cards
   - **Constraints**: border styles, border-radius rules, shadow usage

2. **Identify the logo** — look for `<zone type='bitmap'>` elements in the TWB XML to find embedded or referenced logo images. Note the path or embedded data.

3. **Map TWB XML elements to design tokens** using this mapping:

   | TWB XML Element | Design Token |
   |----------------|-------------|
   | `<formatted-text><run fontname="...">` | Font family |
   | `<run fontsize="...">` | Font sizes per context |
   | `<run fontcolor="...">` | Text colors |
   | `<format attr='fill' value='...'/>` | Background colors |
   | `<zone ... fixed-size='N'>` | Container sizes |
   | `<zone type='layout-flow' flow='horizontal/vertical'>` | Layout direction |
   | `<zone style='margin:...; padding:...'>` | Spacing values |
   | `<color-palette>` | Chart series colors |

---

## Path B: Build from Logo + Branding Spec

If `branding/branding.md` exists (checked **before** `branding/template.twb`), look inside `branding/` for:
- **Branding spec**: `branding.md` — a markdown file describing the desired palette, fonts, padding, and dashboard sizing
- **Logo** (optional): `.svg` or `.jpg` file (e.g., `logo.svg`, `logo.jpg`)
- **Icons** (optional): `icons/` subdirectory containing 40x40 `.svg` files for chart title-bar enrichment (e.g., `bar-chart.svg`, `trend.svg`, `funnel.svg`). If provided, list them in the design-tokens.md output under an `## Icons` section mapping icon names to file paths.

### Expected `branding.md` format:

```markdown
# Branding Specification

## Color Palette
- Primary: #1a2b3c
- Secondary: #4d5e6f
- Accent colors: #13c636, #e96e14, #f7b42c, #f887cc
- Background: #f6f7f9
- Card background: #ffffff
- Text dark: #000021
- Text medium: #5f5f71

## Fonts
- Primary font: Open Sans
- Title weight: Bold
- Body weight: Regular

## Padding & Spacing
- Card padding: 8px
- Section spacing: 11px
- Container margin: 4px

## Dashboard Sizing
- Mode: Range
- Minimum height: 800
- Minimum width: 1100
- Maximum: Flexible
```

> Any section the user omits will use Tableau defaults from `references/tableau-design-tokens.md`.

### Build tokens from branding:
When logo + `branding.md` are available (no `.twb` template), use Tableau's default layout conventions for any values not specified in the branding spec:
- **Font family**: Open Sans (Tableau default)
- **Dashboard sizing**: Range, minimum height 800 and minimum width 1100, no max
- **Container hierarchy**: Use the standard hierarchy from the fallback design tokens
- **Colors**: Map from the provided palette
- **Template layouts**: Use generic layout names (e.g., "2x2 Grid", "KPI Row + 2 Charts")

For every value you infer from fallback defaults rather than the user's files, record it in `design-tokens.md` under `## Fallback Decisions` with:
- the token name
- the fallback value used
- why it was needed

---

## Path C: No Branding Provided

If `branding/` exists but contains neither `branding.md` nor `template.twb` (or `branding/` itself is missing):
1. Confirm that the user wants to proceed with fallback defaults
2. Use the fallback tokens from `references/tableau-design-tokens.md` as a starting point
3. Warn the user that the mock will use generic Tableau defaults
4. Record every fallback-driven design decision in `design-tokens.md`

---

## design-tokens.md Output Template

Generate this file in the project root:

```markdown
# Design Tokens

**Source**: [template.twb / branding directory / fallback defaults]
**Derived for**: [Step 0 approval candidate]

## Target Tableau Version
- **Minimum version**: [2024.2 – 2025.x  |  2026.1+]
- **Selected by**: [user-confirmed | default]
- **Affects**: Step E only — controls workbook `version` attribute, manifest tag set, and whether `<explain-data>` is emitted. See `step-e-twb-generation.md § Tableau Version Targeting`.

## Typography
- **Font family**: [extracted font]
- **Dashboard title**: [size]px, [weight], [color hex]
- **Chart title**: [size]px, [weight], [color hex]
- **Filter/section labels**: [size]px, [weight], [color hex]
- **Worksheet default font size**: [size]px
- **Tooltip font size**: [size]px

## Colors

### Backgrounds
- **Dashboard background**: [hex]
- **Top banner / title area**: [hex]
- **Chart card background**: [hex]
- **Separator line**: [hex]

### Accent Colors (KPI top border bars)
- Accent 1: [hex]
- Accent 2: [hex]
- Accent 3: [hex]
- Accent 4: [hex]

### Chart Series Colors
[Ordered list of hex colors for chart data series]

### Text
- Dark (titles): [hex]
- Medium (labels): [hex]

### Borders
- Default border-style: [value]
- Exceptions: [any special border zones]

## Logo
- **File**: [path to logo file]
- **Dimensions**: [w x h if known]
- **Placement**: Top-left banner area

## Dashboard Sizing
- **Sizing mode**: [Range / Fixed / Automatic]
- **Minimum height**: [px]
- **Minimum width**: [px]
- **Maximum**: [w] x [h] or Flex

## Standard Container Hierarchy
[Container tree extracted from .twb or built from defaults]

## Available Template Layouts
[List of available layouts with descriptions]

## KPI Card Pattern
[Structure of KPI cards]

## Chart Card Pattern
[Structure of chart cards]

## Icons
[If `branding/icons/` exists, list available icons:]
| Icon Name | File | Size |
|-----------|------|------|
| [name] | [branding/icons/filename.svg] | 40x40 |

[If no icons provided, note that Step C will generate simple inline SVG icons matching chart types.]

## Fallback Decisions
| Token / Decision | Fallback Value Used | Why It Was Needed |
|------------------|---------------------|-------------------|
| [token name] | [value] | [missing brand input or template detail] |

## Spacing Reference
| Element | Property | Value |
|---------|----------|-------|
| [element] | [property] | [value] |

## Constraints
- [List of Tableau rendering constraints: no rounded corners, border rules, etc.]
```

## Guidelines

- If extracting from `.twb`, be thorough — capture every styling detail so Steps C and D don't need to reference the TWB directly
- If building from branding assets, clearly mark which values are "assumed defaults" vs "extracted from branding"
- The generated `design-tokens.md` becomes the **single source of truth** for all subsequent steps
- Use explicit wording like `Fallback used:` whenever a value comes from Tableau defaults rather than customer input
- Keep sizing unambiguous by writing `Minimum height` and `Minimum width` instead of a bare `WxH` pair
- Approval is not just aesthetic: the user should be able to see every fallback value you introduced
- Present to the user and **wait for approval** before proceeding to Step A
