# openpyxl API Reference

openpyxl is the standard Python library for reading and writing Excel 2010+
xlsx/xlsm/xltx/xltm files.  It does **not** compute formula results — use
LibreOffice headless (see `recalc.py`) to evaluate formulas after writing.

Source: https://openpyxl.readthedocs.io/

## Installation

```bash
pip install openpyxl
```

Optional extras:
```bash
pip install lxml          # faster XML parsing backend
pip install Pillow        # required for image embedding
```

---

## Workbook

```python
from openpyxl import Workbook, load_workbook

# Create new
wb = Workbook()

# Open existing
wb = load_workbook("file.xlsx")                    # formulas as strings
wb = load_workbook("file.xlsx", data_only=True)    # cached computed values
wb = load_workbook("file.xlsx", read_only=True)    # streaming read, no write
wb = load_workbook("file.xlsx", keep_vba=True)     # preserve .xlsm macros

# Save
wb.save("output.xlsx")

# Save as template
wb.template = True
wb.save("template.xltx")
```

## Worksheets

```python
# Access
ws = wb.active                   # first sheet
ws = wb["Sheet1"]                # by name
ws = wb.worksheets[0]            # by index

# Create / rename / delete
ws = wb.create_sheet("NewSheet")
ws = wb.create_sheet("First", 0)  # insert at position 0
ws.title = "Renamed"
del wb["OldSheet"]

# Copy
ws2 = wb.copy_worksheet(ws)
ws2.title = "Copy"

# Reorder (moves "Sheet2" to position 0)
wb.move_sheet("Sheet2", offset=-1)

# List sheet names
print(wb.sheetnames)   # ["Sheet1", "Sheet2", ...]

# Sheet state: "visible" | "hidden" | "veryHidden"
ws.sheet_state = "hidden"
```

## Cells

```python
# Write
ws["A1"] = "Hello"
ws["B1"] = 42
ws["C1"] = 3.14
ws["D1"] = True
ws["E1"] = None       # clears cell

# Row/column (1-indexed)
ws.cell(row=1, column=1, value="A1")
ws.cell(row=1, column=1).value = "A1"

# Read
val = ws["A1"].value
val = ws.cell(row=1, column=1).value

# Cell metadata
cell = ws["A1"]
cell.row            # int
cell.column         # int
cell.column_letter  # str ("A")
cell.coordinate     # str ("A1")
cell.data_type      # "n" | "s" | "b" | "f" | "e" | "d" | "inlineStr"

# Append a row
ws.append(["Name", "Score", "Grade"])
ws.append(["Alice", 95, "A"])
```

## Iteration

```python
# Iterate all rows (left-to-right, top-to-bottom)
for row in ws.iter_rows():
    for cell in row:
        print(cell.value)

# Specific range
for row in ws.iter_rows(min_row=2, max_row=10, min_col=1, max_col=3):
    for cell in row:
        print(cell.coordinate, cell.value)

# values_only shortcut
for row in ws.iter_rows(values_only=True):
    print(row)    # tuple of raw values

# Columns
for col in ws.iter_cols(min_col=1, max_col=3):
    for cell in col:
        print(cell.value)

# Sheet dimensions
print(ws.min_row, ws.max_row, ws.min_column, ws.max_column)
```

## Formulas

Write formulas as strings starting with `=`.  openpyxl stores them verbatim;
they are evaluated only when the file is opened in Excel/LibreOffice.

```python
ws["A1"] = "=SUM(B1:B10)"
ws["B1"] = "=IF(A1>100, \"High\", \"Low\")"
ws["C1"] = "=VLOOKUP(A1, Sheet2!A:B, 2, FALSE)"
ws["D1"] = "=IFERROR(C1/B1, 0)"

# Cross-sheet
ws["E1"] = "=Assumptions!$B$2 * Revenue"

# Array formulas are stored as strings too
ws["F1"] = "=SUM(A1:A10 * B1:B10)"
```

