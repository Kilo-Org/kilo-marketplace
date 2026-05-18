---
name: docx-ez
description: Create, edit, and export Microsoft Word .docx documents. Use when tasks involve new Word documents (US Letter, Arial font, 1-inch margins), editing existing .docx files via OOXML XML manipulation, tracked changes / redlining, inline comments, tables, structured headings with auto-generated TOC, internal cross-references and bookmarks, template / mail-merge population, image embedding, and LibreOffice headless PDF export. Activate when the user mentions Word, .docx, document editing, redlining, tracked changes, or needs a formatted report.
license: CC0-1.0
compatibility: Python 3.9+ with python-docx and lxml (all paths); Node.js 18+ with npm (docx.js creation path, optional); LibreOffice 7.4+ (PDF export). Linux, macOS, Windows.
metadata:
  category: productivity
  author: shauneshraghi
  source:
    repository: https://github.com/shauneshraghi/skills
    path: docx-ez
    license_path: LICENSE.txt
---

# docx Skill

## Toolchain at a glance

| Task | Tool | Script |
|------|------|--------|
| Create new .docx (Python) | python-docx | `scripts/create_docx.py` |
| Create new .docx (Node.js) | docx.js | `scripts/create_docx.js` |
| Edit existing .docx | lxml direct XML | `scripts/edit_docx.py` |
| Accept / reject tracked changes | lxml | `scripts/accept_changes.py` |
| Manage comments | lxml | `scripts/comment.py` |
| Template / mail-merge | python-docx | `scripts/create_docx.py` or inline |
| Unpack DOCX to editable XML | lxml | `scripts/office/unpack.py` |
| Pack XML back to DOCX | lxml | `scripts/office/pack.py` |
| LibreOffice (sandbox-safe) | C LD_PRELOAD shim | `scripts/office/soffice.py` |
| PDF export | LibreOffice headless | `scripts/export_pdf.sh` |
| Validate round-trip | Python zipfile | `scripts/validate_docx.py` |
| Benchmark / quality check | lxml | `scripts/benchmark.py` |

**Default for new documents:** use `create_docx.py` (Python only, no extra runtime
needed). Use `create_docx.js` when richer TOC field support or bookmark/
cross-reference generation is required.

**Limitation — `.doc` binary format:** python-docx cannot read legacy `.doc` files.
Convert first with LibreOffice:
```bash
soffice --headless --convert-to docx legacy.doc
```

---

## Path A — Create a new document (Python)

```bash
pip install python-docx

# Sample document (all features)
python scripts/create_docx.py output.docx

# From a JSON spec
python scripts/create_docx.py output.docx --spec spec.json
```

### Spec JSON format

```json
{
  "title": "Document Title",
  "author": "Claude",
  "sections": [
    {
      "children": [
        { "type": "heading",   "level": 1, "text": "Introduction" },
        { "type": "paragraph", "text": "Body.", "bold": false, "italic": false,
          "align": "left", "color": "#000000" },
        { "type": "toc" },
        { "type": "table",     "rows": [["A", "B"], ["1", "2"]] },
        { "type": "image",     "path": "logo.png",
          "width_cm": 8, "height_cm": 4 },
        { "type": "page_break" }
      ]
    }
  ]
}
```

Supported `type` values: `heading`, `paragraph`, `toc`, `table`, `image`,
`page_break`.

---

## Path B — Create a new document (Node.js)

Use when you need native bookmark/cross-reference generation or richer TOC API.

```bash
npm install docx
node scripts/create_docx.js output.docx
node scripts/create_docx.js output.docx --spec spec.json
```

Node spec supports additional types: `bookmark`, `xref`.

---

## Path C — Edit an existing document

```bash
pip install python-docx lxml

# Search-replace text
python scripts/edit_docx.py in.docx out.docx --replace "old" "new"

# Insert a new paragraph after a match (tracked change)
python scripts/edit_docx.py in.docx out.docx \
  --insert-after "Section 1" "New paragraph" --author "Claude"

# Mark text as a tracked deletion
python scripts/edit_docx.py in.docx out.docx \
  --delete "remove this" --author "Claude"

# Add an inline comment
python scripts/edit_docx.py in.docx out.docx \
  --comment "target phrase" "Please revise." --author "Claude"
```

