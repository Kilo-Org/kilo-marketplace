---
name: xlsx-ez
description: Create, edit, and analyze Excel (.xlsx / .xlsm) and CSV/TSV spreadsheets. Handles financial models, data tables, charts, formulas, multi-sheet workbooks, and formatted reports. Always uses Excel formulas (never Python-computed hardcodes for business logic). Validates formula correctness after writing via LibreOffice headless recalculation. Triggers on xlsx, xlsm, xls, spreadsheet, excel, csv, tsv tasks.
license: CC0-1.0
compatibility: Python 3.9+ with openpyxl and pandas; LibreOffice 7.4+ (PDF export, formula recalculation). Linux, macOS, Windows.
metadata:
  category: productivity
  author: shauneshraghi
  source:
    repository: https://github.com/shauneshraghi/skills
    path: xlsx-ez
    license_path: LICENSE.txt
---

# xlsx Skill

## Toolchain at a glance

| Task | Tool | Script |
|------|------|--------|
| Create new .xlsx (JSON spec) | openpyxl | `scripts/create_xlsx.py` |
| Edit existing .xlsx (cells, formulas) | openpyxl | `scripts/edit_xlsx.py` |
| Unpack XLSX to editable XML | lxml | `scripts/office/unpack.py` |
| Pack XML back to XLSX | lxml | `scripts/office/pack.py` |
| Validate formula correctness | LibreOffice headless | `scripts/recalc.py` |
| LibreOffice (sandbox-safe) | C LD_PRELOAD shim | `scripts/office/soffice.py` |
| PDF export | LibreOffice headless | `scripts/export_pdf.sh` |
| Validate structure | Python zipfile | `scripts/validate_xlsx.py` |
| Benchmark / quality check | openpyxl | `scripts/benchmark.py` |

## Quick-start

```python
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string

wb = Workbook()
ws = wb.active
ws.title = "Sheet1"

ws["A1"] = "Revenue"
ws["B1"] = 100000
ws["C1"] = "=B1*1.1"   # always use formulas, not hardcoded computed values

wb.save("output.xlsx")
```

## Dependencies

```bash
pip install openpyxl pandas
# LibreOffice for recalc/PDF export
# Ubuntu: apt-get install libreoffice
# macOS:  brew install --cask libreoffice
```

## Creating Workbooks

### Workbook and sheet setup

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Summary"

# Add more sheets
detail = wb.create_sheet("Detail")
wb.create_sheet("Assumptions", 0)  # insert at position 0

# Remove a sheet
del wb["OldSheet"]

# Copy a sheet
ws_copy = wb.copy_worksheet(ws)
ws_copy.title = "Summary_copy"

wb.save("workbook.xlsx")
```

### Writing data

```python
# Direct cell assignment
ws["A1"] = "Label"
ws["B1"] = 42
ws["C1"] = 3.14
ws["D1"] = True

# Row/column coordinates (1-indexed)
ws.cell(row=2, column=1, value="Row 2")

# Bulk write a row
ws.append(["Name", "Value", "Formula"])
ws.append(["Total", None, "=SUM(B2:B10)"])

# Bulk write from list of rows
data = [
    ["Jan", 10000],
    ["Feb", 12000],
    ["Mar", 15000],
]
for row in data:
    ws.append(row)
```

### Formulas

Always write formulas as strings starting with `=`. Never compute values in
Python and hardcode the result — use formulas so the workbook remains live.

```python
ws["C2"] = "=A2*B2"
ws["C10"] = "=SUM(C2:C9)"
ws["D10"] = "=C10/C9-1"           # growth rate
ws["E10"] = "=IFERROR(D10,0)"     # error guard

# Cross-sheet reference
ws["F2"] = "=Detail!B2"

# Absolute references for anchored cells
ws["G2"] = "=B2/$B$1"

# Named ranges work if defined in the workbook
ws["H2"] = "=Revenue*MarginRate"
```

### Column widths and row heights

```python
ws.column_dimensions["A"].width = 20
ws.column_dimensions["B"].width = 12
ws.row_dimensions[1].height = 24    # points

# Auto-fit approximation (openpyxl has no built-in auto-fit)
for col in ws.columns:
    max_len = max((len(str(cell.value)) for cell in col if cell.value), default=0)
    ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)
