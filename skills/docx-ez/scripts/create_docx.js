#!/usr/bin/env node
'use strict';

/**
 * create_docx.js — Create a .docx document from scratch using docx.js
 *
 * Usage:
 *   node create_docx.js <output.docx>                     # sample document
 *   node create_docx.js <output.docx> --spec <spec.json>  # from JSON spec
 *
 * Install dependency once:
 *   npm install docx
 *
 * Spec JSON format: see SKILL.md or references/docx-js.md
 */

const path = require('path');
const fs   = require('fs');

// ── Dependency resolution ────────────────────────────────────────────────────
let docx;
try {
  docx = require('docx');
} catch (_) {
  // Try common local install locations
  const candidates = [
    path.join(process.cwd(), 'node_modules', 'docx'),
    path.join(__dirname, '..', 'node_modules', 'docx'),
    path.join(process.env.HOME || '/tmp', 'node_modules', 'docx'),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) { docx = require(c); break; }
  }
  if (!docx) {
    console.error('Error: docx package not found. Run: npm install docx');
    process.exit(1);
  }
}

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, BorderStyle, TableOfContents,
  BookmarkStart, BookmarkEnd, InternalHyperlink,
  CommentRangeStart, CommentRangeEnd, CommentReference, Comment,
  convertInchesToTwip,
} = docx;

// ── Page constants ───────────────────────────────────────────────────────────
const US_LETTER_W = convertInchesToTwip(8.5);  // 12240
const US_LETTER_H = convertInchesToTwip(11);   // 15840
const MARGIN_1IN  = convertInchesToTwip(1);    // 1440

const DEFAULT_PAGE = {
  page: {
    size:   { width: US_LETTER_W, height: US_LETTER_H },
    margin: { top: MARGIN_1IN, right: MARGIN_1IN, bottom: MARGIN_1IN, left: MARGIN_1IN },
  },
};

// ── Spec builders ────────────────────────────────────────────────────────────

const HEADING_MAP = {
  1: HeadingLevel.HEADING_1,
  2: HeadingLevel.HEADING_2,
  3: HeadingLevel.HEADING_3,
  4: HeadingLevel.HEADING_4,
  5: HeadingLevel.HEADING_5,
  6: HeadingLevel.HEADING_6,
};

function buildNode(node) {
  switch (node.type) {
    case 'heading':
      return new Paragraph({
        heading: HEADING_MAP[node.level] || HeadingLevel.HEADING_1,
        text:    node.text || '',
      });

    case 'paragraph':
      return new Paragraph({
        children: [
          new TextRun({
            text:    node.text    || '',
            bold:    node.bold    || false,
            italics: node.italic  || false,
          }),
        ],
        alignment: node.align
          ? (AlignmentType[node.align.toUpperCase()] || undefined)
          : undefined,
      });

    case 'page_break':
      return new Paragraph({ pageBreakBefore: true });

    case 'bookmark':
      return new Paragraph({
        children: [
          new BookmarkStart({ id: node.id, name: node.name || node.id }),
          new TextRun(node.text || ''),
          new BookmarkEnd({ id: node.id }),
        ],
      });

    case 'xref':
      return new Paragraph({
        children: [
          new InternalHyperlink({
            anchor:   node.anchor,
            children: [
              new TextRun({ text: node.text || node.anchor, style: 'Hyperlink' }),
            ],
          }),
        ],
      });

    case 'toc':
      return new TableOfContents(node.title || 'Table of Contents', {
        hyperlink:         true,
        headingStyleRange: node.levels || '1-3',
      });

    case 'table':
      return buildTable(node);

    default:
      return new Paragraph({ text: String(node.text || '') });
  }
}

function buildTable(node) {
  const tableWidth = US_LETTER_W - MARGIN_1IN * 2;
  const rows = (node.rows || []).map((row, ri) =>
    new TableRow({
      tableHeader: ri === 0,
      children: row.map(cellText =>
        new TableCell({
          children: [new Paragraph({ text: String(cellText) })],
          borders: {
            top:    { style: BorderStyle.SINGLE, size: 1, color: '000000' },
            bottom: { style: BorderStyle.SINGLE, size: 1, color: '000000' },
            left:   { style: BorderStyle.SINGLE, size: 1, color: '000000' },
            right:  { style: BorderStyle.SINGLE, size: 1, color: '000000' },
          },
        })
      ),
    })
  );
  return new Table({
    width: { size: tableWidth, type: WidthType.DXA },
    rows,
  });
}