---

## Path D — Unpack → Edit XML → Pack (OOXML direct editing)

For structural edits to an existing document (tracked changes, comment injection,
XML-level formatting), work directly on the OOXML XML rather than through python-docx.

### Step 1: Unpack
```bash
python scripts/office/unpack.py document.docx unpacked/
```
Extracts all ZIP entries. XML files are pretty-printed with lxml; binary files
(images, fonts) are copied as-is. Smart quotes are encoded as XML entities so
plain-text editors don't corrupt them.

### Step 2: Edit XML
Edit files inside `unpacked/word/`. Key files:
- `word/document.xml` — body text, paragraphs, runs, tracked changes
- `word/comments.xml` — comment bodies
- `word/styles.xml` — named styles (Heading 1, Normal, …)
- `word/settings.xml` — document settings, trackRevisions flag

**Use the Edit tool** for content changes — not sed/awk/Python scripts.

**Always use `xml:space="preserve"`** on `<w:t>` with leading or trailing spaces:
```xml
<w:t xml:space="preserve"> leading space</w:t>
```

**Smart quotes:** Use XML entities for typographic quotes in new content:

| Character | Entity |
|-----------|--------|
| `"` (left double)  | `&#x201C;` |
| `"` (right double) | `&#x201D;` |
| `'` (left single)  | `&#x2018;` |
| `'` (right single / apostrophe) | `&#x2019;` |

**Author name:** Use `"Claude"` for tracked changes and comments unless the user specifies otherwise.

### Step 3: Pack
```bash
python scripts/office/pack.py unpacked/ output.docx --original document.docx
```
Condenses XML whitespace, decodes smart-quote entities back to Unicode, and
repacks as a ZIP. `--original` fills in any binary parts missing from the
unpacked directory.

---

## Accept / reject tracked changes

```bash
# Accept all tracked changes (keep insertions, drop deletions)
python scripts/accept_changes.py in.docx out.docx

# Reject all (drop insertions, restore deletions)
python scripts/accept_changes.py in.docx out.docx --reject
```

Also handles `<w:rPrChange>`, `<w:pPrChange>`, `<w:sectPrChange>` (format-only
tracked changes) by stripping the change markup while keeping current formatting.

---

## Manage comments

```bash
# List all comments (id, author, date, text)
python scripts/comment.py document.docx list

# Add a comment anchored to paragraph 0
python scripts/comment.py in.docx out.docx add "Review this section" \
  --author "Claude" --start 0 --end 0

# Delete comment by id
python scripts/comment.py in.docx out.docx delete 1
```

---

## Template / mail-merge

The fastest approach for populating a template is direct placeholder replacement
using python-docx:

```python
from docx import Document

def fill_template(template_path, data, output_path):
    doc = Document(template_path)
    for p in doc.paragraphs:
        for key, val in data.items():
            for run in p.runs:
                run.text = run.text.replace(f'{{{{key}}}}', str(val))
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for key, val in data.items():
                        for run in p.runs:
                            run.text = run.text.replace(f'{{{{key}}}}', str(val))
    doc.save(output_path)

fill_template('template.docx',
              {'CLIENT': 'Acme', 'DATE': '2025-01-15'},
              'output.docx')
```

See [references/python-docx.md](references/python-docx.md) for the full pattern.

---

## Tracked changes

OOXML represents tracked changes as `<w:ins>` and `<w:del>` elements:

```xml
<!-- Insertion -->
<w:ins w:id="1" w:author="Claude" w:date="2025-01-15T09:00:00Z">
  <w:r><w:t>inserted text</w:t></w:r>
</w:ins>

<!-- Deletion (use w:delText, not w:t) -->
<w:del w:id="2" w:author="Claude" w:date="2025-01-15T09:00:00Z">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
```

For format-only changes use `<w:rPrChange>` inside `<w:rPr>`.

---

## Comments

