# SQL Constructs Not Valid in Qlik LOAD, and Related Failure Modes

Qlik script resembles SQL but is a fundamentally different language. The single most predictable failure mode for AI-generated scripts is SQL syntax inside `LOAD` or `RESIDENT` statements. This reference covers:

1. SQL syntax that does NOT exist in Qlik `LOAD`/`RESIDENT` (and the Qlik alternative for each)
2. The `SQL SELECT` pass-through exception
3. The five most common adjacent failure modes (`NoConcatenate`, `Count()` arguments, `QUALIFY` with prefixed fields, `DROP TABLE` discipline, `NullAsValue` scope)

Pair this with the inline summary in `SKILL.md` Section 1 (the "what" table) — this file covers the "why" and the worked examples.

## 1. SQL Constructs That Do Not Exist in Qlik LOAD

Using any of these in a `LOAD` or `RESIDENT` statement produces a reload error or silent data failure.

| SQL Construct | Why It Fails | Qlik Alternative |
|---|---|---|
| `HAVING` | Not a keyword in Qlik script | Preceding LOAD with `WHERE` on the aggregated field |
| `Count(*)` | No wildcard aggregation; `Count()` requires an explicit expression | `Count(field_name)` for non-null counts; `NoOfRows('TableName')` for row counts |
| `SELECT DISTINCT` | `SELECT` is for SQL pass-through to databases only | `LOAD DISTINCT` (the `LOAD` keyword, not `SELECT`) |
| `IS NULL` / `IS NOT NULL` | Operator syntax not supported in script | `IsNull(field)` / `NOT IsNull(field)` (function form) |
| `BETWEEN` | Not a keyword | `field >= low AND field <= high` |
| `IN (list)` | Not supported | `Match(field, val1, val2, ...)` (exact) or `WildMatch(field, ...)` (pattern) |
| `CASE WHEN` | Not a keyword | `IF()`, `Pick()`, or `Match()` inside a LOAD |
| `LIMIT` | Not a keyword | `FIRST n LOAD ...` prefix (works on any source); `WHERE RecNo() <= N` as a fallback for RESIDENT |
| Table aliases (`FROM table t1`) | Not supported in LOAD | Full table names in square brackets; no alias |
| `WITH ... AS (...)` (CTE) | No CTE syntax in LOAD/RESIDENT | Sequential LOADs into named tables (`[_Stage1]:`, `[_Stage2]:`), reference downstream with `RESIDENT`, then `DROP TABLE` the intermediates |
| `ROW_NUMBER() OVER (...)` | No window functions in LOAD/RESIDENT | `RowNo()` with `ORDER BY` in a RESIDENT load (for partition-less numbering); `AutoNumber(partition_key)` for partitioned row numbers; or aggregate-and-rejoin via `GROUP BY` |
| `LAG()` / `LEAD()` | No window functions in LOAD/RESIDENT | `Previous(field)` for the prior row in the current LOAD; `Peek(field, row_no, table_name)` for arbitrary row offsets in an already-loaded table |
| `UNION` / `UNION ALL` | Not keywords in LOAD/RESIDENT | `CONCATENATE([Target])` prefix; auto-concatenates when field sets fully match (see Section 2.1) |
| `EXCEPT` / `INTERSECT` | Not keywords | `WHERE NOT EXISTS(aliased_key, source_key)` (set difference); `WHERE EXISTS(aliased_key, source_key)` (intersection) — always with an aliased lookup field to avoid the symbol-space pitfall |
| `MERGE INTO target USING source` (SQL upsert) | Not LOAD/RESIDENT syntax; the Qlik `MERGE` prefix is a different mechanism scoped to partial reloads | `CONCATENATE` new rows then dedup with `WHERE NOT EXISTS`; or use the Qlik `MERGE` partial-reload prefix when a change-log feed is available (see `incremental-load-patterns.md`) |
| `LATERAL` / `CROSS APPLY` | No equivalent in LOAD/RESIDENT | Push the row-expanding join to the `SQL SELECT` pass-through layer where database-native LATERAL syntax is valid; or, for delimited-string expansion, use `SubField` + `IterNo()` in a `WHILE` clause |

