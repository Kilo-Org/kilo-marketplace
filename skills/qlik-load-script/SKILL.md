---
name: qlik-load-script
description: >-
  Script syntax reference, QVD optimization, incremental load patterns
  (insert-only, insert/update, insert/update/delete, dual-timestamp for SCD2),
  JOIN/KEEP prefixes, ApplyMap patterns, CROSSTABLE, master calendar generation,
  variable definitions, error handling, logging patterns, null handling
  patterns, diagnostic and validation patterns, subroutine integration, and
  platform gotchas (SET vs LET, dollar-sign expansion timing, SET variable comma
  limitation). Load when writing, reviewing, or debugging Qlik load scripts, QVD
  operations, STORE/LOAD syntax, preceding LOAD, NullAsValue, script
  organization, JOIN, KEEP, ApplyMap, CROSSTABLE, AutoNumber, composite keys, or
  data quality defensive coding.
metadata:
  upstream:
    user-invocable: false
  category: data
  source:
    repository: 'https://github.com/Pupfish-LLC/qlik-toolkit'
    path: skills/qlik-load-script
    license_path: LICENSE
    commit: 2060bc2f278b73751f55ad9f8d569c45c1b2a5ff
---

# Qlik Load Script

Qlik script resembles SQL but is a fundamentally different language. It runs inside the Qlik associative engine, not a relational database. The most critical rule: **Qlik script is NOT SQL.** The single most predictable failure mode for AI-generated scripts is SQL syntax inside LOAD statements. Before writing any LOAD statement, internalize Section 1 below. Before writing any variable function, internalize Section 3.

This skill covers script mechanics, QVD operations, incremental loads, null handling, error handling, diagnostics, variable patterns, master calendar, and subroutine integration. It does NOT cover naming conventions (see `qlik-naming-conventions`), data model design (see `qlik-data-modeling`), expression syntax (see `qlik-expressions`), or optimization strategies (see `qlik-performance`).

## 1. Script Generation Constraints (CRITICAL)

These SQL constructs do NOT exist in Qlik LOAD statements. Using them causes reload errors or silent failures.

| SQL Syntax | Why It Fails | Qlik Alternative |
|---|---|---|
| `HAVING` | Not a keyword in Qlik script | Preceding LOAD with `WHERE` on aggregated field |
| `Count(*)` | No wildcard aggregation | `Count(field_name)` with explicit field |
| `SELECT DISTINCT` | SELECT is for SQL pass-through only | `LOAD DISTINCT` |
| `IS NULL` / `IS NOT NULL` | Operator syntax not supported | `IsNull(field)` / `NOT IsNull(field)` |
| `BETWEEN` | Not a keyword | `field >= low AND field <= high` |
| `IN (list)` | Not supported | `Match(field, v1, v2)` or `WildMatch()` |
| `CASE WHEN` | Not a keyword | `IF()`, `Pick()`, or `Match()` |
| `LIMIT` | Not a keyword | `FIRST n LOAD ...` prefix (works on any source); `WHERE RecNo() <= N` as a fallback |
| Table aliases (`FROM t1`) | Not supported in LOAD | Full table names in brackets |
| `WITH ... AS (...)` (CTE) | No CTE syntax in LOAD/RESIDENT | Sequential LOADs into named tables, then RESIDENT downstream; DROP the intermediates |
| `ROW_NUMBER() OVER (...)` | No window functions in LOAD/RESIDENT | `RowNo()` with `ORDER BY` in a RESIDENT load; or `AutoNumber()` over a `GROUP BY` partition key |
| `LAG()` / `LEAD()` | No window functions in LOAD/RESIDENT | `Previous(field)` for the prior row; `Peek(field, row, table)` for arbitrary offsets |
| `UNION` / `UNION ALL` | Not a keyword | `CONCATENATE([Target])` prefix; auto-concatenates when field sets fully match |
| `EXCEPT` / `INTERSECT` | Not keywords | `WHERE NOT EXISTS(aliased_key, source_key)` (except) / `WHERE EXISTS(...)` (intersect) with an aliased lookup table |
| `MERGE INTO` (SQL upsert) | Not LOAD/RESIDENT syntax; Qlik's `MERGE` prefix is for partial reloads only | `CONCATENATE` new rows + dedup with `WHERE NOT EXISTS`; or the `MERGE` partial-reload prefix (see `references/incremental-load-patterns.md`) |
| `LATERAL` / `CROSS APPLY` | No equivalent in LOAD/RESIDENT | Refactor at the `SQL SELECT` pass-through layer, or expand inline with `SubField` + `IterNo()` for row-multiplying delimited strings |

**Exception:** `SQL SELECT` pass-through statements to database connections CAN use native SQL syntax including all of the above. The constraint applies only to LOAD/RESIDENT operations.

**Dollar-sign expansion safety:** Every `$(variable(...))` call must be checked for commas in arguments. Inside `$()`, commas separate parameters, not expression arguments. See Section 3 for the full rules and examples.