```

### Freeze panes

```python
ws.freeze_panes = "B2"   # freeze row 1 and column A
ws.freeze_panes = "A2"   # freeze row 1 only
ws.freeze_panes = None   # unfreeze
```

## Formatting

### Fonts

```python
from openpyxl.styles import Font

# Header font
header_font = Font(name="Arial", bold=True, size=11, color="FFFFFF")
ws["A1"].font = header_font

# Default body font
body_font = Font(name="Arial", size=10)
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.font = body_font
```

### Fill / background color

```python
from openpyxl.styles import PatternFill

# Solid fill
blue_fill = PatternFill(fill_type="solid", fgColor="4472C4")
ws["A1"].fill = blue_fill

# Financial model color conventions:
# - Blue (#4472C4 or "0070C0"):  hardcoded input values
# - Black (#000000):             formula-derived values
# - Green (#00B050):             cross-sheet links
# - Red (#FF0000):               external file links
# - Yellow background (#FFFF00): key assumptions
INPUT_FILL   = PatternFill(fill_type="solid", fgColor="0070C0")
FORMULA_FILL = PatternFill(fill_type="solid", fgColor="000000")  # (font color)
LINK_FILL    = PatternFill(fill_type="solid", fgColor="00B050")
ASSUME_FILL  = PatternFill(fill_type="solid", fgColor="FFFF00")
```

### Number formats

```python
# Currency: $1,234 (no decimals, zero shown as dash)
ws["B2"].number_format = '$#,##0_);[Red]($#,##0);"-"'

# Currency with 2 decimals
ws["B3"].number_format = '$#,##0.00'

# Percentage: 12.3%
ws["C2"].number_format = '0.0%'

# Percentage with 2 decimals
ws["C3"].number_format = '0.00%'

# Accounting (negatives in parentheses)
ws["D2"].number_format = '#,##0_);(#,##0)'

# Dates
ws["E2"].number_format = 'MM/DD/YYYY'
ws["E3"].number_format = 'MMM-YY'

# General number with comma separator
ws["F2"].number_format = '#,##0'
```

### Alignment

```python
from openpyxl.styles import Alignment

ws["A1"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws["B1"].alignment = Alignment(horizontal="right")
ws["C1"].alignment = Alignment(horizontal="left", indent=1)
```

### Borders

```python
from openpyxl.styles import Border, Side

thin = Side(style="thin")
thick = Side(style="thick")
double = Side(style="double")

ws["A1"].border = Border(top=thick, bottom=thin, left=thin, right=thin)
ws["A2"].border = Border(bottom=double)
```

### Merging cells

```python
ws.merge_cells("A1:D1")   # merge range
ws["A1"].value = "Merged Title"
ws["A1"].alignment = Alignment(horizontal="center")

ws.unmerge_cells("A1:D1")  # unmerge
```

## Applying styles to ranges

```python
from openpyxl.utils import get_column_letter

def style_range(ws, min_row, max_row, min_col, max_col, **style_kwargs):
    for row in ws.iter_rows(min_row=min_row, max_row=max_row,
                            min_col=min_col, max_col=max_col):
        for cell in row:
            for attr, val in style_kwargs.items():
                setattr(cell, attr, val)

# Apply header style to row 1, columns A-E
style_range(ws, 1, 1, 1, 5,
            font=Font(bold=True, color="FFFFFF"),
            fill=PatternFill(fill_type="solid", fgColor="4472C4"),
            alignment=Alignment(horizontal="center"))
```

## Reading Workbooks

```python
from openpyxl import load_workbook

# Read with formulas (default)
wb = load_workbook("data.xlsx")
ws = wb.active
print(ws["A1"].value)     # returns formula string e.g. "=SUM(B1:B10)"

# Read computed values (requires file saved after recalc)
wb_data = load_workbook("data.xlsx", data_only=True)
ws_data = wb_data.active
print(ws_data["A1"].value)   # returns numeric result

# Iterate all rows
for row in ws.iter_rows(min_row=2, values_only=True):
    print(row)

# Iterate specific range
for row in ws.iter_rows(min_row=1, max_row=10, min_col=1, max_col=3):
    for cell in row:
        print(cell.coordinate, cell.value)
```

## Pandas Integration

Use pandas for data loading, transformation, and analysis. Write to xlsx
via openpyxl engine for full formatting control.

```python
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Load data
df = pd.read_excel("input.xlsx", sheet_name="Data", header=0)

# Analysis
summary = df.groupby("Category")["Revenue"].sum().reset_index()

# Write DataFrame to existing workbook (preserves other sheets/formatting)
wb = load_workbook("output.xlsx")
ws = wb["Summary"]
ws.delete_rows(2, ws.max_row)  # clear old data rows

for r in dataframe_to_rows(summary, index=False, header=False):
    ws.append(r)

wb.save("output.xlsx")
```

```python
# Write multiple DataFrames to separate sheets
with pd.ExcelWriter("report.xlsx", engine="openpyxl") as writer:
    df1.to_excel(writer, sheet_name="Revenue", index=False)
    df2.to_excel(writer, sheet_name="Costs", index=False)
    df3.to_excel(writer, sheet_name="Summary", index=False)
```

## Tables (ListObject)

```python
from openpyxl.worksheet.table import Table, TableStyleInfo

table = Table(displayName="SalesData", ref="A1:D100")
style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
                       showLastColumn=False, showRowStripes=True, showColumnStripes=False)