### Notes on the additions

**CTEs.** SQL CTEs (`WITH x AS (...) SELECT ... FROM x`) have no direct equivalent in LOAD. The Qlik idiom is to materialize each CTE-equivalent as a temp table with a `_` prefix, reference it via `RESIDENT`, and `DROP TABLE` it once consumed. Two consequences: (1) every intermediate is visible in the data model until dropped, so the DROP discipline from Section 2.4 applies; (2) preceding LOAD (SKILL.md Section 4) often replaces a two-CTE chain in a single statement when the only goal is to layer expressions.

**Window functions.** `RowNo()` returns the sequential row number within the current LOAD (re-numbered after each `LOAD`); pair it with `ORDER BY` in a RESIDENT load for deterministic numbering. For partitioned row numbers (`ROW_NUMBER() OVER (PARTITION BY x ORDER BY y)`), the common Qlik pattern is to sort the source on the partition + order keys, then use `If(partition_key = Previous(partition_key), Peek('row_n') + 1, 1) AS row_n`. `Previous(field)` returns the value of `field` from the prior input row of the same LOAD; `Peek(field, row_no, table_name)` reaches into an already-loaded table at an arbitrary row.

**UNION / UNION ALL.** Both map to `CONCATENATE`. `UNION ALL` (no dedup) is the closer match — `CONCATENATE` appends without dedup. For `UNION` semantics (distinct rows across the union), follow the concatenate with a `LOAD DISTINCT` resident pass. Per help.qlik.com, when two LOADs share an identical field set (same names AND same count), Qlik auto-concatenates implicitly — no `CONCATENATE` prefix needed (see SPEC-03-08 and Section 2.1 above for the auto-concat rule and its INLINE/RESIDENT failure modes). Use the explicit `CONCATENATE([TargetTable])` prefix when field sets differ or when you want the code to read unambiguously.

Reference: help.qlik.com Cloud — [Concatenate](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/Concatenate.htm).

**EXCEPT / INTERSECT.** Both translate to a `WHERE EXISTS` / `WHERE NOT EXISTS` filter against an aliased lookup table. Always alias the lookup field (load it into a side table under a different name and use the two-parameter `EXISTS(aliased_field, source_field)` form) — otherwise the symbol-space behavior in SKILL.md Section 15 will produce surprising results (the one-parameter form sees values already loaded in the current statement, so it dedups on the fly).

**MERGE INTO (SQL) vs MERGE (Qlik prefix).** The SQL `MERGE INTO target USING source ON ... WHEN MATCHED ... WHEN NOT MATCHED` upsert syntax does not exist in LOAD/RESIDENT. Qlik has a `MERGE` prefix, but it is scoped to **partial reloads** and operates on a change-log feed where the first field is `'Insert'`, `'Update'`, or `'Delete'` — a different mechanism, documented at help.qlik.com Cloud — [Merge](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/Merge.htm). For a full-reload upsert, the idiomatic substitution is `CONCATENATE` the new rows on top, then dedup with `WHERE NOT EXISTS` against the prior version. Full incremental-load patterns including the partial-reload `MERGE` prefix and the dual-timestamp SCD2 pattern are in `incremental-load-patterns.md`.

**LATERAL / CROSS APPLY.** These row-multiplying SQL constructs (one row in, N rows out, where N depends on a per-row expression or sub-query) have no LOAD/RESIDENT equivalent. Two options: (1) push the join to the `SQL SELECT` pass-through layer where the database engine evaluates the LATERAL natively; or (2) if the row-multiplication source is a delimited string (the most common case AI emits in this shape), expand inline with `SubField(field, delimiter, IterNo())` inside a `WHILE Len(Trim(SubField(...))) > 0` clause — see SKILL.md Section 24.

