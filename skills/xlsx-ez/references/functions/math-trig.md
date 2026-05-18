# Excel Math and Trigonometry Functions

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## Summation

`SUM(number1, [number2], ...)` — Adds all numbers in a range or list. Ignores text and blanks.

`SUMIF(range, criteria, [sum_range])` — Adds values where a single condition is met. If sum_range is omitted, sums range itself.
```excel
=SUMIF(A:A, "North", C:C)           → sum C where A="North"
=SUMIF(B:B, ">1000", C:C)           → sum C where B>1000
=SUMIF(A:A, "*east*", C:C)          → wildcard: contains "east"
```

`SUMIFS(sum_range, range1, criteria1, [range2, criteria2], ...)` — Adds values where **all** conditions are met.
```excel
=SUMIFS(C:C, A:A,"North", B:B,">1000")
```

`SUMPRODUCT(array1, [array2], ...)` — Multiplies corresponding elements of arrays then sums. The Swiss Army knife of aggregation — works like an array formula without Ctrl+Shift+Enter.
```excel
=SUMPRODUCT(units, price)                           → total revenue
=SUMPRODUCT((region="North")*(sales>1000)*sales)    → conditional sum
=SUMPRODUCT((A2:A100="X")/COUNTIF(A2:A100,A2:A100)) → count unique "X"s
```

`SUMSQ(number1, [number2], ...)` — Returns the sum of squares of all arguments.

`SUMX2MY2(array_x, array_y)` — Sum of (x² − y²) for corresponding pairs.

`SUMX2PY2(array_x, array_y)` — Sum of (x² + y²) for corresponding pairs.

`SUMXMY2(array_x, array_y)` — Sum of (x − y)² for corresponding pairs.

`SUBTOTAL(function_num, ref1, [ref2], ...)` — Applies a function to a range, **ignoring other SUBTOTAL cells** and optionally hidden rows.

| function_num | Function | (Hidden rows ignored) |
|---|---|---|
| 1 (101) | AVERAGE | 101 ignores hidden |
| 2 (102) | COUNT | |
| 3 (103) | COUNTA | |
| 4 (104) | MAX | |
| 5 (105) | MIN | |
| 6 (106) | PRODUCT | |
| 7 (107) | STDEV | |
| 9 (109) | SUM | |
| 11 (111) | VAR | |

`AGGREGATE(function_num, option, ref1, ...)` — Like SUBTOTAL but supports more functions (1–19) and options to ignore errors, hidden rows, nested subtotals, or any combination.

## Rounding

`ROUND(number, num_digits)` — Rounds to num_digits decimal places. num_digits can be negative to round to tens, hundreds, etc.

`ROUNDUP(number, num_digits)` — Rounds away from zero (always up in magnitude).

`ROUNDDOWN(number, num_digits)` — Rounds toward zero (always down in magnitude).

`INT(number)` — Rounds down to the nearest integer (toward −∞). INT(-2.3) = −3.

`TRUNC(number, [num_digits])` — Truncates toward zero. TRUNC(-2.3) = −2.

`CEILING(number, significance)` — Rounds up to the nearest multiple of significance.

`CEILING.MATH(number, [significance], [mode])` — Rounds up; mode=1 rounds negative numbers toward zero.

`CEILING.PRECISE(number, [significance])` — Always rounds toward +∞.

`ISO.CEILING(number, [significance])` — ISO version of CEILING.PRECISE.

`FLOOR(number, significance)` — Rounds down to the nearest multiple of significance.

`FLOOR.MATH(number, [significance], [mode])` — Rounds down; mode=1 rounds negative numbers away from zero.

`FLOOR.PRECISE(number, [significance])` — Always rounds toward −∞.

`MROUND(number, multiple)` — Rounds to the nearest multiple (standard rounding, not always up/down).

`EVEN(number)` — Rounds up to the nearest even integer.

`ODD(number)` — Rounds up to the nearest odd integer.

## Basic Arithmetic

`ABS(number)` — Absolute value.

`SIGN(number)` — Returns −1, 0, or 1.

`MOD(number, divisor)` — Remainder after division. Result has the same sign as divisor.

`QUOTIENT(numerator, denominator)` — Integer portion of division (truncates toward zero).

`POWER(number, power)` — Equivalent to the ^ operator. POWER(2,10) = 1024.

`SQRT(number)` — Square root. Equivalent to POWER(number, 0.5).

`SQRTPI(number)` — Square root of number × π.

`PRODUCT(number1, [number2], ...)` — Product of all arguments.

`GCD(number1, [number2], ...)` — Greatest common divisor.

