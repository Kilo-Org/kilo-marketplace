# Date Functions

Dates are a common element in many data sources. If a field contains recognizable dates, it will have a **date** data type. Using dates in calculations often requires the use of date-specific functions.

> **VDS Date Limitations**: VDS supports dates only — not datetimes. Functions that return datetime (`DATETIME`, `MAKEDATETIME`, `MAKETIME`, `NOW`) are not supported. Use `TODAY()` instead of `NOW()`. Date literals must use RFC 3339 format strings (e.g., `"2020-01-15"`), not Tableau `#date#` syntax. The `'hour'`, `'minute'`, and `'second'` date_part values are not supported.

---

## Date functions available in VDS

### DATE

Type conversion function that changes string and number expressions into dates, as long as they are in a recognizable format.

|  |  |
| --- | --- |
| Syntax | `DATE(expression)` |
| Output | Date |
| Definition | Returns a date given a number, string, or date `<expression>`. |
| Example | ``` DATE([Employee Start Date]) ```  ``` DATE("September 22, 2018") ```  ``` DATE("9/22/2018") ```  ``` DATE(#2018-09-22 14:52#) ``` |
| Notes | Unlike `DATEPARSE`, there is no need to provide a pattern as `DATE` automatically recognizes many standard date formats. If `DATE` does not recognize the input, however, try using `DATEPARSE` and specifying the format.  `MAKEDATE` is another similar function, but `MAKEDATE` requires the input of numeric values for year, month, and day. |

### DATEADD

Adds a specified number of date parts (months, days, etc) to the starting date.

|  |  |
| --- | --- |
| Syntax | `DATEADD(date_part, interval, date)` |
| Output | Date |
| Definition | Returns the `<date>` with the specified number `<interval>` added to the specified `<date_part>` of that date. For example, adding three months or 12 days to a starting date. |
| Example | Push out all due dates by one week   ``` DATEADD('week', 1, [due date]) ```   Add 280 days to the date February 20, 2021   ``` DATEADD('day', 280, #2/20/21#) = #November 27, 2021# ``` |
| Notes | Supports ISO 8601 dates. |

### DATEDIFF

Returns the number of date parts (weeks, years, etc) between two dates.

|  |  |
| --- | --- |
| Syntax | `DATEDIFF(date_part, date1, date2, [start_of_week])` |
| Output | Integer |
| Definition | Returns the difference between `<date1>` and `<date2>` expressed in units of `<date_part>`. For example, subtracting the dates someone entered and left a band to see how long they were in the band. |
| Example | Number of days between March 25, 1986 and February 20, 2021   ``` DATEDIFF('day', #3/25/1986#, #2/20/2021#) = 12,751 ```   How many months someone was in a band   ``` DATEDIFF('month', [date joined band], [date left band]) ``` |
| Notes | Supports ISO 8601 dates. |

### DATENAME

Returns the name of the specified date part as a discrete string.

|  |  |
| --- | --- |
| Syntax | `DATENAME(date_part, date, [start_of_week])` |
| Output | String |
| Definition | Returns `<date_part>` of `<date>` as a string. |
| Example | ``` DATENAME('year', #3/25/1986#) = "1986" ```  ``` DATENAME('month', #1986-03-25#) = "March" ``` |
| Notes | Supports ISO 8601 dates.  A very similar calculation is DATEPART, which returns the value of the specified date part as a continuous integer. `DATEPART` can be faster because it is a numerical operation.  By changing the attributes of the calculation’s result (dimension or measure, continuous or discrete) and the date formatting, the results of `DATEPART` and `DATENAME` can be formatted to be identical.  An inverse function is DATEPARSE, which takes a string value and formats it as a date. |

### DATEPARSE

Returns specifically formatted strings as dates.

> **VDS Warning**: `DATEPARSE` has heavy data source restrictions and may fail in VDS context. It is only available through a narrow set of connectors, and the published data source must use one of those connectors. Prefer `DATE()` or `MAKEDATE()` when possible, as these have broader compatibility. If `DATEPARSE` fails, consider pre-formatting date strings to a standard format that `DATE()` can recognize.

