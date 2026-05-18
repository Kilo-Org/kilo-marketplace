---
name: pptx-ez
description: "Use this skill any time a .pptx file is involved — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations from scratch; reading or extracting text from any .pptx; editing existing presentations (text, shapes, slides, notes); template-based editing (unpack → edit XML → pack); visual QA with thumbnails. Trigger whenever the user mentions PowerPoint, .pptx, deck, slides, or presentation. Do NOT use this skill for spreadsheets (.xlsx), documents (.docx), or PDF-only tasks."
license: CC0-1.0
compatibility: Python 3.9+ with python-pptx and lxml; LibreOffice 7.4+ (PDF/PNG export). Linux, macOS, Windows.
metadata:
  category: productivity
  author: shauneshraghi
  source:
    repository: https://github.com/shauneshraghi/skills
    path: pptx-ez
    license_path: LICENSE.txt
---

# pptx-ez Skill

## Toolchain at a glance

| Task | Tool | Script |
|------|------|--------|
| Create new .pptx (JSON spec) | python-pptx | `scripts/create_pptx.py` |
| Create from scratch (rich) | PptxGenJS | see [pptxgenjs.md](pptxgenjs.md) |
| Edit existing .pptx (CLI) | python-pptx | `scripts/edit_pptx.py` |
| Edit existing .pptx (XML) | lxml direct | `scripts/office/unpack.py` → edit → `scripts/office/pack.py` |
| Add / duplicate slide | rels-aware | `scripts/add_slide.py` |
| Clean orphaned parts | defusedxml | `scripts/clean.py` |
| Visual thumbnail grid | LibreOffice + Pillow | `scripts/thumbnail.py` |
| PDF / PNG export | LibreOffice headless | `scripts/export_pdf.sh` |
| Validate structure | Python zipfile | `scripts/validate_pptx.py` |

**For template-based editing:** read [editing.md](editing.md) — unpack → edit slide XML → clean → pack.

---

## Path A — Create a new presentation

```bash
pip install python-pptx

# Demo deck (all features)
python scripts/create_pptx.py output.pptx

# From a JSON spec
python scripts/create_pptx.py output.pptx --spec spec.json
```

### Spec JSON format

```json
{
  "title": "Presentation Title",
  "author": "Claude",
  "widescreen": true,
  "slides": [
    {
      "layout": "title",
      "title": "Welcome",
      "subtitle": "Subtitle line"
    },
    {
      "layout": "content",
      "title": "Key Points",
      "content": ["Point one", "Point two", "Point three"],
      "notes": "Speaker notes go here."
    },
    {
      "layout": "two_content",
      "title": "Comparison",
      "left": ["Left A", "Left B"],
      "right": ["Right A", "Right B"]
    },
    {
      "layout": "blank",
      "shapes": [
        {
          "type": "textbox",
          "text": "Freeform text",
          "left_cm": 2, "top_cm": 3, "width_cm": 20, "height_cm": 4,
          "bold": true, "font_size": 28, "font_color": "#333333",
          "align": "center"
        },
        {
          "type": "image",
          "path": "logo.png",
          "left_cm": 5, "top_cm": 10, "width_cm": 12
        },
        {
          "type": "table",
          "rows": [["Name", "Value"], ["Alpha", "100"], ["Beta", "200"]],
          "left_cm": 2, "top_cm": 8, "width_cm": 22, "height_cm": 5,
          "header_bg": "#4472C4", "header_font_color": "#FFFFFF"
        },
        {
          "type": "chart",
          "chart_type": "bar",
          "categories": ["Q1", "Q2", "Q3"],
          "series": [{"name": "Revenue", "values": [120, 145, 160]}],
          "left_cm": 2, "top_cm": 5, "width_cm": 20, "height_cm": 10
        }
      ]
    }
  ]
}
```

Supported `layout` values: `title`, `content`, `two_content`, `title_only`, `blank`.

Supported shape `type` values: `textbox`, `image`, `table`, `chart`.

Supported `chart_type` values: `bar`, `bar_stacked`, `column`, `column_stacked`, `line`, `line_markers`, `pie`, `doughnut`, `area`, `scatter`.

---

## Path B — Edit an existing presentation

