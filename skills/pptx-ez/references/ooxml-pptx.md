# OOXML PresentationML Format Reference

ECMA-376 5th Ed. / ISO 29500 — PresentationML (`.pptx`)

---

## Package structure

A `.pptx` file is a ZIP archive. Mandatory parts:

```
[Content_Types].xml                        # part type registry
_rels/.rels                                # package relationships
ppt/presentation.xml                       # main presentation
ppt/_rels/presentation.xml.rels            # presentation relationships
ppt/slideLayouts/slideLayout*.xml          # slide layouts
ppt/slideMasters/slideMaster*.xml          # slide masters
ppt/theme/theme1.xml                       # theme (fonts, colours)
```

Optional parts (added as needed):

```
ppt/slides/slide*.xml                      # individual slides
ppt/slides/_rels/slide*.xml.rels           # slide relationships
ppt/notesSides/notesSlide*.xml             # speaker notes
ppt/charts/chart*.xml                      # embedded chart XML
ppt/charts/colors*.xml                     # chart colour overrides
ppt/embeddings/Microsoft_Excel_Sheet*.xlsx # chart data workbooks
ppt/media/image*.*                         # embedded images
ppt/tables/table*.xml                      # table style definitions
```

---

## XML namespaces

```xml
xmlns:p   = "http://schemas.openxmlformats.org/presentationml/2006/main"
xmlns:a   = "http://schemas.openxmlformats.org/drawingml/2006/main"
xmlns:r   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
xmlns:mc  = "http://schemas.openxmlformats.org/markup-compatibility/2006"
xmlns:p14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
```

All examples below assume these prefixes are in scope.

---

## presentation.xml skeleton

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">

  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>

  <p:sldIdLst>
    <p:sldId id="256" r:id="rId2"/>
    <p:sldId id="257" r:id="rId3"/>
  </p:sldIdLst>

  <p:sldSz cx="9144000" cy="5143500"/>   <!-- 10 × 7.5 in, EMU (4:3) -->
  <!-- 16:9 widescreen: cx="9144000" cy="5143500" or cx="12192000" cy="6858000" -->

  <p:notesSz cx="6858000" cy="9144000"/>

</p:presentation>
```

Units: all dimensions in EMU. 1 inch = 914 400 EMU. 1 cm = 360 000 EMU.

Common slide sizes:
```
16:9 widescreen:  cx="12192000" cy="6858000"   (13.33 × 7.5 in)
4:3  standard:    cx="9144000"  cy="6858000"   (10 × 7.5 in)
A4 portrait:      cx="6858000"  cy="9144000"
```

---

## slide.xml skeleton

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <!-- shapes go here -->
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>
```

---

## Shape `<p:sp>`

### Placeholder (title)

```xml
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="2" name="Title 1"/>
    <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
    <p:nvPr><p:ph type="title"/></p:nvPr>
  </p:nvSpPr>
  <p:spPr/>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:r>
        <a:rPr lang="en-US" dirty="0"/>
        <a:t>Slide Title</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

Placeholder `type` values: `title`, `body`, `ctrTitle`, `subTitle`, `dt`, `sldNum`, `ftr`, `hdr`.

### Text box

```xml
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="3" name="TextBox 2"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off  x="1828800" y="2743200"/>  <!-- 2 in, 3 in -->
      <a:ext  cx="5486400" cy="1143000"/> <!-- 6 in, 1.25 in -->
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" rtlCol="0">
      <a:normAutofit/>
    </a:bodyPr>
    <a:lstStyle/>
    <a:p>
      <a:r>
        <a:rPr lang="en-US" dirty="0"/>
        <a:t>Text content here</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

### Geometric shape (rectangle)

```xml
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="4" name="Rectangle 3"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="1828800" y="2286000"/>
      <a:ext cx="4572000" cy="1143000"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="4472C4"/></a:solidFill>
    <a:ln><a:solidFill><a:srgbClr val="2F5296"/></a:solidFill></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p/>
  </p:txBody>
</p:sp>
```