|  |  |
| --- | --- |
| Syntax | `DATEPARSE(date_format, date_string)` |
| Output | Date |
| Definition | The `<date_format>` argument describes how the `<date_string>` field is arranged. Because of the variety of ways the string field can be ordered, the `<date_format>` must match exactly. For a full explanation and formatting details, see Convert a Field to a Date Field(Link opens in a new window). |
| Example | ``` DATEPARSE('yyyy-MM-dd', "1986-03-25") = #March 25, 1986# ``` |
| Notes | `DATE` is a similar function that automatically recognizes many standard date formats. `DATEPARSE` may be a better option if `DATE` does not recognize the input pattern.  `MAKEDATE` is another similar function, but `MAKEDATE` requires the input of numeric values for year, month, and day.  Inverse functions, which take dates apart and return the value of their parts, are `DATEPART` (integer output) and `DATENAME` (string output). |
| Database limitations | `DATEPARSE` is available through the following connectors: non-legacy Excel and text file connections, Amazon EMR Hadoop Hive, Cloudera Hadoop, Google Sheets, Hortonworks Hadoop Hive, MapR Hadoop Hive, MySQL, Oracle, PostgreSQL, and Tableau extracts. Some formats may not be available for all connections.  `DATEPARSE` is not supported on Hive variants. Only Denodo, Drill, and Snowflake are supported. |

### DATEPART

Returns the name of the specified date part as an integer.

|  |  |
| --- | --- |
| Syntax | `DATEPART(date_part, date, [start_of_week])` |
| Output | Integer |
| Definition | Returns `<date_part>` of `<date>` as an integer. |
| Example | ``` DATEPART('year', #1986-03-25#) = 1986 ```  ``` DATEPART('month', #1986-03-25#) = 3 ``` |
| Notes | Supports ISO 8601 dates.  A very similar calculation is `DATENAME`, which returns the name of the specified date part as a discrete string. `DATEPART` can be faster because it is a numerical operation. By changing the attributes of the field (dimension or measure, continuous or discrete) and the date formatting, the results of `DATEPART` and `DATENAME` can be formatted to be identical.  An inverse function is `DATEPARSE`, which takes a string value and formats it as a date. |

### DATETRUNC

This function can be thought of as date rounding. It takes a specific date and returns a version of that date at the desired specificity. Because every date must have a value for day, month, quarter, and year, `DATETRUNC` sets the values as the lowest value for each date part up to the date part specified. Refer to the example for more information.

|  |  |
| --- | --- |
| Syntax | `DATETRUNC(date_part, date, [start_of_week])` |
| Output | Date |
| Definition | Truncates the `<date>` to the accuracy specified by the `<date_part>`. This function returns a new date. For example, when you truncate a date that is in the middle of the month at the month level, this function returns the first day of the month. |
| Example | ``` DATETRUNC('day', #9/22/2018#) = #9/22/2018# ```  ``` DATETRUNC('iso-week', #9/22/2018#) = #9/17/2018# ```   (the monday of the week containing 9/22/2018)   ``` DATETRUNC(quarter, #9/22/2018#) = #7/1/2018# ```   (the first day of the quarter containing 9/22/2018)  Note: For week and iso-week, the `start_of_week` comes into play. ISO-weeks always start on Monday. For the locale of this example, an unspecified `start_of_week` means the week starts on Sunday. |
| Notes | Supports ISO 8601 dates.  You shouldn't use `DATETRUNC` to, for example, stop showing the time for a datetime field in a viz. If you want to truncate the way a date displays rather than round its accuracy, adjust the formatting(Link opens in a new window).  For example, `DATETRUNC('day', #5/17/2022 3:12:48 PM#)`, if formatted in the viz to display seconds, would display as `5/17/2022 12:00:00 AM`. The value is truncated to day, but the display goes to seconds. |

### DAY

Returns the day of the month (1-31) as an integer.

|  |  |
| --- | --- |
| Syntax | `DAY(date)` |
| Output | Integer |
| Definition | Returns the day of the given `<date>` as an integer. |
| Example | ``` Day(#September 22, 2018#) = 22 ``` |
| Notes | See also `WEEK`, `MONTH`, `QUARTER`, `YEAR`, and the ISO equivalents. |

### ISDATE

Checks if the string is a valid date format.

