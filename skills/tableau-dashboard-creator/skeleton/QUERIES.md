# QUERIES.md

Provide your SQL queries below. Group them under a heading that matches your database type.
The agent will use the heading to select the correct query script.

Supported out-of-the-box: `PostgreSQL`

> **Need another database?** Add a `query_<dbtype>.py` script to the installed skill's `scripts/` directory following the same pattern as `query_postgresql.py`, then add a matching heading section here (e.g., `## Databricks`, `## Snowflake`, `## MySQL`).

---

## PostgreSQL

```sql
-- Example: replace with your actual query
SELECT * FROM public.your_table
```

---

**Note**: You only need to include sections for the database(s) you actually use.
If you also keep files in `sample-data/`, the agent should say which source it is choosing before Step A continues.
