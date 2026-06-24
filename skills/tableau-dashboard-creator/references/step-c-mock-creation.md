# Step C: HTML Mock Creation

**Identity**: You are a Tableau developer creating an interactive HTML mock that stakeholders can preview in a browser. The mock must faithfully represent Tableau's layout constraints and the customer's design system as defined in `design-tokens.md`.

## Process

1. **Read the approved DASHBOARD-PLAN.md**
2. **Read design-tokens.md** (generated in Step 0) for all styling values
3. **Ask the user for their target screen size** — present these options:
   - **Standard Laptop** (1100×800): Standard laptop screen resolution — good for dashboards viewed primarily on portable devices
   - **Home Screen** (2100×1000): Larger home/desktop monitor — good for dashboards viewed on wide external displays
   - **Custom**: Let the user specify their own width × height
   - If the user skips or doesn't respond, default to **Standard Laptop** (1100×800)
4. **Select the matching template layout** based on the recommended layout in the dashboard plan
5. **Build the HTML mock** following Tableau constraints, using the chosen screen dimensions as the dashboard frame
6. **Save to** `mock-version/v_N/mock.html`

## Entry Requirements

Before Step C begins, verify:
- `DASHBOARD-PLAN.md` is approved
- `design-tokens.md` is approved
- every chart in the plan has a defined slot or layout position
- any fallback-driven design decisions are visible in the approved root docs

If the approved plan cannot fit cleanly inside the minimum dashboard frame, do not force it into one page. Revise the layout or split the experience.

## Technical Requirements

### HTML Structure
- Single self-contained HTML file (inline CSS + JS)
- Use Chart.js via CDN for interactive charts: `https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js`
- Load the font family specified in design-tokens.md (default: Open Sans via Google Fonts)
- Responsive within the sizing range defined in design-tokens.md
- Dashboard frame dimensions are set by the user's screen-size choice (see Process step 3):
  - **Standard Laptop**: minimum height `800px`, minimum width `1100px`
  - **Home Screen**: minimum height `1000px`, minimum width `2100px`
  - **Custom**: user-specified dimensions
  - If the user skipped the prompt, default to Standard Laptop (1100×800)
  - No fixed maximum — the layout must remain proportional beyond the minimum frame

### Tableau Fidelity Rules

**CRITICAL - these constraints must be followed:**

1. **No rounded corners** anywhere unless the user explicitly accepts a non-Tableau-faithful mock
   - `border-radius: 0` on all elements
2. **Container hierarchy** must match Tableau's zone model:
   - Outer: `layout-basic` (absolute positioning root)
   - Inner: `layout-flow` containers (vertical or horizontal flexbox)
   - Fixed-size containers use explicit pixel heights
   - Flex containers fill remaining space
3. **No box shadows** unless explicitly requested (Tableau does not have native shadows)
4. **Border-style: none** on all containers (except logo zone which uses a background-blending border)
5. **Fixed-size elements**: Use explicit `min-height` / `min-width` in CSS on structural elements (title bars, KPI rows, filter bars, accent bars, icons, logo) to prevent compression on smaller screens. Only chart areas and main content should flex.
6. **Tableau-native terminology**: Use Tableau spacing terms (`margin`, `padding`) in design documentation — avoid CSS-specific terms like `gap` which have no Tableau equivalent.
7. **No out-of-bounds rendering**: Titles, legends, labels, canvases, and controls must stay inside their card boundaries at the minimum dashboard frame.
8. **Avoid empty-space-heavy layouts**: if a row or card leaves large dead areas, rebalance the layout or choose a denser template. Do not leave charts visibly undersized relative to their containers.

### Layout Sizing Contract

The mock should be visually disciplined, not just approximate. Apply these rules:
- Use an explicit root dashboard frame with the minimum height and width chosen by the user in the screen-size prompt (defaults to `800px` height and `1100px` width for Standard Laptop)
- Use a consistent outer padding and internal row/column spacing derived from the design tokens
- Give each chart card a defined slot and expected size from `DASHBOARD-PLAN.md`
- KPI cards should use equal widths within a row
- Multi-chart rows should distribute space evenly unless the approved plan explicitly calls for a dominant chart
- Each chart's plot area should occupy roughly `70%` or more of its card after title bars, separators, legends, and padding
- If a legend on the right would compress the plot area too much, move the legend to the bottom or simplify the chart
- If labels, legends, or filter controls overflow at the minimum frame, the layout must be revised rather than stretched