Common `prst` values:
```
rect, roundRect, ellipse, triangle, rtTriangle
rightArrow, leftArrow, chevron, star5, star6
callout1, wedgeRectCallout, cloudCallout
```

---

## Text run properties `<a:rPr>`

```xml
<a:rPr lang="en-US" sz="1800" b="1" i="1" u="sng" dirty="0">
  <a:solidFill><a:srgbClr val="FF0000"/></a:solidFill>
  <a:latin typeface="Arial" pitchFamily="34" charset="0"/>
  <a:highlight><a:srgbClr val="FFFF00"/></a:highlight>
</a:rPr>
```

- `sz` — font size in hundredths of a point (1800 = 18pt)
- `b="1"` bold, `i="1"` italic, `u="sng"` underline single, `strike="sngStrike"`
- `lang` — BCP 47 language tag

---

## Paragraph properties `<a:pPr>`

```xml
<a:pPr algn="ctr" indent="457200" marL="457200" lvl="0">
  <a:spcBef><a:spcPts val="600"/></a:spcBef>
  <a:spcAft><a:spcPts val="300"/></a:spcAft>
  <a:lnSpc><a:spcPct val="115000"/></a:lnSpc>
  <a:buChar char="•"/>            <!-- bullet character -->
  <!-- or: <a:buNone/>             suppress bullet -->
</a:pPr>
```

`algn` values: `l` (left), `ctr` (center), `r` (right), `just` (justify), `dist`.

---

## Image `<p:pic>`

```xml
<p:pic>
  <p:nvPicPr>
    <p:cNvPr id="5" name="Image 4"/>
    <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="rId2"/>
    <a:stretch><a:fillRect/></a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm>
      <a:off x="1828800" y="2743200"/>
      <a:ext cx="4572000" cy="3429000"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
  </p:spPr>
</p:pic>
```

The relationship `rId2` must be registered in `ppt/slides/_rels/slideN.xml.rels`:
```xml
<Relationship Id="rId2"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
  Target="../media/image1.png"/>
```

---

## Table `<p:graphicFrame>` + `<a:tbl>`

```xml
<p:graphicFrame>
  <p:nvGraphicFramePr>
    <p:cNvPr id="6" name="Table 5"/>
    <p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
    <p:nvPr/>
  </p:nvGraphicFramePr>
  <p:xfrm>
    <a:off x="1828800" y="2743200"/>
    <a:ext cx="8229600" cy="3429000"/>
  </p:xfrm>
  <a:graphic>
    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">
      <a:tbl>
        <a:tblPr firstRow="1" bandRow="1">
          <a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId>
        </a:tblPr>
        <a:tblGrid>
          <a:gridCol w="2743200"/>
          <a:gridCol w="2743200"/>
          <a:gridCol w="2743200"/>
        </a:tblGrid>
        <a:tr h="914400">
          <a:tc>
            <a:txBody>
              <a:bodyPr/>
              <a:lstStyle/>
              <a:p><a:r><a:t>Header A</a:t></a:r></a:p>
            </a:txBody>
            <a:tcPr>
              <a:solidFill><a:srgbClr val="4472C4"/></a:solidFill>
            </a:tcPr>
          </a:tc>
          <!-- more <a:tc> ... -->
        </a:tr>
      </a:tbl>
    </a:graphicData>
  </a:graphic>
</p:graphicFrame>
```

### Cell merge (horizontal span)

```xml
<a:tc gridSpan="2">...</a:tc>
<a:tc hMerge="1"><a:txBody>...</a:txBody></a:tc>
```

### Cell merge (vertical span)

```xml
<!-- first cell in span -->
<a:tc rowSpan="2">...</a:tc>
<!-- continuation (next row, same column) -->
<a:tc vMerge="1"><a:txBody>...</a:txBody></a:tc>
```

---

## Chart `<p:graphicFrame>` + `<c:chart>`

