# Null Handling in Qlik Load Scripts

The canonical reference for script-layer null handling. Covers the null constructors and inspection functions (`Null()`, `IsNull()`, `NullCount()`), the three substitution/cleaning strategies (`vCleanNull` for string-encoded nulls, `NullAsValue` for sparse dimensions, explicit guards for date arithmetic), the key-field NULL phantom-association risk, and a defensive-coding decision framework.

For expression-side null handling, keep chart measures explicit about defaults and division guards rather than relying on script-side substitutions.

---

## 1. Null Constructors and Inspection

### `Null()` — explicit NULL constructor

Returns a NULL value. Use inside conditional expressions when a code branch should produce NULL rather than zero, an empty string, or a sentinel.

```qlik
IF(IsNull(registration_date)
    OR registration_date < MakeDate(1901, 1, 2),
   Null(),                                         // explicit NULL when the date is unusable
   Floor((Today() - registration_date) / 365.25)) AS [Customer.TenureYears]
```

Reference: help.qlik.com — Null function. "The Null function returns a null value."

### `IsNull(expr)` — NULL test

Returns true (-1) when `expr` is NULL, false (0) otherwise. The only correct way to test for NULL — SQL operator syntax (`IS NULL` / `IS NOT NULL`) does NOT work in Qlik LOAD or RESIDENT statements (see `references/sql-constructs.md` Section 1).

```qlik
WHERE NOT IsNull(customer_email)                   // filter out rows with NULL email
IF(IsNull(field_value), Null(), Trim(field_value)) // explicit NULL passthrough
```

`IsNull()` does NOT catch string-encoded nulls (`"null"`, `"NaN"`, `"n/a"`). Those are valid strings to Qlik; the test returns false. Use `vCleanNull` (Section 2) for that case.

### `NullCount(expr)` — aggregation of NULL count

Counts NULL values aggregated over the grouping context. The idiomatic Qlik aggregation for null-rate diagnostics.

```qlik
[_NullCheck]:
LOAD
    NullCount([Customer.Region])  AS region_nulls,
    NoOfRows('Customers')         AS total_rows
RESIDENT [Customers];
```

Reference: help.qlik.com — NullCount script and chart functions. "NullCount() returns the number of NULL values aggregated in the expression."

Do not use `Count(*)` as a substitute — `Count(*)` is not valid in Qlik LOAD or chart expressions (only in `SQL SELECT` pass-through). Use `NoOfRows('TableName')` for total row counts and `Count(field)` for non-null counts (see `references/sql-constructs.md` Section 2.2).

---

## 2. vCleanNull Variable Function (String-Encoded Nulls)

### The problem

Source data from ETL pipelines, JSON ingestion, data lakes, and API exports commonly contains literal strings that represent null: `"null"`, `"NaN"`, `"none"`, `"n/a"`, `"[null]"`, and empty strings. These are NOT SQL NULLs. Qlik's `IsNull()` function does NOT catch them. They appear as valid string values in filter panes and break aggregations.

### The pattern

```qlik
// SET preserves the template -- $1 placeholder stays unevaluated until expansion
SET vCleanNull = IF(IsNull($1) OR Len(Trim($1)) = 0
    OR Match(Lower(Trim($1)), 'null', 'nan', 'none', 'n/a', '[null]'),
    Null(), Trim($1));
```

### Usage

```qlik
// Simple field -- pass field name as $1:
$(vCleanNull(customer_name)) AS [Customer.Name],
$(vCleanNull(email_address)) AS [Customer.Email],
$(vCleanNull(phone_number))  AS [Customer.Phone]
```

### Why SET, not LET

`SET` preserves the right side as a literal string template. The `$1` placeholder remains unevaluated until the variable is expanded with `$(vCleanNull(field))`. `LET` would try to evaluate `$1` immediately at definition time and fail.

### Limitation: commas in arguments

The variable function CANNOT wrap expressions containing commas. Inside `$()`, commas separate parameters. If the argument contains a function with commas (`ApplyMap`, `PurgeChar`, `IF`), the call breaks.

```qlik
// WRONG -- PurgeChar has a comma, breaks the variable call:
$(vCleanNull(PurgeChar(given_names, '[]{}' & Chr(34))))

// RIGHT -- write the null check inline with a comment explaining why:
// Cannot use vCleanNull here (comma in PurgeChar args)
IF(IsNull(PurgeChar(given_names, '[]{}' & Chr(34)))
   OR Len(Trim(PurgeChar(given_names, '[]{}' & Chr(34)))) = 0
   OR Match(Lower(Trim(PurgeChar(given_names, '[]{}' & Chr(34)))),
            'null', 'nan', 'none', 'n/a', '[null]'),
   Null(),
   Trim(PurgeChar(given_names, '[]{}' & Chr(34))))  AS [Name.Given]
```

