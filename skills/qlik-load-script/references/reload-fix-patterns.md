# Reload-Fix Patterns

Reload feedback from Qlik typically falls into one of five finding types. Each has a diagnosis and fix pattern. Use this as a triage guide when a user reports a reload error or unexpected post-load behavior.

## Finding Type 1: Reload Failure (Syntax Error)

The reload errored out at a specific line. Almost always an SQL-syntax intrusion or a dollar-sign-expansion comma violation.

1. Locate the exact line that triggered the error.
2. Check against the SQL-constructs list in `references/sql-constructs.md` and the five adjacent failure modes (`NoConcatenate`, `Count()` argument requirements, `QUALIFY` with prefixed fields, `DROP TABLE` discipline, `NullAsValue` scope).
3. If a dollar-sign expansion comma violation, rewrite the variable-function call inline per SKILL.md § 3.
4. If `HAVING` / `Count(*)` / `CASE WHEN` / `IN (list)` / `IS NULL` / `BETWEEN` / `LIMIT`, rewrite using the Qlik alternatives (see SKILL.md § 1).
5. If a missing `NoConcatenate` or `DROP TABLE`, add the statement.
6. Report the fix with reference to the constraint that was violated.

## Finding Type 2: Synthetic Key Detected

Qlik created a `$Syn` synthetic key table because two or more tables share more than one field name. The conceptual treatment (what synthetic keys are, why Qlik creates one, the three prevention mechanisms, common triggers, the QUALIFY failure modes) is in `qlik-data-modeling` → `references/anti-patterns.md` #1 and #4. Script-level fix flow:

1. Identify which tables share the unintended field name(s) causing the association.
2. Check if `QUALIFY` is applied to already-prefixed fields (causes double-prefix; see anti-patterns.md #4).
3. Check if a non-key field appears in multiple tables (`source_system`, `load_date`).
4. Check if `NullAsValue` on a key field is creating phantom associations.
5. If the field should be dropped, add `DROP FIELD` before storing QVDs.
6. If `QUALIFY` created double-prefix, remove `QUALIFY`.
7. If the field should have different names in different tables, update LOAD aliases.
8. Surface as a data-model question if the root cause is design, not implementation.

## Finding Type 3: Data Quality Issues Post-Load

Reload succeeded but data looks wrong — high null rates, duplicates, unexpected aggregations, unexpected row counts.

1. Run diagnostic queries from `diagnostic-patterns.md` (sibling reference file) to pinpoint the issue.
2. Trace the value back through the transform layer.
3. High null rate in a key field? Source may be incomplete — surface as a data question.
4. Duplicates in a key field? Verify deduplication logic (`DISTINCT`, `WHERE NOT EXISTS`).
5. Unexpected type (text instead of number)? Check string functions applied to numeric fields.
6. Row count dropped unexpectedly? Verify `JOIN` logic didn't eliminate valid rows (use `LEFT KEEP`).
7. Re-run the diagnostic to confirm the fix.

## Finding Type 4: Field Type Coercion

A field is treated as the wrong type — string aggregations on what should be numeric, dates not sorting, booleans not filterable.

1. Identify which field and which table.
2. Check if the source is casting (SQL `CAST` or string concatenation in extraction).
3. Check if a string function is applied to a numeric field.
4. Check if date parsing (`Date#`) is missing.
5. Check if `Dual()` is needed for boolean fields with text labels.
6. Apply the correct function at load time (`Num#`, `Date#`, `Dual`) with the right format string.

## Finding Type 5: Incremental Load Issues

Incremental loads missing rows, double-loading rows, or not picking up changes.

1. Verify the last-execution timestamp or delta marker is being saved (see `incremental-load-patterns.md`).
2. Verify the `WHERE` clause uses the correct timestamp column and comparison (`>=` not just `>` — `>` misses rows that arrived during the prior run's execution window).
3. Verify incremental source loads use the same key and field structure as the full reload.
4. Verify the `CONCATENATE` into the persistent table doesn't have `NoConcatenate` (which would create a separate table).
5. Run a full reload to reset state, then re-test the incremental.

## Cross-References

- SQL-construct rewrites: `sql-constructs.md` (sibling reference file)
- Synthetic key diagnosis: `qlik-data-modeling` → `references/anti-patterns.md`
- Diagnostic queries: `diagnostic-patterns.md` (sibling reference file — post-load validation templates)
- Incremental load patterns: `incremental-load-patterns.md` (sibling reference file)
- Null handling: `null-handling.md` (sibling reference file)