```xml
<!-- document.xml -->
<w:commentRangeStart w:id="1"/>
<w:r><w:t>annotated text</w:t></w:r>
<w:commentRangeEnd w:id="1"/>
<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="1"/>
</w:r>

<!-- word/comments.xml -->
<w:comment w:id="1" w:author="Claude" w:date="2025-01-15T09:00:00Z" w:initials="C">
  <w:p><w:r><w:t>Comment body.</w:t></w:r></w:p>
</w:comment>
```

---

## Tables

Python (python-docx):
```python
table = doc.add_table(rows=3, cols=4)
table.style = 'Table Grid'
table.cell(0, 0).text = 'Header'
# Merge: table.cell(0,0).merge(table.cell(0,2))
```

docx.js: see [references/docx-js.md](references/docx-js.md).

---

## Headings and TOC

Python:
```python
doc.add_heading('Chapter 1', level=1)
doc.add_heading('Section 1.1', level=2)
# Insert TOC field (updates when opened):
from scripts.create_docx import add_toc_stub
add_toc_stub(doc)
```

docx.js:
```js
new Paragraph({ heading: HeadingLevel.HEADING_1, text: "Chapter 1" })
new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-3" })
```

---

## Cross-references and bookmarks

docx.js (full support):
```js
new BookmarkStart({ id: "sec1", name: "Section 1" })
new InternalHyperlink({ anchor: "sec1", children: [...] })
```

Raw OOXML:
```xml
<w:bookmarkStart w:id="0" w:name="sec1"/>
<w:bookmarkEnd   w:id="0"/>
<w:hyperlink w:anchor="sec1">...</w:hyperlink>
```

---

## Images

Python:
```python
from docx.shared import Cm
doc.add_picture('photo.png', width=Cm(10))
```

docx.js:
```js
new ImageRun({ type: 'png', data: fs.readFileSync('photo.png'),
               transformation: { width: 400, height: 200 } })
```

---

## PDF export

```bash
bash scripts/export_pdf.sh document.docx ./output/
# or:
soffice --headless --convert-to pdf document.docx --outdir ./output/
```

Install LibreOffice if missing:
```bash
sudo apt-get install -y libreoffice   # Ubuntu/Debian
brew install --cask libreoffice       # macOS
```

---

## Round-trip validation

```bash
python scripts/validate_docx.py document.docx
```

Checks ZIP integrity, required OOXML parts, all XML parses cleanly. Exit 0 = clean.

---

## Lists

**Never use unicode bullet characters (•, –, ▪).** They create double-bullets when combined with list paragraph styles. Use list styles instead.

Python (python-docx):
```python
doc.add_paragraph('First item',  style='List Bullet')
doc.add_paragraph('Second item', style='List Bullet')
doc.add_paragraph('Step one',    style='List Number')
```

docx.js:
```js
new Paragraph({
  text: "First item",
  numbering: { reference: "my-bullet-list", level: 0 },
})
```

Raw OOXML — let list formatting inherit from the `numId`/`ilvl` numbering definition;
never embed a `•` character directly in `<w:t>`.

---

## Hyperlinks

Python:
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_hyperlink(paragraph, url, text):
    part = paragraph.part
    r_id = part.relate_to(url,
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
        is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    run = OxmlElement('w:r')
    rpr = OxmlElement('w:rPr')
    style = OxmlElement('w:rStyle')
    style.set(qn('w:val'), 'Hyperlink')
    rpr.append(style)
    run.append(rpr)
    t = OxmlElement('w:t')
    t.text = text
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)
```

docx.js:
```js
new ExternalHyperlink({
  link: "https://example.com",
  children: [new TextRun({ text: "Link text", style: "Hyperlink" })],
})
```

---

## Footnotes

Python — footnotes require OOXML manipulation (python-docx has no direct API):
```python
# word/footnotes.xml — add a footnote body
# word/document.xml — add the reference run
```

docx.js:
```js
new Paragraph({
  children: [
    new TextRun("Main text"),
    new FootnoteReferenceRun({ id: 1 }),
  ],
})
// Define footnote body in document footnotes array
```

---

## Headers and footers

Python:
```python
section = doc.sections[0]
header = section.header
header.paragraphs[0].text = "Confidential"