## Styles — Font

```python
from openpyxl.styles import Font

ws["A1"].font = Font(
    name="Arial",        # font family
    size=12,             # pt
    bold=True,
    italic=False,
    underline="single",  # "single" | "double" | None
    strike=False,
    color="FF0000",      # hex ARGB (no leading #); "FF" prefix = fully opaque
    vertAlign="superscript",  # "superscript" | "subscript" | None
)

# Convenience: copy and modify
from copy import copy
new_font = copy(ws["A1"].font)
new_font = new_font + Font(bold=True)    # note: Font is immutable-style
```

## Styles — Fill

```python
from openpyxl.styles import PatternFill, GradientFill

# Solid fill
ws["A1"].fill = PatternFill(fill_type="solid", fgColor="FFFF00")

# Pattern fills (fill_type): "solid", "darkGray", "mediumGray", "lightGray",
#   "gray125", "gray0625", "darkHorizontal", "darkVertical", "darkDown",
#   "darkUp", "darkGrid", "darkTrellis", "lightHorizontal", "lightVertical",
#   "lightDown", "lightUp", "lightGrid", "lightTrellis"
ws["B1"].fill = PatternFill(fill_type="lightGray", fgColor="0000FF", bgColor="FFFFFF")

# Gradient fill
ws["C1"].fill = GradientFill(type="linear", degree=45,
                              stop=["FF0000", "FFFF00", "00FF00"])
```

## Styles — Alignment

```python
from openpyxl.styles import Alignment

ws["A1"].alignment = Alignment(
    horizontal="center",   # "general"|"left"|"center"|"right"|"fill"|"justify"|"centerContinuous"|"distributed"
    vertical="center",     # "top"|"center"|"bottom"|"justify"|"distributed"
    text_rotation=0,       # degrees 0-180 or 255 (vertical)
    wrap_text=True,
    shrink_to_fit=False,
    indent=0,              # left indent character count
    reading_order=0,       # 0=context, 1=LTR, 2=RTL
)
```

## Styles — Border

```python
from openpyxl.styles import Border, Side

thin   = Side(style="thin")
medium = Side(style="medium")
thick  = Side(style="thick")
double = Side(style="double")
dashed = Side(style="dashed")
dotted = Side(style="dotted")
none_s = Side(style=None)

ws["A1"].border = Border(
    left=thin,
    right=thin,
    top=medium,
    bottom=double,
    diagonal=dashed,
    diagonal_direction=1,   # 1=down-left, 2=down-right, 3=both
)
```

## Styles — Number Format

Number format codes follow the Excel format string syntax:

```python
# Currency
ws["A1"].number_format = '$#,##0'               # $1,234
ws["A2"].number_format = '$#,##0.00'            # $1,234.56
ws["A3"].number_format = '$#,##0_);[Red]($#,##0)'  # negatives red in parens

# Accounting (zeros shown as dash)
ws["B1"].number_format = '#,##0_);(#,##0);"-"'

# Percentage
ws["C1"].number_format = '0%'
ws["C2"].number_format = '0.0%'
ws["C3"].number_format = '0.00%'

# Date/time
ws["D1"].number_format = 'MM/DD/YYYY'
ws["D2"].number_format = 'YYYY-MM-DD'
ws["D3"].number_format = 'D-MMM-YY'
ws["D4"].number_format = 'HH:MM:SS'

# General number
ws["E1"].number_format = '#,##0'
ws["E2"].number_format = '#,##0.00'
ws["E3"].number_format = '0.000E+00'  # scientific
```

Built-in format IDs (openpyxl.styles.numbers.BUILTIN_FORMATS):
- `0`: General
- `1`: 0
- `2`: 0.00
- `3`: #,##0
- `4`: #,##0.00
- `9`: 0%
- `10`: 0.00%
- `11`: 0.00E+00
- `14`: MM-DD-YY
- `49`: @  (text)

## Column and Row Dimensions

