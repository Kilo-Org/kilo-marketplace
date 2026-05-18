# docx.js API Reference

Version: 9.x — check with `npm show docx version`
Docs: https://docx.js.org

## Installation

```bash
npm install docx
```

---

## Document constructor

```ts
import { Document } from 'docx';

const doc = new Document({
  // Metadata
  creator:         'string',
  title:           'string',
  subject:         'string',
  description:     'string',
  keywords:        'string',
  lastModifiedBy:  'string',
  revision:        1,

  // Styles
  styles:  IStylesOptions,
  fonts:   FontOptions[],

  // Behaviour
  features: {
    trackRevisions: boolean, // wrap all new content in <w:ins>
    updateFields:   boolean, // auto-refresh TOC and field codes on open
  },

  // Content
  comments:   ICommentsOptions,          // see Comments section
  footnotes:  Record<string, { children: Paragraph[] }>,
  numbering:  INumberingOptions,
  sections:   ISectionOptions[],         // REQUIRED
});
```

### ISectionOptions

```ts
{
  properties: {
    type: SectionType,   // CONTINUOUS | NEXT_PAGE | EVEN_PAGE | ODD_PAGE
    page: {
      size:   { width: number, height: number },  // twips
      margin: { top, right, bottom, left, header, footer, gutter },
      pageNumbers: { start: number, formatType: NumberFormat },
    },
    titlePage:   boolean,     // different first-page header/footer
    lineNumbers: ILineNumberOptions,
    column:      { count: number, space: number },
  },
  headers: { default: Header, first: Header, even: Header },
  footers: { default: Footer, first: Footer, even: Footer },
  children: (Paragraph | Table | TableOfContents)[],
}
```

---

## Paragraph

```ts
new Paragraph({
  text:     'string',        // shorthand for single TextRun
  children: XmlComponent[], // TextRun | ImageRun | Hyperlink | ...

  heading:   HeadingLevel,   // HEADING_1..HEADING_6, TITLE
  style:     'string',       // named paragraph style

  alignment: AlignmentType,  // START | CENTER | END | BOTH

  spacing: {
    before:   number,        // twips before paragraph
    after:    number,        // twips after paragraph
    line:     number,        // line spacing
    lineRule: LineRuleType,  // AUTO | EXACT | AT_LEAST
  },

  indent: {
    left:      number,
    right:     number,
    firstLine: number,
    hanging:   number,
  },

  border: {
    top, bottom, left, right: {
      style: BorderStyle,
      size:  number,
      color: 'rrggbb',
    },
  },

  bullet:    { level: number },
  numbering: { reference: 'listId', level: 0 },

  pageBreakBefore: boolean,
  keepLines:       boolean,
  keepNext:        boolean,
  outlineLevel:    number,
  thematicBreak:   boolean,  // horizontal rule
})
```

### HeadingLevel

```ts
HeadingLevel.TITLE
HeadingLevel.HEADING_1  // w:Heading1
HeadingLevel.HEADING_2
HeadingLevel.HEADING_3
HeadingLevel.HEADING_4
HeadingLevel.HEADING_5
HeadingLevel.HEADING_6
```

---

## TextRun

```ts
new TextRun({
  text:         'string',
  bold:         boolean,
  italics:      boolean,
  underline:    { type: UnderlineType, color: 'rrggbb' },
  strike:       boolean,
  doubleStrike: boolean,

  font:      'Arial',         // or { name: 'Arial' }
  size:      24,              // half-points (24 = 12 pt)
  color:     'rrggbb',        // hex without #

  highlight: 'yellow',        // highlight colour name
  shading:   { type: ShadingType, fill: 'rrggbb' },

  superScript: boolean,
  subScript:   boolean,

  break:  1,                  // soft line break count after run
  style:  'string',           // named character style
})
```

---

## Table

```ts
new Table({
  rows:   TableRow[],
  width:  { size: number, type: WidthType },  // WidthType.DXA for twips
  indent: { size: number, type: WidthType },
  borders: {
    top, bottom, left, right, insideH, insideV: {
      style: BorderStyle,
      size:  number,
      color: 'rrggbb',
    },
  },
  layout: TableLayoutType,   // FIXED | AUTOFIT
})
```

### TableRow

