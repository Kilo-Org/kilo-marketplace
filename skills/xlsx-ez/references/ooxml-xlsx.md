# OOXML SpreadsheetML Reference

ECMA-376 Part 1, Chapter 18: SpreadsheetML.
An `.xlsx` file is a ZIP archive containing XML parts conforming to the
Open Packaging Convention (OPC, ECMA-376 Part 2).

Spec PDFs: https://ecma-international.org/publications-and-standards/standards/ecma-376/

---

## Package Structure

```
workbook.xlsx (ZIP)
├── [Content_Types].xml            # part MIME types
├── _rels/
│   └── .rels                      # package relationship → workbook
├── xl/
│   ├── workbook.xml               # workbook: sheet list, defined names
│   ├── styles.xml                 # fonts, fills, borders, cell xfs
│   ├── sharedStrings.xml          # shared string table (optional)
│   ├── calcChain.xml              # formula calculation chain (optional)
│   ├── _rels/
│   │   └── workbook.xml.rels      # workbook → sheets, sharedStrings, styles
│   ├── worksheets/
│   │   ├── sheet1.xml
│   │   ├── sheet2.xml
│   │   └── _rels/
│   │       └── sheet1.xml.rels    # sheet → drawings, tables, comments
│   ├── drawings/
│   │   └── drawing1.xml           # chart/image anchors (SpreadsheetDrawingML)
│   ├── charts/
│   │   └── chart1.xml             # DrawingML chart
│   ├── tables/
│   │   └── table1.xml             # ListObject / Table
│   ├── comments1.xml              # cell comments
│   └── theme/
│       └── theme1.xml             # Office theme colors/fonts
└── docProps/
    ├── app.xml
    └── core.xml
```

### [Content_Types].xml

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"
    ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>
```

---

## Namespaces

| Prefix | URI |
|--------|-----|
| `xmlns` / `xmlns:x` | `http://schemas.openxmlformats.org/spreadsheetml/2006/main` |
| `xmlns:r` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships` |
| `xmlns:mc` | `http://schemas.openxmlformats.org/markup-compatibility/2006` |
| `xmlns:xdr` | `http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing` |
| `xmlns:a` | `http://schemas.openxmlformats.org/drawingml/2006/main` |
| `xmlns:c` | `http://schemas.openxmlformats.org/drawingml/2006/chart` |

---

## workbook.xml

```xml
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <fileVersion appName="xl" lastEdited="7" lowestEdited="7" rupBuild="10000"/>
  <workbookPr defaultThemeVersion="166925"/>
  <bookViews>
    <workbookView xWindow="0" yWindow="0" windowWidth="14400" windowHeight="8000"/>
  </bookViews>
  <sheets>
    <sheet name="Summary" sheetId="1" r:id="rId1"/>
    <sheet name="Detail"  sheetId="2" r:id="rId2" state="hidden"/>
  </sheets>
  <definedNames>
    <definedName name="TaxRate">Assumptions!$B$3</definedName>
    <definedName name="LocalName" localSheetId="0">Sheet1!$A$1</definedName>
  </definedNames>
  <calcPr calcId="191028" fullCalcOnLoad="1"/>
</workbook>
```

`<calcPr fullCalcOnLoad="1"/>` tells Excel/LibreOffice to recalculate all
formulas on load — important when writing formula-heavy workbooks.

---

## worksheet.xml (Sheet)

```xml
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetPr>
    <tabColor rgb="FF4472C4"/>
  </sheetPr>
  <dimension ref="A1:E20"/>
  <sheetViews>
    <sheetView workbookViewId="0" showGridLines="1" showRowColHeaders="1">
      <pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>
      <selection pane="bottomLeft" activeCell="B2" sqref="B2"/>
    </sheetView>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="15" defaultColWidth="8"/>
  <cols>
    <col min="1" max="1" width="20" customWidth="1"/>
    <col min="2" max="4" width="12" customWidth="1"/>
  </cols>
  <sheetData>
    <!-- rows and cells here -->
  </sheetData>
  <mergeCells count="1">
    <mergeCell ref="A1:D1"/>
  </mergeCells>
  <conditionalFormatting sqref="B2:B100">
    <!-- rules here -->
  </conditionalFormatting>
  <dataValidations count="1">
    <!-- validations here -->
  </dataValidations>
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75"
               header="0.3" footer="0.3"/>
  <pageSetup paperSize="1" orientation="portrait" fitToPage="1"
             fitToWidth="1" fitToHeight="0"/>
  <tableParts count="1">
    <tablePart r:id="rId1"/>
  </tableParts>
</worksheet>
```

### Freeze panes — `<pane>` element

