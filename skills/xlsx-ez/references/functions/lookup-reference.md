# Excel Lookup and Reference Functions

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## Modern Lookup (Excel 365+)

### XLOOKUP — Recommended replacement for VLOOKUP/HLOOKUP/INDEX-MATCH

`XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found], [match_mode], [search_mode])`

- **match_mode:** 0=exact (default), -1=exact or next smaller, 1=exact or next larger, 2=wildcard
- **search_mode:** 1=first-to-last (default), -1=last-to-first, 2=binary ascending, -2=binary descending

```excel
=XLOOKUP(D2, A:A, B:B)                       → basic exact match
=XLOOKUP(D2, A:A, B:B, "Not found")          → with default
=XLOOKUP(D2, A:A, B:B, , -1)                 → next smaller (approximate)
=XLOOKUP(D2, A:A, B2:E100, , , -1)           → return multiple columns, search last-to-first
```

### XMATCH — Recommended replacement for MATCH

`XMATCH(lookup_value, lookup_array, [match_mode], [search_mode])`

Returns the position (1-based) of a match. Same match_mode and search_mode as XLOOKUP.

```excel
=XMATCH("Alice", A:A)                → row position of "Alice"
=XMATCH(MAX(B:B), B:B)               → position of the maximum value
```

## Classic Lookups

### VLOOKUP

`VLOOKUP(lookup_value, table_array, col_index_num, [range_lookup])`

Searches the **first column** of table_array for lookup_value and returns a value from col_index_num. range_lookup=FALSE (exact) is almost always required.

```excel
=VLOOKUP(D2, $A$2:$C$100, 2, FALSE)   → exact match, return 2nd column
=VLOOKUP(D2, $A$2:$C$100, 3, TRUE)    → approximate match (table must be sorted ascending)
```

**Limitation:** Can only return columns to the right; breaks if columns are inserted.

### HLOOKUP

`HLOOKUP(lookup_value, table_array, row_index_num, [range_lookup])`

Like VLOOKUP but searches the **first row** and returns from row_index_num.

### INDEX + MATCH — Classic flexible lookup

`INDEX(array, [row_num], [column_num])` — Returns the value at a given row/column intersection.

`MATCH(lookup_value, lookup_array, [match_type])` — Returns the position of a value. match_type: 0=exact, 1=largest ≤ value (ascending), -1=smallest ≥ value (descending).

```excel
# Look up any column, immune to column insertions
=INDEX(B:B, MATCH(D2, A:A, 0))

# Two-way lookup
=INDEX(B2:E10, MATCH(G2, A2:A10, 0), MATCH(H2, B1:E1, 0))

# Return multiple columns (array)
=INDEX(B:D, MATCH(D2, A:A, 0), 0)
```

### LOOKUP

`LOOKUP(lookup_value, lookup_array, [return_array])` — Simplified lookup; requires sorted data. Better replaced by XLOOKUP.

## Dynamic Array Lookups (Excel 365+)

`FILTER(array, include, [if_empty])` — Returns all rows where include is TRUE.

```excel
=FILTER(A2:C100, B2:B100="North")                   → all rows in North region
=FILTER(A2:C100, (B2:B100="North")*(C2:C100>1000))  → AND condition
=FILTER(A2:C100, (B2:B100="North")+(C2:C100>5000))  → OR condition
=FILTER(A2:C100, B2:B100="North", "No results")      → with fallback
```

`SORT(array, [sort_index], [sort_order], [by_col])` — Returns array sorted by a column. sort_order: 1=ascending (default), -1=descending.

```excel
=SORT(A2:C100, 2, -1)                → sort by column 2 descending
=SORT(A2:C100, {2,3}, {1,-1})        → sort by col 2 asc, then col 3 desc
```