```python
# Column width (in character units, roughly)
ws.column_dimensions["A"].width = 20
ws.column_dimensions["A"].hidden = True

# Row height (in points)
ws.row_dimensions[1].height = 30
ws.row_dimensions[1].hidden = True

# Get column letter from number
from openpyxl.utils import get_column_letter, column_index_from_string
get_column_letter(1)            # "A"
get_column_letter(27)           # "AA"
column_index_from_string("A")  # 1
column_index_from_string("AA") # 27
```

## Freeze Panes

```python
ws.freeze_panes = "A2"   # freeze top row (row 1)
ws.freeze_panes = "B1"   # freeze left column (column A)
ws.freeze_panes = "B2"   # freeze row 1 and column A
ws.freeze_panes = None   # remove freeze
```

## Merge / Unmerge Cells

```python
ws.merge_cells("A1:D1")
ws["A1"].value = "Merged Header"
ws["A1"].alignment = Alignment(horizontal="center")

ws.unmerge_cells("A1:D1")

# Merge using row/col coordinates
from openpyxl.utils import get_column_letter
ws.merge_cells(
    start_row=1, start_column=1,
    end_row=1, end_column=4,
)
```

## Tables (ListObject)

```python
from openpyxl.worksheet.table import Table, TableStyleInfo

table = Table(displayName="Sales", ref="A1:D50")
table.tableStyleInfo = TableStyleInfo(
    name="TableStyleMedium9",
    showFirstColumn=False,
    showLastColumn=False,
    showRowStripes=True,
    showColumnStripes=False,
)
ws.add_table(table)

# List tables on a sheet
for tbl in ws._tables.values():
    print(tbl.displayName, tbl.ref)
```

## Named Ranges

```python
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import quote_sheetname

# Workbook-scoped
defn = DefinedName("TaxRate", attr_text="Assumptions!$B$3")
wb.defined_names["TaxRate"] = defn

# Sheet-scoped (localSheetId = index in wb.worksheets)
defn2 = DefinedName("LocalRate", attr_text="Sheet1!$A$1", localSheetId=0)
wb.defined_names["LocalRate"] = defn2

# Retrieve destinations
for dest in defn.destinations:
    sheet_name, cell_ref = dest
    ws = wb[sheet_name]
```

## Data Validation

```python
from openpyxl.worksheet.datavalidation import DataValidation

# Dropdown list from inline values
dv = DataValidation(type="list", formula1='"Yes,No,Maybe"', allow_blank=True)
ws.add_data_validation(dv)
dv.sqref = "B2:B100"

# Dropdown from a range
dv2 = DataValidation(type="list", formula1="$A$1:$A$5")
ws.add_data_validation(dv2)
dv2.sqref = "C2:C100"

# Whole number between 1 and 10
dv3 = DataValidation(type="whole", operator="between", formula1=1, formula2=10)
ws.add_data_validation(dv3)
dv3.sqref = "D2:D100"

# Date
dv4 = DataValidation(type="date", operator="greaterThan", formula1="2020-01-01")
ws.add_data_validation(dv4)
```

## Conditional Formatting

```python
from openpyxl.formatting.rule import (
    ColorScaleRule, DataBarRule, IconSetRule,
    CellIsRule, FormulaRule,
)
from openpyxl.styles import PatternFill, Font

# 3-color scale
ws.conditional_formatting.add("B2:B20", ColorScaleRule(
    start_type="min",   start_color="63BE7B",
    mid_type="percentile", mid_value=50, mid_color="FFEB84",
    end_type="max",     end_color="F8696B",
))

# Data bar
ws.conditional_formatting.add("C2:C20", DataBarRule(
    start_type="min", end_type="max",
    color="638EC6",
))

# Cell value rule: highlight <0 red
red_fill = PatternFill(fill_type="solid", fgColor="FFC7CE")
ws.conditional_formatting.add("D2:D20", CellIsRule(
    operator="lessThan", formula=["0"], fill=red_fill,
))

# Formula-based rule
ws.conditional_formatting.add("E2:E20", FormulaRule(
    formula=["MOD(ROW(),2)=0"],
    fill=PatternFill(fill_type="solid", fgColor="EEF0F4"),
))
```