**Deeper reference:** see `references/sql-constructs.md` for each construct's full failure mode, worked-example rewrites of the SQL→Qlik conversion, the `SQL SELECT` pass-through exception with examples, and the five most common adjacent failure modes (`NoConcatenate`, `Count()` argument requirements, `QUALIFY` with prefixed fields, `DROP TABLE` discipline, `NullAsValue` scope).

### QUALIFY/UNQUALIFY

`QUALIFY` prefixes field names with their table name to prevent unintended associations. Aliasing fields with `AS` in the LOAD is equally valid and usually clearer. `QUALIFY` is a stateful toggle that persists across tabs until reset. Failure modes (double-prefix when combined with manual prefixing, missing UNQUALIFY producing data islands, persistent state contaminating later tabs) and the "pick one prefixing discipline" rule live in `qlik-data-modeling` → `references/anti-patterns.md` #4. Syntax detail with worked examples in `references/sql-constructs.md` Section 2.3.

## 2. SET vs LET

`SET` preserves the right side as literal text (a template, re-evaluated at use time). `LET` evaluates the right side once at script-load time and stores the result.

**Rule:** Use `SET` for expression templates, variable functions with `$1` placeholders, and anything referenced in chart expressions. Use `LET` for values needed as a literal downstream in the script (row counts, FOR-loop bounds, incremental-load timestamps).

**Critical script gotcha:** `SET` does not evaluate function calls on its right side. `SET HidePrefix=Chr(37);` assigns the literal string `Chr(37)`, not `%`. Use `LET HidePrefix=Chr(37);` (evaluates to `%`) or `SET HidePrefix='%';` (literal). Applies to all function calls on the right of SET (`Chr()`, `Num()`, `Date()`, `Today()`, `Time()`, etc.).

See `qlik-expressions/references/variable-rules.md` Section 1 for the full decision criteria, LET evaluation semantics, the dynamic-UI rule, and worked examples.

## 3. Dollar-Sign Expansion

Inside `$()`, commas are parameter delimiters, not expression argument separators. Passing a comma-containing expression (`ApplyMap`, `IF`, `PurgeChar`, `Concat`) as an argument to a variable function breaks the call — the engine splits at the inner commas. The rule: only pass simple field references or literals to variable functions; write comma-containing logic inline with a comment.

See `qlik-expressions/references/variable-rules.md` Section 2 for full coverage — the comma-trap mechanism, the list of commonly triggering functions, the wrong/right worked example, and the rare `Chr(44)` workaround.

**Script-context null variable expansion:** If a `LET` assignment evaluates to null, the variable is empty. `IF $(emptyVar) >= 0 THEN` becomes `IF >= 0 THEN` -- a syntax error. Guard at assignment time with a default: `LET vX = Alt(NoOfRows('MaybeGone'), -1);` or check before expansion: `IF '$(vX)' <> '' AND $(vX) >= 0 THEN`. This applies to any function that can return null (`NoOfRows` on dropped/nonexistent tables, `Peek` past end of table, `FieldValue` out of range, etc.).

## 4. Preceding LOAD

Two LOAD statements sharing one source. The inner (bottom) LOAD executes first. The outer (top) LOAD reads the inner's output and can reference fields calculated by the inner -- so you only write the expensive expression once.

```qlik
[Customers]:
LOAD
    *,
    IF([Customer.TenureYears] < 1, 'New', 'Returning') AS [Customer.TenureBand]
;
LOAD
    customer_id AS [Customer.Key],
    customer_name AS [Customer.Name],
    registration_date,
    Floor((Today() - registration_date) / 365.25) AS [Customer.TenureYears]
FROM [lib://QVDs/Customers.qvd] (qvd);
```

The bottom LOAD pulls from the QVD and computes `[Age]`. The top LOAD reads those rows and references `[Age]` to derive `[Age.Category]`. Only one table (`[Customers]`) is produced. The same pattern works with `RESIDENT`, `INLINE`, and `SQL SELECT` sources.

**When to use:** Avoid repeating the same complex expression in nested IFs. Calculate once in the inner LOAD, reference in the outer. Also used as the Qlik replacement for `HAVING`: aggregate in inner LOAD, filter on the aggregate in outer LOAD with `WHERE`.

## 5. Date/Number Interpretation

Qlik stores every value as a **dual**: a text representation and a numeric representation held together. Dates are stored as serial numbers (days since 1899-12-30). Understanding this dual nature prevents the most common date bugs.

**`Date#()` vs `Date()`:** `Date#(string, 'format')` interprets a text string into its numeric serial value (parsing). `Date(serial, 'format')` formats a numeric serial into a display string. Confusing them is the #1 date bug.

```qlik
// Interpreting a text date from source:
Date#(ship_date, 'MM/DD/YYYY') AS [Order.ShipDate]

// Formatting an already-numeric date for display:
Date(Floor(order_timestamp), 'YYYY-MM-DD') AS [Order.Date]
```

