# Logical Functions

## Why use logical calculations

Logical calculations allow you to determine if a certain condition is true or false (Boolean logic). For example, you might want to categorize values based on certain cutoffs.

A logical calculation might look something like this:

```
IF [Profit] > 0
THEN 'Profitable'
ELSEIF [Profit] = 0 THEN 'Break even'
ELSE 'Loss'
END
```

---

## Logical functions and operators available in Tableau

### AND

|  |  |
| --- | --- |
| Syntax | `<expr1> AND <expr2>` |
| Definition | Performs a logical conjunction on two expressions. (If both sides are true, the logical test returns true.) |
| Output | Boolean (true or false) |
| Example | ``` IF [Season] = "Spring" AND "[Season] = "Fall"  THEN "It's the apocalypse and footwear doesn't matter"  END ```   *"If both (Season = Spring) and (Season = Fall) are true simultaneously, then return It's the apocalypse and footwear doesn't matter".* |
| Notes | Often used with IF and IIF. See also NOT and OR.  If both expressions are `TRUE` (that is, not `FALSE` or `NULL`), then the result is `TRUE`. If either expression is `NULL`, then the result is `NULL`. In all other cases, the result is `FALSE`.  If you create a calculation in which the result of an `AND` comparison is displayed on a worksheet, Tableau displays `TRUE` and `FALSE`. If you would like to change this, use the Format area in the format dialog.  **Note**: The `AND` operator employs *short circuit evaluation*. This means that if the first expression is evaluated to be `FALSE`, then the second expression is not evaluated at all. This can be helpful if the second expression results in an error when the first expression is `FALSE`, because the second expression in this case is never evaluated. |

### CASE

|  |  |
| --- | --- |
| Syntax | `CASE <expression>  WHEN <value1> THEN <then1>  WHEN <value2> THEN <then2>  ...  [ELSE <default>] END` |
| Output | Depends on data type of the `<then>` values. |
| Definition | Evaluates the `expression` and compares it to the specified options (`<value1>`, `<value2>`, etc.). When a `value` that matches expression is encountered, CASE returns the corresponding `return`. If no match is found, the (optional) default is returned. If there is no default and no values match, then Null is returned. |
| Example | ``` CASE [Season]  WHEN 'Summer' THEN 'Sandals'  WHEN 'Winter' THEN 'Boots'  ELSE 'Sneakers'  END ```   *"Look at the Season field. If the value is Summer, then return Sandals. If the value is Winter, then return Boots. If none of the options in the calculation match what is in the Season field, return a Sneakers."* |
| Notes | See also IF and IIF.  Used with WHEN, THEN, ELSE, and END.  **Tip**: Many times you can use a group to get the same results as a complicated CASE function, or use CASE to replace native grouping functionality, such as in the previous example. You may want to test which is more performant for your scenario. |

### ELSE

|  |  |
| --- | --- |
| Syntax | `CASE <expression>  WHEN <value1> THEN <then1>  WHEN <value2> THEN <then2>  ...  [ELSE <default>] END` |
| Definition | An optional piece of an `IF` or `CASE` expression used to specify a default value to return if none of the tested expressions are true. |
| Example | ``` IF [Season] = "Summer" THEN 'Sandals'  ELSEIF [Season] = "Winter" THEN 'Boots'  ELSE 'Sneakers'  END ```  ``` CASE [Season]  WHEN 'Summer' THEN 'Sandals'  WHEN 'Winter' THEN 'Boots'  ELSE 'Sneakers'  END ``` |
| Notes | Used with CASE, WHEN, IF, ELSEIF, THEN, and END  `ELSE` is optional with `CASE` and `IF`. In a calculation where `ELSE` is not specified, if none of the `<test>`are true, the overall calculation will return null.  `ELSE` does not require a condition (such as `[Season] = "Winter"`) and can be thought of as a form of null handling. |

### ELSEIF

|  |  |
| --- | --- |
| Syntax | `[ELSEIF <test2> THEN <then2>]` |
| Definition | An optional piece of an `IF` expression used to specify additional conditions beyond the initial IF. |
| Example | ``` IF [Season] = "Summer" THEN 'Sandals'  ELSEIF [Season] = "Winter" THEN 'Boots'  ELSEIF [Season] = "Spring" THEN 'Sneakers'  ELSEIF [Season] = "Autumn" THEN 'Sneakers' ELSE 'Bare feet'  END ``` |
| Notes | Used with IF, THEN, ELSE, and END  `ELSEIF` can be thought of as additional `IF` clauses. `ELSEIF` is optional and can be repeated multiple times.  Unlike `ELSE`, `ELSEIF` requires a condition (such as `[Season] = "Winter"`). |

