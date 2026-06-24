---
name: "query-tableau-data"
description: "A skill to query Tableau data sources, the \"last mile\" of analytics in an organization. When business users think about company data they often think of a visualization or data set on the BI platform, curated to their needs with useful semantics instead of raw data in a warehouse."
metadata:
  category: data
  source:
    repository: "https://github.com/Action-Co/skills"
    path: "skills/tableau/query-tableau-data"
    license_path: "LICENSE"
---

# Why Tableau?

Tableau is a repository of data sources and visualizations that represent the "_last mile_" of analytics in an organization. When business users think about company data they often think of a visualization or data set on the BI platform, curated to their needs with useful semantics instead of raw data in a warehouse.

The visual context built on top of data sources shapes this otherwise raw resource into something more consumable and actionable for people. Tableau is good at enabling all kinds of users to be productive with data and it thus contains a diversity of perspectives you will not find elsewhere in the data stack.

To query Tableau, you must first explore the data catalog ideally in a _Read-Evaluate-Print Loop (REPL)_ such that you can quickly iterate over different approaches to find the datasources and views you need. You can query data from views directly but querying datasources gives you more flexibility and access to the full dataset, at the cost of having to understand the schema and construct your own query logic. This information can be derived from the view layer and then formalized as a more robust query against the datasource with additional filters, aggregations, or calculations as needed.

---

### Workflow (REPL-first)