`SORTBY(array, sort_array1, [sort_order1], ...)` — Sorts array by values in a parallel sort_array (doesn't have to be part of the returned array).

```excel
=SORTBY(names, scores, -1)           → names sorted by corresponding scores descending
```

`UNIQUE(array, [by_col], [exactly_once])` — Returns distinct values.

```excel
=UNIQUE(A2:A100)                     → unique list
=UNIQUE(A2:A100, , TRUE)             → values that appear exactly once
```

## Navigation and Address Functions

`ADDRESS(row, column, [abs_num], [a1], [sheet_text])` — Returns a cell address as text. abs_num: 1=$A$1, 2=A$1, 3=$A1, 4=A1.

`INDIRECT(ref_text, [a1])` — Converts a text string to a live cell reference. Useful for dynamic sheet/range references but volatile (recalculates on every change).

```excel
=INDIRECT("Sheet" & A1 & "!B2")      → reference to a sheet named by A1
=INDIRECT(ADDRESS(ROW(),1))          → reference to column A of the current row
```

`OFFSET(reference, rows, cols, [height], [width])` — Returns a reference shifted from a starting point. Volatile — prefer INDEX for non-volatile alternatives.

```excel
=OFFSET(A1, 2, 3)                   → value at C3 (2 rows down, 3 columns right)
=OFFSET(A1, 0, 0, COUNTA(A:A), 1)  → dynamic range from A1 to last used cell
```

`INDEX(array, 0, col)` — Returns an entire column of an array (non-volatile alternative to OFFSET for column references).

## Row and Column Utilities

`ROW([reference])` — Returns the row number of a cell; ROW() returns the current row.

`ROWS(array)` — Returns the number of rows in an array or range.

`COLUMN([reference])` — Returns the column number of a cell.

`COLUMNS(array)` — Returns the number of columns in an array or range.

`AREAS(reference)` — Returns the number of contiguous areas in a multi-area reference.

`TRANSPOSE(array)` — Returns a transposed copy of an array (rows ↔ columns). In 365 spills automatically; in older versions requires Ctrl+Shift+Enter.

## Array Reshaping (Excel 365+)

`CHOOSECOLS(array, col_num1, [col_num2], ...)` — Returns specified columns from array.
```excel
=CHOOSECOLS(A1:E10, 1, 3, 5)        → columns A, C, E only
```

`CHOOSEROWS(array, row_num1, [row_num2], ...)` — Returns specified rows from array.

`HSTACK(array1, [array2], ...)` — Appends arrays side by side (horizontally).
```excel
=HSTACK(A1:B5, D1:E5)               → 4-column combined array
```

`VSTACK(array1, [array2], ...)` — Appends arrays one below the other (vertically).
```excel
=VSTACK(Jan_data, Feb_data, Mar_data)
```

`TAKE(array, rows, [columns])` — Returns the first (positive) or last (negative) N rows/columns.
```excel
=TAKE(A1:C100, 10)                  → first 10 rows
=TAKE(A1:C100, -5)                  → last 5 rows
```

`DROP(array, rows, [columns])` — Returns array with the first (positive) or last (negative) N rows/columns removed.

`EXPAND(array, rows, cols, [pad_value])` — Pads array to specified dimensions.

`TOCOL(array, [ignore], [scan_by_col])` — Converts a 2D array to a single column. ignore: 0=none, 1=blanks, 2=errors, 3=both.

`TOROW(array, [ignore], [scan_by_col])` — Converts a 2D array to a single row.

`WRAPROWS(array, wrap_count, [pad_value])` — Reshapes a 1D array into a 2D array with wrap_count values per row.

`WRAPCOLS(array, wrap_count, [pad_value])` — Reshapes a 1D array into a 2D array with wrap_count values per column.

## Other Reference Functions

`FORMULATEXT(reference)` — Returns the formula in the referenced cell as a text string. Returns #N/A if the cell has no formula.

`GETPIVOTDATA(data_field, pivot_table, [field1, item1], ...)` — Retrieves a specific value from a PivotTable. Excel auto-inserts this when you click a PivotTable cell in a formula.

`HYPERLINK(link_location, [friendly_name])` — Creates a clickable hyperlink. link_location can be a URL, file path, or cell reference (`"#Sheet1!A1"`).

`RTD(progID, server, topic1, [topic2], ...)` — Retrieves real-time data from a COM server (rarely used outside financial data feeds).

## Common Patterns

```excel
# Two-column lookup returning multiple fields
=XLOOKUP(id, A:A, B:E)              → spills all 4 matching columns

# Case-insensitive lookup
=XMATCH(LOWER(D2), LOWER(A:A))

# Reverse lookup (value → key)
=XLOOKUP(target_value, B:B, A:A)

# Find last occurrence
=XLOOKUP(D2, A:A, B:B, , 0, -1)

# Dynamic top-N list
=TAKE(SORT(A2:B100, 2, -1), 10)     → top 10 rows by column B

# Distinct sorted list
=SORT(UNIQUE(A2:A100))

# Filter and stack two ranges
=VSTACK(
  FILTER(A2:C50, D2:D50="North"),
  FILTER(A2:C50, D2:D50="South")
)
```