### END

|  |  |
| --- | --- |
| Definition | Used to close an `IF` or `CASE` expression. |
| Example | ``` IF [Season] = "Summer" THEN 'Sandals'  ELSEIF [Season] = "Winter" THEN 'Boots'  ELSE 'Sneakers'  END ```   *"If Season = Summer, then return Sandals. If not, look at the next expression. If Season = Winter, then return Boots. If neither of the expressions are true, return Sneakers."*   ``` CASE [Season]  WHEN 'Summer' THEN 'Sandals'  WHEN 'Winter' THEN 'Boots'  ELSE 'Sneakers'  END ```   **"Look at the Season field. If the value is Summer, then return Sandals. If the value is Winter, then return Boots. If none of the options in the calculation match what is in the Season field, return a Sneakers."** |
| Notes | Used with CASE, WHEN, IF, ELSEIF, THEN, and ELSE. |

### IF

|  |  |
| --- | --- |
| Syntax | `IF <test1> THEN <then1>  [ELSEIF <test2> THEN <then2>...] [ELSE <default>]  END` |
| Output | Depends on data type of the `<then>` values. |
| Definition | Tests a series of expressions and returns the `<then>` value for the first true `<test>`. |
| Example | ``` IF [Season] = "Summer" THEN 'Sandals'  ELSEIF [Season] = "Winter" THEN 'Boots'  ELSE 'Sneakers'  END ```   *"If Season = Summer, then return Sandals. If not, look at the next expression. If Season = Winter, then return Boots. If neither of the expressions are true, return Sneakers."* |
| Notes | See also IF and IIF.  Used with ELSEIF, THEN, ELSE, and END |

### IFNULL

|  |  |
| --- | --- |
| Syntax | `IFNULL(expr1, expr2)` |
| Output | Depends on the data type of the `<expr>` values. |
| Definition | Returns `<expr1>` if it's non-null, otherwise returns `<expr2>`. |
| Example | ``` IFNULL([Assigned Room], "TBD") ```   *"If the Assigned Room field isn't null, return its value. If the Assigned room field is null, return TBD instead."* |
| Notes | Compare with ISNULL. `IFNULL` always returns a value. `ISNULL` returns a boolean (true or false).  See also ZN. |

### IIF

|  |  |
| --- | --- |
| Syntax | `IIF(<test>, <then>, <else>, [<unknown>])` |
| Output | Depends on the data type of the values in the expression. |
| Definition | Checks whether a condition is met (`<test>`), and returns `<then>`if the test is true, `<else>` if the test is false, and an optional value for `<unknown>` if the test is null. If the optional unknown isn't specified, `IIF` returns null. |
| Example | ``` IIF([Season] = 'Summer', 'Sandals', 'Other footwear') ```   *"If Season = Summer, then return Sandals. If not, return Other footwear"*   ``` IIF([Season] = 'Summer', 'Sandals',     IIF('Season' = 'Winter', 'Boots',  'Other footwear') ) ```   *"If Season = Summer, then return Sandals. If not, look at the next expression. If Season = Winter, then return Boots. If neither are true, return Sneakers."*   ``` IIF('Season' = 'Summer', 'Sandals',     IIF('Season' = 'Winter', 'Boots',         IIF('Season' = 'Spring', 'Sneakers', 'Other footwear')    ) ) ```   *"If Season = Summer, then return Sandals. If not, look at the next expression. If Season = Winter, then return Boots. If none of the expressions are true, return Sneakers."* |
| Notes | See also IF andCASE.  `IIF` doesn't have an equivalent to `ELSEIF` (like `IF`) or repeated `WHEN` clauses (like `CASE`). Instead, multiple tests can be evaluated sequentially by nesting `IIF` statements as the `<unknown>` element. The first (outermost) true is returned.  That is to say, in the calculation below, the result will be Red, not Orange, because the expression stops being evaluated as soon as A=A is evaluated as true:  `IIF('A' = 'A', 'Red', IIF('B' = 'B', 'Orange', IIF('C' = 'D', 'Yellow', 'Green')))` |

### IN