| Attribute | Meaning |
|-----------|---------|
| `xSplit`  | Number of columns frozen (from left) |
| `ySplit`  | Number of rows frozen (from top) |
| `topLeftCell` | First visible cell in unfrozen pane |
| `state`   | "frozen" or "split" |
| `activePane` | "topLeft" \| "topRight" \| "bottomLeft" \| "bottomRight" |

---

## Row and Cell elements

```xml
<sheetData>
  <!-- r = row number (1-indexed); ht = height in points; customHeight="1" to apply -->
  <row r="1" ht="20" customHeight="1">
    <!-- r = cell address; s = style index (into CellXfs); t = cell type -->
    <c r="A1" s="1" t="s">      <!-- t="s" = shared string -->
      <v>0</v>                   <!-- shared string index -->
    </c>
    <c r="B1" s="2">            <!-- no t attr = numeric -->
      <v>42</v>
    </c>
    <c r="C1" s="3" t="str">   <!-- t="str" = inline computed string -->
      <f>CONCATENATE("A","B")</f>
      <v>AB</v>
    </c>
    <c r="D1" t="inlineStr">   <!-- inline string (no sharedStrings) -->
      <is><t>Hello</t></is>
    </c>
    <c r="E1" t="b">           <!-- boolean -->
      <v>1</v>
    </c>
    <c r="F1" t="e">           <!-- error -->
      <v>#DIV/0!</v>
    </c>
  </row>
  <row r="2">
    <c r="A2" s="1">
      <f>SUM(B2:B10)</f>        <!-- formula; no t means result is numeric -->
      <v>0</v>                  <!-- cached result (may be stale until recalc) -->
    </c>
  </row>
</sheetData>
```

### Cell type (`t`) attribute

| Value | Meaning |
|-------|---------|
| (absent) | Numeric |
| `n` | Numeric (explicit) |
| `s` | Shared string (value is index into sharedStrings.xml) |
| `str` | Formula result is a string |
| `inlineStr` | Inline string (uses `<is><t>` child, not `<v>`) |
| `b` | Boolean (0 or 1) |
| `e` | Error string (e.g. `#DIV/0!`) |
| `d` | ISO 8601 date string (rarely used) |

---

## sharedStrings.xml

Strings stored in a deduplicated table referenced by index.

```xml
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
     count="4" uniqueCount="3">
  <si><t>Revenue</t></si>                         <!-- index 0 -->
  <si><t>Cost</t></si>                             <!-- index 1 -->
  <si>                                             <!-- index 2: rich text -->
    <r><rPr><b/><sz val="12"/></rPr><t>Bold</t></r>
    <r><t xml:space="preserve"> normal</t></r>
  </si>
</sst>
```

---

## styles.xml

Styles are stored as indexed arrays.  A cell's `s` attribute is an index
into `<cellXfs>` (CellXf), which references indices into fonts, fills, etc.

```xml
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">

  <!-- 1. Fonts (indexed) -->
  <fonts count="2">
    <font>                        <!-- index 0: default -->
      <sz val="10"/>
      <name val="Arial"/>
    </font>
    <font>                        <!-- index 1: bold header -->
      <b/>
      <sz val="11"/>
      <name val="Arial"/>
      <color rgb="FFFFFFFF"/>
    </font>
  </fonts>

  <!-- 2. Fills (indices 0 and 1 are reserved for none/gray125) -->
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill>                        <!-- index 2: solid blue -->
      <patternFill patternType="solid">
        <fgColor rgb="FF4472C4"/>
      </patternFill>
    </fill>
  </fills>

  <!-- 3. Borders (index 0 = no borders) -->
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>                      <!-- index 1: thin all-around -->
      <left style="thin"/>
      <right style="thin"/>
      <top style="thin"/>
      <bottom style="thin"/>
      <diagonal/>
    </border>
  </borders>

  <!-- 4. Cell Style Xfs (base formats) -->
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>

  <!-- 5. Cell Xfs (applied formats; s= attribute on cells) -->
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>  <!-- 0: default -->
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0"    <!-- 1: bold + blue -->
        applyFont="1" applyFill="1"/>
    <xf numFmtId="7" fontId="0" fillId="0" borderId="0" xfId="0"    <!-- 2: currency -->
        applyNumberFormat="1"/>
  </cellXfs>

  <!-- 6. Number Formats (custom; ids 0-163 are built-in) -->
  <numFmts count="1">
    <numFmt numFmtId="164" formatCode="$#,##0_);[Red]($#,##0)"/>
  </numFmts>

</styleSheet>
```

### Built-in numFmtId values (selection)

| ID | Format |
|----|--------|
| 0  | General |
| 1  | 0 |
| 2  | 0.00 |
| 3  | #,##0 |
| 4  | #,##0.00 |
| 9  | 0% |
| 10 | 0.00% |
| 11 | 0.00E+00 |
| 14 | m/d/yyyy |
| 49 | @ (text) |