function buildSection(sec) {
  return {
    properties: DEFAULT_PAGE,
    children:   (sec.children || []).map(buildNode),
  };
}

function buildComments(specs) {
  if (!specs || specs.length === 0) return undefined;
  return {
    children: specs.map(c =>
      new Comment({
        id:       String(c.id),
        author:   c.author   || 'Author',
        date:     c.date ? new Date(c.date) : new Date(),
        initials: (c.author || 'A').charAt(0).toUpperCase(),
        children: [new Paragraph({ children: [new TextRun(c.text || '')] })],
        ...(c.parentId ? { parentId: String(c.parentId) } : {}),
      })
    ),
  };
}

function buildDocument(spec) {
  const comments = buildComments(spec.comments);
  return new Document({
    creator:     spec.author      || 'docx skill',
    title:       spec.title       || '',
    description: spec.description || '',
    styles: {
      default: {
        document: {
          run: { font: { name: 'Arial' }, size: 24 },
        },
      },
    },
    features: {
      trackRevisions: spec.trackRevisions || false,
      updateFields:   true,
    },
    ...(comments ? { comments } : {}),
    sections: (spec.sections || [{ children: [] }]).map(buildSection),
  });
}

// ── Sample document ──────────────────────────────────────────────────────────

function sampleSpec() {
  return {
    title:  'Sample Document',
    author: 'docx skill',
    sections: [{
      children: [
        { type: 'heading', level: 1, text: 'Sample Document' },
        { type: 'paragraph', text: 'Generated by the docx skill (docx.js). This sample demonstrates headings, tables, bookmarks, cross-references, a TOC, and comments.' },
        { type: 'toc' },

        { type: 'heading', level: 1, text: 'Introduction' },
        { type: 'bookmark', id: 'intro', name: 'Introduction', text: '' },
        { type: 'paragraph', text: 'This section introduces the document. The OOXML format (ECMA-376 / ISO 29500) is a ZIP-based XML package. This skill generates conformant output via docx.js (Node.js) and python-docx + lxml (Python).' },

        { type: 'heading', level: 2, text: 'Background' },
        { type: 'paragraph', text: 'Key tools: docx.js for new documents, python-docx + lxml for editing existing ones, and LibreOffice for headless PDF export.' },

        { type: 'heading', level: 1, text: 'Toolchain' },
        { type: 'table', rows: [
          ['Task',            'Tool',           'Script'],
          ['Create new',      'docx.js',        'create_docx.js'],
          ['Edit existing',   'python-docx',    'edit_docx.py'],
          ['PDF export',      'LibreOffice',    'export_pdf.sh'],
          ['Validate',        'Python zipfile', 'validate_docx.py'],
          ['Benchmark (POI)', 'lxml',           'benchmark.py'],
        ]},

        { type: 'heading', level: 1, text: 'Cross-references' },
        { type: 'paragraph', text: 'Back-reference to the Introduction: ' },
        { type: 'xref', anchor: 'intro', text: 'Introduction' },
      ],
    }],
    comments: [
      {
        id:     '1',
        author: 'Reviewer',
        text:   'This sample document exercises the main docx skill features.',
        date:   new Date().toISOString(),
      },
    ],
  };
}

// ── Entry point ───────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args[0] === '--help') {
    console.log('Usage: node create_docx.js <output.docx> [--spec <spec.json>]');
    process.exit(args[0] === '--help' ? 0 : 1);
  }

  const outPath = args[0];

  let spec;
  const specIdx = args.indexOf('--spec');
  if (specIdx !== -1 && args[specIdx + 1]) {
    const specPath = args[specIdx + 1];
    try {
      spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
    } catch (e) {
      console.error(`Error reading spec "${specPath}": ${e.message}`);
      process.exit(1);
    }
  } else {
    spec = sampleSpec();
  }

  const doc    = buildDocument(spec);
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outPath, buffer);
  console.log(`Created: ${outPath} (${buffer.length.toLocaleString()} bytes)`);
}

main().catch(err => { console.error(err.message); process.exit(1); });
