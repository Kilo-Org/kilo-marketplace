# Create Level of Detail Expressions in Tableau

Level of Detail expressions (also known as LOD expressions) allow you to compute values at the data source level and the visualization level. However, LOD expressions let you control the granularity you want to compute. They can be performed at a more granular level (INCLUDE), a less granular level (EXCLUDE), or an entirely independent level (FIXED).

This article explains the types of LOD expressions you can use in Tableau, when to use them, and how to format them.


## Types of LOD expressions

There are three types of LOD expressions you can create in Tableau:

* FIXED
* INCLUDE
* EXCLUDE

You can also scope an LOD expression to the table. This is called a Table-Scoped LOD expression.

### FIXED

FIXED level of detail expressions compute a value using the specified dimensions, without reference to the dimensions in the view.

#### Example

The following FIXED level of detail expression computes the sum of sales per region:

`{FIXED [Region] : SUM([Sales])}`

The view level of detail is [**Region**] and [**State**]. But FIXED level of detail expressions don't look at the dimensions in the view, only the dimensions specified in the calculation (here, **Region**). Therefore, the values for the individual states in each region are identical. For more information, see [AGGREGATE.md](./functions/AGGREGATE.md).

If the keyword had been INCLUDE instead of FIXED, the values would be different for each state. INCLUDE uses the dimension in the expression ([Region]) and any additional dimensions in the view ([State]) when evaluating the expression.

### INCLUDE

INCLUDE level of detail expressions compute values using the specified dimensions in addition to whatever dimensions are in the view.

INCLUDE can be useful when you want to calculate at a fine level of detail in the database, but reaggregate at a coarser level of detail in your view. Fields based on INCLUDE level of detail expressions change as you add or remove dimensions from the view.

#### Example 1

This INCLUDE level of detail expression computes total sales per customer:

`{ INCLUDE [Customer Name] : SUM([Sales]) }`

With the LOD on the Rows shelf, aggregated as AVG, and [Region] on the Columns shelf, the view shows the average customer sales amount per region.

#### Example 2

This INCLUDE level of detail expression calculates sum of sales on a per-state basis:

`{ INCLUDE [State] : SUM(Sales)}`

The calculation is placed on the Rows shelf and is aggregated as an average. The resulting visualization averages the sum of sales by state across categories.

### EXCLUDE

EXCLUDE level of detail expressions declare dimensions to omit from the view level of detail.

EXCLUDE is useful for 'percent of total' or 'difference from overall average' scenarios. They're comparable to Totals and Reference Lines.

EXCLUDE can't be used in row-level expressions (where there are no dimensions to omit). They can modify a view-level calculation or other LODs.

#### Example 1

The following EXCLUDE level of detail expression computes the average sales total per month then excludes the month.

`{EXCLUDE [Order Date (Month / Year)] : AVG({FIXED [Order Date (Month / Year)] : SUM([Sales])})}`

Notice that this is a nested level of detail expression—that is, a level of detail expression within another level of detail expression.

#### Example 2

Create a level of detail expression, named "ExcludeRegion", that excludes [Region] from the sum of [Sales]:

`{EXCLUDE [Region]: SUM([Sales])}`


### Table-Scoped

It’s possible to define a level of detail expression at the table level without using any of the scoping keywords. For example, the following expression returns the minimum (earliest) order date for the entire table:

`{MIN([Order Date])}`

This is equivalent to a FIXED level of detail expression with no dimension declaration:

`{FIXED : MIN([Order Date])}`

---

## LOD expression syntax

A level of detail expression has the following structure:

{[FIXED | INCLUDE | EXCLUDE] <*dimension declaration* > **:** <*aggregate expression*>}

### { }

The entire level of detail expression is enclosed in curly braces.

### [FIXED | INCLUDE | EXCLUDE]

The first element after the opening curly brace is one of the following scoping keywords:

#### FIXED

* FIXED level of detail expressions compute values using the specified dimensions without reference to the view level of detail—that is, regardless of other dimensions in the view.
* FIXED level of detail expressions ignore all the filters in the view other than context filters, data source filters, and extract filters.

Example: `{ FIXED [Region] : SUM([Sales]) }`

For more information about FIXED level of detail expressions, and for some example FIXED level of detail scenarios, see the FIXED section.

#### INCLUDE

* INCLUDE level of detail expressions compute values using the specified dimensions in addition to whatever dimensions are in the view.
* INCLUDE level of detail expressions are most useful when including a dimension that isn’t in the view.

Example: `{ INCLUDE [Customer Name] : SUM([Sales]) }`

For more information about INCLUDE level of detail expressions, and for some example INCLUDE level of detail scenarios, see the INCLUDE section.

#### EXCLUDE

* EXCLUDE level of detail expressions explicitly remove dimensions from the expression—that is, they subtract dimensions from the view level of detail.
* EXCLUDE level of detail expressions are most useful for eliminating a dimension in the view.

Example: `{EXCLUDE [Region]: SUM([Sales])}`

For more information about EXCLUDE level of detail expressions, and for some example EXCLUDE level of detail scenarios, see the EXCLUDE section.

#### Table-scoped

* For a table-scoped level of detail expression, no scoping keyword is required. For more information, see the Table-Scoped section.

### Dimension Declaration

Specifies one or more dimensions that set the scope of the aggregate expression, according to the keyword.

* FIXED [Name]

Use commas to separate multiple dimensions.

* `[Segment], [Category], [Region]`

You can use any expression that evaluates as dimension, including Date expressions.

* `{FIXED YEAR([Order Date]) : SUM(Sales)}` aggregates the sum of Sales at the Year level.
* `{INCLUDE DATETRUNC('day', [Order Date]) : AVG(Profit)}` aggregates the sum of Sales for [Order Date] truncated to the day date part. Because it’s an INCLUDE expression, it also uses the dimensions in the view to aggregate the value.

**Note**: It's recommended that you drag fields into the calculation editor when creating dimension declarations, instead of typing them. For example, if you see YEAR([Order Date]) on a shelf and then type that as the dimension declaration, it won’t match the field on the shelf. But if you drag the field from the shelf into the expression, it becomes DATEPART('year', [Order Date]), and that matches the field on the shelf.

With calculations saved to the Data pane Tableau can't match the name of a calculation to its contents. For example:

* Create a calculation: `MyCalculation = YEAR([Order Date])`
* Create an EXCLUDE level of detail expression `{EXCLUDE YEAR([Order Date]) : SUM(Sales)}`

If you use both calculations in the view, **MyCalculation** isn't excluded. The LOD doesn't understand that YEAR([Order Date]) is the same thing as **MyCalculation**.

Similarly, if the EXCLUDE expression specified MyCalculation ( `{EXCLUDE MyCalculation : SUM(Sales)}`), then YEAR([Order Date]) isn't excluded.

### : (a colon)

A colon separates the dimension declaration from the aggregate expression.

### Aggregate Expression

The aggregate expression is the calculation that is performed. For example, `SUM(Sales)` or `AVG(Discount)`. The results of the calculation in the aggregate expression depend on the dimension declaration and keyword.

The aggregate expression must be aggregated. The ATTR aggregation isn’t supported, however. It doesn't have to be a simple aggregation, it can contain calculations, including other LOD expressions: `{FIXED [Question] : AVG(IF [Answer] = "Red" THEN 1 ELSE 0 END )}`

Table calculations aren’t permitted in the aggregate expression.

Table-scoped LODs contain only the aggregate expression inside the braces, such as `{MIN(Grade)}`.
