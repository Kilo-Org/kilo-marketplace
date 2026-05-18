# OOXML Format Reference

ECMA-376 5th Ed. / ISO 29500 — WordprocessingML (`.docx`)

---

## Package structure

A `.docx` file is a ZIP archive. Mandatory parts:

```
[Content_Types].xml              # part type registry
_rels/.rels                      # package relationships
word/document.xml                # main document body
word/_rels/document.xml.rels     # document relationships
word/styles.xml                  # paragraph and character styles
word/settings.xml                # document settings (track-changes flag)
word/theme/theme1.xml            # theme fonts and colours
```

Optional parts the skill may add or modify:

```
word/comments.xml                # inline reviewer comments
word/footnotes.xml
word/endnotes.xml
word/numbering.xml               # list definitions
word/header1.xml / word/footer1.xml
```

---

## XML namespaces

```xml
xmlns:w  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
xmlns:r  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
xmlns:mc = "http://schemas.openxmlformats.org/markup-compatibility/2006"
xmlns:w14= "http://schemas.microsoft.com/office/word/2010/wordml"
```

All examples below assume `xmlns:w` is in scope.

---

## document.xml skeleton

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <!-- paragraphs and tables go here -->
    <w:sectPr>  <!-- always the last child of w:body -->
      <w:pgSz  w:w="12240" w:h="15840"/>   <!-- US Letter: 8.5 × 11 in -->
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"
               w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
```

---

## Paragraph `<w:p>`

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading1"/>
    <w:jc     w:val="center"/>
    <w:spacing w:before="240" w:after="120" w:line="276" w:lineRule="auto"/>
    <w:ind     w:left="720"  w:hanging="360"/>
    <w:numPr>
      <w:ilvl  w:val="0"/>
      <w:numId w:val="1"/>
    </w:numPr>
  </w:pPr>

  <w:r>
    <w:rPr>
      <w:b/>                              <!-- bold -->
      <w:i/>                              <!-- italic -->
      <w:u    w:val="single"/>            <!-- underline -->
      <w:sz   w:val="24"/>               <!-- 12 pt (half-points) -->
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
      <w:color  w:val="FF0000"/>
      <w:highlight w:val="yellow"/>
    </w:rPr>
    <w:t xml:space="preserve">Text content </w:t>
  </w:r>
</w:p>
```

**Unit note:** `w:sz` is in half-points; `w:spacing`, `w:ind`, `w:pgMar`,
`w:pgSz` are in twentieths of a point (twips). 1 inch = 1440 twips.

---

## Tracked changes

Enable globally in `word/settings.xml`:

```xml
<w:settings xmlns:w="...">
  <w:trackChanges/>
</w:settings>
```

### Insertion `<w:ins>`

```xml
<w:ins w:id="1" w:author="Claude" w:date="2025-01-15T09:00:00Z">
  <w:r>
    <w:rPr><!-- optional run properties --></w:rPr>
    <w:t>inserted text</w:t>
  </w:r>
</w:ins>
```

`<w:ins>` may also wrap `<w:p>` to mark a whole new paragraph as inserted.

### Deletion `<w:del>`

```xml
<w:del w:id="2" w:author="Claude" w:date="2025-01-15T09:00:00Z">
  <w:r>
    <w:rPr><!-- optional --></w:rPr>
    <w:delText xml:space="preserve">deleted text</w:delText>
  </w:r>
</w:del>
```

Critical: inside `<w:del>`, use `<w:delText>` (not `<w:t>`).

### Run-property change `<w:rPrChange>`

```xml
<w:r>
  <w:rPr>
    <w:b/>                       <!-- new: bold -->
    <w:rPrChange w:id="3" w:author="Claude" w:date="2025-01-15T09:00:00Z">
      <w:rPr/>                   <!-- original: not bold -->
    </w:rPrChange>
  </w:rPr>
  <w:t>text with format change</w:t>
</w:r>
```

### Paragraph-property change `<w:pPrChange>`

```xml
<w:pPr>
  <w:jc w:val="center"/>        <!-- new alignment -->
  <w:pPrChange w:id="4" w:author="Claude" w:date="2025-01-15T09:00:00Z">
    <w:pPr>
      <w:jc w:val="left"/>      <!-- original alignment -->
    </w:pPr>
  </w:pPrChange>
</w:pPr>
```

**Attribute rules:**
- `w:id` — unique integer across all revision marks in the document
- `w:author` — reviewer display name (string)
- `w:date` — ISO 8601 UTC, e.g. `2025-01-15T09:00:00Z`

---

## Comments

### word/comments.xml

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:comment w:id="1" w:author="Claude" w:date="2025-01-15T09:00:00Z" w:initials="C">
    <w:p>
      <w:pPr><w:pStyle w:val="CommentText"/></w:pPr>
      <w:r>
        <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
        <w:annotationRef/>
      </w:r>
      <w:r><w:t>This needs revision.</w:t></w:r>
    </w:p>
  </w:comment>