**SET DateFormat dependency:** `Date#()` without a format argument uses the app's `SET DateFormat`. If source dates differ from the app format, you MUST specify the format string explicitly. Silent misinterpretation produces wrong dates with no error.

**Num#() and Num():** Same pattern. `Num#(string, 'format')` parses text to number. `Num(number, 'format')` formats for display. For money: `Num#(revenue, '#,##0.00')`.

## 6. Null Handling (Summary)

Three strategies, each for a different null shape:

| Field Type | Null Shape | Strategy |
|---|---|---|
| String dimensions from external sources | String-encoded (`"null"`, `"NaN"`, `"n/a"`) — `IsNull()` does NOT catch these | `vCleanNull` |
| Sparse dimensions for filter pane display | Genuine SQL NULL | `NullAsValue` (with reset) |
| Date/numeric calculations | Genuine NULL plus non-NULL sentinel dates (`1900-01-01`, epoch zero) | Explicit `IsNull` + range guards |
| Key fields | Any null | **Never mask** — surface as data quality issue |

`NullAsValue` is field-specific and stateful — persists until reset with `NullAsNull *;` + `SET NullValue =;`. Never apply to key fields (creates phantom associations through the substituted string) or measure fields (breaks `Sum`/`Avg`).

For date arithmetic, the threat is non-NULL sentinels (sources substitute `1900-01-01` for "unknown"), not genuine NULLs — those propagate to NULL correctly. Guard against both: `IF(IsNull(d) OR d < MakeDate(1901,1,2) OR d > Today(), Null(), ...)`.

Full treatment — `Null()` / `IsNull()` / `NullCount()` constructors, the `vCleanNull` variable function with comma-trap workarounds, the `NullAsValue` scope-management pattern, the key-field NULL phantom-association risk, date-arithmetic sentinel guards, and the layered defensive-coding strategy — is in `references/null-handling.md`. For null handling in expressions (`Alt`, `Coalesce`, `RangeSum`, division guards), see `qlik-expressions` SKILL.md Section 9.

## 7. Data-Driven Patterns

**Range bucketing via mapping expansion (`ApplyMap`):** for **static, enumerable, integer** buckets applied globally (age bands, score ranges, star ratings). Inline table + `WHILE IterNo()` expansion + `ApplyMap`. Edit the inline table to change buckets.

```qlik
[_Def]: LOAD * INLINE [from, to, label, sort
0,  17, 0-17,  1
18, 24, 18-24, 2
65, 200, 65+,  7] (delimiter is ',');

_Map: MAPPING LOAD Num#(from) + IterNo() - 1, Dual(Trim(label), Num#(sort))
RESIDENT [_Def] WHILE Num#(from) + IterNo() - 1 <= Num#(to);
DROP TABLE [_Def];

ApplyMap('_Map', [Age], Dual('Unknown', 0)) AS [Age.Group]
```

**IntervalMatch prefix:** for **data-driven, per-entity, or time-varying** intervals — SCD2 effective-dating, DV2 satellite point-in-time, version history, per-line tier definitions. One-key + N-key forms (up to 5 extra key fields), supports overlapping intervals, produces a `$Syn` by construction (resolve with `LEFT JOIN` + `DROP TABLE` of the IntervalMatch output). Quick decision: interval table changes per entity or over time → `IntervalMatch`; static global reference list → Range Bucketing. Full syntax, SCD2 worked example with NULL upper-bound handling, performance notes, and three wrong-choice scenarios in `references/interval-match.md`.

**Boolean fields via Dual:** `Dual('Active', 1)` enables text display AND numeric aggregation (`Sum([Is.Active])` = count of active). Wrap in a SET variable function for reuse. See `script-templates/clean-null-function.qvs` for vDualBool.

**Metadata-driven table loading:** Define an inline metadata table (TableName, SourceTable, PrimaryKey, Enabled) and loop through it with FOR/Peek. Adding a new table = adding a metadata row.

```qlik
FOR i = 0 TO NoOfRows('_Metadata') - 1
    LET vTableName = Peek('TableName', $(i), '_Metadata');
    LET vEnabled   = Peek('Enabled', $(i), '_Metadata');
    IF '$(vEnabled)' = 'Y' THEN
        [$(vTableName)]:
        LOAD * FROM [lib://Connection/$(vTableName).qvd] (qvd);
    END IF
NEXT i
```

**Concat-and-Peek for UI-variable build:** Materialize a delimited string (typically `|`-separated tokens) once at reload and expose it via a variable. The common consumer is the Dashboard Bundle Variable Input control, whose Dynamic values mode parses a pipe-delimited string rather than enumerating a field — a bare field reference in that control collapses to one scalar.

```qlik
[_PipeBuild]:
LOAD Concat([Code] & '~' & [Label], '|') AS pipe RESIDENT [Menu];
LET vPipe = Peek('pipe', 0, '_PipeBuild');
DROP TABLE [_PipeBuild];
```

