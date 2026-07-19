## Table Calculation Functions

Table calculation functions perform computations on values in a table (the result set returned by a query). They operate row-by-row within a **partition** — a subset of rows defined by the calculation's scope.

### VDS Usage Constraint

**All table calculation functions in VDS must be expressed via the `tableCalculation` object wrapper — not by placing function syntax directly in a `calculation` string.** The `tableCalcType` field controls which operation is applied. Raw function syntax (e.g., `RUNNING_SUM(SUM([Sales]))`) is only valid when `tableCalcType` is set to `"CUSTOM"`.

Requires **Tableau >= 2025.3**.

> **For the full `tableCalculation` object schema, partitioning semantics, and worked examples for each type, see [TABLE_CALCULATIONS.md](../TABLE_CALCULATIONS.md).**

---

## Table calculation functions

### FIRST()

Returns the number of rows from the current row to the first row in the partition.

#### Example

When the current row index is 3, `FIRST() = -2`.

---

### INDEX()

Returns the index of the current row in the partition, without any sorting with regard to value. The first row index starts at 1.

#### Example

For the third row in the partition, `INDEX() = 3`.

---

### LAST()

Returns the number of rows from the current row to the last row in the partition.

#### Example

When the current row index is 3 of 7, `LAST() = 4`.

---

### LOOKUP(expression, [offset])

Returns the value of the expression in a target row, specified as a relative offset from the current row. Use `FIRST()+n` and `LAST()-n` for offsets relative to the first/last rows in the partition. If `offset` is omitted, the comparison row can be set on the field. Returns NULL if the target row cannot be determined.

#### Example

`LOOKUP(SUM([Profit]), FIRST()+2)` computes the SUM(Profit) in the third row of the partition.

---

### PREVIOUS_VALUE(expression)

Returns the value of this calculation in the previous row. Returns the given expression if the current row is the first row of the partition.

#### Example

`SUM([Profit]) * PREVIOUS_VALUE(1)` computes the running product of SUM(Profit).

---

### RANK(expression, ['asc' | 'desc'])

Returns the standard competition rank for the current row in the partition. Identical values are assigned an identical rank. Default order is descending.

With this function, the set of values (6, 9, 9, 14) would be ranked (4, 2, 2, 1).

Nulls are ignored in ranking functions. They are not numbered and do not count against the total number of records in percentile rank calculations.

> In VDS, use `tableCalcType: "RANK"` in the `tableCalculation` object rather than calling `RANK()` directly in a calculation string.

#### Example

`RANK(SUM([Profit]))` ranks each row by sum of profit, descending, with gaps for ties.

---

### RANK_DENSE(expression, ['asc' | 'desc'])

Returns the dense rank for the current row in the partition. Identical values are assigned an identical rank, but no gaps are inserted into the number sequence. Default order is descending.

With this function, the set of values (6, 9, 9, 14) would be ranked (3, 2, 2, 1).

Nulls are ignored in ranking functions.

---

### RANK_MODIFIED(expression, ['asc' | 'desc'])

Returns the modified competition rank for the current row in the partition. Identical values are assigned an identical rank. Default order is descending.

With this function, the set of values (6, 9, 9, 14) would be ranked (4, 3, 3, 1).

Nulls are ignored in ranking functions.

---

### RANK_PERCENTILE(expression, ['asc' | 'desc'])

Returns the percentile rank for the current row in the partition. Default order is ascending.

With this function, the set of values (6, 9, 9, 14) would be ranked (0.00, 0.67, 0.67, 1.00).

Nulls are ignored in ranking functions.

> In VDS, use `tableCalcType: "PERCENTILE"` in the `tableCalculation` object.

---

### RANK_UNIQUE(expression, ['asc' | 'desc'])

Returns the unique rank for the current row in the partition. Identical values are assigned different ranks. Default order is descending.

With this function, the set of values (6, 9, 9, 14) would be ranked (4, 2, 3, 1).

Nulls are ignored in ranking functions.

---

### RUNNING_AVG(expression)

Returns the running average of the given expression, from the first row in the partition to the current row.

> In VDS, use `tableCalcType: "RUNNING_TOTAL"` with the appropriate aggregation in the `tableCalculation` object.

#### Example

`RUNNING_AVG(SUM([Profit]))` computes the running average of SUM(Profit).

---

### RUNNING_COUNT(expression)

Returns the running count of the given expression, from the first row in the partition to the current row.

#### Example

`RUNNING_COUNT(SUM([Profit]))` computes the running count of SUM(Profit).

---

### RUNNING_MAX(expression)

Returns the running maximum of the given expression, from the first row in the partition to the current row.

#### Example

`RUNNING_MAX(SUM([Profit]))` computes the running maximum of SUM(Profit).

---

### RUNNING_MIN(expression)

Returns the running minimum of the given expression, from the first row in the partition to the current row.

#### Example

`RUNNING_MIN(SUM([Profit]))` computes the running minimum of SUM(Profit).

---

### RUNNING_SUM(expression)

Returns the running sum of the given expression, from the first row in the partition to the current row.

#### Example

`RUNNING_SUM(SUM([Profit]))` computes the running sum of SUM(Profit).

---

### SIZE()

Returns the number of rows in the partition.

#### Example

`SIZE() = 5` when the current partition contains five rows.

---

### TOTAL(expression)

Returns the total for the given expression across the entire table calculation partition, regardless of the current row.