footer = section.footer
footer.paragraphs[0].text = "Page "
# Add page number field via OxmlElement for auto-numbering
```

docx.js:
```js
new Header({ children: [new Paragraph("Confidential")] })
new Footer({ children: [new Paragraph({ children: [new TextRun("Page "), new PageNumber()] })] })
```

---

## XML reference

### Element order in `<w:pPr>`
Must follow schema order: `<w:pStyle>` → `<w:numPr>` → `<w:spacing>` → `<w:ind>` → `<w:jc>` → `<w:rPr>` (last).

### RSIDs
`w:rsidR`, `w:rsidRPr`, `w:rsidDefault` must be 8-digit hex (e.g. `00AB1234`). Omit
rather than invent; Word/LibreOffice regenerates them on next open.

### Tracked changes — minimal edits

Only mark what changes. When changing "30 days" to "60 days":
```xml
<w:r><w:t xml:space="preserve">The term is </w:t></w:r>
<w:del w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>30</w:delText></w:r>
</w:del>
<w:ins w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:t>60</w:t></w:r>
</w:ins>
<w:r><w:t xml:space="preserve"> days.</w:t></w:r>
```

Inside `<w:del>`: use `<w:delText>` (not `<w:t>`).

### Deleting entire paragraphs

Mark the paragraph mark deleted so it merges with the next paragraph on accept:
```xml
<w:p>
  <w:pPr>
    <w:rPr>
      <w:del w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z"/>
    </w:rPr>
  </w:pPr>
  <w:del w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
    <w:r><w:delText>Entire paragraph content.</w:delText></w:r>
  </w:del>
</w:p>
```

Without the `<w:del/>` in `<w:pPr><w:rPr>`, accepting leaves a ghost empty paragraph.

### Critical docx.js rules

- **Never mix `children` and `text`** on the same `Paragraph` — `text` is ignored when `children` is set.
- **`TextRun` bold** via `{ bold: true }` option, not a `<b>` wrapper.
- **Numbered lists** need `numbering: { reference, level }` on every `Paragraph` in the list; cannot be set once for a group.
- **TOC** requires a field instruction run; call `updateFields: true` in document settings or the reader must refresh manually.

---

## Quality checklist

- [ ] `python scripts/validate_docx.py output.docx` exits 0
- [ ] `python scripts/benchmark.py` passes (no --poi required)
- [ ] Open in LibreOffice Writer — no corruption warnings
- [ ] All headings appear in the Document Navigator
- [ ] TOC entries match headings (update fields: Ctrl+A → F9)
- [ ] Tracked-changes panel shows insertions/deletions with correct author/date
- [ ] Accepting changes leaves no ghost empty paragraphs
- [ ] Comments appear in margin with correct author, date, and body text
- [ ] Lists use paragraph styles, not unicode bullet characters
- [ ] Tables render with visible borders, correct widths, and merged cells
- [ ] Images display inline without distortion
- [ ] Cross-references navigate to the correct bookmark target
- [ ] PDF export is readable with no missing glyphs
- [ ] Unpack → edit → pack round-trip: `validate_docx.py` still exits 0

---

## Dependencies

```bash
# Python (all paths)
pip install python-docx lxml defusedxml

# Node.js (optional creation path)
npm install docx

# System (PDF export + validation)
sudo apt-get install -y libreoffice gcc   # Ubuntu/Debian
brew install --cask libreoffice          # macOS
```

The `gcc` dependency is needed only if the LibreOffice AF_UNIX socket shim
(`scripts/office/soffice.py`) must be compiled for sandboxed containers.

---

## References

- [python-docx.md](references/python-docx.md) — python-docx API reference
- [docx-js.md](references/docx-js.md) — docx.js v9 API reference
- [ooxml.md](references/ooxml.md) — OOXML/ECMA-376 XML anatomy and patterns
- [poi-corpus.md](references/poi-corpus.md) — Apache POI test corpus benchmark guide
