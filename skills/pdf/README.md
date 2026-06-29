# PDF Skill

Read, extract, and manipulate PDF files via a bundled Python CLI script powered by [pypdf](https://pypdf.readthedocs.io/) and [pdfplumber](https://github.com/jsvine/pdfplumber).

## What It Does

Provides a single CLI entry point (`scripts/pdf_ops.py`) with 8 subcommands covering common PDF operations:

| Category | Subcommands |
|---|---|
| **Inspect** | `info` |
| **Extract** | `text`, `tables`, `extract-images` |
| **Convert** | `to-images` |
| **Manipulate** | `merge`, `split`, `rotate` |
| **Security** | `decrypt` |

### Scanned / Image PDFs

If text extraction returns empty results, the PDF is likely a scanned document. Use `to-images` to render pages as PNG — the AI agent can then read the content visually. This approach is more reliable and lightweight than OCR.

## Setup

### Via mythril-agent-skills

```bash
pip install mythril-agent-skills              # text, tables, merge, split, rotate, decrypt
pip install mythril-agent-skills[pdf-images]   # also enables to-images (PDF-to-PNG)
```

### Standalone

```bash
pip install pypdf pdfplumber      # core features
pip install pypdfium2              # optional, for to-images
```

## Quick Examples

```bash
# Inspect a PDF
python3 scripts/pdf_ops.py info document.pdf

# Extract text from all pages
python3 scripts/pdf_ops.py text document.pdf

# Extract text from pages 1-5
python3 scripts/pdf_ops.py text document.pdf --pages 1-5

# Extract tables as markdown
python3 scripts/pdf_ops.py tables document.pdf

# Convert pages to images
python3 scripts/pdf_ops.py to-images document.pdf --output-dir ./pages/

# Merge PDFs
python3 scripts/pdf_ops.py merge a.pdf b.pdf c.pdf -o merged.pdf

# Split specific pages
python3 scripts/pdf_ops.py split document.pdf --pages 1-5 -o first_five.pdf

# Extract embedded images
python3 scripts/pdf_ops.py extract-images document.pdf --output-dir ./images/
```

## Dependencies

- Python 3.10+
- `pypdf` >= 4.0.0 — merge, split, rotate, metadata, decrypt, extract images
- `pdfplumber` >= 0.10.0 — text and table extraction
- `pypdfium2` >= 4.0.0 (optional) — PDF-to-image conversion
