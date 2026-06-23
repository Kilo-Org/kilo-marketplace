# Snowflake Error Taxonomy

## `Object does not exist` / `does not exist or not authorized`

Likely causes:

- wrong database or schema
- wrong environment (`prod` vs personal/dev schema)
- typo in relation name
- role lacks access
- view points to an upstream relation that moved

Checks:

- fully qualify the relation
- list or describe the object in the target schema
- confirm role and warehouse context

## `invalid identifier`

Likely causes:

- misspelled column
- column exists on a different table alias
- referring to a SELECT alias from `where` instead of `qualify` / outer query
- quoted identifier mismatch

Checks:

- describe the relation
- qualify the column with the alias
- isolate the expression into a smaller query

## `ambiguous column name`

Likely causes:

- same column name on multiple joined relations
- unqualified select, filter, order, or group by field

Fix:

- qualify every shared column with its alias

## Parser errors like `unexpected ','`, `unexpected ')'`, `syntax error line ...`

Likely causes:

- malformed CTE chain
- trailing comma
- dialect mismatch from copied SQL
- reserved word used as alias

Checks:

- strip to the failing CTE
- rebuild one clause at a time

## `Numeric value ... is not recognized`

Likely causes:

- non-numeric strings in a numeric cast
- currency or punctuation embedded in values
- mixed-type `coalesce`

Checks:

- inspect `try_to_number()` failures
- standardize types before arithmetic

## Division by zero or implausible percentages

Likely causes:

- denominator can be zero
- denominator population differs from numerator population

Fix:

- use `nullif(denominator, 0)`
- verify denominator grain and scope

## Query runs but returns duplicates

Likely causes:

- one-to-many join without prior aggregation
- duplicate source rows at the assumed key
- joining on non-unique natural keys

Checks:

- count duplicates by key on both sides
- aggregate right side before join if the output grain requires one row per key

## Query runs but returns zero rows

Likely causes:

- too-tight or wrong-grain date filter
- join keys do not overlap
- timestamps compared in different timezones or grains
- soft-delete filter removes all rows

Checks:

- test filters one by one
- inspect overlap of join keys
- compare raw timestamp vs `::date` behavior

## Timeout or excessive runtime

Likely causes:

- unbounded scan on a large fact table
- heavy join before filtering
- distinct or window over too-broad input
- warehouse too small or suspended/resumed unexpectedly

Checks:

- constrain time range
- reduce columns
- run the base CTE first
- inspect `EXPLAIN`

## Query looks correct but data is stale or incomplete

Likely causes:

- upstream ingestion lag
- incremental model not yet caught up
- mirror/outage backfill landed late
- reading a transformed table when the source is fresher

Checks:

- compare source vs downstream counts for affected dates
- inspect load timestamps if available
- verify table cadence assumptions