Consume on the UI side with dollar-sign expansion (`='$(vPipe)'`). The technique generalizes beyond Variable Input — anywhere a UI control or set-analysis clause needs a delimited string of distinct values, this is the pattern. See `qlik-visualization` → `references/variable-input-control.md` for the full UI consumption walkthrough including value-label form and chart-side double-dollar dereferencing.

## 8. JOIN/KEEP Prefixes (Summary)

JOIN and KEEP combine two tables. **Critical difference from SQL:** Qlik joins on ALL fields with matching names between the two tables, not just the field you intend as a key. Unintended field-name overlaps produce wrong results silently — e.g., a `Status` field present in both Customers and Orders causes a LEFT JOIN to drop every order whose Status does not match its customer's Status, with no error raised.

**The rule:** Before any JOIN, list the fields in both tables and alias every non-key field that shares a name. Never rely on Qlik to "figure out" the intended key.

**JOIN vs KEEP:** JOIN merges into one table; KEEP filters both tables to matching rows but keeps them separate in the data model. **Row multiplication:** if the join key is not unique on both sides, rows multiply (1000-row fact × 3-per-key lookup = 3000 rows). **Decision:** JOIN for small lookups with unique keys; ApplyMap for large lookups or when a default value is needed (Section 9); the associative engine handles dimension-to-fact naturally. See `qlik-performance` for JOIN vs ApplyMap benchmarks.

Full reference: `references/join-keep-patterns.md` (silent-collision worked example with WRONG/RIGHT side-by-side, LEFT/INNER JOIN syntax with RESIDENT, JOIN vs KEEP semantics, row multiplication, decision framework).

## 9. ApplyMap Patterns

ApplyMap performs a key-value lookup from a mapping table. Faster than JOIN for large datasets and safer (no row multiplication, provides a default for unmatched keys).

```qlik
// Create mapping table (two-column: key, value):
[_RegionMap]: MAPPING LOAD [%Customer.Key], [Customer.Region]
RESIDENT [Customers];

// Apply in a LOAD statement:
ApplyMap('_RegionMap', [%Customer.Key], 'Unknown') AS [Customer.Region]
```

**Critical gotcha -- never alias the result with the same name as the lookup field:**

```qlik
// WRONG -- silently replaces the code with the mapped name:
LOAD
    OrderID,
    ApplyMap('_RegionMap', RegionCode, 'Unknown') AS RegionCode  // BUG
FROM ...;
// Result: RegionCode column now contains 'North America', 'Europe', etc.
// The original codes are permanently lost. Any downstream table or
// association that still expects codes in RegionCode is now broken.

// RIGHT -- alias the result to a distinct name:
LOAD
    OrderID,
    RegionCode,                                                    // keep the code
    ApplyMap('_RegionMap', RegionCode, 'Unknown') AS [Region.Name] // add the label
FROM ...;
```

The Qlik script engine does not raise an error for the broken form. Both the input and output resolve to the same field name, and the ApplyMap result wins -- silently replacing the raw code values. Always give the ApplyMap output a distinct alias (typically the `.Name` or `.Label` suffix) so the original key field remains intact.

**MAP...USING vs ApplyMap:** `MAP...USING` applies a mapping automatically to every subsequent LOAD of the named field. `ApplyMap` is explicit, per-expression. Prefer ApplyMap for clarity; use MAP...USING only for global, consistent field translations (e.g., country code to country name everywhere). See `qlik-performance` for ApplyMap optimization on large datasets.

## 10. QVD Operations (Summary)

Three things to internalize before writing QVD reads:

1. **STORE writes one table per statement:** `STORE * FROM [TableName] INTO [lib://Connection/file.qvd] (qvd);`. There is no append mode — for incremental output, see `references/incremental-load-patterns.md`.
2. **Optimized read** is preserved by `LOAD *`, field subsetting, `AS` renaming, `LOAD DISTINCT`, `CONCATENATE`, and single-parameter `EXISTS(field)` **when `field` exactly matches a field name stored in the QVD**. It is forced to standard by any field transform, derived fields, two-parameter `EXISTS(field, expression)`, WHERE clauses other than single-parameter EXISTS, single-parameter EXISTS where the field name does not match the QVD's stored name (e.g., the current load aliases it), or `MAP ... USING`. Folklore correction: field renaming and reordering do NOT break optimized read.
3. **Read each QVD from disk exactly once.** Load to a temp, serve all downstream maps and tables from RESIDENT, then DROP the temp.

`binary [app];` is a separate mechanism for copying a whole data model — must be the first statement, one per script, loads data and section access only.

Full reference: `references/qvd-operations.md` (STORE, optimized vs standard rules with worked examples, NoConcatenate around QVD loads, multi-QVD concatenation, file-list patterns, partial reload prefixes, binary load). Decision framing — when to optimize, when to layer, when to split a generator/consumer architecture — is in `qlik-performance`.

## 11. Incremental Load Patterns (Summary)