> In VDS, use `tableCalcType: "PERCENT_OF_TOTAL"` or `"PERCENT_FROM"` in the `tableCalculation` object for total-based calculations.

#### Example

`TOTAL(SUM([Sales]))` returns the sum of all Sales values within the partition.

---

### WINDOW_AVG(expression, [start, end])

Returns the average of the expression within the window. The window is defined as offsets from the current row. Use `FIRST()+n` and `LAST()-n` for offsets from the first or last row in the partition. If start and end are omitted, the entire partition is used.

> In VDS, use `tableCalcType: "MOVING_CALCULATION"` for windowed aggregations.

#### Example

`WINDOW_AVG(SUM([Profit]), -2, 0)` returns the window average of SUM(Profit) from the two previous rows to the current row.

---

### WINDOW_CORR(expression1, expression2, [start, end])

Returns the Pearson correlation coefficient of two expressions within the window. Results range from -1 to +1, where 1 is an exact positive linear relationship, 0 is no linear relationship, and -1 is an exact negative relationship. If start and end are omitted, the entire partition is used.

> Note: The aggregate equivalent `CORR` is not supported in VDS. `WINDOW_CORR` is only available via `tableCalcType: "CUSTOM"` with a `tableCalculation` wrapper.

#### Example

`WINDOW_CORR(SUM([Profit]), SUM([Sales]), -5, 0)` returns the Pearson correlation of SUM(Profit) and SUM(Sales) from the five previous rows to the current row.

---

### WINDOW_COUNT(expression, [start, end])

Returns the count of the expression within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_COUNT(SUM([Profit]), FIRST()+1, 0)` computes the count of SUM(Profit) from the second row to the current row.

---

### WINDOW_COVAR(expression1, expression2, [start, end])

Returns the *sample covariance* of two expressions within the window. Uses n-1 normalization (appropriate for random samples estimating a larger population). If start and end are omitted, the entire partition is used.

> Note: The aggregate equivalent `COVAR` is not supported in VDS. `WINDOW_COVAR` is only available via `tableCalcType: "CUSTOM"` with a `tableCalculation` wrapper.

#### Example

`WINDOW_COVAR(SUM([Profit]), SUM([Sales]), -2, 0)` returns the sample covariance from the two previous rows to the current row.

---

### WINDOW_COVARP(expression1, expression2, [start, end])

Returns the *population covariance* of two expressions within the window. Uses n normalization (appropriate when data covers the full population). If start and end are omitted, the entire partition is used.

> Note: The aggregate equivalent `COVARP` is not supported in VDS. `WINDOW_COVARP` is only available via `tableCalcType: "CUSTOM"` with a `tableCalculation` wrapper.

#### Example

`WINDOW_COVARP(SUM([Profit]), SUM([Sales]), -2, 0)` returns the population covariance from the two previous rows to the current row.

---

### WINDOW_MEDIAN(expression, [start, end])

Returns the median of the expression within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_MEDIAN(SUM([Profit]), FIRST()+1, 0)` computes the median of SUM(Profit) from the second row to the current row.

---

### WINDOW_MAX(expression, [start, end])

Returns the maximum of the expression within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_MAX(SUM([Profit]), FIRST()+1, 0)` computes the maximum of SUM(Profit) from the second row to the current row.

---

### WINDOW_MIN(expression, [start, end])

Returns the minimum of the expression within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_MIN(SUM([Profit]), FIRST()+1, 0)` computes the minimum of SUM(Profit) from the second row to the current row.

---

### WINDOW_PERCENTILE(expression, number, [start, end])

Returns the value corresponding to the specified percentile within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_PERCENTILE(SUM([Profit]), 0.75, -2, 0)` returns the 75th percentile for SUM(Profit) from the two previous rows to the current row.

---

### WINDOW_STDEV(expression, [start, end])

Returns the sample standard deviation of the expression within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_STDEV(SUM([Profit]), FIRST()+1, 0)` computes the standard deviation of SUM(Profit) from the second row to the current row.

---

### WINDOW_STDEVP(expression, [start, end])

Returns the biased (population) standard deviation of the expression within the window. If start and end are omitted, the entire partition is used.

> Note: The aggregate equivalent `STDEVP` is not supported in VDS. `WINDOW_STDEVP` is only available via `tableCalcType: "CUSTOM"` with a `tableCalculation` wrapper.

#### Example

`WINDOW_STDEVP(SUM([Profit]), FIRST()+1, 0)` computes the biased standard deviation of SUM(Profit) from the second row to the current row.

---

### WINDOW_SUM(expression, [start, end])

Returns the sum of the expression within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_SUM(SUM([Profit]), FIRST()+1, 0)` computes the sum of SUM(Profit) from the second row to the current row.

---

### WINDOW_VAR(expression, [start, end])

Returns the sample variance of the expression within the window. If start and end are omitted, the entire partition is used.

#### Example

`WINDOW_VAR(SUM([Profit]), FIRST()+1, 0)` computes the variance of SUM(Profit) from the second row to the current row.

---

### WINDOW_VARP(expression, [start, end])

Returns the biased (population) variance of the expression within the window. If start and end are omitted, the entire partition is used.

> Note: The aggregate equivalent `VARP` is not supported in VDS. `WINDOW_VARP` is only available via `tableCalcType: "CUSTOM"` with a `tableCalculation` wrapper.

#### Example

`WINDOW_VARP(SUM([Profit]), FIRST()+1, 0)` computes the biased variance of SUM(Profit) from the second row to the current row.
