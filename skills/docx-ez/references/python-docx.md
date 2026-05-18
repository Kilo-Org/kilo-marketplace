# python-docx API Reference

Version: 1.x — check with `python -c "import docx; print(docx.__version__)"`
Docs: https://python-docx.readthedocs.io

## Installation

```bash
pip install python-docx
```

---

## Document

```python
from docx import Document

# New document
doc = Document()

# Open existing
doc = Document('existing.docx')

# Save
doc.save('output.docx')
```

### Core properties

```python
props = doc.core_properties
props.title    = 'My Document'
props.author   = 'Claude'
props.subject  = 'Report'
props.keywords = 'docx, report'
```

---

## Sections (page setup)

```python
from docx.shared import Cm, Inches

for section in doc.sections:
    section.page_width    = Cm(21.59)  # 8.5 in — US Letter
    section.page_height   = Cm(27.94)  # 11 in
    section.top_margin    = Cm(2.54)   # 1 in
    section.bottom_margin = Cm(2.54)
    section.left_margin   = Cm(2.54)
    section.right_margin  = Cm(2.54)
    section.header_distance = Cm(1.27)
    section.footer_distance = Cm(1.27)
```

### Orientation

```python
from docx.enum.section import WD_ORIENT

section.orientation = WD_ORIENT.LANDSCAPE
# swap dimensions for landscape:
w, h = section.page_width, section.page_height
section.page_width, section.page_height = h, w
```

---

## Paragraphs

```python
p = doc.add_paragraph('Hello world')        # plain text
p = doc.add_paragraph(style='List Bullet')  # with style
p = doc.add_paragraph()                     # empty, add runs manually
```

### Paragraph formatting

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

pf = p.paragraph_format
pf.alignment       = WD_ALIGN_PARAGRAPH.CENTER  # LEFT, CENTER, RIGHT, JUSTIFY
pf.space_before    = Pt(12)
pf.space_after     = Pt(6)
pf.line_spacing    = Pt(18)       # or a float for multiple: 1.5
pf.left_indent     = Cm(1)
pf.right_indent    = Cm(1)
pf.first_line_indent = Cm(0.5)
pf.keep_together   = True
pf.keep_with_next  = True
pf.page_break_before = True
```

---

## Runs (inline text)

```python
run = p.add_run('Bold italic text')
run.bold      = True
run.italic    = True
run.underline = True
run.strike    = True         # strikethrough (actually: run.font.strike)
```

### Run font properties

```python
from docx.shared import Pt, RGBColor

font = run.font
font.name      = 'Arial'
font.size      = Pt(12)
font.color.rgb = RGBColor(0xFF, 0x00, 0x00)  # red
font.bold      = True
font.italic    = True
font.underline = True
font.strike    = True
font.superscript = True
font.subscript   = True
font.highlight_color = WD_COLOR_INDEX.YELLOW  # from docx.enum.text
```

---

## Headings

```python
doc.add_heading('Document Title', level=0)  # Title style
doc.add_heading('Chapter 1',      level=1)  # Heading 1
doc.add_heading('Section 1.1',    level=2)  # Heading 2
# levels 0-9 map to Title, Heading 1 … Heading 9
```

To customise font on a heading:
```python
h = doc.add_heading('My Heading', level=1)
for run in h.runs:
    run.font.name = 'Arial'
```

---

## Tables

```python
table = doc.add_table(rows=3, cols=4)
table.style = 'Table Grid'   # or 'Light Shading', 'Medium Grid 1', etc.

# Access cells
cell = table.cell(0, 0)      # (row_index, col_index)
cell.text = 'Header'

# Iterate
for row in table.rows:
    for cell in row.cells:
        print(cell.text)
```

### Cell formatting

```python
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

# Background shading
tcPr = cell._tc.get_or_add_tcPr()
shd  = OxmlElement('w:shd')
shd.set(qn('w:fill'), 'EEEEEE')   # hex colour
shd.set(qn('w:val'),  'clear')
tcPr.append(shd)
```

### Merge cells

```python
# Horizontal merge (columns 0-2 in row 0)
table.cell(0, 0).merge(table.cell(0, 2))

# Vertical merge (rows 1-3 in column 0)
table.cell(1, 0).merge(table.cell(3, 0))
```

### Column widths

```python
from docx.shared import Cm

table.columns[0].width = Cm(6)
table.columns[1].width = Cm(10)
```

---

## Images

```python
from docx.shared import Cm, Inches

# Inline — width only (aspect ratio preserved)
doc.add_picture('photo.png', width=Inches(4))

