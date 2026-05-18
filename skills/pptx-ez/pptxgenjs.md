# PptxGenJS Reference

Use PptxGenJS when you need: gradient backgrounds, precise pixel placement, rich text arrays,
complex shapes with shadows, or full programmatic control over every slide element.

Docs: https://gitbrent.github.io/PptxGenJS/

## Setup

```bash
npm install pptxgenjs
```

```javascript
const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';    // 'LAYOUT_16x9' | 'LAYOUT_16x10' | 'LAYOUT_4x3' | 'LAYOUT_WIDE'
pres.author = 'Claude';
pres.title  = 'Presentation Title';

let slide = pres.addSlide();

pres.writeFile({ fileName: "output.pptx" });
```

## Layout dimensions (coordinates in inches)

| Layout | Width | Height |
|--------|-------|--------|
| `LAYOUT_16x9` | 10" | 5.625" |
| `LAYOUT_16x10` | 10" | 6.25" |
| `LAYOUT_4x3` | 10" | 7.5" |
| `LAYOUT_WIDE` | 13.3" | 7.5" |

---

## Text

```javascript
// Basic text
slide.addText("Hello World", {
  x: 0.5, y: 0.5, w: 9, h: 1.5,
  fontSize: 32, fontFace: "Arial",
  color: "363636", bold: true,
  align: "center", valign: "middle",
});

// Character spacing (use charSpacing, not letterSpacing — letterSpacing is silently ignored)
slide.addText("SPACED", { x: 1, y: 1, w: 8, h: 1, charSpacing: 6 });

// Text box with no internal margin (use when aligning text with shapes at same x)
slide.addText("Label", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  margin: 0,
});

// Rich text array
slide.addText([
  { text: "Bold ",   options: { bold: true } },
  { text: "italic ", options: { italic: true } },
  { text: "normal" },
], { x: 1, y: 2, w: 8, h: 1, fontSize: 18 });

// Multi-line (requires breakLine: true on each line except the last)
slide.addText([
  { text: "Line 1", options: { breakLine: true } },
  { text: "Line 2", options: { breakLine: true } },
  { text: "Line 3" },
], { x: 0.5, y: 0.5, w: 8, h: 2 });
```

---

## Bullets

```javascript
// ✅ CORRECT — use bullet: true, never unicode •
slide.addText([
  { text: "First item",  options: { bullet: true, breakLine: true } },
  { text: "Second item", options: { bullet: true, breakLine: true } },
  { text: "Third item",  options: { bullet: true } },
], { x: 0.5, y: 1, w: 8, h: 3 });

// ❌ WRONG — unicode bullets create double-bullets
slide.addText("• First item", { ... });

// Nested / indented
{ text: "Sub-item", options: { bullet: true, indentLevel: 1 } }

// Numbered list
{ text: "First",  options: { bullet: { type: "number" }, breakLine: true } }
{ text: "Second", options: { bullet: { type: "number" } } }
```

---

## Shapes

```javascript
// Rectangle
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1, w: 3, h: 2,
  fill: { color: "4472C4" },
  line: { color: "2F5296", width: 2 },
});

// Oval
slide.addShape(pres.shapes.OVAL, {
  x: 4, y: 1, w: 2, h: 2,
  fill: { color: "FF0000" },
});

// Line
slide.addShape(pres.shapes.LINE, {
  x: 1, y: 3, w: 5, h: 0,
  line: { color: "888888", width: 1, dashType: "dash" },
});

// With transparency
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "0088CC", transparency: 50 },
});

// Rounded rectangle (rectRadius only works with ROUNDED_RECTANGLE)
// ⚠️ Do not pair with rectangular accent overlays — they won't cover rounded corners
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  rectRadius: 0.1,
});
```

### Shadow

```javascript
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 },
});
```

Shadow rules:
- `color`: 6-char hex, no `#`, no alpha — use `opacity` instead
- `offset`: must be **non-negative** — negative values corrupt the file
- To shadow upward (footer bar): `angle: 270` with positive `offset`
- `type`: `"outer"` | `"inner"`

**Note**: Gradient fills are not natively supported. Use a gradient image as slide background.

---

## Images

```javascript
// From file path
slide.addImage({ path: "images/logo.png", x: 1, y: 1, w: 5, h: 3 });

// From base64 (faster, no disk I/O)
slide.addImage({ data: "image/png;base64,iVBORw0KGgo...", x: 1, y: 1, w: 4, h: 3 });

// Aspect-ratio safe: specify only w or h, not both
slide.addImage({ path: "chart.png", x: 0.5, y: 1.5, w: 9 });
```

---

## Tables

```javascript
let rows = [
  [{ text: "Header A", options: { bold: true, fill: { color: "4472C4" }, color: "FFFFFF" } },
   { text: "Header B", options: { bold: true, fill: { color: "4472C4" }, color: "FFFFFF" } }],
  ["Value 1", "Value 2"],
  ["Value 3", "Value 4"],
];

slide.addTable(rows, {
  x: 0.5, y: 1.5, w: 9,
  colW: [4.5, 4.5],
  border: { type: "solid", color: "CCCCCC", pt: 1 },
  fontFace: "Calibri",
  fontSize: 14,
});
```

---

## Charts

```javascript
let chartData = [
  { name: "Revenue", labels: ["Q1","Q2","Q3","Q4"], values: [120, 145, 160, 175] },
  { name: "Cost",    labels: ["Q1","Q2","Q3","Q4"], values: [80,  92,  100, 108] },
];

slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1, w: 9, h: 4.5,
  title: "Quarterly Performance",
  showTitle: true,
  showLegend: true,
  legendPos: "b",
  barDir: "col",    // "col" = vertical bars; "bar" = horizontal
});
```

Chart types: `BAR`, `LINE`, `PIE`, `DOUGHNUT`, `AREA`, `SCATTER`, `BUBBLE`, `RADAR`.

---

## Slide background

```javascript
// Solid color
slide.background = { color: "1E2761" };

// Image
slide.background = { path: "bg.jpg" };
slide.background = { data: "image/jpeg;base64,..." };
```

---

## Speaker notes

```javascript
slide.addNotes("Presenter notes here.\n\nSecond paragraph.");
```

---

## Multiple slides

```javascript
let slide1 = pres.addSlide();
slide1.addText("Title Slide", { x: 1, y: 2, w: 8, h: 2, fontSize: 44, bold: true, align: "center" });
slide1.background = { color: "1E2761" };

let slide2 = pres.addSlide();
slide2.addText("Content Slide", { ... });

pres.writeFile({ fileName: "deck.pptx" });
```

---

## Common pitfalls

- **`letterSpacing` is silently ignored** — use `charSpacing` instead
- **`offset` on shadows must be non-negative** — negative values corrupt the XML
- **`rectRadius` only works on `ROUNDED_RECTANGLE`** — not `RECTANGLE`
- **Gradient fills** are not natively supported — use a background image
- **8-char hex colors** (with alpha) are not supported for shadow `color` — use `opacity`
- **Default text box margin** shifts text right/down — set `margin: 0` when aligning with shapes