table.tableStyleInfo = style
ws.add_table(table)
```

## Charts

```python
from openpyxl.chart import BarChart, LineChart, PieChart, Reference

# Bar chart (column chart)
chart = BarChart()
chart.type = "col"           # "col" = vertical bars; "bar" = horizontal
chart.title = "Revenue"
chart.grouping = "clustered"

data = Reference(ws, min_col=2, min_row=1, max_col=4, max_row=10)
cats = Reference(ws, min_col=1, min_row=2, max_row=10)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.shape = 4

ws.add_chart(chart, "F2")   # anchor cell

# Line chart
from openpyxl.chart import LineChart
lc = LineChart()
lc.title = "Trend"
lc.add_data(data, titles_from_data=True)
lc.set_categories(cats)
ws.add_chart(lc, "F20")
```

---

## Named Ranges

```python
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import quote_sheetname

defn = DefinedName("RevenueRange", attr_text=f"{quote_sheetname('Sheet1')}!$B$2:$B$13")
wb.defined_names["RevenueRange"] = defn
```

## Data Validation

```python
from openpyxl.worksheet.datavalidation import DataValidation

# Dropdown list
dv = DataValidation(type="list", formula1='"Option1,Option2,Option3"', allow_blank=True)
dv.sqref = "C2:C100"
ws.add_data_validation(dv)

# Integer range
dv2 = DataValidation(type="whole", operator="between", formula1=0, formula2=100)
dv2.sqref = "D2:D100"
ws.add_data_validation(dv2)
```

## Conditional Formatting

```python
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, CellIsRule
from openpyxl.styles import PatternFill

# Color scale (green-yellow-red)
color_scale = ColorScaleRule(
    start_type="min", start_color="00FF00",
    mid_type="percentile", mid_value=50, mid_color="FFFF00",
    end_type="max", end_color="FF0000",
)
ws.conditional_formatting.add("B2:B100", color_scale)

# Highlight cells below threshold
red_fill = PatternFill(fill_type="solid", fgColor="FFC7CE")
rule = CellIsRule(operator="lessThan", formula=["0"], fill=red_fill)
ws.conditional_formatting.add("B2:B100", rule)
```

## Formula Recalculation

After writing formulas, run `recalc.py` to validate with LibreOffice:

```bash
python scripts/recalc.py output.xlsx
```

The script returns JSON:
```json
{
  "status": "success",
  "total_formulas": 42,
  "total_errors": 0,
  "error_summary": {}
}
```

If `total_errors > 0`, the `error_summary` lists affected cells by error type
(`#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#NULL!`, `#NUM!`, `#N/A`).

**Zero formula errors are required before delivering any workbook.**

## PDF Export

```bash
bash scripts/export_pdf.sh output.xlsx
# or with an explicit output directory:
bash scripts/export_pdf.sh output.xlsx ./exports/
```

Or use the `office/soffice.py` helper for sandboxed environments:

```python
from office.soffice import run_soffice
run_soffice(["--headless", "--convert-to", "pdf", "output.xlsx", "--outdir", "./"])
```

## CSV / TSV

