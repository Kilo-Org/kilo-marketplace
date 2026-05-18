# python-pptx API Reference

Version: 1.x — check with `python -c "import pptx; print(pptx.__version__)"`
Docs: https://python-pptx.readthedocs.io

## Installation

```bash
pip install python-pptx
```

---

## Presentation

```python
from pptx import Presentation

# New presentation
prs = Presentation()

# Open existing
prs = Presentation('existing.pptx')

# Save
prs.save('output.pptx')
```

### Slide size

```python
from pptx.util import Cm, Inches

# 16:9 widescreen (default in modern PowerPoint)
prs.slide_width  = Cm(33.867)   # 13.33 in
prs.slide_height = Cm(19.05)    # 7.5 in

# 4:3 standard
prs.slide_width  = Inches(10)
prs.slide_height = Inches(7.5)
```

Units: all measurements in EMUs (English Metric Units). 1 inch = 914 400 EMU.
`Inches()`, `Cm()`, `Pt()`, `Emu()` all return EMU integers.

### Core properties

```python
props = prs.core_properties
props.title    = 'My Deck'
props.author   = 'Claude'
props.subject  = 'Quarterly Review'
props.keywords = 'pptx, report'
```

---

## Slides

```python
# Add a slide using a layout
layout = prs.slide_layouts[1]          # Title and Content
slide  = prs.slides.add_slide(layout)

# Access by index
slide = prs.slides[0]                  # first slide

# Total count
print(len(prs.slides))
```

### Slide layouts (default template)

| Index | Name |
|-------|------|
| 0 | Title Slide |
| 1 | Title and Content |
| 2 | Title and Two Content |
| 3 | Title, Content, and Caption |
| 4 | Two Content |
| 5 | Title Only |
| 6 | Blank |
| 7 | Content with Caption |
| 8 | Picture with Caption |

Look up by name for robustness across templates:

```python
def layout_by_name(prs, name):
    for layout in prs.slide_layouts:
        if layout.name == name:
            return layout
    return prs.slide_layouts[6]  # blank fallback
```

---

## Placeholders

```python
# Title
slide.shapes.title.text = 'Slide Title'

# By placeholder index (layout-dependent)
slide.placeholders[0].text = 'Title'
slide.placeholders[1].text = 'Content'

# Inspect available placeholders
for ph in slide.placeholders:
    print(ph.placeholder_format.idx, ph.name)
```

---

## Text Frames

```python
tf = shape.text_frame
tf.word_wrap = True
tf.text = 'Replaces all text in the first paragraph'

# Paragraphs
para = tf.paragraphs[0]
para.text  = 'First paragraph'
para.level = 0    # indent level (0=top, 1=sub, etc.)

para2 = tf.add_paragraph()
para2.text = 'Second paragraph'
```

### Paragraph alignment

```python
from pptx.enum.text import PP_ALIGN

para.alignment = PP_ALIGN.LEFT     # LEFT, CENTER, RIGHT, JUSTIFY
```

### Paragraph spacing

```python
from pptx.util import Pt

para.space_before = Pt(6)
para.space_after  = Pt(6)
para.line_spacing = Pt(18)    # or float multiple: 1.5
```

---

## Runs (inline text)

```python
run = para.add_run()
run.text = 'Bold italic text'
```

### Run font properties

```python
from pptx.dml.color import RGBColor
from pptx.util import Pt

font = run.font
font.name      = 'Arial'
font.size      = Pt(18)
font.bold      = True
font.italic    = True
font.underline = True
font.color.rgb = RGBColor(0xFF, 0x00, 0x00)   # red
font.color.theme_color = MSO_THEME_COLOR.ACCENT_1
```

---

## Shapes

### Text box

```python
from pptx.util import Inches, Pt

txBox = slide.shapes.add_textbox(
    Inches(1), Inches(2), Inches(6), Inches(1.5)
)
tf = txBox.text_frame
```

### Geometric shape

```python
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Cm

# Rectangle (type 1)
shape = slide.shapes.add_shape(1, Cm(2), Cm(4), Cm(10), Cm(3))

# Rounded rectangle (type 5)
shape = slide.shapes.add_shape(5, Cm(2), Cm(4), Cm(10), Cm(3))
```

Common `MSO_AUTO_SHAPE_TYPE` values:
```
RECTANGLE = 1
ROUNDED_RECTANGLE = 5
OVAL = 9
TRIANGLE = 5 (isoceles)
RIGHT_ARROW = 13
CHEVRON = 52
```

### Shape fill and line

```python
from pptx.dml.color import RGBColor

shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(0x44, 0x72, 0xC4)

shape.fill.background()          # transparent

shape.line.color.rgb  = RGBColor(0x20, 0x40, 0x80)
shape.line.width      = Pt(1.5)
shape.line.dash_style = MSO_LINE.DASH
```

### Shape position and size

```python
from pptx.util import Cm

shape.left   = Cm(2)
shape.top    = Cm(3)
shape.width  = Cm(12)
shape.height = Cm(4)
```