|  |  |
| --- | --- |
| Syntax | `ISDATE(string)` |
| Output | Boolean |
| Definition | Returns true if a given `<string>` is a valid date. |
| Example | ``` ISDATE(09/22/2018) = true ```  ``` ISDATE(22SEP18) = false ``` |
| Notes | The required argument must be a string. ISDATE cannot be used for a field with a date data type—the calculation will return an error. |

### ISOQUARTER

|  |  |
| --- | --- |
| Syntax | `ISOQUARTER(date)` |
| Output | Integer |
| Definition | Returns the ISO8601 week-based quarter of a given `<date>` as an integer. |
| Example | ``` ISOQUARTER(#1986-03-25#) = 1 ``` |
| Notes | See also `ISOWEEK`, `ISOWEEKDAY`, `ISOYEAR`, and the non-ISO equivalents. |

### ISOWEEK

|  |  |
| --- | --- |
| Syntax | `ISOWEEK(date)` |
| Output | Integer |
| Definition | Returns the ISO8601 week-based week of a given `<date>` as an integer. |
| Example | ``` ISOWEEK(#1986-03-25#) = 13 ``` |
| Notes | See also `ISOWEEKDAY`, `ISOQUARTER`, `ISOYEAR`, and the non-ISO equivalents. |

### ISOWEEKDAY

|  |  |
| --- | --- |
| Syntax | `ISOWEEKDAY(date)` |
| Output | Integer |
| Definition | Returns the ISO8601 week-based weekday of a given `<date>` as an integer. |
| Example | ``` ISOWEEKDAY(#1986-03-25#) = 2 ``` |
| Notes | See also `ISOWEEK`, `ISOQUARTER`, `ISOYEAR`, and the non-ISO equivalents. |

### ISOYEAR

|  |  |
| --- | --- |
| Syntax | `ISOYEAR(date)` |
| Output | Integer |
| Definition | Returns the ISO8601 week-based year of a given `<date>` as an integer. |
| Example | ``` ISOYEAR(#1986-03-25#) = 1,986 ``` |
| Notes | See also `ISOWEEK`, `ISOWEEKDAY`, `ISOQUARTER`, and the non-ISO equivalents. |

### MAKEDATE

|  |  |
| --- | --- |
| Syntax | `MAKEDATE(year, month, day)` |
| Output | Date |
| Definition | Returns a date value constructed from the specified `<year>`, `<month>`, and `<day>`. |
| Example | ``` MAKEDATE(1986,3,25) = #1986-03-25# ``` |
| Notes | **Note**: Incorrectly entered values will be adjusted into a date, such as `MAKEDATE(2020,4,31) = May 1, 2020` rather than returning an error that there is no 31st day of April.  Available for Tableau Data Extracts. Check for availability in other data sources.  `MAKEDATE` requires numerical inputs for the parts of a date. If your data is a string that should be a date, try the `DATE` function. `DATE` automatically recognizes many standard date formats. If `DATE` does not recognize the input try using `DATEPARSE`. |

### MAX

|  |  |
| --- | --- |
| Syntax | `MAX(expression)` or `MAX(expr1, expr2)` |
| Output | Same data type as the argument, or `NULL` if any part of the argument is null. |
| Definition | Returns the maximum of the two arguments, which must be of the same data type.  `MAX` can also be applied to a single field as an aggregation. |
| Example | ``` MAX(4,7) = 7 MAX(#3/25/1986#, #2/20/2021#) = #2/20/2021#  MAX([Name]) = "Zander" ``` |
| Notes | **For strings**  `MAX` is usually the value that comes last in alphabetical order.  For database data sources, the `MAX` string value is highest in the sort sequence defined by the database for that column.  **For dates**  For dates, the `MAX` is the most recent date. If `MAX` is an aggregation, the result will not have a date hierarchy. If `MAX` is a comparison, the result will retain the date hierarchy.  **As an aggregation**  `MAX(expression)` is an aggregate function and returns a single aggregated result. This displays as `AGG(expression)` in the viz.  **As a comparison**  `MAX(expr1, expr2)` compares the two values and returns a row-level value.  See also `MIN`. |

### MIN

