# Calculation syntax in detail

See the following sections to learn more about the different components of Tableau calculations and how to format them to work in Tableau.

## Function syntax

Functions are the main components of a calculation and can be used for various purposes.

Every function in Tableau requires a particular syntax. For example, the following calculation uses two functions, `LEN` and `LEFT`, as well as several logical operators (`IF`, `THEN`, `ELSE`, `END`, and `>` ).

`IF LEN([Name])> 5 THEN LEFT([Name],5) ELSE [Name] END`

* `LEN` takes a single argument, such as `LEN([Name])` which returns the number of characters (that is, the length) for each value in the Name field.
* `LEFT` takes two arguments, a field and a number, such as `LEFT([Name], 5)` which returns the first five characters from each value in the Name field starting from the left.
* The logical operators `IF`, `THEN`, `ELSE`, and `END` work together to create a logical test.

This calculation evaluates the length of a name and, if it's more than five characters, returns only the first five. Otherwise, it returns the entire name.

In the calculation editor, functions are colored blue.

#### Using multiple functions in a calculation

You can use more than one function in a calculation. For example:

`IF SUM([Sales]) != 0 THEN SUM([Profit]) / SUM([Sales]) END`

There are three functions in the calculation: IF, and two uses of SUM. The two SUM aggregations are separated with the division operator (/).

A function can also be part of another function (or, nested). In the example above, `SUM([Sales])` is computed before the division because it is inside parentheses. For more information on why, see Parentheses.

### Field syntax

Fields can be inserted into your calculations. Often, a function's syntax indicates where a field should be inserted into the calculation. For example: `SUM(expression)`.

Field names should be encompassed by brackets [ ] in a calculation when the field name contains a space or is not unique. For example, [Sales Categories].

The type of function you use determines the type of field you use. For example, with the SUM function, you can insert a numerical field, but you cannot insert a date field. For more information, see Understanding data types in calculations.

The fields you choose to include in your calculations also depend on the purpose of calculation. For example, if you want to calculate profit ratio your calculation will use the Sales and Profit fields from your data source:

`SUM([Sales])/SUM([Profit])`

Fields are colored orange in Tableau calculations.

### Operator syntax

To create calculations, you need to understand the operators supported by Tableau. This section discusses the basic operators that are available and the order (precedence) they are performed.

Operators are colored black in Tableau calculations.

#### + (addition)

The + operator means addition when applied to numbers and concatenation when applied to strings. When applied to dates, it can be used to add a number of days to a date.

For example:

* `7 + 3`
* `Profit + Sales`
* `'abc' + 'def' = 'abcdef'`
* `#April 15, 2024# + 15 = #April 30, 2024#`

#### – (subtraction)

The - operator means subtraction when applied to numbers and negation if applied to an expression. When applied to dates, it can be used to subtract a number of days from a date. Hence, it can also be used to calculate the difference in days between two dates.

For example:

* `7 - 3`
* `Profit - Sales`
* `-(7+3) = -10`
* `#April 16, 2024# - 15 = #April 1, 2024#`
* `#April 15, 2024# - #April 8, 2024# = 7`

#### \* (multiplication)

The \* operator means numeric multiplication.

For example: `5 * 4 = 20`

#### / (division)

The / operator means numeric division.

For example: `20 / 4 = 5`

#### % (modulo)

The % operator returns the remainder of a division operation. Modulo can only operate on integers.

For example: `9 % 2 = 1`. (Because 2 goes into 9 four times with a remainder of 1.)

#### ==, =, >, <, >=, <=, !=, <> (comparisons)

These are the basic comparison operators that can be used in expressions.

Their meanings are as follows:

* **==** or **=** (equal to)
* **>** (greater than)
* **<** (less than)
* **>=** (greater than or equal to)
* **<=** (less than or equal to)
* **!=** or **<>** (not equal to)

Each operator compares two numbers, dates, or strings and returns either TRUE, FALSE, or NULL.

#### ^ (power)

This symbol is equivalent to the POWER function. It raises a number to the specified power.

For example: `6^3 = 216`

#### AND

This is a logical operator. An expression or a boolean must appear on either side of it.

For example: `IIF(Profit=100 AND Sales =1000, "High", "Low")`

See `AND` in Logical Functions for more information.

#### OR