---

## Images

```python
from pptx.util import Cm

# Inline image — width only (aspect ratio preserved)
pic = slide.shapes.add_picture('photo.png', Cm(2), Cm(5), width=Cm(12))

# Explicit dimensions
pic = slide.shapes.add_picture('photo.png', Cm(2), Cm(5), Cm(12), Cm(8))
```

Supported formats: PNG, JPEG, GIF, TIFF, BMP, WMF, EMF.

---

## Tables

```python
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor

rows, cols = 4, 3
tbl_shape = slide.shapes.add_table(rows, cols, Cm(2), Cm(5), Cm(22), Cm(8))
tbl       = tbl_shape.table

# Column widths
tbl.columns[0].width = Cm(8)

# Cell access
cell = tbl.cell(0, 0)
cell.text = 'Header'

# Cell fill
cell.fill.solid()
cell.fill.fore_color.rgb = RGBColor(0x44, 0x72, 0xC4)

# Text formatting within a cell
para = cell.text_frame.paragraphs[0]
run  = para.runs[0] if para.runs else para.add_run()
run.text       = 'Header'
run.font.bold  = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Merge cells (horizontal)
cell_a = tbl.cell(0, 0)
cell_b = tbl.cell(0, 2)
cell_a.merge(cell_b)
```

---

## Charts

```python
from pptx.chart.data import CategoryChartData, ChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Cm

# Category chart (bar, column, line, pie, area)
chart_data = CategoryChartData()
chart_data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
chart_data.add_series('Revenue', (120, 145, 160, 175))
chart_data.add_series('Cost',    ( 80,  92, 100, 108))

frame = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Cm(3), Cm(5), Cm(24), Cm(12),
    chart_data,
)
chart = frame.chart
```

### Chart customization

```python
chart.has_legend              = True
chart.legend.position         = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False

chart.has_title               = True
chart.chart_title.text_frame.text = 'Quarterly Performance'

# Value axis
chart.value_axis.has_title    = True
chart.value_axis.axis_title.text_frame.text = 'USD (millions)'
chart.value_axis.minimum_scale = 0

# Category axis
chart.category_axis.has_title = True
```

### Scatter chart

```python
from pptx.chart.data import XyChartData

data = XyChartData()
series = data.add_series('Series 1')
series.add_data_point(1.0, 2.5)
series.add_data_point(2.0, 3.1)

frame = slide.shapes.add_chart(
    XL_CHART_TYPE.XY_SCATTER,
    Cm(2), Cm(4), Cm(20), Cm(12), data,
)
```

### Chart type constants (`XL_CHART_TYPE`)

```
BAR_CLUSTERED, BAR_STACKED, BAR_STACKED_100
COLUMN_CLUSTERED, COLUMN_STACKED, COLUMN_STACKED_100
LINE, LINE_MARKERS, LINE_STACKED, LINE_STACKED_100
PIE, PIE_EXPLODED, DOUGHNUT, DOUGHNUT_EXPLODED
AREA, AREA_STACKED, AREA_STACKED_100
XY_SCATTER, XY_SCATTER_LINES, XY_SCATTER_SMOOTH
BUBBLE, RADAR, SURFACE
```

---

## Speaker notes

```python
notes_slide = slide.notes_slide
tf          = notes_slide.notes_text_frame
tf.text     = 'Presenter notes here.'

# Add formatted note
para = tf.add_paragraph()
run  = para.add_run()
run.text = 'Extra point'
```

---

## Iterating shapes

```python
for slide in prs.slides:
    for shape in slide.shapes:
        print(shape.shape_type, shape.name)
        if shape.has_text_frame:
            print(shape.text_frame.text)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    print(cell.text)
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            print(shape.image.ext, shape.image.blob[:4])
```

---

## Deleting a slide

python-pptx has no native `slides.remove()`. Use the XML relationship:

```python
def delete_slide(prs, idx):
    xml_slides = prs.slides._sldIdLst
    slide = prs.slides[idx]
    rId = xml_slides[idx].get(
        '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    )
    prs.part.drop_rel(rId)
    xml_slides.remove(xml_slides[idx])
```

---

## Duplicating a slide

```python
import copy

def duplicate_slide(prs, src_idx):
    src   = prs.slides[src_idx]
    blank = prs.slides.add_slide(src.slide_layout)
    dst_tree = blank.shapes._spTree
    src_tree = src.shapes._spTree
    for el in list(dst_tree):
        dst_tree.remove(el)
    for el in src_tree:
        dst_tree.append(copy.deepcopy(el))
```

---

## Limitations

- No native tracked-changes or comments API — use `lxml` direct XML if needed
- Chart data is embedded as an XLSX part; use `chart.chart_data` to update series
- Slide transitions and animations: python-pptx reads but has limited write support
- `.ppt` (legacy binary): convert first with LibreOffice:
  ```bash
  soffice --headless --convert-to pptx legacy.ppt
  ```