`LCM(number1, [number2], ...)` — Least common multiple.

## Logarithms and Exponentials

`EXP(number)` — Returns eⁿ (Euler's number raised to the power n).

`LN(number)` — Natural logarithm (base e).

`LOG(number, [base])` — Logarithm to a specified base (default 10).

`LOG10(number)` — Base-10 logarithm.

## Combinatorics

`FACT(number)` — Factorial (n!).

`FACTDOUBLE(number)` — Double factorial (n!! = n × (n−2) × (n−4) × …).

`COMBIN(number, number_chosen)` — Number of combinations C(n, k) = n! / (k! × (n−k)!). Order does not matter.

`COMBINA(number, number_chosen)` — Combinations with repetition.

`PERMUT(number, number_chosen)` — Number of permutations P(n, k) = n! / (n−k)!. Order matters.

`MULTINOMIAL(number1, [number2], ...)` — Multinomial coefficient (n1+n2+…)! / (n1! × n2! × …).

`SERIESSUM(x, n, m, coefficients)` — Sum of a power series: Σ(coefficients[i] × x^(n + m×i)).

## Number Representation

`ROMAN(number, [form])` — Converts to Roman numeral text. form 0=classic, 4=simplified.

`ARABIC(text)` — Converts Roman numeral text to a number.

`BASE(number, radix, [min_length])` — Converts to a text string in the given radix (2–36).

`DECIMAL(text, radix)` — Converts a text string in the given radix to a decimal number.

## Random Numbers

`RAND()` — Returns a uniform random number in [0, 1). Volatile — recalculates on every change. To freeze: paste as values.

`RANDBETWEEN(bottom, top)` — Returns a random integer between bottom and top (inclusive). Volatile.

`RANDARRAY([rows], [columns], [min], [max], [integer])` — Returns an array of random numbers. integer=TRUE for whole numbers.

## Dynamic Array Generators (Excel 365+)

`SEQUENCE(rows, [columns], [start], [step])` — Generates a numeric sequence spilling into rows×columns cells.
```excel
=SEQUENCE(10)                        → 1 to 10 in a column
=SEQUENCE(5, 4, 0, 0.25)             → 5×4 grid starting at 0, step 0.25
=SEQUENCE(1, 12, DATE(2024,1,1), 30) → approximate monthly dates
```

## Trigonometry

All trig functions use **radians**. Multiply degrees by PI()/180 or use RADIANS().

`PI()` — Returns π ≈ 3.14159265358979.

`RADIANS(degrees)` — Converts degrees to radians.

`DEGREES(radians)` — Converts radians to degrees.

`SIN(number)` / `COS(number)` / `TAN(number)` — Basic trig functions.

`ASIN(number)` / `ACOS(number)` / `ATAN(number)` — Inverse trig (return radians).

`ATAN2(x_num, y_num)` — Two-argument arctangent; returns angle in radians for the point (x, y). Handles all quadrants correctly.

`SINH(number)` / `COSH(number)` / `TANH(number)` — Hyperbolic functions.

`ASINH(number)` / `ACOSH(number)` / `ATANH(number)` — Inverse hyperbolic functions.

`COT(number)` / `COTH(number)` — Cotangent / hyperbolic cotangent.

`ACOT(number)` / `ACOTH(number)` — Inverse cotangent / hyperbolic.

`SEC(number)` / `SECH(number)` — Secant / hyperbolic secant.

`CSC(number)` / `CSCH(number)` — Cosecant / hyperbolic cosecant.

## Matrix Operations

`MDETERM(array)` — Matrix determinant.

`MINVERSE(array)` — Matrix inverse. Returns array; enter with Ctrl+Shift+Enter in older Excel.

`MMULT(array1, array2)` — Matrix multiplication. Columns of array1 must equal rows of array2.

`MUNIT(dimension)` — Returns the identity matrix of dimension × dimension.

## Common Patterns

```excel
# Round to nearest 5
=MROUND(A1, 5)

# Round price up to nearest cent
=CEILING(A1, 0.01)

# Round down to nearest quarter hour
=FLOOR(A1*96, 1)/96              ← A1 is a time fraction

# Weighted average
=SUMPRODUCT(weights, values) / SUM(weights)

# Count distinct values
=SUMPRODUCT(1/COUNTIF(A2:A100, A2:A100))

# Running percentage of total
=SUM($B$2:B2) / SUM($B$2:$B$100)

# Hypotenuse
=SQRT(SUMSQ(A1, B1))
# Or:
=SQRT(A1^2 + B1^2)

# Distance between two coordinates
=SQRT(SUMXMY2(coords1, coords2))
```
