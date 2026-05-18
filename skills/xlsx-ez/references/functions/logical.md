# Excel Logical Functions

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## Boolean Constants

`TRUE()` — Returns the logical value TRUE. Usually written without parentheses as a literal.

`FALSE()` — Returns the logical value FALSE. Usually written without parentheses as a literal.

## Conditionals

`IF(logical_test, [value_if_true], [value_if_false])` — Returns one value if the condition is TRUE, another if FALSE. Both branches are optional (omitted branches return 0 or FALSE).

`IFS(test1, value1, [test2, value2], ...)` — Checks conditions in sequence and returns the value for the first TRUE condition. Cleaner than nested IF for multiple branches. No explicit else; add a final `TRUE, default_value` to catch the remainder.

`SWITCH(expression, value1, result1, [value2, result2], ..., [default])` — Compares an expression against a list of values and returns the matching result. Last argument with no matching value becomes the default.

## Error Handling

`IFERROR(value, value_if_error)` — Returns value_if_error if the expression produces any error, otherwise returns the value. The go-to for wrapping VLOOKUP, XLOOKUP, MATCH, and division.

`IFNA(value, value_if_na)` — Like IFERROR but only traps #N/A errors; other errors propagate normally. Useful when #N/A specifically means "not found" and other errors should remain visible.

## Logical Operators

`AND(logical1, [logical2], ...)` — Returns TRUE only if **all** arguments are TRUE. Short-circuits to FALSE on the first FALSE.

`OR(logical1, [logical2], ...)` — Returns TRUE if **any** argument is TRUE. Short-circuits to TRUE on the first TRUE.

`NOT(logical)` — Reverses the logical value: TRUE→FALSE, FALSE→TRUE.

**Note:** AND/OR/NOT are often used inside IF rather than standalone:
```excel
=IF(AND(A1>0, B1>0), "Both positive", "No")
=IF(OR(A1="Yes", A1="Y"), "Confirmed", "Pending")
```

## Lambda-Based Functions (Excel 365+)

These functions require Microsoft 365 / Excel for the web and may not be available
in older Excel versions or LibreOffice.

### Defining Custom Functions

`LAMBDA([parameter1, parameter2, ...], calculation)` — Creates a reusable custom function without VBA. Define once in a Named Range, call anywhere.

```excel
# Define "Discount" in Name Manager:
=LAMBDA(price, rate, price * (1 - rate))

# Use:
=Discount(A2, 10%)
```

`LET(name1, value1, [name2, value2, ...], calculation)` — Assigns intermediate calculation results to named variables. Avoids repeating the same sub-expression and improves readability.

```excel
=LET(
  sales,   B2:B13,
  target,  C2,
  ratio,   SUM(sales)/target,
  IF(ratio >= 1, "Met", "Behind")
)
```

### Higher-Order Array Functions

These accept a LAMBDA as an argument to transform arrays.

`MAP(array1, [array2, ...], lambda)` — Applies a LAMBDA to each element (or corresponding elements) of one or more arrays and returns a same-sized result array.

```excel
=MAP(A1:A10, LAMBDA(x, x * x))      → squares each value
=MAP(A1:A5, B1:B5, LAMBDA(a,b, a+b)) → element-wise sum
```

`REDUCE([initial_value], array, lambda)` — Accumulates a single value by repeatedly calling LAMBDA(accumulator, element) across the array.

```excel
=REDUCE(0, A1:A10, LAMBDA(acc, x, acc + x))   → equivalent to SUM
=REDUCE(1, A1:A5, LAMBDA(acc, x, acc * x))    → product
```

`SCAN([initial_value], array, lambda)` — Like REDUCE but returns all intermediate values (running total, running max, etc.).

```excel
=SCAN(0, A1:A10, LAMBDA(acc, x, acc + x))     → running total array
```

`BYCOL(array, lambda)` — Applies LAMBDA to each column of array and returns a 1-row result.

```excel
=BYCOL(A1:D10, LAMBDA(col, SUM(col)))          → sum of each column
```

`BYROW(array, lambda)` — Applies LAMBDA to each row of array and returns a 1-column result.

```excel
=BYROW(A1:D10, LAMBDA(row, MAX(row)))           → max of each row
```

`MAKEARRAY(rows, cols, lambda)` — Creates a rows×cols array by calling LAMBDA(row_num, col_num) for each cell position.

```excel
=MAKEARRAY(5, 5, LAMBDA(r, c, r * c))          → multiplication table
```

## Common Patterns

```excel
# Multi-branch without nested IF
=IFS(score>=90,"A", score>=80,"B", score>=70,"C", TRUE,"F")

# SWITCH on a category code
=SWITCH(status, "O","Open", "C","Closed", "P","Pending", "Unknown")

# Safe division
=IFERROR(numerator/denominator, 0)

# Safe VLOOKUP with default
=IFERROR(VLOOKUP(id, table, 2, 0), "—")

# Exclusive OR (one but not both)
=AND(OR(A1,B1), NOT(AND(A1,B1)))

# All conditions met in a range
=AND(A1:A10 > 0)    ← array formula; Ctrl+Shift+Enter in older Excel

# Reusable named LAMBDA: percentage change
# Name: PctChg = LAMBDA(old, new, (new-old)/old)
=PctChg(A1, B1)
```