|  |  |
| --- | --- |
| Syntax | `<expr1> IN <expr2>` |
| Output | Boolean (true or false) |
| Definition | Returns `TRUE` if any value in `<expr1>` matches any value in `<expr2>`. |
| Example | ``` SUM([Cost]) IN (1000, 15, 200) ```   *"Is the value of the Cost field 1000, 15, or 200?"*   ``` [Field] IN [Set] ```   *"Is the value of the field present in the set?"* |
| Notes | The values in `<expr2>` can be a set, list of literal values, or combined field.  See also WHEN. |

### ISDATE

|  |  |
| --- | --- |
| Syntax | `ISDATE(string)` |
| Output | Boolean (true or false) |
| Definition | Returns true if a `<string>` is a valid date. The input expression must be a string (text) field. |
| Example | ``` ISDATE("2018-09-22") ```   *"Is the string 2018-09-22 a properly formatted date?"* |
| Notes | What is considered a valid date depends on the locale(Link opens in a new window) of the system evaluating the calculation. For example:  In the USA:   * `ISDATE("2018-09-22") = TRUE` * `ISDATE("2018-22-09") = FALSE`   In the UK:   * `ISDATE("2018-09-22") = FALSE` * `ISDATE("2018-22-09") = TRUE` |

### ISNULL

|  |  |
| --- | --- |
| Syntax | `ISNULL(expression)` |
| Output | Boolean (true or false) |
| Definition | Returns true if the `<expression>` is NULL (does not contain valid data). |
| Example | ``` ISNULL([Assigned Room]) ```   *"Is the Assigned Room field null?"* |
| Notes | Compare with IFNULL. `IFNULL` always returns a value. `ISNULL` returns a boolean.  See also ZN. |

### MAX

|  |  |
| --- | --- |
| Syntax | `MAX(expression)` or `MAX(expr1, expr2)` |
| Output | Same data type as the argument, or `NULL`if any part of the argument is null. |
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

### NOT

|  |  |
| --- | --- |
| Syntax | `NOT <expression>` |
| Output | Boolean (true or false) |
| Definition | Performs logical negation on an expression. |
| Example | ``` IF NOT [Season] = "Summer"  THEN 'Don't wear sandals'  ELSE 'Wear sandals'  END ```   *"If Season doesn't equal Summer, then return Don't wear sandals. If not, return Wear sandals."* |
| Notes | Often used with IF and IIF. See also AND and OR. |

### OR

|  |  |
| --- | --- |
| Syntax | `<expr1> OR <expr2>` |
| Output | Boolean (true or false) |
| Definition | Performs a logical disjunction on two expressions. |
| Example | ``` IF [Season] = "Spring" OR [Season] = "Fall"  THEN "Sneakers"  END ```   *"If either (Season = Spring) or (Season = Fall) is true, then return Sneakers."* |
| Notes | Often used with IF and IIF. See also AND and NOT.  If either expression is `TRUE`, then the result is `TRUE`. If both expressions are `FALSE`, then the result is `FALSE`. If both expressions are `NULL`, then the result is `NULL`.  If you create a calculation which displays the result of an `OR` comparison on a worksheet, Tableau displays TRUE and FALSE. If you would like to change this, use the Format area in the format dialog.  **Note**: The `OR` operator employs *short circuit evaluation.* This means that if the first expression is evaluated to be `TRUE`, then the second expression is not evaluated at all. This can be helpful if the second expression results in an error when the first expression is `TRUE`, because the second expression in this case is never evaluated. |

### THEN

|  |  |
| --- | --- |
| Syntax | `IF <test1> THEN <then1>  [ELSEIF <test2> THEN <then2>...]  [ELSE <default>]  END` |
| Definition | A required part of an `IF`, `ELSEIF`, or `CASE` expression, used to define what result to return if a specific value or test is true. |
| Example | ``` IF [Season] = "Summer" THEN 'Sandals'  ELSEIF [Season] = "Winter" THEN 'Boots'  ELSE 'Sneakers'  END ```   *"If Season = Summer, then return Sandals. If not, look at the next expression. If Season = Winter, then return Boots. If neither of the expressions are true, return Sneakers."*   ``` CASE [Season]  WHEN 'Summer' THEN 'Sandals'  WHEN 'Winter' THEN 'Boots'  ELSE 'Sneakers'  END ```   **"Look at the Season field. If the value is Summer, then return Sandals. If the value is Winter, then return Boots. If none of the options in the calculation match what is in the Season field, return a Sneakers."** |
| Notes | Used with CASE, WHEN, IF, ELSEIF, THEN, ELSE, and END |

### WHEN

