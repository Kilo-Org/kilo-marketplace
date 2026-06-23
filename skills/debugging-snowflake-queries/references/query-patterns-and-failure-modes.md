# Query Patterns and Failure Modes

Use these as generic examples of how Snowflake query failures happen in real warehouse work.

## 1. Wrong environment or schema

Failure mode:

- The query points at the wrong database, schema, or environment.
- The object exists somewhere else, so the SQL looks reasonable but fails or returns stale data.

Transferable lesson:

- A large share of `object does not exist` and stale-result bugs are environment bugs, not logic bugs.
- Verify the exact relation path before rewriting the query.

## 2. Filter column lives on a metadata or enrichment table

Failure mode:

- A query applies a filter using a column that does not live on the main fact table.
- The column actually comes from a side table joined by request id, event id, or some other surrogate key.

Generic pattern:

```sql
from fact_table f
left join fact_metadata m
    on f.id = m.id
where coalesce(m.some_flag, false) = false
```

Transferable lesson:

- When a filter seems semantically right but the column is missing, check whether it belongs to an enrichment table rather than the core fact.

## 3. Wrong source for the analytical question

Failure mode:

- The query is syntactically correct, but the chosen source has partial coverage, different semantics, or lag that makes the answer wrong.

Transferable lesson:

- If the business answer is implausible, re-check source suitability before rewriting aggregations.
- Coverage problems often look like logic bugs.

## 4. Identity scope mismatch

Failure mode:

- Counts are inflated or deflated because guest, anonymous, test, internal, or unresolved identities are mixed with the intended population.

Transferable lesson:

- Bad counts often come from entity scope, not arithmetic.
- Always ask which entity classes should be included or excluded.

## 5. Freshness issue masquerading as a metric change

Failure mode:

- One day or hour drops sharply because one upstream input is incomplete while another is current.

Transferable lesson:

- Sudden cliffs are often ingestion or freshness issues.
- Compare source-vs-downstream row counts by time bucket before changing the metric logic.

## 6. Historical query copied after naming drift

Failure mode:

- A copied query references an old database name, schema name, or renamed object.

Transferable lesson:

- Historical SQL ages badly.
- Inspect current warehouse structure instead of trusting old snippets.

## 7. Bridge table required for cross-system joins

Failure mode:

- Two systems represent the same entity with different IDs.
- The query tries to infer the relationship directly from string patterns or naming similarity.

Transferable lesson:

- If systems use different identifiers, look for a canonical mapping table first.
- Do not improvise cross-system joins unless the mapping is proven.

## 8. Soft-delete or CDC tombstones distort results

Failure mode:

- Mirrored operational tables contain deleted rows or tombstones that remain queryable.

Transferable lesson:

- If mirrored-source counts exceed expectations, inspect delete markers, CDC status fields, or load-state columns.

## 9. One-to-many enrichment inflates facts

Failure mode:

- A fact table is joined to an enrichment table with multiple rows per key.
- Counts, sums, or distincts are inflated after the join.

Transferable lesson:

- Aggregate the enrichment side to one row per join key before joining when the output grain requires it.

## 10. Date filter applied at the wrong grain

Failure mode:

- Filtering on `timestamp >= ...` in one table and `date >= ...` in another causes mismatched populations.
- Truncation or timezone conversion silently removes expected rows.

Transferable lesson:

- Align all inputs to the same time grain and boundary before comparing counts.
