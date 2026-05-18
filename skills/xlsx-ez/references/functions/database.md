# Excel Database Functions

Database functions perform calculations on a column of values in a list or table
that match a criteria range. Each function takes the form `Dfunction(database, field, criteria)`:
- **database**: the table range including headers
- **field**: column name (as text) or column number (1-based)
- **criteria**: a two-row range where the first row is a header and the second is the condition

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

`DAVERAGE(database, field, criteria)` — Averages values in a column of the database that match the criteria.

`DCOUNT(database, field, criteria)` — Counts cells containing numbers in a column of the database that match the criteria.

`DCOUNTA(database, field, criteria)` — Counts non-empty cells in a column of the database that match the criteria.

`DGET(database, field, criteria)` — Extracts a single record from the database that matches the criteria; returns an error if more than one record matches.

`DMAX(database, field, criteria)` — Returns the maximum value from records in the database that match the criteria.

`DMIN(database, field, criteria)` — Returns the minimum value from records in the database that match the criteria.

`DPRODUCT(database, field, criteria)` — Multiplies values in a column of the database that match the criteria.

`DSTDEV(database, field, criteria)` — Estimates standard deviation based on a sample of database records matching the criteria.

`DSTDEVP(database, field, criteria)` — Calculates standard deviation based on the entire population of database records matching the criteria.

`DSUM(database, field, criteria)` — Adds numbers in a column of the database that match the criteria.

`DVAR(database, field, criteria)` — Estimates variance based on a sample of database records matching the criteria.

`DVARP(database, field, criteria)` — Calculates variance based on the entire population of database records matching the criteria.

## Example

```
A1: Name    B1: Sales    C1: Region
A2: Alice   B2: 5000     C2: North
A3: Bob     B3: 3000     C3: South
A4: Carol   B4: 7000     C4: North

Criteria range (E1:F2):
E1: Region  F1: Sales
E2: North   F2: >4000

=DSUM(A1:C4, "Sales", E1:F2)   → 12000 (Alice + Carol, both North with Sales>4000)
=DCOUNT(A1:C4, "Sales", E1:E2) → 2     (count of North records)
```