```bash
pip install python-pptx lxml

# Search-replace text across all slides
python scripts/edit_pptx.py in.pptx out.pptx --replace "draft" "final"

# Add a speaker note to a slide (1-based index)
python scripts/edit_pptx.py in.pptx out.pptx --add-note 2 "Remember to demo the live chart."

# Append a blank slide
python scripts/edit_pptx.py in.pptx out.pptx --add-slide blank

# Delete a slide by index (1-based)
python scripts/edit_pptx.py in.pptx out.pptx --delete-slide 3

# Add a text box to a slide
python scripts/edit_pptx.py in.pptx out.pptx \
  --add-textbox 1 "Confidential" --left 0.5 --top 0.2 --width 8 --height 0.5

# Duplicate a slide (appends copy)
python scripts/edit_pptx.py in.pptx out.pptx --duplicate-slide 1
```

---

## Slide layouts (python-pptx index → name)

```
0  Title Slide          (title + subtitle placeholders)
1  Title and Content    (title + body)
2  Title and Two Content
3  Title, Content, and Caption
4  Title Only
5  Blank
6  Centered Text
7  Picture with Caption
8  Title and Vertical Text
9  Vertical Title and Text
```

Access by name is more stable across templates:

```python
def layout_by_name(prs, name):
    for layout in prs.slide_layouts:
        if layout.name == name:
            return layout
    return prs.slide_layouts[5]  # blank fallback
```

---

## Core python-pptx patterns

### New presentation with 16:9 aspect

```python
from pptx import Presentation
from pptx.util import Cm

prs = Presentation()
prs.slide_width  = Cm(33.867)   # 13.33 in
prs.slide_height = Cm(19.05)    # 7.5 in
```

### Title slide

```python
layout = prs.slide_layouts[0]
slide  = prs.slides.add_slide(layout)
slide.shapes.title.text        = 'My Title'
slide.placeholders[1].text     = 'Subtitle'
```

### Bullet content slide

```python
from pptx.util import Pt
layout = prs.slide_layouts[1]
slide  = prs.slides.add_slide(layout)
slide.shapes.title.text = 'Bullets'
tf = slide.placeholders[1].text_frame
tf.text = 'First bullet'
for line in ['Second', 'Third']:
    p = tf.add_paragraph()
    p.text  = line
    p.level = 0
```

### Text formatting

```python
from pptx.dml.color import RGBColor
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN

run = para.add_run()
run.text = 'Bold red text'
run.font.bold      = True
run.font.size      = Pt(24)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
para.alignment     = PP_ALIGN.CENTER
```

### Shape (rectangle)

```python
from pptx.util import Cm
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor

shape = slide.shapes.add_shape(
    1,   # MSO_SHAPE.RECTANGLE
    Cm(2), Cm(4), Cm(10), Cm(3)
)
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(0x44, 0x72, 0xC4)
shape.line.color.rgb      = RGBColor(0x2F, 0x52, 0x96)
```

### Image

```python
from pptx.util import Cm
slide.shapes.add_picture('photo.png', Cm(3), Cm(5), width=Cm(12))
```

### Table

```python
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor

rows, cols = 4, 3
tbl = slide.shapes.add_table(rows, cols, Cm(2), Cm(6), Cm(22), Cm(7)).table
tbl.columns[0].width = Cm(8)
tbl.columns[1].width = Cm(7)
tbl.columns[2].width = Cm(7)

# Header row
for c in range(cols):
    cell = tbl.cell(0, c)
    cell.text = f'Header {c+1}'
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0x44, 0x72, 0xC4)
    run = cell.text_frame.paragraphs[0].runs[0]
    run.font.bold      = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
```

### Chart (bar)

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Cm

data = CategoryChartData()
data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
data.add_series('Revenue', (120, 145, 160, 175))
data.add_series('Cost',    ( 80,  92, 100, 108))

chart_frame = slide.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED,
    Cm(3), Cm(5), Cm(24), Cm(12),
    data,
)
chart = chart_frame.chart
chart.has_legend = True
chart.has_title  = True
chart.chart_title.text_frame.text = 'Quarterly Performance'
```

Supported chart types (from `XL_CHART_TYPE`):
```
BAR_CLUSTERED, BAR_STACKED, BAR_STACKED_100
COLUMN_CLUSTERED, COLUMN_STACKED, COLUMN_STACKED_100
LINE, LINE_MARKERS, LINE_STACKED, LINE_STACKED_100
PIE, PIE_EXPLODED, DOUGHNUT
AREA, AREA_STACKED
XY_SCATTER, BUBBLE
RADAR, SURFACE
```

### Speaker notes

```python
notes_slide  = slide.notes_slide
notes_tf     = notes_slide.notes_text_frame
notes_tf.text = 'Presenter note for this slide.'
```

---

## Find-replace across all slides

```python
from pptx import Presentation