|  |  |
| --- | --- |
| Syntax | `MIN(expression)` or `MIN(expr1, expr2)` |
| Output | Same data type as the argument, or `NULL`if any part of the argument is null. |
| Definition | Returns the minimum of the two arguments, which must be of the same data type.  `MIN` can also be applied to a single field as an aggregation. |
| Example | ``` MIN(4,7) = 4 MIN(#3/25/1986#, #2/20/2021#) = #3/25/1986# MIN([Name]) = "Abebi" ``` |
| Notes | **For strings**  `MIN` is usually the value that comes first in alphabetical order.  For database data sources, the `MIN` string value is lowest in the sort sequence defined by the database for that column.  **For dates**  For dates, the `MIN` is the earliest date. If `MIN` is an aggregation, the result will not have a date hierarchy. If `MIN` is a comparison, the result will retain the date hierarchy.  **As an aggregation**  `MIN(expression)` is an aggregate function and returns a single aggregated result. This displays as `AGG(expression)` in the viz.  **As a comparison**  `MIN(expr1, expr2)` compares the two values and returns a row-level value.  See also `MAX`. |

### MONTH

|  |  |
| --- | --- |
| Syntax | `MONTH(date)` |
| Output | Integer |
| Definition | Returns the month of the given `<date>` as an integer. |
| Example | ``` MONTH(#1986-03-25#) = 3 ``` |
| Notes | See also `DAY`, `WEEK`, `QUARTER`, `YEAR`, and the ISO equivalents |

### QUARTER

|  |  |
| --- | --- |
| Syntax | `QUARTER(date)` |
| Output | Integer |
| Definition | Returns the quarter of the given `<date>` as an integer. |
| Example | ``` QUARTER(#1986-03-25#) = 1 ``` |
| Notes | See also `DAY`, `WEEK`, `MONTH`, `YEAR`, and the ISO equivalents |

### TODAY

|  |  |
| --- | --- |
| Syntax | `TODAY()` |
| Output | Date |
| Definition | Returns the current local system date. |
| Example | ``` TODAY() = 1986-03-25 ``` |
| Notes | `TODAY` does not take an argument.  If the data source is a live connection, the system date could be in another timezone. |

### WEEK

|  |  |
| --- | --- |
| Syntax | `WEEK(date)` |
| Output | Integer |
| Definition | Returns the week of the given `<date>` as an integer. |
| Example | ``` WEEK(#1986-03-25#) = 13 ``` |
| Notes | See also `DAY`, `MONTH`, `QUARTER`, `YEAR`, and the ISO equivalents |

### YEAR

|  |  |
| --- | --- |
| Syntax | `YEAR(date)` |
| Output | Integer |
| Definition | Returns the year of the given `<date>` as an integer. |
| Example | ``` YEAR(#1986-03-25#) = 1,986 ``` |
| Notes | See also `DAY`, `WEEK`, `MONTH`, `QUARTER`, and the ISO equivalents |

## date\_part

Many date functions in Tableau take the argument `date_part`, which is a string constant that tells the function what part of a date to consider, such as day, week, quarter, etc. The valid `date_part` values that you can use are:

| date\_part | Values |
| --- | --- |
| `'year'` | Four-digit year |
| `'quarter'` | 1-4 |
| `'month'` | 1-12 or "January", "February", and so on |
| `'dayofyear'` | Day of the year; Jan 1 is 1, Feb 1 is 32, and so on |
| `'day'` | 1-31 |
| `'weekday'` | 1-7 or "Sunday", "Monday", and so on |
| `'week'` | 1-52 |
| `'iso-year'` | Four-digit ISO 8601 year |
| `'iso-quarter'` | 1-4 |
| `'iso-week'` | 1-52, start of week is always Monday |
| `'iso-weekday'` | 1-7, start of week is always Monday |

## The `[start_of_week]` parameter

Some functions have the optional parameter `[start_of_week]`. The `start_of_week` parameter can be used to specify what day is considered the first day of the week, such as "Sunday" or "Monday". If it is omitted, the start of week is determined by the data source. See Date Properties for a Data Source.

For the examples below, 22 September is a Sunday and 24 September is a Tuesday. The DATEDIFF function is being used to calculate the weeks between these dates.

`DATEDIFF('week', #2013-09-22#, #2013-09-24#, 'monday') = 1`

* Because start\_of\_week is 'monday', these dates are in different weeks.

`DATEDIFF('week', #2013-09-22#, #2013-09-24#, 'sunday') = 0`

* Because start\_of\_week is 'sunday', these dates are in the same week.