|  |  |
| --- | --- |
| Syntax | `CASE <expression>  WHEN <value1> THEN <then1>  WHEN <value2> THEN <then2>  ...  [ELSE <default>] END` |
| Definition | A required part of a `CASE` expression. Finds the first `<value>` that matches `<expression>` and returns the corresponding `<then>`. |
| Example | ``` CASE [Season]  WHEN 'Summer' THEN 'Sandals'  WHEN 'Winter' THEN 'Boots'  ELSE 'Sneakers'  END ```   *"Look at the Season field. If the value is Summer, then return Sandals. If the value is Winter, then return Boots. If none of the options in the calculation match what is in the Season field, return a Sneakers."* |
| Notes | Used with CASE, THEN, ELSE, and END.  `CASE` also supports `WHEN IN` construction, such as:   ``` CASE <expression>  WHEN IN <set1> THEN <then1>  WHEN IN <combinedfield> THEN <then2>  ...  ELSE <default>  END ```   The values that `WHEN IN` compare to must be a set, list of literal values, or combined field. See also IN. |

### ZN

|  |  |
| --- | --- |
| Syntax | `ZN(expression)` |
| Output | Depends on the data type of the `<expression>`, or 0. |
| Definition | Returns <expression> if it isn't null, otherwise returns zero. |
| Example | ``` ZN([Test Grade]) ```   *"If the test grade isn't null, return its value. If the test grade is null, return 0."* |
| Notes | `ZN` is a specialized case of IFNULL where alternative if the expression is null is always 0 rather than being specified in the calculation.  `ZN` is especially useful when performing additional calculations and a null would render the entire calculation null. However, use caution interpreting these results as null is not always synonymous with 0 and could represent missing data.  See also ISNULL. |



**Note**: some of these are actually logical operators and appear in black, not blue. For more information, see Operator syntax.

Note on CASE, IF, and IIF

CASE is often easier to use than IF or IIF. In many instances, IF, IIF, and CASE can be used interchangeably. A CASE statement can always be rewritten as an IF statement, although the CASE function will generally be more concise and may be easier to understand. However, not all IF statements can be written as CASE statements, because each ELSEIF could refer to a different field.

**Tip**: Let's compare an example using the same logic across these three functions:

|  |  |  |
| --- | --- | --- |
| CASE | IF | IIF |
| ``` CASE [Region] WHEN 'West' THEN 1 WHEN 'East' THEN 2 WHEN 'South' THEN 3 WHEN 'North' Then 4 ELSE 5 END ``` | ``` IF [Region] = 'West' THEN 1 ELSEIF [Region] = 'East' THEN 2 ELSEIF [Region] = 'South' THEN 3 ELSEIF [Region] = 'North' THEN 4 ELSE 5 END ``` | ``` IIF([Region] = 'West', 1,  IIF([Region] = 'East', 2,   IIF([Region] = 'South', 3,    IIF([Region] = 'North', 4,    5, 0)   )  ) ) ``` |
| The CASE structure is very simple and easy to write and understand. However, the expression (here, [Region]) cannot be a logical operation, unlike with IF or IIF.  Nulls are handled the same for CASE as they are for IF. | The IF THEN structure permits multiple ELSEIF clauses, which makes multiple evaluations much easier than with IIF.  **Null handling**: any unknown (null) results are handled by the same ELSE clause as false results. Here, any region other than the four specified (including null) will be assigned a value of 5. | The IIF structure handles unknown results differently than false results and has a different syntax than IF. The tradeoff for specific null handling is nesting, as above, which can be clumsy to write and understand.  **Null handling**: any non-null region other than the four specified will be assigned a value of 5, but a null value will be assigned a 0. |

**Note**: Many times you can use a group to get the same results as a complicated case function. Test to see if one option is more performant than the other.

### Examples

CASE functions can be useful for scenarios such as realiasing:

```
CASE LEFT(DATENAME('weekday',[Order Date]),3)
WHEN 'Sun' THEN 0
WHEN 'Mon' THEN 1
WHEN 'Tue' THEN 2
WHEN 'Wed' THEN 3
WHEN 'Thu' THEN 4
WHEN 'Fri' THEN 5
WHEN 'Sat' THEN 6
END
```

or giving the end user the ability to select which measure to view in a chart when used with a parameter(Link opens in a new window):

```
CASE [Choose a Measure]
WHEN "Sales" THEN SUM([Sales])
WHEN "Profit" THEN AVG([Profit])
WHEN "Quantity" THEN COUNT([Quantity])
WHEN "Shipping Cost" THEN MEDIAN([Shipping Cost])
END
```
