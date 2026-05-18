# Apache POI Test Corpus

The Apache POI project (Apache 2.0 License) ships a comprehensive `.docx`/`.doc`
test corpus in `test-data/document/`. Use these files to validate output quality
and round-trip fidelity.

## Location

Clone the fork:
```bash
git clone https://github.com/shauneshraghi/poi.git
```

Test files are at:
```
poi/test-data/document/
```

## Key test files by category

### Tracked changes

| File | Content |
|------|---------|
| `bug56075-changeTracking_on.docx` | Tracked insertions and deletions enabled |
| `bug56075-changeTracking_off.docx` | Same content with changes accepted |
| `documentProtection_trackedChanges_no_password.docx` | Protected tracked-changes doc |
| `testRangeInsertion.doc` | Range insertion revision marks |
| `testRangeDelete.doc` | Range deletion revision marks |

### Comments

| File | Content |
|------|---------|
| `comment.docx` | Single-author comment with range anchoring |
| `testComment.docx` | Multi-range comments |
| `documentProtection_comments_no_password.docx` | Protected comments |

### Headings and structure

| File | Content |
|------|---------|
| `heading123.docx` | H1/H2/H3 paragraphs, outline levels |
| `Headers.docx` | Multiple header types |
| `DiffFirstPageHeadFoot.docx` | Different header/footer on first page |
| `headerFooter.docx` | Standard header and footer |

### Tables

| File | Content |
|------|---------|
| `TestTableCellAlign.docx` | Vertical cell alignment (top/centre/bottom) |
| `TestTableColumns.docx` | Multi-column widths |
| `table-merges.doc` | Horizontal and vertical cell merges |
| `deep-table-cell.docx` | Nested tables |
| `innertable.doc` | Table inside a table cell |
| `table-alignment.docx` | Table horizontal alignment |
| `table-indent.docx` | Table indent from margin |
| `table_footnotes.docx` | Footnotes inside table cells |

## Running the benchmark

```bash
# Single file — tracked-changes mode
python scripts/benchmark.py \
  --poi poi/test-data/document/bug56075-changeTracking_on.docx \
  --mode tracked-changes

# Single file — comments mode
python scripts/benchmark.py \
  --poi poi/test-data/document/comment.docx \
  --mode comments

# Full directory scan (auto-detects mode per file)
python scripts/benchmark.py \
  --poi poi/test-data/document/ \
  --mode all \
  --output benchmark_results.json
```

## What the benchmark checks

| Check | Pass criterion |
|-------|---------------|
| `xml-wellformed` | `word/document.xml` parses without errors |
| `has-tracked-changes` | At least one `<w:ins>` or `<w:del>` found (for tracking files) |
| `has-comments` | At least one `<w:comment>` found (for comment files) |
| `has-headings` | At least one `Heading1`–`Heading6` paragraph style found |
| `has-tables` | At least one `<w:tr>` found (for table files) |

## Acceptance threshold

All applicable checks must pass for files in the relevant categories.
Files that do not match a category (no headings, no tables, etc.) are
skipped for that category's check.
