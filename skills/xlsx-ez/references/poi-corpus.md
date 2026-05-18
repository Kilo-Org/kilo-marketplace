# Apache POI Spreadsheet Test Corpus

Test files for .xlsx quality benchmarking, located at:
`/home/user/poi/test-data/spreadsheet/`

Source: https://github.com/apache/poi/tree/trunk/test-data/spreadsheet

The corpus contains 347 `.xlsx` / `.xlsm` files covering a wide range of
SpreadsheetML features.

---

## File Index by Category

### Formulas

| File | Feature |
|------|---------|
| `50755_workday_formula_example.xlsx` | WORKDAY date formula |
| `FormulaEvalTestData_Copy.xlsx` | Formula evaluation |
| `FormulaSheetRange.xlsx` | Cross-sheet formula ranges |
| `MatrixFormulaEvalTestData.xlsx` | Array formulas |
| `NewlineInFormulas.xlsx` | Newlines inside formula strings |
| `DataTableCities.xlsx` | Data table (what-if analysis) |

### Formatting

| File | Feature |
|------|---------|
| `50784-font_theme_colours.xlsx` | Font theme color references |
| `50786-indexed_colours.xlsx` | Indexed (palette) colors |
| `50846-border_colours.xlsx` | Border color formatting |
| `FillWithoutColor.xlsx` | Pattern fills without explicit color |
| `Formatting.xlsx` | General cell formatting |
| `SheetTabColors.xlsx` | Colored sheet tabs |
| `NumberFormatTests.xlsx` | Number format codes |
| `NumberFormatApproxTests.xlsx` | Approximate number formatting |
| `DateFormatTests.xlsx` | Date format codes |
| `DateFormatNumberTests.xlsx` | Date/number combined formats |
| `ElapsedFormatTests.xlsx` | Elapsed time formats ([h]:mm:ss) |
| `GeneralFormatTests.xlsx` | General format type |
| `FormatChoiceTests.xlsx` | Conditional format choice |
| `FormatKM.xlsx` | K/M magnitude formatting |
| `HeaderFooterComplexFormats.xlsx` | Complex header/footer format codes |

### Conditional Formatting

| File | Feature |
|------|---------|
| `55406_Conditional_formatting_sample.xlsx` | Basic conditional formatting |
| `61060-conditional-number-formatting.xlsx` | Number-format-based CF rules |
| `ConditionalFormattingSamples.xlsx` | Various CF rule types |
| `NewStyleConditionalFormattings.xlsx` | Excel 2010+ CF styles |
| `FormatConditionTests.xlsx` | Condition type coverage |

### Tables and Pivot

| File | Feature |
|------|---------|
| `50867_with_table.xlsx` | Single ListObject table |
| `ExcelTables.xlsx` | Multiple table styles |
| `ExcelPivotTableSample.xlsx` | Pivot table |

### Charts

| File | Feature |
|------|---------|
| `123233_charts.xlsx` | Chart objects |

### Miscellaneous

| File | Feature |
|------|---------|
| `0-www-crossref-org.lib.rivier.edu_education-files_suffix-generator.xlsm` | Macro-enabled workbook |
| `1_NoIden.xlsx` | Workbook without identification |
| `45430.xlsx` – `50096.xlsx` | Apache POI bug regression files |

---

## Running the Benchmark

```bash
# Run all checks on all xlsx files
python benchmark.py --poi /home/user/poi/test-data/spreadsheet/ --output results.json

# Single file
python benchmark.py --poi /home/user/poi/test-data/spreadsheet/ExcelTables.xlsx --mode tables

# Specific mode on a directory
python benchmark.py --poi /home/user/poi/test-data/spreadsheet/ --mode formats
```

### Available Modes

| Mode | What it checks |
|------|---------------|
| `all` | Auto-detect per filename (default) |
| `formulas` | Presence of `<f>` formula elements |
| `tables` | Presence of `xl/tables/*.xml` parts |
| `charts` | Presence of `xl/charts/*.xml` parts |
| `formats` | Non-trivial fonts/fills/borders in styles.xml |

### Mode Auto-Detection Heuristics

| Filename contains | Mode assigned |
|-------------------|---------------|
| formula, workday, function, calc | `formulas` |
| table, listobject | `tables` |
| chart, graph, plot | `charts` |
| colour, color, font, border, fill, format, style | `formats` |
| (anything else) | `all` |

---

## Interpreting Results

```
PASS: /path/to/file.xlsx
  ✓ zip-readable
  ✓ workbook-xml
  ✓ sheets-parseable: 3 sheet(s)
  ✓ has-formulas: 42 formula cell(s)

FAIL: /path/to/other.xlsx
  ✓ zip-readable
  ✓ workbook-xml
  ✓ sheets-parseable: 1 sheet(s)
  ✗ has-tables: 0 table part(s)
```

A file **passes** if all applicable checks succeed.  The `all` mode runs
zip-readable, workbook-xml, and sheets-parseable on every file, plus
feature-specific checks based on the filename heuristic.

---

## Baseline Pass Rates (observed)

Running `--mode all` (auto-detect) on the full corpus:

| Check | Expected behavior |
|-------|------------------|
| `zip-readable` | All .xlsx pass — invalid ZIPs would indicate corpus corruption |
| `workbook-xml` | All .xlsx pass |
| `sheets-parseable` | All standard files pass; deeply nested structures require `huge_tree=True` |
| Feature checks | Vary — a formatting file won't have formulas, etc. |

The benchmark intentionally runs the **applicable** check per file based
on the heuristic, so a formatting file is not penalized for lacking formulas.