| Source Pattern | Strategy | Key Requirement |
|---|---|---|
| Append-only transactions | Insert-only (by timestamp/key) | Monotonic key or reliable timestamp |
| Mutable dimension (SCD1) | Insert/update (by ModifiedDate) | Reliable modification timestamp |
| Full-refresh staging | Full replace each cycle | None |
| SCD Type 2 dimension | **Dual-timestamp** (effective_from + effective_to) | Both timestamps tracked |
| Mutable with deletes | Insert/update/delete | Change detection + deletion flag or full-key comparison |

**Critical:** The dual-timestamp SCD Type 2 pattern must capture BOTH newly created records AND records whose effective_to changed (previously current records that were closed). Missing the closure condition = silent data loss. See `references/incremental-load-patterns.md` for complete working code and `script-templates/dual-timestamp-incremental.qvs` for the ready-to-use template.

## 12. Master Calendar

A master calendar provides a continuous date dimension with custom periods (fiscal year, relative date flags). It must derive date ranges from loaded data, never hard-coded. Custom period labels (quarter, fiscal quarter, year-month, year-week) must be wrapped in `Dual()` so they sort chronologically while displaying as text.

**Dual() for chronological sort -- when it is and is not needed:**

`Month()`, `MonthName()`, and `WeekDay()` **already return Dual values** per help.qlik.com -- the text component is the month/day name and the numeric component is the underlying integer (or, for `MonthName()`, the serial number of the month start). They sort numerically in charts despite displaying as text. Wrapping them in `Dual(..., Num(...))` is redundant and inflates the symbol table by storing every text/number pair as a fresh dual value instead of reusing the engine's built-in dual.

References:
- Month: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/DateAndTimeFunctions/month.htm
- MonthName: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/DateAndTimeFunctions/monthname.htm
- WeekDay: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/DateAndTimeFunctions/weekday.htm

```qlik
// CORRECT -- Month() is already Dual; sorts as 1-12, displays as "Jan", "Feb":
Month([Order.Date])     AS [Calendar.Month]

// REDUNDANT -- wrapping a built-in Dual in Dual() wastes symbol-table memory:
Dual(Month([Order.Date]), Num(Month([Order.Date])))   AS [Calendar.Month]
```

`Dual()` IS required for **derived labels** built by string concatenation, because the concatenation result is plain text with no underlying numeric component. Add the numeric sort key explicitly:

```qlik
// Quarter label -- 'Q' & ... is plain text, needs Dual for numeric sort:
Dual('Q' & Ceil(Month([Order.Date])/3), Ceil(Month([Order.Date])/3))   AS [Calendar.Quarter]

// Year-month label -- the formatted text sorts lexically; pair with a numeric key:
Dual(Date(MonthStart([Order.Date]), 'YYYY-MM'),
     Year([Order.Date]) * 100 + Month([Order.Date]))   AS [Calendar.YearMonth]

// Fiscal quarter label -- hand-built text with no numeric component:
Dual('FY' & vFY & '-Q' & vFQ, vFY * 10 + vFQ)   AS [Calendar.FiscalYearQuarter]
```

The rule: if the value comes straight from `Month()`, `MonthName()`, or `WeekDay()`, leave it alone. If the value is built with `&`, `Date(..., 'format')`, or any other string-producing expression, wrap it in `Dual(text, numeric_sort_key)`.

**Fiscal year configuration:** Set `vFiscalYearStartMonth` (e.g., 7 for July start). The template handles the year offset automatically: FY2026 runs Jul 2025 - Jun 2026 when start=7.

**Multiple date fields:** If your model has Order.Date, Ship.Date, and Invoice.Date, choose one primary date as the calendar key. Other dates filter via set analysis. Alternatively, create separate calendar tables with prefixed fields (OrderCal.Year, ShipCal.Year) for direct filtering on any date.

**Relative date flags:** The template includes IsCurrentMonth, IsCurrentYear, IsPriorYear, IsYTD, IsPriorYTD, IsRolling12, and IsToday. These enable period-over-period comparisons without set analysis.

See `script-templates/master-calendar.qvs` for the production-ready template.

## 13. Error Handling and Logging

`TRACE` for milestone logging, `ScriptError` vs `ScriptErrorCount` for error tracking, `ErrorMode` for halt-vs-continue behavior. The single biggest gotcha is confusing `ScriptError` (resets after every successful statement, recent-statement only) with `ScriptErrorCount` (cumulative across the reload) — guarding against an error across multiple operations requires snapshotting `ScriptErrorCount` before and comparing after. Second-most-common surprise: a bare `;` inside an unquoted TRACE message terminates the statement early — use periods/dashes as in-text separators, or quote the entire message.

Full reference: `references/error-handling.md` (TRACE semicolon trap, ScriptError vs ScriptErrorCount snapshot pattern, ErrorMode 0/1/2 semantics, file-existence guards via FileTime, field-value inspection patterns, and the relationship between the `error-handling.qvs` framework and `references/diagnostic-patterns.md`).

## 14. NoConcatenate and Auto-Concatenation