def replace_all(prs, old, new):
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if old in run.text:
                        run.text = run.text.replace(old, new)
```

Limitation: if the target string is split across multiple runs (e.g. by formatting), run-level replace will miss it. Use `edit_pptx.py --replace` which handles cross-run matches via XML text normalization.

---

## PDF / PNG export

```bash
bash scripts/export_pdf.sh presentation.pptx ./output/
# Produces: output/presentation.pdf

# PNG (one file per slide)
soffice --headless --convert-to png presentation.pptx --outdir ./output/
```

Install LibreOffice if missing:
```bash
sudo apt-get install -y libreoffice   # Ubuntu/Debian
brew install --cask libreoffice       # macOS
```

---

## Round-trip validation

```bash
python scripts/validate_pptx.py presentation.pptx
```

Checks ZIP integrity, required OPC parts, all XML parses cleanly. Exit 0 = clean.

---

## Text extraction

```bash
# Full text dump (requires: pip install "markitdown[pptx]")
python -m markitdown presentation.pptx

# Check for leftover placeholder text
python -m markitdown presentation.pptx | grep -iE "xxxx|lorem|ipsum|todo|placeholder"
```

---

## Visual thumbnail grid

```bash
# Install requirements
pip install Pillow
sudo apt-get install -y poppler-utils

# Create thumbnail grid (for template analysis, not QA)
python scripts/thumbnail.py deck.pptx
# → thumbnails.jpg

python scripts/thumbnail.py template.pptx grid --cols 4
# → grid.jpg
```

For QA use full-resolution individual slide images (soffice + pdftoppm):

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
# → slide-01.jpg, slide-02.jpg ...

# Re-render specific slides after fixes:
pdftoppm -jpeg -r 150 -f 2 -l 2 output.pdf slide-fixed
```

---

## OOXML direct-edit workflow

For complex template editing, unpack → edit slide XML → clean → pack:

```bash
pip install lxml defusedxml

# 1. Unpack (pretty-prints XML, encodes smart quotes as &#x201C; etc.)
python scripts/office/unpack.py template.pptx unpacked/

# 2. Edit slide XML directly (each slide is ppt/slides/slideN.xml)
# Use the Edit tool — do NOT use sed or Python scripts
# See editing.md for patterns and pitfalls

# 3. Add a new slide (handles rels, Content_Types.xml, sldIdLst)
python scripts/add_slide.py unpacked/ slide2.xml
# Prints the <p:sldId> to insert into ppt/presentation.xml

# 4. Remove orphaned slides and media
python scripts/clean.py unpacked/

# 5. Repack (condenses XML, restores smart quotes)
python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
```

---

## Design guidance

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

### Color palettes

Pick colors that fit the topic. One color should dominate (60–70% visual weight).

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| Midnight Executive | `1E2761` | `CADCFC` | `FFFFFF` |
| Forest & Moss | `2C5F2D` | `97BC62` | `F5F5F5` |
| Coral Energy | `F96167` | `F9E795` | `2F3C7E` |
| Warm Terracotta | `B85042` | `E7E8D1` | `A7BEAE` |
| Ocean Gradient | `065A82` | `1C7293` | `21295C` |
| Charcoal Minimal | `36454F` | `F2F2F2` | `212121` |
| Teal Trust | `028090` | `00A896` | `02C39A` |
| Berry & Cream | `6D2E46` | `A26769` | `ECE2D0` |

Use dark backgrounds for title + conclusion slides, light for content ("sandwich" structure).

### Typography

| Header Font | Body Font |
|-------------|----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Trebuchet MS | Calibri |
| Impact | Arial |

| Element | Size |
|---------|------|
| Slide title | 36–44 pt bold |
| Section header | 20–24 pt bold |
| Body text | 14–16 pt |
| Captions | 10–12 pt |

### Spacing

- 0.5" minimum margins from slide edges
- 0.3–0.5" between content blocks
- Leave breathing room — do not fill every inch