### The `SQL SELECT` pass-through exception

`SQL SELECT` statements directed at database connections (typically via `LIB CONNECT TO`) are handed off to the database engine, which interprets them in its native dialect. **Inside `SQL SELECT`, all of the above SQL syntax is valid** — `HAVING`, `Count(*)`, `BETWEEN`, `IN`, `CASE WHEN`, table aliases, `LIMIT`/`TOP`/`FETCH` (per the database dialect), and so on.

The constraint applies only to `LOAD` and `RESIDENT` operations executed by the Qlik script engine itself.

```qlik
// Valid: native SQL inside a SQL SELECT pass-through
LIB CONNECT TO [lib://SourceDB];
SQL SELECT
    customer_id,
    Count(*) AS order_count
FROM orders
WHERE order_date BETWEEN '2026-01-01' AND '2026-12-31'
  AND status IN ('Active', 'Pending')
GROUP BY customer_id
HAVING Count(*) > 5;

// Invalid: same SQL syntax in a Qlik LOAD/RESIDENT
[OrderSummary]:
LOAD customer_id, Count(*) AS order_count   // FAILS: Count(*) and HAVING are not script syntax
RESIDENT [Orders]
WHERE order_date BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY customer_id
HAVING Count(*) > 5;
```

The Qlik equivalent is a preceding LOAD with `WHERE` on the aggregated field:

```qlik
[OrderSummary]:
LOAD customer_id, order_count
WHERE order_count > 5;
LOAD customer_id, Count(order_id) AS order_count
RESIDENT [Orders]
WHERE Match(status, 'Active', 'Pending')
  AND order_date >= MakeDate(2026,1,1)
  AND order_date <= MakeDate(2026,12,31)
GROUP BY customer_id;
```

## 2. Additional Failure Modes

These five patterns are the next most common sources of reload failures and silent data corruption after the SQL-syntax issues above.

### 2.1 NoConcatenate on auto-concatenation risk

Two distinct outcomes when a new `LOAD` shares field names with an existing table — only one of them is auto-concatenation:

**(1) Full match (same names AND same field count) → silent auto-concatenation.** Qlik appends the new rows into the existing table and never registers the new table name. `NoOfRows('NewTable')` returns NULL, and `DROP TABLE [NewTable]` fails.

Always use `NoConcatenate` on temp tables that dedup, filter, or pivot existing data:

```qlik
[_TempA]: LOAD key FROM source;
[_TempB]: NoConcatenate LOAD DISTINCT key RESIDENT [_TempA];
DROP TABLE [_TempA];
```

`INLINE` LOADs trigger the same full-match rule: two `LOAD * INLINE` blocks with identical column structures auto-concatenate even though they look visually distinct in source. The typical symptom is a later `RESIDENT [SecondTable]` failing with "table not found." Fix by adding a discriminator column or by prefixing with `NoConcatenate`.

**(2) Partial overlap (some shared names but different field count) → NOT auto-concatenated.** Qlik keeps the two tables separate and emits a "tables ... cannot be concatenated implicitly" warning. The shared field names then create unintended associations between the two tables in the data model: a single shared field links them (often surprising the developer), and two or more shared fields generate a `$Syn` synthetic key. The fix is either to alias the overlapping non-key fields with `AS` so the names don't collide, to force concatenation with the explicit `CONCATENATE([TargetTable])` prefix (which fills the missing fields with NULL in the target), or to redesign the model — see `qlik-data-modeling` for synthetic-key resolution.