Two distinct outcomes when a new LOAD shares field names with an existing table:

- **Full match (same names AND same field count) → silent auto-concatenation.** The new rows are appended into the existing table and the new table name is never registered: `NoOfRows('NewTable')` returns NULL and `DROP TABLE [NewTable]` fails. The same rule applies to `LOAD * INLINE` blocks with matching columns and to RESIDENT loads that mirror their source.
- **Partial overlap (some shared names but different field count) → NOT auto-concatenated.** Qlik keeps the tables separate and emits a "tables ... cannot be concatenated implicitly" warning. The shared field names then create unintended associations: a single shared field links the tables (often surprising the developer), and two or more shared fields generate a `$Syn` synthetic key. See `qlik-data-modeling` `references/anti-patterns.md` #5 (Multiple Shared Fields Between Two Tables) for the synthetic-key resolution that flows from this count-rule mismatch.

The basic NoConcatenate pattern, the INLINE auto-concat trap, the explicit `CONCATENATE([TargetTable])` prefix (which forces concatenation even when field sets differ), and the QVD-specific application live in `references/sql-constructs.md` Section 2.1 and `references/qvd-operations.md` (NoConcatenate Around QVD Loads, Multi-QVD Concatenation).

Reference: help.qlik.com Cloud — [Concatenate](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/Concatenate.htm) and [NoConcatenate](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/NoConcatenate.htm).

**Mapping LOAD tables persist until script end and are invisible to meta-functions.** Tables created via `Mapping LOAD` remain in memory for the lifetime of the script run — they are NOT auto-dropped when `ApplyMap()` consumes them. To release a mapping table before script end, use `DROP MAPPING TABLE [MappingTableName];` (the `MAPPING` keyword is required; plain `DROP TABLE` does not apply to mapping tables). See help.qlik.com — [Drop Table](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptRegularStatements/Drop_Table.htm). During their lifetime, mapping tables are invisible to the associative engine's data model: `NoOfRows('MappingTableName')`, `FieldValueCount()`, `FieldName()`, and all other table/field meta-functions return null or -1 for mapping tables. Validate indirectly by checking the row count of the downstream table that consumes the mapping (e.g., if the target table loads 0 rows, the mapping was likely empty or misconfigured).

## 15. EXISTS Symbol Space Behavior

`EXISTS(field, value)` checks the **entire symbol space** (all tables with that field name), not one table. This includes values already loaded in the current statement.

**Cross-table contamination:** If `[Dimension]`, `[_TempA]`, and `[_TempB]` all have `key_field`, then `WHERE NOT EXISTS(key_field)` checks all three. This produces unexpected zero-row results.

**Self-referencing dedup (documented gotcha):** `WHERE NOT EXISTS(field)` using one-parameter form checks values that have already been loaded **during the current LOAD statement**, not just previously loaded tables. The symbol table updates row by row as the load progresses. When a value loads, it immediately becomes "existing." The next row with the same value sees it as already existing and is skipped. Result: only the **first occurrence** of each value loads. This is intentional Qlik behavior but often unintended by the developer.

```qlik
// Only loads ONE row per customer_id, even if source has duplicates:
LOAD * FROM [lib://QVDs/Orders.qvd] (qvd)
WHERE NOT EXISTS(customer_id);

// To load ALL rows for non-existing keys, alias the lookup field
// so the current load's values don't pollute the check:
[_Existing]:
LOAD DISTINCT customer_id AS _existing_cust RESIDENT [Customers];

LOAD * FROM [lib://QVDs/Orders.qvd] (qvd)
WHERE NOT EXISTS(_existing_cust, customer_id);

DROP TABLE [_Existing];
```

**Workaround for both issues:** Load the lookup field into a separate table under a different alias, then use the two-parameter form: `WHERE NOT EXISTS(aliased_field, source_field)`. This avoids self-referencing dedup AND cross-table contamination. Note that the two-parameter form forces standard QVD read mode.

## 16. CROSSTABLE Prefix

CROSSTABLE unpivots columnar data into normalized rows. Common when loading Excel pivot tables or wide-format source data.

```qlik
// Source has: Product, Jan, Feb, Mar (with sales values in month columns)
// Result: Product, Month, Sales (one row per product-month combination)
CROSSTABLE(Month, Sales, 1)
LOAD * FROM [lib://Data/SalesPivot.xlsx] (ooxml, embedded labels, table is Sheet1);
```

**Syntax:** `CROSSTABLE(AttributeField, DataField, NoOfQualifyingFields)`. The third parameter specifies how many left-side columns to keep as-is (qualifying columns). All remaining columns become attribute-value pairs. If your source has `Region, Product, Jan, Feb, Mar`, use `NoOfQualifyingFields = 2` to keep Region and Product as row identifiers.

## 17. AutoNumber and Composite Keys

**Composite key pattern:** Concatenate multiple fields with a delimiter to create a synthetic key. Use a safe delimiter that cannot appear in the data.