### Chart.js Canvas Sizing

Chart.js requires a non-zero-height container to render. Flex layouts with `min-height: 0` can collapse chart containers to zero pixels, producing blank canvases (sad face icon). Follow these rules:

1. **Canvas wrapper min-height**: Every `.chart-body` (or equivalent canvas wrapper) must have `min-height: 140px` (or a value appropriate to the layout). Never use `min-height: 0` on a chart container.
2. **Do not force canvas dimensions**: Do not apply `width: 100% !important` or `height: 100% !important` to `<canvas>` elements. Chart.js manages its own canvas sizing when `responsive: true` and `maintainAspectRatio: false` are set. Forcing dimensions overrides Chart.js internals and can cause rendering failures.
3. **Canvas display block**: Set `canvas { display: block; }` to prevent the inline-element gap that adds unexpected whitespace below the canvas.
4. **DZV overlay containers**: Overlay panels that contain their own `<canvas>` elements (e.g., drill-down panels) need the same `min-height` treatment on their body containers.
5. **Side panels**: Collapsible side panels (e.g., credit detail panels) should call `chart.resize()` after the CSS transition completes (~300ms) to force Chart.js to recalculate dimensions for the newly visible container.

### Design Token Application

Apply all values from `design-tokens.md`. Map the tokens to CSS:

```css
/* Map these from design-tokens.md — values shown are examples */
body {
    font-family: /* from design-tokens: Typography > Font family */;
    background-color: /* from design-tokens: Colors > Dashboard background */;
    margin: 0;
    font-size: /* from design-tokens: Typography > Worksheet default font size */;
}

.dashboard-title {
    font-size: /* from design-tokens: Typography > Dashboard title size */;
    font-weight: /* from design-tokens: Typography > Dashboard title weight */;
    color: /* from design-tokens: Colors > Text > Dark */;
    background-color: /* from design-tokens: Colors > Top banner area */;
    padding: 4px;
    padding-bottom: 0;
    margin-bottom: 1px;
}

.chart-title {
    font-size: /* from design-tokens: Typography > Chart title size */;
    color: /* from design-tokens: Colors > Text > Dark */;
    margin: 4px;
    margin-left: 10px;
}

.filter-label {
    font-size: /* from design-tokens: Typography > Filter labels size */;
    font-weight: bold;
    color: /* from design-tokens: Colors > Text > Medium */;
}

.chart-card {
    background-color: /* from design-tokens: Colors > Chart card background */;
    padding: 8px;
    border: none;
    border-radius: 0;  /* CRITICAL */
}

.kpi-accent-bar {
    height: 3px;
    margin: 0;
    /* background-color: from design-tokens: Colors > Accent Colors */
}

.separator-line {
    height: 3px;
    background-color: /* from design-tokens: Colors > Separator line */;
    margin: 0 10px;
}

/* Inner padding for all worksheet/sheet zones — space between zone border and content */
.sheet-zone {
    padding: 8px;
}

/* Flexible spacer — every flow container should include one to prevent layout collapse */
.spacer {
    flex: 1;
}

/* Chart.js canvas container — must have a concrete min-height */
.chart-body {
    flex: 1;
    position: relative;
    min-height: 140px;  /* CRITICAL — prevents flex collapse */
}

.chart-body canvas {
    display: block;  /* removes inline gap */
    /* Do NOT add width/height 100% !important — Chart.js manages its own sizing */
}
```

### Container Layout Pattern

Follow this HTML structure mirroring Tableau's zone hierarchy (adapt based on design-tokens.md container hierarchy):