```xml
<p:graphicFrame>
  <p:nvGraphicFramePr>
    <p:cNvPr id="7" name="Chart 6"/>
    <p:cNvGraphicFramePr/>
    <p:nvPr/>
  </p:nvGraphicFramePr>
  <p:xfrm>
    <a:off x="457200" y="457200"/>
    <a:ext cx="8229600" cy="5029200"/>
  </p:xfrm>
  <a:graphic>
    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">
      <c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
               r:id="rId3"/>
    </a:graphicData>
  </a:graphic>
</p:graphicFrame>
```

`rId3` points to `ppt/charts/chart1.xml` via slide relationships.

### chart.xml skeleton

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <c:chart>
    <c:title>
      <c:tx><c:rich><a:bodyPr/><a:lstStyle/>
        <a:p><a:r><a:t>Chart Title</a:t></a:r></a:p>
      </c:rich></c:tx>
      <c:overlay val="0"/>
    </c:title>
    <c:plotArea>
      <c:barChart>
        <c:barDir val="col"/>
        <c:grouping val="clustered"/>
        <c:ser>
          <c:idx val="0"/>
          <c:order val="0"/>
          <c:tx><c:strRef><c:f>Sheet1!$B$1</c:f></c:strRef></c:tx>
          <c:cat><c:strRef><c:f>Sheet1!$A$2:$A$5</c:f></c:strRef></c:cat>
          <c:val><c:numRef><c:f>Sheet1!$B$2:$B$5</c:f></c:numRef></c:val>
        </c:ser>
      </c:barChart>
      <c:catAx><c:axId val="1"/><c:scaling><c:orientation val="minMax"/></c:scaling>
        <c:crossAx val="2"/></c:catAx>
      <c:valAx><c:axId val="2"/><c:scaling><c:orientation val="minMax"/></c:scaling>
        <c:crossAx val="1"/></c:valAx>
    </c:plotArea>
    <c:legend><c:legendPos val="b"/></c:legend>
  </c:chart>
  <c:externalData r:id="rId1"/>
</c:chartSpace>
```

Chart type elements: `<c:barChart>`, `<c:lineChart>`, `<c:pieChart>`, `<c:doughnutChart>`, `<c:areaChart>`, `<c:scatterChart>`, `<c:bubbleChart>`, `<c:radarChart>`, `<c:surfaceChart>`.

---

## Speaker notes `<p:notes>`

Notes are stored in `ppt/notesSides/notesSlideN.xml`, linked from the slide via:
```xml
<!-- ppt/slides/_rels/slide1.xml.rels -->
<Relationship Id="rId3"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
  Target="../notesSides/notesSlide1.xml"/>
```

```xml
<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <!-- slide thumbnail placeholder: ph type="sldImg" -->
      <!-- notes body placeholder: ph type="body" idx="1" -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Notes Placeholder 2"/>
          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph type="body" idx="1"/></p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p><a:r><a:t>Presenter notes text.</a:t></a:r></a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:notes>
```

---

## [Content_Types].xml minimal template

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/slides/slide1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/theme/theme1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <!-- Notes slide (when present): -->
  <Override PartName="/ppt/notesSides/notesSlide1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>
</Types>
```

---

## Round-trip editing pattern (Python)

```python
import zipfile
from lxml import etree

PML = 'http://schemas.openxmlformats.org/presentationml/2006/main'
DML = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS  = {'p': PML, 'a': DML}

def edit_pptx(src, dst, edit_fn):
    with zipfile.ZipFile(src, 'r') as z:
        parts = {n: z.read(n) for n in z.namelist()}

    # Edit a specific slide
    slide_xml = parts['ppt/slides/slide1.xml']
    tree = etree.fromstring(slide_xml)
    edit_fn(tree, NS)
    parts['ppt/slides/slide1.xml'] = etree.tostring(
        tree, xml_declaration=True, encoding='UTF-8', standalone=True
    )

    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
```

Useful XPath:
```python
# All text runs on a slide
tree.findall('.//a:r/a:t', NS)

# All shape names
[sp.find('p:nvSpPr/p:cNvPr', NS).get('name')
 for sp in tree.findall('.//p:sp', NS)]

# Slides listed in presentation.xml
prs_tree.findall('.//p:sldIdLst/p:sldId', NS)
```
