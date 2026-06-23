# Result Correctness Checklist

Use this when SQL executes successfully but the answer is wrong or suspicious.

## Grain

- What is the intended grain of the final output?
- What is the grain of each input table?
- Does every join preserve the intended grain?

## Population

- Are numerator and denominator drawn from the same entity set?
- Are anonymous, internal, soft-deleted, or test rows excluded consistently?
- Are org and personal rows being mixed accidentally?

## Time window

- Are all inputs filtered to the same time grain and range?
- Is one table event-time and another load-time?
- Is the query comparing `timestamp` to `date` in a way that truncates unexpectedly?

## Join quality

- Does the join key have one row per entity on both sides?
- Is there hidden one-to-many inflation?
- Would pre-aggregating the right side change the result materially?

## Null behavior

- Are left joins followed by `where right_table.col = ...` that accidentally turn them into inner joins?
- Are `coalesce()` defaults hiding missingness?
- Are null-denominator rows supposed to disappear or remain null?

## Duplicates

- Does the primary entity appear more than once after each join?
- Are duplicate rows coming from the source or from the query logic?

## Freshness

- Is the source complete for the affected dates?
- Is the downstream model known to lag?
- Did an outage or delayed ingest create an apparent product anomaly?

## Definitions

- Are two metrics being compared even though they encode different business rules?
- Is a backend event being treated as equivalent to user activity?
- Is first-event logic being compared to any-event logic?

## Minimal diagnostics to run

```sql
-- row counts by day
select date_trunc('day', created_at) as day, count(*)
from some_table
where created_at >= '2026-06-01'
group by 1
order by 1;
```

```sql
-- duplicate keys
select key, count(*)
from some_cte
group by 1
having count(*) > 1
order by 2 desc
limit 50;
```

```sql
-- unmatched left entities
select count(distinct l.key) as unmatched
from left_side l
left join right_side r
    on l.key = r.key
where r.key is null;
```

```sql
-- denominator sanity
select
    count(*) as rows,
    count_if(denominator = 0) as zero_denominator_rows,
    min(denominator) as min_denominator,
    max(denominator) as max_denominator
from suspicious_result;
```
