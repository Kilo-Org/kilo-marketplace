# Calculations in Tableau

This article describes how to create and format calculations in Tableau. It lists the basic components of calculations and explains the proper syntax for each.

## Folder Contents

| File | Description |
| --- | --- |
| [SYNTAX.md](./SYNTAX.md) | Detailed syntax reference for all calculation components — functions, fields, operators, literals, parameters, and comments |
| [TYPES.md](./TYPES.md) | Overview of data types supported in calculations and how to use them correctly with functions |
| [LEVEL_OF_DETAIL.md](./LEVEL_OF_DETAIL.md) | Reference for Level of Detail (LOD) expressions — FIXED, INCLUDE, and EXCLUDE — and when to use each |
| [TABLE_CALCULATIONS.md](./TABLE_CALCULATIONS.md) | Guide to table calculations: transformations applied to local query results such as running totals, rankings, and percentages |
| [BEST_PRACTICES.md](./BEST_PRACTICES.md) | Tips and guidelines for writing efficient calculations and avoiding common performance pitfalls |
| [functions/FUNCTIONS.md](./functions/FUNCTIONS.md) | Index and reference for all built-in VDS functions organized by category |

> **Important**: `Level of Detail Expressions`, `Table Calculations` and `Functions` are your most powerful primitives for calculations. In particular, `Functions` allow you to leverage powerful built-in operations in the Tableau calculations language.

## Why use calculations?

Calculations allow you to create new data from data that already exists in your data source, as well as perform computations on your data. This allows you to perform complex analyzes and add fields to your data source on your own and on the fly.

## When to use calculations?

The first hurdle to learning calculations in Tableau is to recognize when you actually need to use one. You can use calculations for many, many reasons. Some examples might include:

* To segment data
* To convert the data type of a field, such as converting a string to a date.
* To aggregate data
* To filter results
* To calculate ratios

Some common scenarios might include:

* The data you need for your analysis is missing from your data source.

  For example, if you have a Sales and Profit field in your data source, but you want to calculate cost, you can *create* a Cost field using a formula similar to the following.

  `[Sales] - [Profit]`

* You want to transform values in your query.

  For example, you might want to calculate the difference in profit from one year to the other.

* You want to quickly categorize data.

  For example, you might want to quickly classify the data in your query as profitable or nonprofitable. You can create a calculated field using a calculation similar to the following:

  ```
  IF SUM([Profit]) > 0
  THEN "Profitable"
  ELSE "Nonprofitable"
  END
  ```

---

## Calculation building blocks

There are four basic components to calculations in Tableau:

* **Functions**: Statements used to transform the values or members in a field.
  + Functions require *arguments*, or specific pieces of information. Depending on the function, arguments can be fields, literals, parameters, or nested functions.
* **Fields**: Dimensions or measures from your data source.
* **Operators**: Symbols that denote an operation.
* **Literal expressions**: Constant values that are hardcoded, such as "High" or 1,500.

Not all calculations need to contain all four components. Additionally, calculations can contain:

* **Parameters**: Placeholder variables that can be inserted into calculations to replace constant values.
  For more information on parameters, see Create Parameters.
* **Comments**: Notes about a calculation or its parts, not included in the computation of the calculation.

For more information about how to use and format each of these components in a calculation, see the following sections.

### Example calculation explained

For example, consider the following calculation, which adds 14 days to a date ([Initial Visit]). A calculation like this could be useful for automatically finding the date for a two-week followup.

`DATEADD('day', 14, [Initial Visit])`

The components of this calculation can be broken down as:

* Function: `DATEADD`, which requires three arguments.
  + date\_part ('day')
  + interval (14)
  + date ([Initial Visit]).
* Field: [Initial Visit]
* Operators: n/a
* Literal expressions:

+ String literal: 'day'
+ Numeric literal: 14

In this example, the hardcoded constant 14 could be replaced with a parameter, which would allow the user to select how many days out to look for a followup appointment.

```
DATEADD('day', [How many days out?], [Initial Visit])
```

## At a glance: calculation syntax

|  |  |  |
| --- | --- | --- |
| **Components** | **Syntax** | **Example** |
| **Functions** | See [FUNCTIONS.md](./functions/FUNCTIONS.md) for an index of all supported functions in VDS | `SUM(expression)` |
| **Fields** | A field in a calculation is often surrounded by brackets [ ].  See Field syntax for more information. | `[Category]` |
| **Operators** | `+`, `-`, `*`, `/`, `%`, `==`, `=`, `>`, `<`, `>=`, `<=`, `!=`, `<>`, `^`, `AND`, `OR`, `NOT`, `( )`.  See Operator syntax for information on the types of operators you can use in Tableau calculation and the order they are performed in a formula. | `[Price]*(1-[discount])` |
| **Literal expressions** | Numeric literals are written as numbers.  String literals are written with quotation marks.  Date literals are written with the # symbol.  Boolean literals are written as either true or false.  Null literals are written as null.  See Literal expression syntax for more information. | `1.3567`  `"Unprofitable"`  `#August 22, 2005#`  `true`  `Null` |
| **Parameters** | A parameter in a calculation is surrounded by brackets [ ], like a field. See Create Parameters for more information. | `[Bin Size]` |
| **Comments** | To enter a comment in a calculation, type two forward slashes //. See Add comments to a calculation for more information.  Multi-line comments can be added by typing /\* to start the comment and \*/ to end it. | `SUM([Sales]) / SUM([Profit])`  `/*John's calculation`  `To be used for profit ratio`  `Do not edit*/` |

> _Note_: For more detailed syntax descriptions see [SYNTAX.md](./SYNTAX.md) and [TYPES.md](./TYPES.md).

---

### Related Documentation

- [FIELDS.md](../FIELDS.md) — how to include calculations and table calculations in a query field
- [FILTERS.md](../FILTERS.md) — using calculated filter fields
- [PARAMETERS.md](../PARAMETERS.md) — overriding parameters referenced in calculations
- [LIMITATIONS.md](../LIMITATIONS.md) — unsupported calculation functions and categories