Explore the data catalog and reason through your task using a **REPL** tool. This workflow is inspired by research on [Recursive Language Models](https://arxiv.org/abs/2512.24601), which shows that holding large inputs as REPL variables — rather than loading them into the context window — scales beyond context limits. Recursion (e.g., sub-agent delegation) is implemented by individual harnesses, not by this skill itself.

> **RULE: Do not write files for exploration.** Run `uv run python -c "..."` directly.
> Writing exploration code to disk is a exploration workflow anti-pattern. Use `scripts/` only to
> formalize a reusable workflow _after_ REPL exploration is complete.

Hold catalog, schema, and query results as Python variables inside a `Session`, and surface only printed summaries to your context window. This keeps information-dense payloads out of the context window, where they degrade reasoning quality on linear-complexity tasks. Only print counts, filtered lists, and small row samples — never full payloads. This loop lets you iterate until you have a clear strategy for next steps in your task.

1. **Understand the Problem Space.** What question is the user trying to answer? What are the fundamental components of your task? You will advise on which datasources or views serve their needs after mapping the catalog.

2. **Authenticate first — run this before anything else.**

   ```python
   from query_tableau_data_py.config import SdkConfig
   from query_tableau_data_py.session import Session
   with Session(SdkConfig()) as session:
       si = session.server_info
       print(f"Server {si.product_version} (API {si.rest_api_version} — auto-negotiated), VDS tier: {si.vds_feature_tier}")
       print("AUTH OK")
   ```

   If this raises:
   - `ValidationError` → `.env` is missing required fields (`TABLEAU_SERVER_URL`, `PAT_NAME`, `PAT_VALUE`)
   - `AuthenticationError` → credentials are wrong or PAT is expired
   - `OSError` / `ConnectionError` → server URL is wrong or network is down

   If credentials are missing or invalid, **stop and ask the user** to complete the setup steps in [README.md § HITL](./README.md#tasks-that-require-a-human-in-the-loop-hitl). Creating a PAT and configuring `.env` requires human access to the Tableau UI.

   Do not manually check for `.env` — place it in the skill root directory (next to `.env.template` and `pyproject.toml`). `SdkConfig` looks for `.env` in cwd first, then the skill root, and raises immediately if anything is missing. Let it fail loudly. See [AUTH.md](docs/api/AUTH.md) to troubleshoot.

3. **Scope the Site.** Before calling any inventory function, take a fast site-scale snapshot. This makes exactly 4 HTTP requests regardless of site size — no timeout risk.

    ```python
    scope = session.scope_site()
    print(f"{scope.datasource_count} datasources, {scope.workbook_count} workbooks, {scope.view_count} views")
    print(f"{len(scope.projects)} projects")
    for p in scope.projects[:20]:
        print(f"  {p.name}")
    ```

    Use the counts to choose your inventory strategy:

    ```python
    if scope.datasource_count < 500 and scope.workbook_count < 1000:
        # Small/medium site: full inventory is fast in the REPL (default page_size=1000)
        datasources = session.inventory_datasources()
        workbooks   = session.inventory_workbooks()
        views       = session.inventory_views()
    else:
        # Large site: use project filtering + limits in the REPL
        datasources = session.inventory_datasources(limit=1000)
        workbooks   = session.inventory_workbooks(limit=1000)
        views       = session.inventory_views(limit=5000)
        # Certified datasources are the highest-quality signal on large sites
        certified   = [ds for ds in datasources if ds.is_certified]
        # Narrow to specific projects using names from scope.projects
        target_ds   = session.inventory_datasources(filter_project="<project>")
    ```

    > **Script escape hatch:** If you need an exhaustive pull that exceeds the REPL tool's timeout budget (e.g., fetching all 456k views to find the global top N), write a purpose-built script to `scripts/`, run it, and read results back from `temp/` via `data.py`. This is the exception — most discovery and analysis stays in the REPL.

    > **Note:** Session is sync-only (`with`, not `async with`). For async apps (Streamlit, FastAPI), see [INTEGRATION.md](docs/sdk/INTEGRATION.md).

    Filter programmatically — do not print full lists. Prioritize certified datasources (`ds.is_certified`) as quality signals. Rank views by `total_view_count` to identify the most-used assets. To resolve workbook names for views, join `inventory_views()` with `inventory_workbooks()` on `workbook_luid`.

4. **Trace Lineage on Candidates.** For selected datasources and workbooks, fetch targeted lineage to understand relationships — one HTTP request per asset, no pagination, no timeout risk.

    - `session.datasource_lineage(luid)` — downstream workbooks/sheets/dashboards, upstream tables/databases, 30-field preview
    - `session.workbook_lineage(luid)` — sheets, dashboards, upstream published datasources

    Use workbook lineage to bridge from a popular view to the published datasource that powers it. Use datasource lineage to understand downstream impact before choosing a target to query.

    > _Note_: Do not query dashboards — they surface data from the "first view" only, which may be unrelated to your needs. Use `workbook_lineage()` to find the individual sheet and its upstream datasource instead. Sheets must be published to be queryable; unpublished sheets inform schema understanding only.

5. **Introspect the Datasource**: Retrieve field metadata and hold it as a Python object. Filter to the fields relevant to your question.

    Fields are grouped by logical table in `schema.field_groups`. Each `FieldGroup` has a `logical_table_caption` attribute (the table's display name) and a `fields` list. Iterate as:
    ```python
    dims = [f for fg in schema.field_groups for f in fg.fields if f.role == "DIMENSION"]
    measures = [f for fg in schema.field_groups for f in fg.fields if f.role == "MEASURE"]
    ```

    > _Note_: Some published datasources have "API Access" disabled — a Tableau permission not exposed in the catalog. The only way to detect it is to attempt introspection and catch the 401. When looping over multiple datasources, use defensive introspection:
    > ```python
    > from query_tableau_data_py.errors import IntrospectionError
    > for ds in candidates:
    >     try:
    >         schema = session.introspect(ds.luid)
    >     except IntrospectionError as e:
    >         if "401" in str(e):
    >             print(f"SKIP {ds.name!r} — API Access not enabled")
    >         else:
    >             raise
    > ```
    > Enabling API Access requires a site admin or content owner with "Download Full Data" permission.

6. **Establish an Effective Shared Reality**: If acting on behalf of a user, ensure that you have a clear understanding of their intent by asking clarifying questions and recommending solutions based on your new knowledge of the data catalog. This will narrow down the relevant data sources and fields to query, allowing for both of you to align on a shared data strategy.

7. **Query the Datasource.** After establishing a data strategy and aligning with stakeholders, execute the VDS query and print only a summary — row count and a few sample rows:

    Next steps may include analyzing data, generating insights, or creating visualizations based on the retrieved information.

    > _Note_: VDS only works with published datasources, not those embedded inside workbooks.

---

### Using the Code

This skill contains a _Python_ package (`query_tableau_data_py`) with a modular script suite (`auth.py`, `catalog.py`, `inventory.py`, `lineage.py`, `introspect_datasource.py`, `introspect_workbook.py`, `query.py`, `query_view.py`) and a demo orchestrator, `main.py`. The demo is an example, not a reusable entry point — for your own workflows, use `Session` directly in a **REPL** or write a new script that imports it. See [credentials setup](docs/api/AUTH.md).

**Start here — REPL exploration: [REPL.md](./docs/REPL.md)** — a complete **REPL** session demonstrating the full workflow: auth check → inventory → lineage → introspection → VDS query.

**Building a reusable script?** Only write to `scripts/` after validating your approach in the **REPL**. See the [SDK Reference](./docs/sdk/SDK.md) for module documentation, import patterns, and complete examples.

**Need to persist results to disk?** See [TEMP_DATA.md](./docs/sdk/TEMP_DATA.md) for file-based persistence conventions.

**Output conventions:**
- Reusable scripts you write → save to `scripts/` (committed to git)
- Temp exploration data (JSON, CSV, Markdown) → save to `temp/` (gitignored; clean up when done)

---

## Skill Structure

```bash
skills/query-tableau-data/
├── SKILL.md                              # entry point, navigation, usage
├── README.md                             # landing page and instructions for humans
├── pyproject.toml                        # runtime uv project config (no dev deps)
├── .env.template                         # template for environment variables
│
├── docs/                                 # detailed deep-dives & instructions
│   ├── README.md                         # documentation index with links to deep-dives
│   ├── REPL.md                           # complete REPL exploration session
│   ├── DDD.md                            # domain-driven design & ubiquitous language
│   ├── sdk/                              # SDK usage patterns, module reference, examples
│   ├── vds/                              # VDS operation deep-dives
│   └── api/                              # API reference for the main query workflows
│
├── scripts/                              # store reusable scripts & workflows
│
├── temp/                                 # local exploration output (gitignored)
│
└── src/                                  # source code
    ├── schemas/
    │   └── vds.20261.0.openapi.json      # OpenAPI schema for the VDS API
    │
    └── query_tableau_data_py/         # Python package (importable as query_tableau_data_py)
        └── main.py                       # demo orchestrator / entry-point script
```

> _Note_: This skill was last updated as of Tableau version `2026.1.0`.
