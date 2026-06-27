## Best Practices for Creating Calculations in Tableau

This article describes several tips and guidelines for creating efficient calculations in Tableau. These guidelines are meant to help you optimize your workbook performance. For more information about all the ways you can improve workbook performance, see the Optimize Workbook Performance series.

## General Rule: Avoid using a calculated field multiple times in another calculation

Referencing the same calculated field multiple times within another calculation will result in performance issues. If you use a calculated field within a calculation (also known as creating a Nested Calculation), try to reference it only once in the calculation.

Note that referencing a field (terminal field) multiple times in a calculation shouldn't degrade performance.

### Example

Let's say you create a calculated field that uses a complicated multiple line calculation to find mentions, or Twitter handles, in tweets. The calculated field is titled, Twitter Handle. Each handle that is returned starts with the '@' sign (for example: @user).

For your analysis, you want to remove the '@' symbol.

To do so, you can use the following calculation to remove the first character from the string:

`RIGHT([Twitter Handle], LEN([Twitter Handle]) -1)`

This calculation is quite simple. However, since it references the Twitter Handle calculation twice, it performs that calculation twice for each record in your data source: once for the RIGHT function and again for the LEN function.

In order to avoid calculating the same calculation more than once, you can rewrite the calculation to one that uses the Twitter Handle calculation only once. In this example, you can use MID to accomplish the same goal:

`MID([Twitter Handle], 2)`

## Tip 1: Convert multiple equality comparisons to a CASE expression or a group

Let's say you have the following calculation, which uses the calculated field, Person (calc), multiple times and employs a series of OR functions. This calculation, though a simple logical expression, will cause query performance issues because it performs the Person (calc) calculation at least ten times.

`IF [Person (calc)] = 'Henry Wilson'
OR [Person (calc)] = 'Jane Johnson'
OR [Person (calc)] = 'Michelle Kim'
OR [Person (calc)] = 'Fred Suzuki'
OR [Person (calc)] = 'Alan Wang'
THEN 'Lead'
ELSEIF [Person (calc)] = 'Susan Nguyen'
OR [Person (calc)] = 'Laura Rodriguez'
OR [Person (calc)] = 'Ashley Garcia'
OR [Person (calc)] = 'Andrew Smith'
OR [Person (calc)] = 'Adam Davis'
THEN 'IC'
END`

Instead of using an equality comparison, try the following solutions.

### Solution 1

Use a CASE expression. For example:

`CASE [Person (calc)]
WHEN 'Henry Wilson' THEN 'Lead'
WHEN 'Jane Johnson' THEN 'Lead'
WHEN 'Michelle Kim' THEN 'Lead'
WHEN 'Fred Suzuki' THEN 'Lead'
WHEN 'Alan Wang' THEN 'Lead'

WHEN 'Susan Nguyen' THEN 'IC'
WHEN 'Laura Rodriguez' THEN 'IC'
WHEN 'Ashley Garcia' THEN 'IC'
WHEN 'Andrew Smith' THEN 'IC'
WHEN 'Adam Davis' THEN 'IC'
END`

In this example, the calculated field, Person (calc), is only referenced once. Therefore, it is only performed once. CASE expressions are also further optimized in the query pipeline, so you gain an additional performance benefit.

### Solution 2

Create a group instead of a calculated field. For more information, see Group Your Data.

## Tip 2: Convert multiple string calculations into a single REGEXP expression

> **VDS Note**: REGEXP functions are only available when the underlying published data source uses a supported connector (Text File, Hadoop Hive, Google BigQuery, PostgreSQL, Tableau Data Extract, Microsoft Excel, Salesforce, Vertica, Pivotal Greenplum, Teradata 14.1+, Snowflake, Oracle). If the data source does not support REGEXP, this optimization cannot be used in a VDS `calculation` field.



### Example 1: CONTAINS

Let's say you have the following calculation, which uses the calculated field, Category (calc), multiple times. This calculation, though also a simple logical expression, will cause query performance issues because it performs the Category (calc) calculation multiple times.