```qlik
[%Region.Product.Key]: [Region] & '|' & [Product] AS [%Region.Product.Key]
```

**AutoNumber:** Replaces a field's values with sequential integers for memory optimization. Reduces RAM by eliminating long string keys from the symbol table.

```qlik
AutoNumber([%Region.Product.Key], '%Region.Product.Key');
```

**Critical warning:** AutoNumber numbering depends on load order. Per help.qlik.com: "You can only connect autonumber keys that have been generated in the same data load, as the integer is generated according to the order the table is read." Consequences:
- The same business value receives different integers if the load order changes (added/removed source rows, changed sort, different reload sequence).
- AutoNumber values are NOT stable across apps or across reloads. Never use them as persistent identifiers, foreign keys to other apps, or in inter-app data exchange.
- If you need stable keys across reloads or apps, use `Hash128`/`Hash160`/`Hash256` on the business key instead -- Qlik help explicitly recommends this.

**Community best practice:** Apply AutoNumber only in the final app-level model load, not in the QVD extraction layer. The reasoning is twofold: (1) extracted QVDs may be consumed by multiple downstream apps, each of which would assign its own unrelated integers to the same business values, breaking associations; and (2) AutoNumber inside a LOAD FROM QVD forces standard (non-optimized) read mode, defeating the purpose of the extraction layer. This is widely held expert guidance (Rob Wunderlich, Henric Cronström) rather than a Tier-1 documented rule, but the underlying mechanisms are both documented.

## 18. Subroutine Integration

`$(Must_Include=lib://Connection/path/file.qvs);` fails the reload if the file is missing; `$(Include=...)` silently skips. `CALL SubName(param1, param2);` invokes after the include.

**Critical scoping rule:** `LET`/`SET` inside a SUB create GLOBAL variables that persist after the subroutine returns — they will overwrite caller variables of the same name. Only the SUB's formal parameter list is locally scoped. A bare `LET` inside a SUB leaks state to the caller. Use the parameter list for anything that must not leak; use naming prefixes (`vSub_MySub_Counter`) for variables that intentionally stay global.

Two distinct behaviors apply to formal parameters (per help.qlik.com Sub..End Sub): (1) **Extra formal parameters with no matching actual argument** are NULL-initialized at SUB entry and truly local — their value is discarded at `END SUB`. Use these as pure local working variables. (2) **Formal parameters whose corresponding actual argument is a variable name** use **copy-out semantics** — the parameter's value at `END SUB` is written back to the caller's variable. This means a SUB can return computed values to the caller through its parameter list; it is NOT purely local in this case.

Full reference: `references/subroutine-patterns.md` (Must_Include vs Include, CALL syntax, variable scoping rules with worked example, FOR EACH file/value iteration with Cloud wildcard caveat, phantom field detection after subroutine return, composite key concatenate-before/split-after workaround).

## 19. Synthetic Keys

Synthetic key concepts (what they are, how Qlik detects them, prevention mechanisms, common triggers, worked fix examples) and the QUALIFY failure modes live in `qlik-data-modeling` → `references/anti-patterns.md` #1 and #4. Script-level resolution mechanics: rename overlapping non-key fields with `AS` aliases at load time, `DROP FIELDS` for unwanted metadata fields before storing QVDs, or use QUALIFY/UNQUALIFY (Section 1) on un-prefixed wildcard loads.

## 20. LIB CONNECT TO

`LIB CONNECT TO [ConnectionName];` targets subsequent `SQL SELECT` statements at a specific data connection. Without it, SQL goes to whatever connection was last active.

```qlik
LIB CONNECT TO [lib://SourceDB];
SQL SELECT * FROM customers;
```

**lib:// path format:** All file and connection references in Qlik Sense/Cloud use `lib://` prefix. `FROM [lib://DataFiles/data.csv]` for files. The connection name in brackets must match the data connection name exactly (case-sensitive in Cloud).

**Cloud space-aware prefix:** In Qlik Cloud shared or managed spaces, the **space name comes before the colon** and the **connection name comes after**:

```qlik
// Correct Qlik Cloud space-aware syntax:
LOAD * FROM [lib://SalesSpace:DataFiles/orders.csv] (txt, delimiter is ',', embedded labels);
LIB CONNECT TO 'SalesSpace:OperationalDB';
```

The format is `lib://<SpaceName>:<ConnectionName>/...`. Reversing the order (`lib://DataFiles:SalesSpace/...`) fails to resolve the connection at reload. Personal space does not require a prefix; only shared and managed spaces use this syntax.

## 21. Script Organization

| Approach | When to Use |
|---|---|
| Tabs (in-app sections) | Simple single-app projects, all code visible in one editor |
| Include files (.qvs) | Multi-app projects, shared code, version control |
| Numeric prefix | `01_Config.qvs`, `02_Extract_SourceA.qvs`, `03_Transform.qvs` |

**Split when** a single tab exceeds ~500 lines. Split by logical function (config, extract per source, transform, model load, calendar, diagnostics).