This is a logical operator. An expression or a boolean must appear on either side of it.

For example: `IIF(Profit=100 OR Sales =1000, "High", "Low")`

See `OR` in Logical Functions for more information.

#### NOT

This is a logical operator. It can be used to negate another boolean or an expression. For example,

`IIF(NOT(Sales = Profit),"Not Equal","Equal")`

#### Other Operators

CASE, ELSE, ELSEIF, IF, THEN, WHEN, and END are also operators used for Logical Functions.

### Operator precedence

All operators in a calculation are evaluated in a specific order. For example, `2*1+2` is equal to 4 and not equal to 6, because multiplication is performed before addition (the \* operator is always evaluated before the + operator).

If two operators have the same precedence such as addition and subtraction (+ or -) they are evaluated from left to right in the calculation.

Parentheses can be used to change the order of precedence. See the Parentheses section for more information.

| Precedence | Operator |
| --- | --- |
| 1 | – (negate) |
| 2 | ^ (power) |
| 3 | \*, /, % |
| 4 | +, – |
| 5 | ==, =, >, <, >=, <=, !=, <> |
| 6 | NOT |
| 7 | AND |
| 8 | OR |

#### Parentheses

Parentheses can be used as needed to force an order of precedence. Operators that appear within parentheses are evaluated before those outside of parentheses, starting from the innermost parentheses and moving outward.

For example, (1 + (2\*2+1)\*(3\*6/3) ) = 31 because the operators within the innermost parentheses are performed first. The calculation is calculated in the following order:

1. (2\*2+1) = 5
2. (3\*6/3) = 6
3. (1+ 5\*6) = 31

### Literal expression syntax

This section describes the proper syntax for using literal expressions in Tableau calculations. A literal expression signifies a constant value that is represented as is. When you are using functions you will sometimes want to use literal expressions to represent numbers, strings, dates, and more.

For example, you may have a function where your input is a date. Rather than type "May 1, 2005", which would be interpreted a string, you would type #May 1, 2005#. This is equivalent to using a date function to convert the argument from a string to a date (refer to Date Functions).

You can use numeric, string, date, boolean, and null literals in Tableau calculations. Each type, and how to format them, are described below.

Literal expressions are colored black and gray in Tableau calculations.

#### Numeric Literals

A numeric literal is written as a number. For example, to input the number one as a numeric literal, enter `1`. If you want to input the number 0.25 as a numeric literal, enter `0.25`.

#### String Literals

A string literal can be written either using 'single quote' or "double quote".

If your string has a single or double quote within it, use the other option for the outermost string literals.

For example, to input the string `"cat"` as a string literal, type`'"cat"'`. For `'cat'` type `"'cat'"`. If you want to type the string `She's my friend` as a string literal, use double quotes for the literals, as in `"She's my friend."`

#### Date Literals

> **VDS Note**: In VDS filter values and date comparisons, use RFC 3339 format strings (e.g., `"2020-01-15"`), not Tableau's `#date#` literal syntax. Tableau `#date#` syntax is used in Tableau Desktop calculations but is not valid in VDS API requests.

#### Boolean Literals

Boolean literals are written as either true or false. To input "true" as a boolean literal, enter `true`.

#### Null Literals

Null literals are written as Null. To input "Null" as a Null literal, enter `Null`.

### Add parameters to a calculation

Parameters are placeholder variables that can be inserted into calculations to replace constant values. When you use a parameter in a calculation, you can then expose a parameter control in a view or dashboard to allow users to dynamically change the value.

For details, see [PARAMETERS.md](../PARAMETERS.md).

### Add comments to a calculation

You can add comments to a calculation to make notes about it or its parts. Comments are not included in the computation of the calculation.

To add a comment to a calculation, type two forward slash (//) characters.

For example:

`SUM([Sales])/SUM([Profit]) //My calculation`

In this example, `//My calculation` is a comment.

A comment starts at the two forward slashes (//) and goes to the end of the line. To continue with your calculation, you must start a new line.

A multi-line comment can be written by starting the comment with a forward slash followed by an asterisk (/\*), and closed with an asterisk followed by a forward slash (\*/). For example:

```
SUM([Sales])/SUM([Profit])
/* This calculation is
used for profit ratio.
Do not edit */
```

Comments are colored gray in Tableau calculations.
