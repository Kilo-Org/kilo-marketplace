# Snowflake Query Debugging Playbook

## 1. Start from the exact failure

Capture one of these before changing anything:

- Exact error text
- Exact query text
- Exact wrong result and why it is wrong
- Exact runtime symptom: timeout, warehouse suspended, empty result, duplicates, stale data

If the user only gives a description, reconstruct the smallest plausible query that matches it.

## 2. Classify the issue

### A. Compile or name-resolution failures

Examples:

- `SQL compilation error`
- `Object does not exist`
- `invalid identifier`
- `ambiguous column name`
- `unexpected ','` or parser errors

First checks:

- Is the table/view name fully qualified?
- Is the schema correct for this environment?
- Does the column actually exist on this relation?
- Did a CTE alias shadow a table alias?
- Did a SELECT alias get referenced in the wrong clause?

### B. Permissions or environment failures

Examples:

- `not authorized`
- warehouse not available
- cannot operate on object in current role

First checks:

- Current database, schema, warehouse, and role
- Whether the object exists but is inaccessible
- Whether the query is pointing at prod vs dev vs personal schema incorrectly

### C. Type, cast, and null-semantics failures

Examples:

- `Numeric value ... is not recognized`
- date cast errors
- division by zero
- silent null propagation

First checks:

- Which expression fails when isolated?
- Are mixed types being compared or coalesced?
- Should `try_to_*` be used for diagnosis?
- Is the denominator scoped correctly and wrapped with `nullif()`?

### D. Result correctness failures

Examples:

- Count too high
- Count too low
- duplicated rows
- empty results
- percentages over 100%

First checks:

- What is the intended grain?
- Which join changed row count?
- Which filter removes the expected rows?
- Are two definitions being compared as if they were the same metric?

### E. Performance failures

Examples:

- query times out
- query scans too much data
- warehouse scales unexpectedly

First checks:

- Add or tighten date filters on large facts
- Remove unnecessary columns and joins
- Run `EXPLAIN` where appropriate
- Check whether a pre-aggregated mart already exists

### F. Upstream freshness or ingestion failures

Examples:

- one day looks implausibly low
- table is present but data seems delayed
- backend mirror disagrees with dbt mart

First checks:

- Compare source vs transformed table for the affected window
- Inspect ingestion or `_snowflake_inserted_at` style timestamps if present
- Check whether the model is intraday-current or batch-lagged

## 3. Reduce the query

Strip the query down aggressively.

### Pattern: isolate one CTE

```sql
with base as (
    -- original base logic only
)
select *
from base
limit 100;
```

### Pattern: measure row counts by stage

```sql
with a as (...),
b as (...),
c as (...)
select 'a' as stage, count(*) as rows from a
union all
select 'b' as stage, count(*) as rows from b
union all
select 'c' as stage, count(*) as rows from c;
```

### Pattern: inspect one join boundary

```sql
with left_side as (...),
right_side as (...)
select
    count(*) as rows_after_join,
    count(distinct l.join_key) as left_keys,
    count(distinct r.join_key) as right_keys
from left_side l
left join right_side r
    on l.join_key = r.join_key;
```

## 4. Verify grain explicitly

Write grain comments or notes while debugging.

Examples:

- one row per user
- one row per user per day
- one row per invoice
- one row per request id

Most bad joins are really grain mismatches:

- user joined to user-day
- invoice joined to payment-attempt
- org joined to org-member without re-aggregation

## 5. Count before and after every join

Use diagnostics like:

```sql
with left_side as (...),
right_side as (...)
select
    count(*) as rows_after_join,
    count(distinct l.primary_key) as left_entities_after_join,
    count(distinct case when r.join_key is null then l.primary_key end) as unmatched_left_entities
from left_side l
left join right_side r
    on l.join_key = r.join_key;
```

If `rows_after_join` exceeds `left_entities_after_join` unexpectedly, suspect one-to-many inflation.

## 6. Debug zero-row outputs

Check in this order:

1. Does the base table have rows in the time window?
2. Does each filter individually preserve rows?
3. Does the join key exist on both sides?
4. Is the timestamp in the timezone or grain you think it is?
5. Are soft-deleted rows being excluded correctly?

Diagnostic pattern:

```sql
select count(*) from some_table where created_at >= '2026-06-01';
select count(*) from some_table where created_at >= '2026-06-01' and some_flag = true;
select count(*) from some_table where created_at >= '2026-06-01' and some_flag = true and user_id is not null;
```

## 7. Debug duplicates and inflated counts

Check whether the primary entity appears more than once:

```sql
select
    primary_key,
    count(*) as cnt
from suspicious_cte
group by 1
having count(*) > 1
order by cnt desc
limit 50;
```

If duplicates are expected on the right side, aggregate before joining.

```sql
with right_agg as (
    select
        join_key,
        max(some_value) as some_value
    from right_side
    group by 1
)
select ...
from left_side l
left join right_agg r
    on l.join_key = r.join_key;
```

## 8. Debug stale or incomplete data

Compare adjacent days or source-vs-model counts.

```sql
select
    date_trunc('day', created_at) as day,
    count(*) as rows
from source_table
where created_at >= '2026-06-01'
group by 1
order by 1;
```

If one day is far below normal, compare the upstream source, transformed mart, and any ingestion timestamp fields.

## 9. Debug cast and type issues

Find the bad values before coercing everything.

```sql
select raw_value
from some_table
where try_to_number(raw_value) is null
  and raw_value is not null
limit 100;
```

```sql
select raw_date
from some_table
where try_to_timestamp_ntz(raw_date) is null
  and raw_date is not null
limit 100;
```

Use `try_to_*` for diagnosis, then decide whether to clean, filter, or cast.

## 10. Debug performance

For large fact tables:

- add date filters first
- select only columns needed for the diagnostic
- test the base CTE alone
- join only after the base row count looks plausible
- avoid `select *` while debugging scan-heavy tables

If needed, inspect the plan:

```sql
explain using text
select ...;
```

Look for full scans, late filters, or fan-out joins.

## 11. Final rewrite rules

When delivering the fix:

- keep the final query as small as possible
- preserve the proven filters and join constraints
- include `nullif()` on percentage denominators
- comment non-obvious grain or assumptions
- mention if the real root cause was upstream freshness, not SQL logic