```ts
new TableRow({
  children:    TableCell[],
  tableHeader: boolean,       // repeat row as header on page break
  cantSplit:   boolean,
  height:      { value: number, rule: HeightRule },
})
```

### TableCell

```ts
new TableCell({
  children:      (Paragraph | Table)[],
  columnSpan:    number,      // horizontal merge
  rowSpan:       number,      // vertical merge
  width:         { size: number, type: WidthType },
  verticalAlign: VerticalAlign,   // TOP | CENTER | BOTTOM
  borders:       { top, bottom, left, right: BorderOptions },
  shading:       { fill: 'rrggbb', type: ShadingType },
  margins:       { top, bottom, left, right: number },
})
```

---

## TableOfContents

```ts
new TableOfContents('Title', {
  hyperlink:                        boolean,
  headingStyleRange:                '1-3',    // \o switch
  stylesWithLevels:                 StyleLevel[],  // \t switch
  useAppliedParagraphOutlineLevel:  boolean,  // \u switch
  cachedEntries:                    ToCEntry[],
})

// ToCEntry
{ title: 'string', level: 1, page: 1, href: 'bookmark-id' }
```

Requires `features: { updateFields: true }` in the `Document` constructor.

---

## Bookmarks and cross-references

```ts
import { BookmarkStart, BookmarkEnd, InternalHyperlink, PageReference } from 'docx';

// Define a bookmark target
new Paragraph({
  children: [
    new BookmarkStart({ id: 'sec1', name: 'Section 1' }),
    new TextRun('Section 1'),
    new BookmarkEnd({ id: 'sec1' }),
  ]
})

// Link to bookmark
new InternalHyperlink({
  anchor: 'sec1',
  children: [new TextRun({ text: 'Section 1', style: 'Hyperlink' })],
})

// Display page number where bookmark appears
new PageReference('sec1')
```

---

## Comments

```ts
import { Comment, CommentRangeStart, CommentRangeEnd, CommentReference } from 'docx';

new Document({
  comments: {
    children: [
      new Comment({
        id:       '1',
        author:   'Alice',
        date:     new Date('2025-01-15'),
        initials: 'A',
        children: [
          new Paragraph({ children: [new TextRun('Please revise this.')] }),
        ],
      }),
    ],
  },
  sections: [{
    children: [
      new Paragraph({
        children: [
          new CommentRangeStart(1),
          new TextRun('annotated text'),
          new CommentRangeEnd(1),
          new CommentReference(1),
        ],
      }),
    ],
  }],
})
```

---

## Images

```ts
import { ImageRun } from 'docx';
import fs from 'fs';

// Inline
new ImageRun({
  type: 'png',
  data: fs.readFileSync('image.png'),
  transformation: { width: 400, height: 200 },
})

// Floating (text wraps around)
new ImageRun({
  type:           'png',
  data:           fs.readFileSync('image.png'),
  transformation: { width: 300, height: 200 },
  floating: {
    horizontalPosition: { offset: 914400 },  // EMUs
    verticalPosition:   { offset: 914400 },
    wrap: { type: 'square', side: 'right' },
  },
})
```

Supported formats: `jpeg`, `jpg`, `png`, `gif`, `bmp`.

---

## Export

```ts
import { Packer } from 'docx';
import fs from 'fs';

// To file
const buffer = await Packer.toBuffer(doc);
fs.writeFileSync('output.docx', buffer);

// To Base64 string
const b64 = await Packer.toBase64String(doc);

// To readable stream
const stream = Packer.toStream(doc);
stream.pipe(fs.createWriteStream('output.docx'));
```

---

## Unit helpers

```ts
import { convertInchesToTwip, convertMillimetersToTwip } from 'docx';

convertInchesToTwip(1)        // 1440
convertInchesToTwip(8.5)      // 12240  (US Letter width)
convertInchesToTwip(11)       // 15840  (US Letter height)
convertMillimetersToTwip(25.4) // 1440
```

---

## US Letter / Arial defaults (copy-paste template)

```js
const doc = new Document({
  creator: 'docx skill',
  styles: {
    default: {
      document: {
        run: { font: { name: 'Arial' }, size: 24 },  // 12 pt
      },
    },
  },
  features: { updateFields: true },
  sections: [{
    properties: {
      page: {
        size:   { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, text: 'Title' }),
      new Paragraph({ text: 'Body paragraph.' }),
    ],
  }],
});
```
