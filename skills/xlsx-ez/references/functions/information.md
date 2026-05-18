# Excel Information Functions

Information functions return metadata about cells, values, and the environment.
The IS* family returns TRUE/FALSE and is especially useful in error-handling formulas.

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## IS* Type-Testing Functions

`ISBLANK(value)` — TRUE if the cell is empty.

`ISNUMBER(value)` — TRUE if the value is a number.

`ISTEXT(value)` — TRUE if the value is text.

`ISNONTEXT(value)` — TRUE if the value is anything other than text (including blank).

`ISLOGICAL(value)` — TRUE if the value is TRUE or FALSE.

`ISREF(value)` — TRUE if the value is a valid cell reference.

`ISFORMULA(reference)` — TRUE if the cell contains a formula.

`ISEVEN(number)` — TRUE if the number is even. *Note: also in Math category.*

`ISODD(number)` — TRUE if the number is odd. *Note: also in Math category.*

`ISOMITTED(value)` — TRUE if the value was omitted (used inside LAMBDA to handle optional parameters).

## IS* Error-Testing Functions

`ISERROR(value)` — TRUE if the value is any error (#VALUE!, #REF!, #DIV/0!, #N/A, #NAME?, #NULL!, #NUM!).

`ISERR(value)` — TRUE if the value is any error **except** #N/A. Useful when #N/A is a valid "not found" signal.

`ISNA(value)` — TRUE if the value is the #N/A error specifically.

`ERROR.TYPE(error_val)` — Returns a number identifying the error type:
  - 1 = #NULL!
  - 2 = #DIV/0!
  - 3 = #VALUE!
  - 4 = #REF!
  - 5 = #NAME?
  - 6 = #NUM!
  - 7 = #N/A
  - 8 = #GETTING_DATA
  - #N/A = not an error

## Value Information

`CELL(info_type, [reference])` — Returns information about a cell's formatting, location, or contents.

Common info_type values:
| info_type | Returns |
|-----------|---------|
| "address" | Absolute reference as text |
| "col" | Column number |
| "row" | Row number |
| "contents" | Cell value |
| "type" | "b"=blank, "l"=label/text, "v"=value |
| "format" | Number format code |
| "protect" | 1 if locked, 0 if not |
| "filename" | Full path and filename |
| "width" | Column width in characters |

`TYPE(value)` — Returns a number indicating the data type:
  - 1 = number
  - 2 = text
  - 4 = logical (TRUE/FALSE)
  - 8 = formula
  - 16 = error
  - 64 = array

`N(value)` — Converts a value to a number. TRUE→1, FALSE→0, text→0, date→serial. Rarely needed; mainly used to embed comments: `=SUM(A1:A10) + N("sum of sales")`.

`NA()` — Returns the #N/A error value deliberately (marks a cell as intentionally missing data).

## Sheet and Workbook Information

`SHEET([value])` — Returns the sheet number of a reference or the current sheet if omitted.

`SHEETS([reference])` — Returns the number of sheets in a reference, or the total sheet count if omitted.

`INFO(type_text)` — Returns information about the operating environment:
  - "directory" — current directory path
  - "numfile" — number of active worksheets
  - "osversion" — operating system version
  - "recalc" — recalculation mode ("Automatic" or "Manual")
  - "release" — Excel version number
  - "system" — "mac" or "pcdos"

## Common Patterns

```excel
# Guard against division by zero
=IF(ISERROR(A1/B1), 0, A1/B1)
# Simpler with IFERROR:
=IFERROR(A1/B1, 0)

# Only sum cells that contain numbers (ignore text/blanks)
=SUMIF(A1:A10, ">0") + SUMIF(A1:A10, "<0")
# Or: SUMPRODUCT with ISNUMBER:
=SUMPRODUCT(ISNUMBER(A1:A10)*A1:A10)

# Detect if a VLOOKUP returned a result
=IF(ISNA(VLOOKUP(D1,A:B,2,0)), "Not found", VLOOKUP(D1,A:B,2,0))
# Simpler:
=IFERROR(VLOOKUP(D1,A:B,2,0), "Not found")

# Show formula text for auditing
=FORMULATEXT(A1)       ← returns e.g. "=SUM(B1:B10)"
```