# Inline — explicit dimensions
doc.add_picture('photo.png', width=Cm(10), height=Cm(6))

# After a specific paragraph
from docx.oxml.ns import qn
last_para = doc.paragraphs[-1]
run = last_para.add_run()
run.add_picture('logo.png', width=Cm(3))
```

Supported formats: PNG, JPEG, GIF, TIFF, BMP, WMF.

---

## Styles

```python
# List available styles
for s in doc.styles:
    print(s.name, s.type)

# Apply a named style
p = doc.add_paragraph('Text', style='Intense Quote')

# Modify an existing style
style      = doc.styles['Normal']
style.font.name = 'Arial'
style.font.size = Pt(12)

# Create a new paragraph style
from docx.enum.style import WD_STYLE_TYPE
my_style = doc.styles.add_style('MyBody', WD_STYLE_TYPE.PARAGRAPH)
my_style.base_style    = doc.styles['Normal']
my_style.font.name     = 'Calibri'
my_style.font.size     = Pt(11)
my_style.paragraph_format.space_after = Pt(8)
```

---

## Headers and footers

```python
from docx.shared import Pt

section = doc.sections[0]

# Header
header = section.header
hp     = header.paragraphs[0]
hp.text = 'Confidential'
hp.style = doc.styles['Header']

# Footer with page number
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

footer = section.footer
fp     = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run    = fp.add_run()
fldChar1 = OxmlElement('w:fldChar')
fldChar1.set(qn('w:fldCharType'), 'begin')
instrText = OxmlElement('w:instrText')
instrText.text = ' PAGE '
fldChar2 = OxmlElement('w:fldChar')
fldChar2.set(qn('w:fldCharType'), 'end')
run._r.append(fldChar1)
run._r.append(instrText)
run._r.append(fldChar2)
```

---

## TOC field (raw XML)

python-docx has no native TOC API; insert the field directly:

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_toc(doc, title='Table of Contents'):
    # Heading paragraph
    doc.add_paragraph(title, style='TOC Heading')
    # Field paragraph
    p = doc.add_paragraph()
    p._p.clear()
    def fld_run(*children):
        r = OxmlElement('w:r')
        for c in children: r.append(c)
        return r
    def fld_char(kind):
        fc = OxmlElement('w:fldChar')
        fc.set(qn('w:fldCharType'), kind)
        return fc
    instr = OxmlElement('w:instrText')
    instr.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    p._p.append(fld_run(fld_char('begin')))
    p._p.append(fld_run(instr))
    p._p.append(fld_run(fld_char('separate')))
    p._p.append(fld_run(fld_char('end')))
```

Update the TOC: open in Word (Ctrl+A, F9) or LibreOffice (Tools > Update Fields).

---

## Iterating document content

```python
# All paragraphs (top-level only — misses table cells)
for p in doc.paragraphs:
    print(p.style.name, p.text)

# All paragraphs including table cells
from docx.oxml.ns import qn
for p in doc.element.body.iter(qn('w:p')):
    from docx.text.paragraph import Paragraph
    para = Paragraph(p, doc)
    print(para.text)

# All tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text)
```

---

## Template / mail-merge pattern

```python
def fill_template(template_path: str, data: dict, output_path: str) -> None:
    """Replace {{KEY}} placeholders throughout the document."""
    doc = Document(template_path)
    # Paragraphs
    for p in doc.paragraphs:
        for key, value in data.items():
            if f'{{{{key}}}}' in p.text:
                for run in p.runs:
                    run.text = run.text.replace(f'{{{{key}}}}', str(value))
    # Table cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for key, value in data.items():
                        if f'{{{{key}}}}' in p.text:
                            for run in p.runs:
                                run.text = run.text.replace(
                                    f'{{{{key}}}}', str(value)
                                )
    doc.save(output_path)

# Example
fill_template(
    'contract_template.docx',
    {'CLIENT_NAME': 'Acme Corp', 'DATE': '2025-01-15', 'AMOUNT': '$50,000'},
    'contract_acme.docx',
)
```

---

## Limitations

- No native tracked-changes API — use `scripts/edit_docx.py` (lxml) for `<w:ins>`/`<w:del>`
- No native comments API — use `scripts/edit_docx.py` (lxml) for `<w:comment>`
- No native TOC API — use raw XML field insertion (see above)
- No macro/VBA execution
- Limited SmartArt and Chart support
- `.doc` (legacy binary) format: must convert to `.docx` first via LibreOffice:
  ```bash
  soffice --headless --convert-to docx legacy.doc
  ```