Custom numFmtIds must be ≥ 164.

---

## Tables (xl/tables/table1.xml)

```xml
<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
       id="1" name="SalesData" displayName="SalesData" ref="A1:D50">
  <autoFilter ref="A1:D50"/>
  <tableColumns count="4">
    <tableColumn id="1" name="Month"/>
    <tableColumn id="2" name="Revenue"/>
    <tableColumn id="3" name="Cost"/>
    <tableColumn id="4" name="Profit"/>
  </tableColumns>
  <tableStyleInfo name="TableStyleMedium9"
                  showFirstColumn="0" showLastColumn="0"
                  showRowStripes="1" showColumnStripes="0"/>
</table>
```

The sheet references this via `<tablePart r:id="rId1"/>` and
`xl/worksheets/_rels/sheet1.xml.rels` maps rId1 → `../tables/table1.xml`.

---

## Conditional Formatting

```xml
<conditionalFormatting sqref="B2:B100">
  <!-- Color scale -->
  <cfRule type="colorScale" priority="1">
    <colorScale>
      <cfvo type="min"/>
      <cfvo type="percentile" val="50"/>
      <cfvo type="max"/>
      <color rgb="FF63BE7B"/>
      <color rgb="FFFFEB84"/>
      <color rgb="FFF8696B"/>
    </colorScale>
  </cfRule>
  <!-- Cell value rule -->
  <cfRule type="cellIs" operator="lessThan" priority="2" dxfId="0">
    <formula>0</formula>
  </cfRule>
  <!-- Formula rule (alternate row shading) -->
  <cfRule type="expression" priority="3" dxfId="1">
    <formula>MOD(ROW(),2)=0</formula>
  </cfRule>
</conditionalFormatting>
```

`dxfId` references a `<dxf>` entry in `<dxfs>` inside `styles.xml`.

---

## Data Validation

```xml
<dataValidations count="2">
  <!-- Dropdown list -->
  <dataValidation type="list" allowBlank="1" showDropDown="0" sqref="C2:C100">
    <formula1>"Yes,No,Maybe"</formula1>
  </dataValidation>
  <!-- Integer range -->
  <dataValidation type="whole" operator="between"
                  showErrorMessage="1" errorTitle="Invalid"
                  error="Enter 1–100" sqref="D2:D100">
    <formula1>1</formula1>
    <formula2>100</formula2>
  </dataValidation>
</dataValidations>
```

---

## Comments (xl/comments1.xml)

```xml
<comments xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <authors>
    <author>Alice</author>
  </authors>
  <commentList>
    <comment ref="B3" authorId="0">
      <text>
        <r><rPr><b/></rPr><t>Note: </t></r>
        <r><t>Review this value.</t></r>
      </text>
    </comment>
  </commentList>
</comments>
```

The legacy VML drawing (`xl/drawings/vmlDrawing1.vml`) positions comment
boxes.  Modern xlsx files may use `xl/drawings/drawing1.xml` instead.

---

## Chart (xl/charts/chart1.xml) — outline

```xml
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <c:chart>
    <c:title><c:tx><c:rich>...</c:rich></c:tx></c:title>
    <c:plotArea>
      <c:barChart>
        <c:barDir val="col"/>
        <c:grouping val="clustered"/>
        <c:ser>
          <c:idx val="0"/>
          <c:order val="0"/>
          <c:tx>...</c:tx>
          <c:cat>
            <c:strRef><c:f>Sheet1!$A$2:$A$13</c:f></c:strRef>
          </c:cat>
          <c:val>
            <c:numRef><c:f>Sheet1!$B$2:$B$13</c:f></c:numRef>
          </c:val>
        </c:ser>
      </c:barChart>
    </c:plotArea>
    <c:legend><c:legendPos val="b"/></c:legend>
  </c:chart>
</c:chartSpace>
```

---

## Reading xlsx with lxml (low-level)

```python
import zipfile
from lxml import etree

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def read_sheet(path: str, part: str = "xl/worksheets/sheet1.xml"):
    with zipfile.ZipFile(path) as z:
        data = z.read(part)
    parser = etree.XMLParser(huge_tree=True, recover=True)
    root = etree.fromstring(data, parser)
    for row in root.findall(f".//{{{NS}}}row"):
        for cell in row.findall(f"{{{NS}}}c"):
            ref   = cell.get("r")       # e.g. "A1"
            ctype = cell.get("t", "n")  # cell type
            v_el  = cell.find(f"{{{NS}}}v")
            f_el  = cell.find(f"{{{NS}}}f")
            print(ref, ctype, v_el.text if v_el is not None else None,
                  f_el.text if f_el is not None else None)
```