**Script execution manifest:** A documentation file listing each script file, its purpose, dependencies, and run order.

## 22. Cross-Layer Field Rename Mechanics

Three mechanisms for renaming fields in scripts, from simple to systematic:

- **Aliasing in LOAD:** `source_field AS [UI.Field.Name]` -- use for per-field transforms during extraction or model load.
- **RENAME FIELD:** `RENAME FIELD old_name TO [New.Name];` -- use for individual post-load renames. **Collision warning:** RENAME FIELD affects ALL tables containing that field name. If `region` exists in both `[Customers]` and `[Products]`, `RENAME FIELD region TO [Customer.Region]` renames it in both tables. Use Mapping RENAME or aliasing in LOAD when you need table-specific renames.
- **Mapping LOAD + RENAME FIELDS USING** (shorthand: "Mapping RENAME"): Bulk rename from a mapping table — two statements working together, a `Mapping LOAD` that builds the lookup table and `RENAME FIELDS USING <MapName>;` that applies the rename. Use for systematic cross-layer renaming (e.g., all raw extract names to model-layer names in one operation). Same cross-table behavior as RENAME FIELD, so ensure source field names are unique across tables before applying.

```qlik
[_RenameMap]: MAPPING LOAD old_name, new_name INLINE [
old_name, new_name
acct_status, Customer.Status
ship_addr_line1, Customer.ShipAddress
] (delimiter is ',');
RENAME FIELDS USING [_RenameMap];
```

See `qlik-naming-conventions` for the naming strategy (what names to use at each layer).

## 23. Placeholder Logic for Blocked Dependencies

When a source table is unavailable, produce a documented empty table with the expected schema so the pipeline continues. Every placeholder must include: what it replaces, expected source, resolution condition, and a TRACE warning.

```qlik
// PLACEHOLDER: Product loyalty data not yet available
// Source: loyalty_program.product_affinity (via lib://LoyaltyDB)
// Resolves when: Loyalty team delivers API access (ETA: Q2 2026)
TRACE [WARNING] Using placeholder for Product.Loyalty -- source not available;
[ProductLoyalty]:
LOAD * INLINE [
    Product.Key, Loyalty.Tier, Loyalty.Points
] (delimiter is ',');
```

## 24. String Functions

**PurgeChar** strips multiple characters in one call. Always requires two arguments:
```qlik
// WRONG -- missing second argument:
PurgeChar(my_field)
// RIGHT:
PurgeChar(my_field, '[]{}' & Chr(34))
```

**SubField + IterNo** for array expansion:
```qlik
LOAD key_field,
    Trim(SubField(clean_list, ',', IterNo())) AS [Expanded.Value]
RESIDENT [Source]
WHILE Len(Trim(SubField(clean_list, ',', IterNo()))) > 0;
```

Clean delimiters with PurgeChar before expanding.

## Supporting Files

- `references/sql-constructs.md` -- SQL constructs not valid in Qlik LOAD/RESIDENT, the SQL SELECT pass-through exception, and the five most common adjacent failure modes (NoConcatenate, Count() argument requirements, QUALIFY with prefixed fields, DROP TABLE discipline, NullAsValue scope)
- `references/qvd-operations.md` -- STORE syntax, optimized vs standard read rules, NoConcatenate around QVD loads, multi-QVD concatenation, file-list patterns, partial reload prefixes, binary load
- `references/join-keep-patterns.md` -- JOIN/KEEP silent-collision worked example, LEFT/INNER JOIN syntax with RESIDENT, JOIN vs KEEP semantics, row multiplication, decision framework
- `references/null-handling.md` -- canonical script-layer null handling (Null/IsNull/NullCount, vCleanNull, NullAsValue, key-field NULL, date sentinel guards, decision framework)
- `references/error-handling.md` -- TRACE semicolon trap, ScriptError vs ScriptErrorCount snapshot pattern, ErrorMode 0/1/2, file-existence guards, field-value inspection, framework-vs-standalone selection
- `references/subroutine-patterns.md` -- Must_Include vs Include, CALL syntax, SUB variable scoping rules, FOR EACH iteration with Cloud wildcard caveat, phantom field detection, composite key workaround
- `references/incremental-load-patterns.md` -- Complete incremental load patterns with working code
- `references/interval-match.md` -- IntervalMatch prefix (one-key + N-key syntax), synthetic-key resolution via LEFT JOIN + DROP TABLE, SCD2 effective-dating worked example, performance notes, IntervalMatch vs Range Bucketing decision block with three wrong-choice scenarios
- `references/diagnostic-patterns.md` -- TRACE templates, row count logging, validation queries
- `script-templates/master-calendar.qvs` -- Production-ready master calendar
- `script-templates/error-handling.qvs` -- Error handling and logging framework
- `script-templates/clean-null-function.qvs` -- Null-cleaning variable functions
- `script-templates/dual-timestamp-incremental.qvs` -- SCD Type 2 incremental load