Mapping tables are exempt from both rules (they are consumed at `ApplyMap()` time and don't appear in the data model).

Reference: help.qlik.com Cloud — [Concatenate](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/Concatenate.htm) and [NoConcatenate](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/NoConcatenate.htm).

### 2.2 Count() requires an explicit expression — no `Count(*)`

`Count(*)` does not exist in Qlik LOAD or chart expressions. The `Count()` signature requires an explicit field or expression argument. The SQL `Count(*)` convention is only valid inside `SQL SELECT` pass-through statements (which Qlik hands off to the database engine).

In Qlik `LOAD` / `RESIDENT` context:

- **Count non-null values in a field:** `Count(field_name)`.
- **Count distinct values in a field:** `Count(DISTINCT field_name)`.
- **Count NULL values in a field:** `NullCount(field_name)`.
- **Count all rows in a loaded table:** `NoOfRows('TableName')` after the LOAD.

For clarity, prefer `Count(field_name)` over `Count(<literal>)` so the countable field is explicit. The SQL `Count(*)` convention is invalid in Qlik LOAD context — use `NoOfRows()` for row counts.

A widely-recommended community pattern is to add an explicit counter field during the load (`1 AS [Order.Counter]`) and use `Sum([Order.Counter])` downstream. This avoids ambiguity over which field/table is being counted, especially in associative chart context, and reduces engine work.

Avoid `Count()` directly on key fields: when a key links two tables, the engine cannot determine which table the count should run against, and the result is ambiguous.

### 2.3 QUALIFY / UNQUALIFY with already-prefixed fields

`QUALIFY *` prefixes every field with its table name to prevent unintended associations. If fields are already entity-prefixed by the naming convention (e.g., `Order.Status`, `Product.Category`), applying `QUALIFY *` creates double-prefixed fields (`TableName.Order.Status`) — breaking downstream field references and creating unintended synthetic keys.

**Rule:** Skip `QUALIFY` entirely when fields are already entity-prefixed. The naming convention has already prevented the ambiguity that `QUALIFY` exists to solve. Document the omission with a brief comment so the next reader doesn't add `QUALIFY` back.

**If `QUALIFY` is used:** it is a stateful toggle that affects every subsequent `LOAD` until `UNQUALIFY *` is called. Always `UNQUALIFY` the keys you need to associate on, immediately after `QUALIFY *`:

```qlik
QUALIFY *;
UNQUALIFY [%Customer.Key], [%Order.Key];   // keep keys associating
// ... table loads ...
UNQUALIFY *;                                // reset
```

Forgetting to `UNQUALIFY` the keys is silent — no error, no warning, just a data model with no associations.

See `qlik-naming-conventions` for the entity-prefix convention that obviates `QUALIFY` in most modern Qlik apps.

### 2.4 DROP TABLE discipline for temp tables

Every table prefixed with `_` (the temp-table convention) must have a corresponding `DROP TABLE`. Missing drops cause memory bloat and can trigger reload timeouts on large datasets.

```qlik
[_Staging]: LOAD ... FROM ... ;
// ... use _Staging to build mapping tables, resident loads, etc. ...
DROP TABLE [_Staging];
```

Mapping tables created with `MAPPING LOAD` PERSIST in memory until script end — they are NOT auto-dropped when `ApplyMap()` consumes them. To release a mapping table early, use `DROP MAPPING TABLE [MappingTableName];` (the `MAPPING` keyword is required; plain `DROP TABLE` does not apply to mapping tables). See help.qlik.com — [Drop Table](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptRegularStatements/Drop_Table.htm).

### 2.5 NullAsValue scope persistence and key corruption

See `null-handling.md` Section 3 (NullAsValue pattern, scope-management example, key/measure-field corruption failure modes) and Section 4 (substituted vs bare NULL keys, phantom-association risk) for full coverage.

## See Also

- `qlik-load-script` SKILL.md Section 1 — inline summary table.
- `qlik-load-script` SKILL.md Section 14 — NoConcatenate full treatment with the INLINE auto-concat trap.
- `null-handling.md` — canonical script-layer null handling (Null/IsNull/NullCount, vCleanNull, NullAsValue with scope/corruption failure modes, key-field NULL, date sentinel guards, decision framework).
- `qlik-naming-conventions` — entity-prefix convention that obviates `QUALIFY`.
- help.qlik.com Cloud — Aggregation functions (Count, NullCount), Concatenate / NoConcatenate, NullAsValue.
