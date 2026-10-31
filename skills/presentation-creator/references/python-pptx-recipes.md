# python-pptx recipes

Verified against **python-pptx 1.0.2**; minimum supported **0.6.21**. Import surface is stable
across 1.0.x. All snippets assume a presentation created with a blank layout so there is no
template-placeholder dependence.

## Setup and canvas

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]          # 6 == "Blank" in the default template
slide = prs.slides.add_slide(blank)
```

EMU is the internal unit: 1 inch = 914400 EMU. `Inches()`, `Pt()`, `Emu()` all return ints;
do arithmetic in EMU and convert only at the edges.

## Text box with styled runs

```python
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

box = slide.shapes.add_textbox(Inches(0.6), Inches(0.5), Inches(12.1), Inches(1.0))
tf = box.text_frame
tf.word_wrap = True

p = tf.paragraphs[0]                  # first paragraph already exists
p.alignment = PP_ALIGN.LEFT
run = p.add_run()
run.text = "Assertion-style headline"
run.font.size = Pt(30)
run.font.bold = True
run.font.name = "Segoe UI Semibold"
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
```

Setting `p.text = "..."` replaces all runs; prefer `add_run()` to keep per-run styling.

## Bulleted body

```python
body = slide.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.1), Inches(5.0))
tf = body.text_frame
tf.word_wrap = True
tf.vertical_anchor = MSO_ANCHOR.TOP

items = ["First point", "Second point", "Third point"]
for i, text in enumerate(items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = text
    p.level = 0
    p.font.size = Pt(18)
    p.space_after = Pt(8)
```

`paragraph.font` sets the default for the paragraph's runs; explicit run fonts override it.

## Solid-fill card (also gives a contrast surface)

```python
from pptx.enum.shapes import MSO_SHAPE

card = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.6), Inches(5.8), Inches(4.8)
)
card.fill.solid()
card.fill.fore_color.rgb = RGBColor(0xF2, 0xF4, 0xF7)
card.line.fill.background()          # no outline
card.shadow.inherit = False          # flatten the default shadow
```

`card.text_frame` lets you put text inside the shape; text inherits the shape's fill for
contrast checks. Use `shape.fill.background()` for the reverse (text on slide background).

## Full-bleed background band

```python
band = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(2.2)
)
band.fill.solid()
band.fill.fore_color.rgb = RGBColor(0x0B, 0x3D, 0x91)
band.line.fill.background()
band.shadow.inherit = False
```

## Picture slide (path must exist locally)

```python
pic = slide.shapes.add_picture(
    "/abs/path/image.png", Inches(6.9), Inches(1.6), width=Inches(5.8)
)
```

Omit `height` to preserve aspect ratio. Prefer local files; never download at build time.

## Table

```python
rows, cols = 5, 3
tbl_shape = slide.shapes.add_table(
    rows, cols, Inches(0.6), Inches(1.8), Inches(12.1), Inches(4.0)
)
table = tbl_shape.table

headers = ["Feature", "Today", "Target"]
for c, text in enumerate(headers):
    cell = table.cell(0, c)
    cell.text = text
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0x1F, 0x6F, 0xEB)
    for p in cell.text_frame.paragraphs:
        for r in p.runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            r.font.size = Pt(14)

for r_i, row in enumerate([["A", "1", "2"], ["B", "3", "4"]], start=1):
    for c_i, text in enumerate(row):
        table.cell(r_i, c_i).text = text
```

## Quote

```python
quote = slide.shapes.add_textbox(Inches(1.2), Inches(2.4), Inches(10.9), Inches(2.6))
tf = quote.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
r = p.add_run()
r.text = "\u201cThe best deck is the one that ships.\u201d"
r.font.italic = True
r.font.size = Pt(26)
attr = tf.add_paragraph()
attr.text = "\u2014 Author"
attr.font.size = Pt(14)
```

## Native chart

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

data = CategoryChartData()
data.categories = ["Q1", "Q2", "Q3", "Q4"]
data.add_series("Revenue", (1.2, 2.4, 3.1, 4.6))

gf = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.9), Inches(1.8), Inches(11.5), Inches(4.8), data
)
chart = gf.chart
chart.has_legend = True
```

Chart types: `COLUMN_CLUSTERED` (bar), `LINE_MARKERS` (line), `PIE` (pie). For a pie chart use
a single series.

## Speaker notes

```python
slide.notes_slide.notes_text_frame.text = "One paragraph of speaker notes."
```

`slide.notes_slide` is created on first access.

## Save

```python
prs.save("deck.pptx")
```

The writer refuses to run on an existing path only if you add the guard yourself;
`build_deck.py` handles the overwrite check with `--force`.
