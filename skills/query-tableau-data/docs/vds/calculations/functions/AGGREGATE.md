# Aggregate Functions in Tableau

## Why use aggregate functions

Aggregate functions allow you to summarize or change the granularity of your data.

For example, you might want to know exactly how many orders your store had for a particular year. You can use the COUNTD function to tally the exact number of unique orders your company had, and then break the visualization down by year.

The calculation might look something like this:

`COUNTD(Order ID)` or `IIF(SUM([Sales]) !=0, SUM([Profit])/SUM([Sales]), 0)`

> **VDS Note**: Only the following aggregation functions are supported as the `function` property in VDS queries: `SUM`, `AVG`, `MEDIAN`, `COUNT`, `COUNTD`, `MIN`, `MAX`, `STDEV`, `VAR`, `COLLECT` (non-spatial), `YEAR`, `QUARTER`, `MONTH`, `WEEK`, `DAY`, `TRUNC_YEAR`, `TRUNC_QUARTER`, `TRUNC_MONTH`, `TRUNC_WEEK`, `TRUNC_DAY`. See LIMITATIONS.md for the full list.

---

## Aggregate functions available in VDS

**Aggregations and floating-point arithmetic**: The results of some aggregations may not always be exactly as expected. For example, you may find that the SUM function returns a value such as -1.42e-14 for a column of numbers that you know should sum to exactly 0. This happens because the Institute of Electrical and Electronics Engineers (IEEE) 754 floating-point standard requires that numbers be stored in binary format, which means that numbers are sometimes rounded at extremely fine levels of precision. You can eliminate this potential distraction by using the ROUND function (see Number Functions) or by formatting the number to show fewer decimal places.

### AVG

|  |  |
| --- | --- |
| Syntax | `AVG(expression)` |
| Definition | Returns the average of all the values in the expression. Null values are ignored. |
| Notes | `AVG` can only be used with numeric fields. |

### COUNT

|  |  |
| --- | --- |
| Syntax | `COUNT(expression)` |
| Definition | Returns the number of items. Null values are not counted. |

### COUNTD

|  |  |
| --- | --- |
| Syntax | `COUNTD(expression)` |
| Definition | Returns the number of distinct items in a group. Null values are not counted. |

### MAX

|  |  |
| --- | --- |
| Syntax | `MAX(expression)` or `MAX(expr1, expr2)` |
| Output | Same data type as the argument, or `NULL`if any part of the argument is null. |
| Definition | Returns the maximum of the two arguments, which must be of the same data type.  `MAX` can also be applied to a single field as an aggregation. |
| Example | ``` MAX(4,7) = 7 MAX(#3/25/1986#, #2/20/2021#) = #2/20/2021#  MAX([Name]) = "Zander" ``` |
| Notes | **For strings**  `MAX` is usually the value that comes last in alphabetical order.  For database data sources, the `MAX` string value is highest in the sort sequence defined by the database for that column.  **For dates**  For dates, the `MAX` is the most recent date. If `MAX` is an aggregation, the result will not have a date hierarchy. If `MAX` is a comparison, the result will retain the date hierarchy.  **As an aggregation**  `MAX(expression)` is an aggregate function and returns a single aggregated result. This displays as `AGG(expression)` in the viz.  **As a comparison**  `MAX(expr1, expr2)` compares the two values and returns a row-level value.  See also `MIN`. |

### MEDIAN

|  |  |
| --- | --- |
| Syntax | `MEDIAN(expression)` |
| Definition | Returns the median of an expression across all records. Null values are ignored. |
| Notes | `MEDIAN` can only be used with numeric fields. |
| Database limitations | `MEDIAN` is **not** available for the following data sources: Access, Amazon Redshift, Cloudera Hadoop, HP Vertica, IBM DB2, IBM PDA (Netezza), Microsoft SQL Server, MySQL, SAP HANA, Teradata.  For other data source types, you can extract your data into an extract file to use this function. See Extract Your Data(Link opens in a new window). |

### MIN

|  |  |
| --- | --- |
| Syntax | `MIN(expression)` or `MIN(expr1, expr2)` |
| Output | Same data type as the argument, or `NULL`if any part of the argument is null. |
| Definition | Returns the minimum of the two arguments, which must be of the same data type.  `MIN` can also be applied to a single field as an aggregation. |
| Example | ``` MIN(4,7) = 4 MIN(#3/25/1986#, #2/20/2021#) = #3/25/1986# MIN([Name]) = "Abebi" ``` |
| Notes | **For strings**  `MIN` is usually the value that comes first in alphabetical order.  For database data sources, the `MIN` string value is lowest in the sort sequence defined by the database for that column.  **For dates**  For dates, the `MIN` is the earliest date. If `MIN` is an aggregation, the result will not have a date hierarchy. If `MIN` is a comparison, the result will retain the date hierarchy.  **As an aggregation**  `MIN(expression)` is an aggregate function and returns a single aggregated result. This displays as `AGG(expression)` in the viz.  **As a comparison**  `MIN(expr1, expr2)` compares the two values and returns a row-level value.  See also `MAX`. |

### STDEV

|  |  |
| --- | --- |
| Syntax | `STDEV(expression)` |
| Definition | Returns the statistical standard deviation of all values in the given expression based on a sample of the population. |

### SUM

|  |  |
| --- | --- |
| Syntax | `SUM(expression)` |
| Definition | Returns the sum of all values in the expression. Null values are ignored. |
| Notes | `SUM` can only be used with numeric fields. |

### VAR

|  |  |
| --- | --- |
| Syntax | `VAR(expression)` |
| Definition | Returns the statistical variance of all values in the given expression based on a sample of the population. |

---

## Rules for aggregate calculations

The rules that apply to aggregate calculations are as follows:

* For any aggregate calculation, you cannot combine an aggregated value and a disaggregated value. For example, `SUM(Price)*[Items]` is not a valid expression because SUM(Price) is aggregated and Items is not. However, `SUM(Price*Items)` and `SUM(Price)*SUM(Items)` are both valid.
* Constant terms in an expression act as aggregated or disaggregated values as appropriate. For example: `SUM(Price*7)` and `SUM(Price)*7` are both valid expressions.
* All of the functions can be evaluated on aggregated values. However, the arguments to any given function must either all be aggregated or all disaggregated. For example: `MAX(SUM(Sales),Profit)` is not a valid expression because Sales is aggregated and Profit is not. However, `MAX(SUM(Sales),SUM(Profit))` is a valid expression.
* The result of an aggregate calculation is always a measure. This includes expressions like ATTR(Dimension) or MIN(Dimension).
* Like predefined aggregations, aggregate calculations are computed correctly for grand totals. Refer to Grand Totals for more information.