### When to use

- Fields from ETL pipelines, data lakes, or API ingestion where nulls may be string-encoded
- Any field where literal `"null"` or `"NaN"` strings have been observed in the data
- As a default defensive measure on all string fields from external sources

### When NOT to use

- Fields where the literal string `"null"` is a valid business value (rare but possible)
- Key fields — use explicit null checks and TRACE warnings instead; null keys indicate data quality issues that should not be masked
- Numeric fields — use `IsNull()` directly; string-encoded nulls in numeric fields indicate a type-coercion issue worth investigating

### PurgeChar for encoding artifacts

For fields polluted with bracket-encoded null markers like `[null]`, `{null}`, or stray quotes, strip the encoding characters before testing:

```qlik
$(vCleanNull(Trim(PurgeChar(field_name, '[]{}' & Chr(34))))) AS [Output.Field]
```

`PurgeChar` always requires two arguments — the string and the characters to strip. The vCleanNull comma limitation still applies: when chaining `PurgeChar` inside `vCleanNull`, expand inline as shown above.

### Complete variable function file

See `script-templates/clean-null-function.qvs` for the full set of null-cleaning utilities including `vCleanNull`, `vCleanDate`, `vCleanNumeric`, and `vDualBool`.

**`vDualBool` overview:** Converts a boolean-like field to `Dual()` with text display and numeric value. `Dual('Active', 1)` for true-like values, `Dual('Inactive', 0)` for false, `Dual('Unknown', -1)` for NULL. This gives text in filter panes, numeric for `Sum()`, and correct sort order. The function matches common true values (`'true'`, `'yes'`, `'y'`, `'1'`, `'active'`, `'enabled'`). For domain-specific true values like `'approved'` or `'confirmed'`, write a custom IF instead.

---

## 3. NullAsValue (Sparse Dimension Display)

### The problem

Sparse dimension fields where many records have NULL values. In Qlik filter panes, NULL values appear as `-` and cannot be selected alongside non-null values in the same selection set. Users want to see `'No Entry'` or `'Unknown'` as a selectable value.

### The pattern

```qlik
SET NullValue = 'No Entry';
NullAsValue [Customer.Region], [Customer.Segment], [Product.SubCategory];

[Customers]:
LOAD
    customer_id    AS [Customer.Key],
    customer_name  AS [Customer.Name],
    region         AS [Customer.Region],
    segment        AS [Customer.Segment]
FROM [lib://QVDs/Customers.qvd] (qvd);

// Always reset after each table load unless null replacement should persist:
NullAsNull *;
SET NullValue =;
```

### Use the loaded (output) field name

When a LOAD renames a field with `AS`, use the output alias in the `NullAsValue` declaration:

```qlik
// PREFERRED -- uses the loaded field name (the AS alias):
NullAsValue [Customer.Region];
LOAD region AS [Customer.Region] FROM ...;

// AMBIGUOUS -- uses the source column name; behavior when AS is in use
// is not documented and should be tested before relying on it:
NullAsValue region;
LOAD region AS [Customer.Region] FROM ...;
```

### Scope persistence and failure modes

`NullAsValue` is field-specific and stateful — it persists across all subsequent LOADs until explicitly reset with `NullAsNull *;` and `SET NullValue =;`. **Always pair every `NullAsValue` block with that reset immediately after the LOAD that needed it.**

Two failure modes when the switch is left active or applied to the wrong field type:

1. **Key field corruption.** Applying `NullAsValue` to key fields converts NULL to a string value (e.g., `'No Entry'`). Every NULL key in the source becomes the same string — creating phantom associations between unrelated rows (a customer with a NULL region key and an order with a NULL region key now "match" through the substituted string). See Section 4 below for the full phantom-association treatment.
2. **Measure field corruption.** Applying `NullAsValue` to measure fields converts NULL to a string. `Sum(field)` then silently breaks because the field is no longer numeric for the substituted rows.

Reference: help.qlik.com Cloud — NullAsValue statement. "The NullAsValue statement operates as a switch and will operate on subsequent loading statements. It can be switched off again by means of the NullAsNull statement."

### When to use

- Sparse dimension fields where NULL should be a selectable filter value
- Fields that serve as dimension headers in filter panes
- Classification fields where `'Unknown'` or `'Not Assigned'` is a meaningful category

### When NOT to use