```html
<div class="dashboard-root">                    <!-- layout-basic -->
  <div class="content-wrapper">                 <!-- Content (vert flow) -->
    <div class="top-banner">                    <!-- Logo, Info, Last update -->
      <div class="logo-area">...</div>
      <div class="spacer"></div>                <!-- Flexible spacer -->
      <div class="update-info">...</div>
    </div>
    <div class="dashboard-title">Title</div>    <!-- Dashboard Title -->
    <div class="filter-bar">                    <!-- Top Filters -->
      <span class="filter-label">Filters</span>
      <div class="filter-controls">...</div>
      <div class="spacer"></div>                <!-- Flexible spacer -->
    </div>
    <div class="main-content">                  <!-- Charts & Hidden Filters -->
      <div class="charts-area">                 <!-- KPI & Charts -->
        <div class="kpi-row">...</div>          <!-- Main KPI (if applicable) -->
        <div class="chart-row">...</div>        <!-- Chart rows -->
        <div class="spacer"></div>              <!-- Flexible spacer -->
      </div>
      <div class="hidden-filters">...</div>     <!-- Hidden Filters panel -->
    </div>
  </div>
</div>
```

### Logo Integration

If a logo file was identified in design-tokens.md:
- Embed the logo in the top-banner area
- For SVG: inline the SVG or use `<img>` with a relative path
- For PNG: use `<img>` with a relative path or base64-encode for self-containment
- Match the dimensions and padding from the design tokens

### Icon Integration

Chart title bars should include a small icon for visual enrichment:
- If `branding/icons/` contains SVG files, use the matching icon for each chart (filenames should match the icon names suggested in DASHBOARD-PLAN.md, e.g., `bar-chart.svg`, `trend.svg`)
- If no icons are provided, generate simple monochrome 40x40 SVG icons inline, using the brand primary color and matching the chart type (e.g., a small bar-chart icon for bar charts, a line icon for trend charts)
- Icons are placed in the chart title bar at 40x40 pixels, before the chart title text

### DOM Security Rules

- **Never use `innerHTML`** to set content — even for hardcoded data. Security hooks flag it as an XSS risk.
- Use `textContent` for plain text (labels, KPI values, titles).
- Use safe DOM methods (`createElement`, `appendChild`, `setAttribute`) when building HTML elements dynamically.
- For Chart.js tooltips and callbacks, use the Chart.js API (which handles rendering safely) rather than injecting raw HTML.

### Chart Implementation

Use Chart.js with dummy data that represents the expected data shape:
- Match chart types from DASHBOARD-PLAN.md
- Use realistic dummy values and labels
- Apply chart series colors from design-tokens.md
- Use accent colors from design-tokens.md for KPI cards
- Include tooltips showing the metric name and value
- Keep chart proportions consistent with their assigned slots; a full-width chart should visibly dominate a half-width chart
- Favor readable axes and labels over squeezing in more marks or decorations

### Interactive Elements

Implement where applicable:
- **Filter dropdowns**: HTML `<select>` elements that filter chart data via JS
- **Dashboard action filters**: Click handlers on charts that highlight/filter other charts
- **Collapsible hidden filters panel**: Toggle button functionality (DZV pattern)
- **KPI cards**: Display values with optional comparison indicators

## Output

Save to `mock-version/v_N/mock.html` where N is the current version number (start with 1).

Present the mock to the user (tell them to open the HTML file in a browser) and **wait for approval** before proceeding to Step D. If the user requests changes, overwrite `mock.html` in the current `v_N` directory (do NOT create a new version directory — version increments only happen at Steps D or E).

When the user approves the mock, review whether the approved mock diverged from the current `DASHBOARD-PLAN.md` or `design-tokens.md` (e.g., added/removed KPIs, changed chart types, adjusted layout, new colors). If it did, update those root-level files to match the approved mock before proceeding to Step D.

When presenting the mock, include a short review checklist:
- layout fits cleanly within the minimum dashboard frame
- no chart or control is clipped or out of bounds
- chart proportions feel intentional, with no oversized empty areas
- any fallback-driven design choices are called out explicitly
- any interaction that is illustrative rather than Tableau-exact is called out explicitly

> **Important — this is an iterative process.** The HTML mock is unlikely to be perfect on the first attempt. Expect multiple revision cycles — this is normal and by design. Encourage the user to share the mock with stakeholders for feedback before approving. A well-validated mock saves significant rework in later steps (D and E). Take your time here — it's better to iterate on the mock than to rebuild the implementation spec or workbook.