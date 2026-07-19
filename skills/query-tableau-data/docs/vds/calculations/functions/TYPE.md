# Type Conversion

## Why use type conversion functions

Type conversion functions allow you to convert fields from one data type to another (this is called "casting"). For example, if you have date information in a field with a string data type, you won't be able to use that field in date calculations unless the field is cast (changed) to a date data type.

For example, to use a string date field in a DATEDIFF function, you'd also need to use a date type conversion:

`DATEDIFF('day', [Date Field], DATE([String Date Field]) )`

Without the DATE function changing the data type, you'd get an error that "DATEDIFF is being called with (string, date, string)".

> **VDS Note**: VDS does not support datetime output — use `DATE` not `DATETIME`. Functions that produce datetime (`DATETIME`, `MAKEDATETIME`, `MAKETIME`) are not supported. Spatial constructors (`MAKELINE`, `MAKEPOINT`) are also not supported.

---

## Type conversion functions available in VDS

### DATE

|  |  |
| --- | --- |
| Syntax | `DATE(expression)` |
| Output | Date |
| Definition | Returns a date given a number, string, or date expression. |
| Example | ``` DATE([Employee Start Date]) ```  ``` DATE("September 22, 2018") ```  ``` DATE("9/22/2018") ``` |
| Notes | Unlike DATEPARSE, there is no need to provide a pattern as DATE automatically recognizes many standard date formats. If DATE does not recognize the input, however, try using DATEPARSE and specifying the format. MAKEDATE is another similar function, but MAKEDATE requires the input of numeric values for year, month, and day. |

### FLOAT

|  |  |
| --- | --- |
| Syntax | `FLOAT(expression)` |
| Output | Floating point number (decimal) |
| Definition | Casts its argument as a floating point number. |
| Example | ``` FLOAT(3) = 3.000 ``` |
| Notes | See also INT which returns an integer. |

### INT

|  |  |
| --- | --- |
| Syntax | `INT(expression)` |
| Output | Integer |
| Definition | Casts its argument as an integer. For expressions, this function truncates results to the closest integer toward zero. |
| Example | ``` INT(8/3) = 2 ```  ``` INT(-9.7) = -9 ``` |
| Notes | When a string is converted to an integer it is first converted to a float and then rounded.  See also FLOAT which returns a decimal. See also ROUND, CEILING, and FLOOR. |

### MAKEDATE

|  |  |
| --- | --- |
| Syntax | `MAKEDATE(year, month, day)` |
| Output | Date |
| Definition | Returns a date value constructed from the specified numerical year, month, and date. |
| Example | ``` MAKEDATE(1986,3,25) = #1986-03-25# ```   Note that incorrectly entered values will be adjusted into a date, such as MAKEDATE(2020,4,31) = May 1, 2020 rather than returning an error that there is no 31st day of April. |
| Notes | Available for Tableau Data Extracts. Check for availability in other data sources.  MAKEDATE requires numerical inputs for the parts of a date. If your data is a string that should be a date, try the DATE function. DATE automatically recognizes many standard date formats. If DATE does not recognize the input try using DATEPARSE. |

### STR

|  |  |
| --- | --- |
| Syntax | `STR(expression)` |
| Output | String |
| Definition | Casts its argument as a string. |
| Example | ``` STR([ID]) ``` |

---

## Cast Boolean expressions

A Boolean can be cast to an integer, float, or string, but not a date.

* `True` maps to 1, 1.0, or "1"
* `False` maps to 0, 0.0, or "0"
* `Unknown` maps to `Null`