- **Key fields** — see Section 4 below; substituting NULL with a string creates phantom associations
- **Measure fields intended for `Sum`/`Avg`** — converts NULL to a string, breaking numeric aggregation
- **Date fields used in arithmetic** — the substituted string breaks date math

### Scope management example

```qlik
// Apply NullAsValue for Customer table only
SET NullValue = 'Unknown';
NullAsValue [Customer.Region], [Customer.Segment];

[Customers]:
LOAD customer_id AS [Customer.Key],
     region AS [Customer.Region],
     segment AS [Customer.Segment]
FROM [lib://QVDs/Customers.qvd] (qvd);

// Reset before loading Product table (Product.Category should NOT get 'Unknown')
NullAsNull *;
SET NullValue =;

// Product NULLs stay as NULL (correct for this table)
[Products]:
LOAD product_id AS [Product.Key],
     category AS [Product.Category]
FROM [lib://QVDs/Products.qvd] (qvd);
```

---

## 4. Key-Field NULL: The Phantom-Association Risk

Never mask NULL values on key fields. The phantom-association risk has two distinct shapes depending on whether the NULL is substituted or left bare.

### Substituted NULL keys (NullAsValue applied to a key)

If `NullAsValue` is mistakenly applied to a key field, every NULL key in the source becomes the same substituted string (e.g., `'No Entry'`). Rows from unrelated parents now share that same key value and associate with each other through the substitution. Symptom: customers with no region key, orders with no region key, and products with no region key all appear to share a region — the engine cannot tell that those NULLs were unrelated. The same failure mode applies to measure fields, where the substituted string breaks `Sum`/`Avg` — see Section 3 "Scope persistence and failure modes" above.

### Bare NULL keys (left as-is)

Qlik's associative engine excludes NULL values from associations — a NULL key on the fact side will not associate with anything on the dimension side. This is correct behavior, but it is a silent data-quality issue:

- Fact rows with NULL keys do not aggregate against the dimension; they appear as orphaned values in the fact table.
- Selections on the dimension never include the orphaned fact rows.
- Totals computed against the dimension undercount the NULL-key facts.

### The right response: surface, do not mask

```qlik
// Detect NULL keys during load and TRACE a warning
[_KeyCheck]:
LOAD NullCount([Customer.Key]) AS null_key_count
RESIDENT [Customers];
LET vNullKeys = Peek('null_key_count', 0, '_KeyCheck');
DROP TABLE [_KeyCheck];

IF $(vNullKeys) > 0 THEN
    TRACE [WARNING] Customers table has $(vNullKeys) NULL key values;
    TRACE [WARNING] These rows will not associate with dependent tables;
END IF
```

Then escalate to the data source owner. A NULL key is upstream data quality — substituting it in Qlik hides the issue and creates phantom associations.

---

## 5. Null Guards on Date Arithmetic

### The problem

Per Qlik's null-value-handling documentation, NULL propagates through arithmetic operators: `Today() - NULL` returns NULL, and `Floor(NULL / 365.25)` also returns NULL. So a genuinely NULL date does not by itself produce a nonsense age — it produces a correctly NULL age. The real problem is **non-NULL garbage dates** that upstream systems substitute for missing values:

