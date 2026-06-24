# Temporary Data

> **Prefer REPL exploration for interactive workflows.** Holding catalog, schema, and query results as Python variables keeps data out of the LLM's context window and eliminates cleanup overhead. Use `temp/` persistence for explicit use cases: user-requested CSV export, multi-session continuity, or cross-tool handoff. See [SDK.md — REPL Exploration](SDK.md) for the recommended default pattern.

When persistence is needed, the best practice is to **store API responses and query results in `temp/`**. The skill's `.gitignore` excludes `temp/*` (keeping only `temp/.gitkeep`), so nothing inside is ever committed to version control. This lets you explore large result sets locally with standard Unix tools, then delete the contents when you are done.

> **Tip:** Clean up `temp/` at the end of your session to avoid leaving stale data on disk.
> ```bash
> rm temp/data_catalog_ddmmyy.json
> rm temp/datasource_superstore_123_ddmmyy.json
> rm temp/query_superstore_123_ddmmyy.csv
> ```

## Format Guide

| Phase | Format | File Pattern | Native Unix Tools |
|-------|--------|--------------|-------------------|
| Discovery (GraphQL) | JSON | `temp/data_catalog_{timestamp}.json` | `jq`, `cat`, `python -m json.tool` |
| Discovery (REST fallback) | JSON | `temp/published_datasources_{timestamp}.json` | `jq`, `cat`, `python -m json.tool` |
| Deep Metadata | JSON | `temp/datasource_{name}_{luid}_{timestamp}.json` | `jq`, `cat`, `python -m json.tool` |
| Query Results | CSV | `temp/query_{name}_{luid}_{timestamp}.csv` | `head`, `tail`, `cut`, `grep`, `awk`, `column -t -s,` |
| Query Results | JSON | `temp/query_{name}_{luid}_{timestamp}.json` | `jq`, `cat`, `python -m json.tool` |
| Human Readability | Markdown | `temp/inspect_{luid}_{timestamp}.md` | `cat`, `less` |


### Example Exploration Commands

```bash
# JSON: List all datasource names from GraphQL catalog
jq '.data.publishedDatasourcesConnection.nodes[].name' temp/data_catalog_*.json

# JSON: Show datasources with more than 10 fields
jq '.data.publishedDatasourcesConnection.nodes[] | select((.fields | length) > 10) | .name' temp/data_catalog_*.json

# JSON: Show datasources in the "Sales" project
jq '.data.publishedDatasourcesConnection.nodes[] | select(.projectName == "Sales")' temp/data_catalog_*.json

# JSON: Show field names and types for a specific datasource
jq '.data.publishedDatasourcesConnection.nodes[] | select(.name == "Superstore") | .fields[] | {name, dataType, role}' temp/data_catalog_*.json

# JSON: List datasource names from REST fallback
jq '.datasources.datasource[].name' temp/published_datasources_*.json

# JSON: Pretty-print metadata to terminal
python -m json.tool temp/inspect_*.json

# Markdown: Read the human-readable report
less temp/inspect_*.md
```
