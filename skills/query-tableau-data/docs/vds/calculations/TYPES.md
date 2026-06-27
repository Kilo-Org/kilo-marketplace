# Understanding data types in calculations

If you create calculated fields, you need to know how to use and combine the different data types(Link opens in a new window) in calculations. Many functions that are available to you when you define a calculation only work when they are applied to specific data types.

For example, the `DATEPART()` function can accept only a date data type as an argument. You can enter `DATEPART('year', DATE("2024-04-15"))` and expect a valid result: 2024. You cannot enter `DATEPART('year',"Tom Sawyer")` and expect a valid result. In fact, this example returns an error because "`Tom Sawyer`" is a string, not a date.

**Note**: Although Tableau attempts to fully validate all calculations, some data type errors cannot be found until the query is run against the database. These issues appear as error dialogs at the time of the query rather than in the calculation dialog box.

The data types supported by Tableau are described below. Refer to [TYPE.md](./functions/TYPE.md) to learn about converting from one data type to another.

### String

A sequence of zero or more characters. For example, "`Wisconsin`", "`ID-44400`", and "`Tom Sawyer`" are all strings. Strings are recognized by single or double quotes. The quote character itself can be included in a string by repeating it. For example, `'O''Hanrahan'`.

### Date

A date value. For example, `"January 23, 1972"`. In VDS queries, dates must be expressed as RFC 3339 format strings (e.g., `"2020-01-15"`). VDS does not support datetime — only date.

> **VDS Note**: VDS does not support datetimes. Calculations that produce datetime output will fail. Use date functions that return dates (e.g., `TODAY()`, `DATE()`, `MAKEDATE()`) rather than datetime functions.

### Number

Numerical values in Tableau can be either *integers* or *floating-point numbers*.

With floating-point numbers, results of some aggregations may not always be exactly as expected. For example, you may find that the SUM function returns a value such as -1.42e-14 for a field of numbers that you know should sum to exactly 0. This happens because the Institute of Electrical and Electronics Engineers (IEEE) 754 floating-point standard requires that numbers be stored in binary format, which means that numbers are sometimes rounded at extremely fine levels of precision. You can eliminate this potential distraction by formatting the number to show fewer decimal places. For more information, see ROUND in Number functions available in Tableau.

Operations that test floating point values for equality can behave unpredictably for the same reason. Such comparisons can occur when using level of detail expressions as dimensions, in categorical filtering, creating ad-hoc groups, creating IN/OUT sets, and with data blending.

**Note**: The largest signed 64-bit integer is 9,223,372,036,854,775,807. When connecting to a new data source, any column with data type set to Number (whole) can accommodate values up to this limit; for larger values, because Number (whole) does not use floating-points, Tableau displays "Null." When the data type is set to Number (decimal), larger values can be accommodated.

### Boolean

A field that contains the values `TRUE` or `FALSE`.
An unknown value arises when the result of a comparison is unknown.
For example, the expression `7 > Null` yields unknown. Unknown
booleans are automatically converted to Null.