- **Sentinel dates** — sources that use `1900-01-01`, `1901-01-01`, or `1970-01-01` to represent `"unknown"` instead of NULL. These are valid dates, so NULL propagation does not protect you; `Today() - '1900-01-01'` returns ~46,000 and `/ 365.25` returns ~125.
- **String-encoded nulls coerced upstream** — a source column with the literal string `"null"` that was silently cast to a date somewhere in the pipeline.
- **Future dates from data entry bugs** — e.g., `registration_date = 2099-01-01` produces a large negative tenure.
- **Zero dates** — some databases store `0000-00-00`, which may round-trip as December 30, 1899 (Qlik's epoch zero), producing a ~125 year tenure.

```qlik
// Looks defensible but still produces garbage when source uses sentinel dates:
Floor((Today() - registration_date) / 365.25) AS [Customer.TenureYears]
// If registration_date = 1900-01-01 (sentinel for "unknown"): TenureYears = 125
```

### The pattern

Guard date arithmetic against **both** NULL and known sentinel/out-of-range values. The NULL check is cheap defensive insurance; the range check is what actually catches the sentinel-date bug:

```qlik
// RIGHT -- guard against NULL AND sentinel/out-of-range dates:
IF(IsNull(registration_date)
    OR registration_date < MakeDate(1901, 1, 2)       // catches epoch-zero, 1900-01-01 sentinels
    OR registration_date > Today(),                   // catches future-date data entry bugs
   Null(),
   Floor((Today() - registration_date) / 365.25)) AS [Customer.TenureYears]
```

### Common date arithmetic patterns with guards

```qlik
// Customer tenure (guards both NULL and sentinel/future dates)
IF(IsNull(registration_date)
    OR registration_date < MakeDate(1901, 1, 2)
    OR registration_date > Today(),
   Null(),
   Floor((Today() - registration_date) / 365.25)) AS [Customer.TenureYears]

// Days since last order (NULL-safe by default, but guard sentinel dates)
IF(IsNull(last_order_date) OR last_order_date < MakeDate(1901, 1, 2), Null(),
    Today() - last_order_date) AS [Customer.DaysSinceLastOrder]

// Date difference between two fields (NULL propagates, so IsNull is optional
// but explicit is clearer; add range guards if sentinels are possible)
IF(IsNull(start_date) OR IsNull(end_date), Null(),
    end_date - start_date) AS [Duration.Days]

// Tenure in months (guard sentinels and future hires)
IF(IsNull(hire_date)
    OR hire_date < MakeDate(1901, 1, 2)
    OR hire_date > Today(),
   Null(),
   Floor((Today() - hire_date) / 30.44)) AS [Employee.TenureMonths]
```

### Why this is easy to miss

When the source actually returns NULL, Qlik's NULL propagation produces the correct result (NULL) without any guard — so a naive script passes testing during development when the test data is clean. The bug only surfaces in production when an upstream system substitutes a sentinel date like `1900-01-01` for missing values. The calculation runs without error, the result is a plausible-looking number (125 is a valid age, just wrong), and the bug only becomes visible when someone notices impossible values in reports or when aggregations are skewed by phantom centenarians.

### When to apply

Any expression that involves:
- Subtraction between dates: `dateA - dateB`
- Division of a date difference: `(dateA - dateB) / N`
- Date functions on potentially-null fields: `Year(date_field)`, `Month(date_field)`

**Rule of thumb:** if a field is used as an operand in date math and it can ever be NULL, wrap the entire expression in an IsNull guard plus a range guard for known sentinels.

---

## 6. Defensive Null Handling Strategy

### Decision framework

| Field Type | Null Source | Strategy | Example |
|---|---|---|---|
| String dimension from external source | String-encoded nulls (`"null"`, `"NaN"`) | `vCleanNull` | `$(vCleanNull(region)) AS [Region]` |
| Sparse dimension for filter panes | Genuine SQL NULLs | `NullAsValue` (with reset) | `NullAsValue [Customer.Segment]` |
| Date/numeric used in calculations | Any null source | `IsNull` guard + sentinel range | `IF(IsNull(date) OR date<MakeDate(1901,1,2), Null(), ...)` |
| Boolean field | NULL = unknown state | `Dual` with `-1` | `$(vDualBool(is_active, Active, Inactive))` |
| Key field | Any null source | **Never mask.** TRACE a warning. | Null key = data quality issue (Section 4) |

### Layered application

In a typical extraction script, all three strategies may apply to different fields in the same LOAD:

```qlik
SET NullValue = 'No Entry';
NullAsValue [Customer.Region], [Customer.Segment];

[Customers]:
LOAD
    customer_id                                           AS [Customer.Key],
    $(vCleanNull(customer_name))                          AS [Customer.Name],
    region                                                AS [Customer.Region],
    segment                                               AS [Customer.Segment],
    IF(IsNull(registration_date)
        OR registration_date < MakeDate(1901, 1, 2)
        OR registration_date > Today(), Null(),
       Floor((Today() - registration_date) / 365.25))    AS [Customer.TenureYears],
    $(vDualBool(is_active, Active, Inactive))             AS [Customer.IsActive]
RESIDENT [_RawCustomers];

NullAsNull *;
SET NullValue =;
```

In this example:
- `customer_id`: no null masking (key field; nulls indicate data issues)
- `customer_name`: `vCleanNull` (catches `"null"` strings from upstream)
- `region`, `segment`: `NullAsValue` (sparse dimensions, need filter pane display)
- `registration_date`: `IsNull` guard + sentinel-date range check (used in tenure calculation)
- `is_active`: `Dual` boolean with `Unknown/-1` for NULL

---

## See Also

- `qlik-load-script` SKILL.md Section 6 — inline summary of the three strategies
- Expression-side measures should document defaults and use explicit null/division guards where needed
- `script-templates/clean-null-function.qvs` — `vCleanNull`, `vCleanDate`, `vCleanNumeric`, `vDualBool` definitions
- help.qlik.com Cloud — Null function, IsNull function, NullCount function, NullAsValue statement, Null-value handling
