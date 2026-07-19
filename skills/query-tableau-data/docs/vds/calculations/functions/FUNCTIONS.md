# Functions in Tableau

Functions are the primary building blocks of calculations in Tableau. They transform, aggregate, and evaluate data by accepting arguments — fields, literals, parameters, or nested functions — and returning a result. Every calculation in VDS that does more than simple arithmetic will rely on one or more of the function categories listed below.

For a broader introduction to calculations and how functions fit alongside fields, operators, and literals, see [CALCULATIONS.md](../CALCULATIONS.md).

## Contents

| File | Description |
| --- | --- |
| [AGGREGATE.md](./AGGREGATE.md) | Functions that summarize or change the granularity of data, such as `SUM`, `AVG`, `MIN`, `MAX`, and `COUNT` |
| [DATES.md](./DATES.md) | Functions for working with date fields — parsing, truncating, adding intervals, and extracting date parts; includes VDS-specific limitations |
| [LOGICAL.md](./LOGICAL.md) | Boolean logic functions and control flow — `IF`, `IIF`, `CASE`, `AND`, `OR`, `NOT`, `ISNULL`, and related operators |
| [NUMBER.md](./NUMBER.md) | Mathematical functions for numeric fields — rounding, powers, trigonometry, and other numeric computations |
| [REGEX.md](./REGEX.md) | Regular expression functions (`REGEXP_MATCH`, `REGEXP_EXTRACT`, `REGEXP_REPLACE`) for pattern matching and extraction on supported data sources |
| [STRING.md](./STRING.md) | Functions for manipulating text fields — concatenation, trimming, searching, replacing, and changing case |
| [TABLE_CALCS.md](./TABLE_CALCS.md) | Functions that operate on the local result set row-by-row, such as `RUNNING_SUM`, `RANK`, `LOOKUP`, and `WINDOW_AVG`; subject to VDS usage constraints |
| [TYPE.md](./TYPE.md) | Type conversion (casting) functions for changing a field from one data type to another, such as `STR`, `INT`, `DATE`, and `FLOAT` |
| [USER.md](./USER.md) | Functions that return information about the current user, used to build user filters and row-level security |