### Avoid (common mistakes)

- **Never repeat the same layout** on consecutive slides — vary columns, cards, callouts
- **Never center body text** — left-align paragraphs; center only titles
- **Never default to blue** — choose colors that reflect the specific topic
- **Never use unicode bullets (•)** — use `bullet: true` (PptxGenJS) or `<a:buChar>` (XML); unicode bullets create double-bullets
- **Never put a decorative line under titles** — hallmark of AI-generated slides; use whitespace instead
- **Never use low-contrast text** — check foreground vs background on every slide
- **Set `margin: 0`** on text boxes when aligning text with shapes or icons at the same x-position (default padding shifts text right)
- **Bold all headers and inline labels** (`b="1"` on `<a:rPr>` for titles, section headers, "Status:", "Note:", etc.)

---

## XML quick reference (PresentationML)

Units: EMU (English Metric Units). 1 inch = 914400 EMU. 1 cm = 360000 EMU.

Namespaces:
```
p:  http://schemas.openxmlformats.org/presentationml/2006/main
a:  http://schemas.openxmlformats.org/drawingml/2006/main
r:  http://schemas.openxmlformats.org/officeDocument/2006/relationships
```

Slide size (16:9 widescreen): `cx="12192000" cy="6858000"`

Font size in `<a:rPr>`: `sz` attribute is in hundredths of a point. `sz="2400"` = 24 pt.

Smart-quote XML entities (use these when editing XML directly):
| Character | Name | Entity |
|-----------|------|--------|
| `"` | Left double quote | `&#x201C;` |
| `"` | Right double quote | `&#x201D;` |
| `'` | Left single quote | `&#x2018;` |
| `'` | Right single quote | `&#x2019;` |

Whitespace preservation: `<a:t xml:space="preserve"> leading space</a:t>`

**Never use `xml.etree.ElementTree`** for parsing PPTX XML — it corrupts namespaces. Use `defusedxml.minidom` (safe + namespace-preserving) or `lxml.etree`.

---

## QA workflow

**Assume there are problems. Your job is to find them.**

```bash
# 1. Text QA
python -m markitdown output.pptx
python -m markitdown output.pptx | grep -iE "xxxx|lorem|todo|placeholder"

# 2. Convert to images
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide

# 3. Visual inspect (use a subagent with fresh eyes)
# Prompt: "Inspect these slides for overlapping elements, text overflow,
#          low contrast, empty areas, missing content, misaligned columns.
#          List all issues found."

# 4. Fix → re-render affected slides → repeat
```

Check for:
- Overlapping elements (text through shapes, stacked boxes)
- Text overflow or clipped at box boundaries
- Decorative elements sized for single-line titles that wrapped
- Elements too close (< 0.3") or touching the slide edge (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text or icons against background
- Leftover placeholder content

---

## Quality checklist

- [ ] Open in LibreOffice Impress — no corruption warnings
- [ ] All slides present and in correct order
- [ ] Title text correct on every slide
- [ ] Bullet levels rendered correctly
- [ ] Tables display with visible borders and correct cell content
- [ ] Images inline without distortion
- [ ] Charts render with correct data and legend
- [ ] Speaker notes visible in notes panel
- [ ] PDF export is readable with no missing glyphs
- [ ] `python scripts/validate_pptx.py output.pptx` exits 0

---

## Dependencies

```bash
# Python (required)
pip install python-pptx lxml defusedxml

# Text extraction
pip install "markitdown[pptx]"

# Thumbnail grid
pip install Pillow

# Node.js (PptxGenJS creation path)
npm install -g pptxgenjs

# LibreOffice (PDF/PNG export, thumbnail conversion)
sudo apt-get install -y libreoffice   # Ubuntu/Debian
brew install --cask libreoffice       # macOS

# pdftoppm for per-slide images
sudo apt-get install -y poppler-utils

# gcc (optional: AF_UNIX socket shim for sandboxed containers)
sudo apt-get install -y gcc
```

---

## References

- [python-pptx.md](references/python-pptx.md) — python-pptx API reference
- [ooxml-pptx.md](references/ooxml-pptx.md) — PresentationML OOXML anatomy
- [editing.md](editing.md) — Template-based editing workflow and XML pitfalls
- [pptxgenjs.md](pptxgenjs.md) — PptxGenJS creation reference