## Images

```python
from openpyxl.drawing.image import Image

img = Image("logo.png")
img.width  = 200   # pixels
img.height = 100
ws.add_image(img, "A1")
```

Requires Pillow:  `pip install Pillow`

## Charts

openpyxl has a chart API but it is limited.  For complex charts, prefer
writing the data to the sheet and letting the user configure the chart
in Excel, or use a chart template (xlsm with embedded chart).

```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
chart.type = "col"          # "col" or "bar"
chart.title = "Sales"
chart.y_axis.title = "Amount"
chart.x_axis.title = "Month"

data = Reference(ws, min_col=2, min_row=1, max_col=2, max_row=13)
cats = Reference(ws, min_col=1, min_row=2, max_row=13)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.width  = 15   # cm
chart.height = 10

ws.add_chart(chart, "E2")
```

## Page Setup / Print

```python
from openpyxl.worksheet.page import PageMargins

ws.page_setup.orientation      = "landscape"  # "portrait" | "landscape"
ws.page_setup.paperSize        = 1            # 1=Letter, 9=A4
ws.page_setup.fitToPage        = True
ws.page_setup.fitToWidth       = 1
ws.page_setup.fitToHeight      = 0

ws.page_margins = PageMargins(left=0.7, right=0.7, top=0.75, bottom=0.75,
                               header=0.3, footer=0.3)

ws.print_title_rows = "1:1"    # repeat row 1 on each page
ws.print_title_cols = "A:A"   # repeat column A on each page

ws.print_area = "A1:H50"
```

## Headers and Footers

```python
ws.oddHeader.left.text   = "&A"          # sheet name
ws.oddHeader.center.text = "My Report"
ws.oddHeader.right.text  = "&D"          # date

ws.oddFooter.left.text   = "&F"          # filename
ws.oddFooter.center.text = "Page &P of &N"
ws.oddFooter.right.text  = "Confidential"
```

## pandas Integration

```python
import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import load_workbook

# Write DataFrame to worksheet (preserves other sheets)
wb = load_workbook("existing.xlsx")
ws = wb["Data"]
for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)
wb.save("existing.xlsx")

# Write multiple DataFrames with ExcelWriter
with pd.ExcelWriter("out.xlsx", engine="openpyxl") as writer:
    df1.to_excel(writer, sheet_name="Sheet1", index=False)
    df2.to_excel(writer, sheet_name="Sheet2", index=False, startrow=2)

# Read with pandas
df = pd.read_excel("in.xlsx", sheet_name="Sheet1", header=0, skiprows=1)
```

## Utility Functions

```python
from openpyxl.utils import (
    get_column_letter,          # 1 → "A"
    column_index_from_string,   # "A" → 1
    coordinate_from_string,     # "A1" → ("A", 1)
    coordinate_to_tuple,        # "A1" → (1, 1)
    range_boundaries,           # "A1:C3" → (1, 1, 3, 3) (min_col, min_row, max_col, max_row)
    quote_sheetname,            # "My Sheet" → "'My Sheet'"
    absolute_coordinate,        # "A1" → "$A$1"
)
```

## Known Limitations

- **No formula evaluation**: openpyxl never calculates formula results.
  Use LibreOffice or Excel to populate cached values.
- **data_only=True returns None** when cached values are absent (file was
  never saved by a recalculating engine).
- **No VBA editing**: macros in .xlsm are preserved (`keep_vba=True`) but
  not editable via openpyxl.
- **Chart read-back**: chart objects can be added but inspecting existing
  chart XML is limited.
- **Large files**: use `read_only=True` and `write_only=True` modes for
  streaming very large files.