`IF CONTAINS([Segment (calc)],'UNKNOWN')
OR CONTAINS([Segment (calc)],'LEADER')
OR CONTAINS([Segment (calc)],'ADVERTISING')
OR CONTAINS([Segment (calc)],'CLOSED')
OR CONTAINS([Segment (calc)],'COMPETITOR')
OR CONTAINS([Segment (calc)],'REPEAT')
THEN 'UNKNOWN'
ELSE [Segment (calc)] END`

You can use a REGEXP expression to get the same results without as much repetition.

#### Solution

`IF REGEXP_MATCH([Segment (calc)], 'UNKNOWN|LEADER|ADVERTISING|CLOSED|COMPETITOR|REPEAT') THEN 'UNKNOWN'
ELSE [Segment (calc)] END`



With string calculations that use a similar pattern, you can use the same REGEXP expression.

### Example 2: STARTSWITH

`IF STARTSWITH([Segment (calc)],'UNKNOWN')
OR STARTSWITH([Segment (calc)],'LEADER')
OR STARTSWITH([Segment (calc)],'ADVERTISING')
OR STARTSWITH([Segment (calc)],'CLOSED')
OR STARTSWITH([Segment (calc)],'COMPETITOR')
OR STARTSWITH([Segment (calc)],'REPEAT')
THEN 'UNKNOWN'`

#### Solution

`IF REGEXP_MATCH([Segment (calc)], '^(UNKNOWN|LEADER|ADVERTISING|CLOSED|COMPETITOR|REPEAT)') THEN 'UNKNOWN'
ELSE [Segment (calc)] END`

Note that the '^' symbol is used in this solution.

### Example 3: ENDSWITH

`IF ENDSWITH([Segment (calc)],'UNKNOWN')
OR ENDSWITH([Segment (calc)],'LEADER')
OR ENDSWITH([Segment (calc)],'ADVERTISING')
OR ENDSWITH([Segment (calc)],'CLOSED')
OR ENDSWITH([Segment (calc)],'COMPETITOR')
OR ENDSWITH([Segment (calc)],'REPEAT')
THEN 'UNKNOWN'
ELSE [Segment (calc)] END`

#### Solution

`IF REGEXP_MATCH([Segment (calc)], '(UNKNOWN|LEADER|ADVERTISING|CLOSED|COMPETITOR|REPEAT)$') THEN 'UNKNOWN'
ELSE [Segment (calc)] END`

Note that the '$' symbol is used in this solution.

## Tip 3: Manipulate strings with REGEXP instead of LEFT, MID, RIGHT, FIND, LEN

Regular expressions can be a very powerful tool. When doing complex string manipulation, consider using regular expressions. In a lot of cases, using a regular expression will result in a shorter and more efficient calculation.

> **VDS Note**: See the connector restrictions in Tip 2 above — REGEXP is only usable if your data source supports it.

### Example 1

Let's say you have the following calculation, which removes protocols from URLs. For example: "https://www.tableau.com" becomes "www.tableau.com".

`IF (STARTSWITH([Server], "http://")) THEN
MID([Server], Len("http://") + 1)
ELSEIF(STARTSWITH([Server], "https://")) THEN
MID([Server], Len("https://") + 1)
ELSEIF(STARTSWITH([Server], "tcp:")) THEN
MID([Server], Len("tcp:") + 1)
ELSEIF(STARTSWITH([Server], "\\")) THEN
MID([Server], Len("\\") + 1)
ELSE [Server]
END`

#### Solution

You can simplify the calculation and improve performance by using a REGEXP\_REPLACE function.

`REGEXP_REPLACE([Server], "^(http://|https://|tcp:|\\\\)", "")`

### Example 2

Let's say you have the following calculation, which returns the second part of an IPv4 address. For example: "172.16.0.1" becomes "16".

`IF (FINDNTH([Server], ".", 2) > 0) THEN
MID([Server],
FIND([Server], ".") + 1,
FINDNTH([Server], ".", 2) - FINDNTH([Server], ".", 1) - 1
)
END`

#### Solution

You can simplify the calculation and improve performance by using a REGEXP\_EXTRACT function.

`REGEXP_EXTRACT([Server], "\.([^\.]*)\.")`