```python
import csv

# Read CSV
with open("data.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Write CSV
with open("out.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Name", "Value"])
    writer.writeheader()
    writer.writerows(rows)

# pandas CSV round-trip
import pandas as pd
df = pd.read_csv("data.csv")
df.to_csv("out.csv", index=False)

# TSV
df = pd.read_csv("data.tsv", sep="\t")
df.to_csv("out.tsv", sep="\t", index=False)
```

## Unpack → Edit XML → Pack (OOXML direct editing)

When you need to modify cell XML, styles, or relationships directly:

```bash
# Step 1: Extract to editable XML directory
python scripts/office/unpack.py workbook.xlsx unpacked/

# Step 2: Edit files in unpacked/xl/
#   xl/workbook.xml          — sheet list, named ranges
#   xl/worksheets/sheet1.xml — cell data, formulas, conditional formatting
#   xl/styles.xml            — fonts, fills, borders, number formats
#   xl/sharedStrings.xml     — shared string table

# Step 3: Repack (fills missing binary files from original)
python scripts/office/pack.py unpacked/ output.xlsx --original workbook.xlsx
```

Smart quotes are encoded as XML entities on unpack (`"` → `&#x201C;`) and decoded on pack.

---

## Edit an existing workbook

```bash
pip install openpyxl

# Replace all occurrences of "Draft" with "Final" across all sheets
python scripts/edit_xlsx.py in.xlsx out.xlsx --replace "Draft" "Final"

# Set a specific cell to a plain value
python scripts/edit_xlsx.py in.xlsx out.xlsx --set-cell Sheet1 1 3 "Q1 Revenue"

# Set a formula
python scripts/edit_xlsx.py in.xlsx out.xlsx --set-formula Sheet1 10 3 "=SUM(C2:C9)"

# Rename a sheet
python scripts/edit_xlsx.py in.xlsx out.xlsx --rename-sheet "Sheet1" "Summary"
```

---

## Scripts Reference

| Script | Purpose |
|---|---|
| `scripts/create_xlsx.py` | Create a new workbook from a JSON spec |
| `scripts/edit_xlsx.py` | Edit cells, formulas, and sheet names in an existing workbook |
| `scripts/recalc.py` | Validate formulas via LibreOffice recalculation |
| `scripts/validate_xlsx.py` | Check ZIP integrity and XML well-formedness |
| `scripts/export_pdf.sh` | Export .xlsx to PDF via LibreOffice headless |
| `scripts/office/unpack.py` | Unpack XLSX to directory of editable XML files |
| `scripts/office/pack.py` | Repack XML directory back to XLSX |
| `scripts/office/soffice.py` | LibreOffice environment helper (AF_UNIX shim) |
| `scripts/benchmark.py` | Run quality checks (standalone + optional POI corpus) |

## Quality Checklist

Before delivering any workbook:

- [ ] All formulas start with `=` — no Python-computed hardcodes for business logic
- [ ] `recalc.py` returns `status: success` with `total_errors: 0`
- [ ] Font is Arial throughout (or as specified)
- [ ] Number formats match domain conventions (currency, %, accounting)
- [ ] Financial model follows color coding convention if applicable
- [ ] Column widths are readable (not too narrow, not excessively wide)
- [ ] Headers are bold and distinguished from data rows
- [ ] Sheet names are descriptive
- [ ] No unnecessary empty sheets remain
- [ ] `validate_xlsx.py` passes ZIP + XML integrity check

## Common Pitfalls

- **#REF! errors**: formula references a deleted row/column or wrong sheet name
- **#NAME? errors**: function name misspelled or named range not defined
- **#DIV/0! errors**: division by a cell that may be zero — wrap in `IFERROR`
- **#VALUE! errors**: wrong argument types — check that text cells aren't in numeric ranges
- **Formulas not recalculated**: openpyxl writes formulas but doesn't compute them;
  always run `recalc.py` to verify with LibreOffice
- **data_only=True returns None**: file was never opened/saved by a full Excel/LibreOffice
  session; cached values are absent — run `recalc.py` first
- **Merged cells and tables conflict**: don't add a Table over merged cells
- **Sheet name > 31 chars**: Excel limit; openpyxl does not enforce this automatically

---

## References

- [openpyxl.md](references/openpyxl.md) — openpyxl API reference
- [ooxml-xlsx.md](references/ooxml-xlsx.md) — SpreadsheetML OOXML anatomy and patterns
- [poi-corpus.md](references/poi-corpus.md) — Apache POI test corpus benchmark guide