</w:comments>
```

### Anchoring in document.xml

```xml
<w:p>
  <w:commentRangeStart w:id="1"/>
  <w:r><w:t>annotated text</w:t></w:r>
  <w:commentRangeEnd w:id="1"/>
  <w:r>
    <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
    <w:commentReference w:id="1"/>
  </w:r>
</w:p>
```

### Part registration

**[Content_Types].xml** — add:
```xml
<Override PartName="/word/comments.xml"
  ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
```

**word/_rels/document.xml.rels** — add:
```xml
<Relationship Id="rIdN"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
  Target="comments.xml"/>
```

---

## Tables

```xml
<w:tbl>
  <w:tblPr>
    <w:tblStyle w:val="TableGrid"/>
    <w:tblW w:w="9638" w:type="dxa"/>      <!-- full width in twips -->
    <w:tblBorders>
      <w:top    w:val="single" w:sz="4" w:color="auto"/>
      <w:left   w:val="single" w:sz="4" w:color="auto"/>
      <w:bottom w:val="single" w:sz="4" w:color="auto"/>
      <w:right  w:val="single" w:sz="4" w:color="auto"/>
      <w:insideH w:val="single" w:sz="4" w:color="auto"/>
      <w:insideV w:val="single" w:sz="4" w:color="auto"/>
    </w:tblBorders>
  </w:tblPr>
  <w:tblGrid>
    <w:gridCol w:w="4819"/>
    <w:gridCol w:w="4819"/>
  </w:tblGrid>

  <w:tr>
    <w:trPr><w:tblHeader/></w:trPr>    <!-- repeat as header -->
    <w:tc>
      <w:tcPr><w:tcW w:w="4819" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>Header A</w:t></w:r></w:p>
    </w:tc>
    <w:tc>
      <w:tcPr><w:tcW w:w="4819" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>Header B</w:t></w:r></w:p>
    </w:tc>
  </w:tr>
</w:tbl>
```

### Horizontal merge (column span)

```xml
<w:tcPr>
  <w:gridSpan w:val="3"/>     <!-- spans 3 columns -->
</w:tcPr>
```

### Vertical merge (row span)

```xml
<!-- First cell in the span -->
<w:tcPr><w:vMerge w:val="restart"/></w:tcPr>
<!-- Continuation cells (same column, subsequent rows) -->
<w:tcPr><w:vMerge/></w:tcPr>
```

---

## Bookmarks and cross-references

```xml
<!-- Define bookmark -->
<w:bookmarkStart w:id="0" w:name="intro"/>
  <w:r><w:t>Introduction</w:t></w:r>
<w:bookmarkEnd   w:id="0"/>

<!-- Internal hyperlink -->
<w:hyperlink w:anchor="intro">
  <w:r>
    <w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>
    <w:t>see Introduction</w:t>
  </w:r>
</w:hyperlink>

<!-- Page-number field (PAGEREF) -->
<w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText xml:space="preserve"> PAGEREF intro \h </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:t>1</w:t></w:r>    <!-- cached value; updated by Word/LO -->
<w:r><w:fldChar w:fldCharType="end"/></w:r>
```

---

## Table of Contents field

```xml
<w:p>
  <w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr>
  <w:r><w:t>Contents</w:t></w:r>
</w:p>
<w:p>
  <w:pPr><w:pStyle w:val="TOC1"/></w:pPr>
  <w:r><w:fldChar w:fldCharType="begin"/></w:r>
  <w:r><w:instrText xml:space="preserve"> TOC \o "1-3" \h \z \u </w:instrText></w:r>
  <w:r><w:fldChar w:fldCharType="separate"/></w:r>
  <!-- cached entries here -->
  <w:r><w:fldChar w:fldCharType="end"/></w:r>
</w:p>
```

Switches: `\o "1-3"` (heading levels), `\h` (hyperlinks), `\z` (hide tabs in web view),
`\u` (use outline levels).

---

## Round-trip editing pattern (Python)

```python
import zipfile, shutil
from lxml import etree

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

def edit_docx(src, dst, edit_fn):
    shutil.copy(src, dst)
    with zipfile.ZipFile(dst, 'r') as z:
        parts = {n: z.read(n) for n in z.namelist()}

    tree = etree.fromstring(parts['word/document.xml'])
    edit_fn(tree, NS)
    parts['word/document.xml'] = etree.tostring(
        tree, xml_declaration=True, encoding='UTF-8', standalone=True
    )

    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
```

Useful XPath examples:
```python
# All paragraphs
doc.findall('.//w:p', NS)

# All tracked insertions
doc.findall('.//w:ins', NS)

# All comments
comments_root.findall('.//w:comment', NS)

# Paragraphs with Heading1 style
[p for p in doc.findall('.//w:p', NS)
 if p.find('w:pPr/w:pStyle[@w:val="Heading1"]', NS) is not None]
```

---

## [Content_Types].xml minimal template

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/theme/theme1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <!-- Add when comments are present: -->
  <Override PartName="/word/comments.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>
```
