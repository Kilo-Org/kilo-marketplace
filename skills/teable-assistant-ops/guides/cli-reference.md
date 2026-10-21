# CLI Operations Reference

Use `teable config show` to check current endpoint, baseId, and token status.

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `record get` defaults to all fields | Use `--projection '["fldXXX","fldYYY"]'` to select specific fields |
| `record create/update` with `{"fields":{...}}` object format | Object format auto-converts; canonical form: `--header '[...]' --records '[[...]]'` |
| `--search "keyword"` scope | Plain string auto-wraps to `{"value":"keyword"}`; for field-scoped: `--search '{"value":"keyword","fieldId":"fldXXX"}'` |
| `field update --name "X"` | `--name` is a convenience flag; for other properties use `--updates '{"name":"X"}'` |
| `table create --fields '[{...}]'` object format | Object format auto-converts; canonical shorthand: `--fields '["X:text"]'` |
| Treating `table delete` as permanent | It moves the table to project trash. Verify the table ID first; restore from trash after an accidental deletion. |

## Field Type Aliases

When creating tables or fields, use these shorthand type aliases:

| Alias | Type | Example |
|-------|------|---------|
| `text` | Single-line text | `"Title:text"` |
| `long` | Long text (rich text) | `"Notes:long"` |
| `num` | Number | `"Amount:num"` |
| `date` | Date | `"Due:date"` |
| `check` | Checkbox | `"Done:check"` |
| `rate` | Rating | `"Score:rate"` |
| `user` | User | `"Assignee:user"` |
| `file` | Attachment | `"Files:file"` |
| `auto` | Auto-number | `"ID:auto"` |
| `created` | Created time | `"Created:created"` |
| `modified` | Last modified time | `"Modified:modified"` |
| `sel:A,B,C` | Single select | `"Status:sel:Todo,Done"` |
| `mul:A,B,C` | Multi-select | `"Tags:mul:Bug,Feature"` |

Advanced types (link, lookup, rollup, formula, AI) require `field create` with options — see [field.simple.md](../api-reference/field.simple.md).

**Name resolution**: `field create` accepts table/field names in place of IDs (e.g., `foreignTableName: "Projects"` instead of `foreignTableId: "tblXXX"`). This reduces the need to look up IDs before creating link/lookup/rollup fields.

## Data Queries

**`record get` vs `sql-query`** — if you'll write back to the same records, use `record get` (returns record IDs); for analytics or cross-table reads, use `sql-query`.

- **record get** — record IDs for subsequent writes, `--search` for fuzzy search, simple pagination. Returns compact tabular output with an `id` column per row.
- **sql-query** — JOINs across tables, aggregations (COUNT/SUM/AVG/GROUP BY), complex WHERE, subqueries. Returns flat rows without record IDs. Read-only (SELECT only).
- **Aggregation**: prefer `sql-query` with GROUP BY. Alternatively, `search-api --query "aggregation"` + `call-api` for the dedicated aggregation endpoint.

```bash
# record get defaults to all fields; use --projection to select specific ones
teable record get --table-id tblXXX --projection '["fldXXX","fldYYY"]'
# SQL: must use dbTableName/dbFieldName from table get/field get, double-quote identifiers
teable sql-query --sql 'SELECT "name" FROM "bseXXX"."tbl_users" LIMIT 100'
```

### SQL Critical Rules

1. **Must use database names**: get `dbTableName` from `table get`, `dbFieldName` from `field get` — display names won't work
2. **Table format**: `dbTableName` from `table get` is one dotted value (e.g. `bseXXX.tbl_users`); split it on the dot into two quoted identifiers: `"bseXXX"."tbl_users"`
3. **Double-quote all identifiers**: `SELECT "fieldName" FROM "schema"."table"`
4. **SELECT only** — read-only (PostgreSQL 15.4), no INSERT/UPDATE/DELETE
5. **Always add `LIMIT 100`** to non-aggregate queries to avoid large result sets
6. **JSON fields**: `json_extract_path_text("field"::json, 'key')`
7. **Dates are UTC** — convert with `timezone('Asia/Shanghai', col)` for local time

**System fields** (always available, use these exact column names): `__id`, `__auto_number`, `__created_time`, `__last_modified_time`, `__created_by`, `__last_modified_by`, `__version`

**View types**: `grid` (default), `kanban`, `form`, `gallery`, `calendar`, `plugin` — see [view.filter.md](../api-reference/view.filter.md) and related view docs for configuration.

### View Configuration

`view create` creates a bare view. Use `view update` to configure filters, sorts, grouping, and column visibility afterward:

```bash
teable view update --table-id tblXXX --view-id viwXXX --filter '<json>' --sort '<json>' --group '<json>' --column-meta '<json>'
```

See [view.filter.md](../api-reference/view.filter.md), [view.sort.md](../api-reference/view.sort.md), [view.group.md](../api-reference/view.group.md), [view.column.md](../api-reference/view.column.md) for JSON formats.

## Record Operations

> **Tip**: for exact value formats without typecast, see [record.value-format.md](../api-reference/record.value-format.md)

**Single record**: `record get --table-id tblXXX --record-id recXXX` fetches one record by ID, ignoring `--search`/`--take`/`--skip`.

**Value semantics**: `""` = skip field (no change), `null` = clear cell; checkbox: `true` = checked, `null` = unchecked

**`--typecast`**: auto-converts human-readable values (user name/email → user ID, record name → link record ID). See value types table below.

**Value types in compact array format:**

| Type | Format | Notes |
|------|--------|-------|
| Text | `"string"` | |
| Number | `42` or `123.45` | |
| Checkbox | `true` / `null` | `true` = checked, `null` = unchecked (NOT `false`) |
| Date | `"2025-01-27"` | ISO string, with or without time |
| Select | `"Done"` | |
| Multi-select | `["A","B"]` | Array of strings |
| Link | `"Record Name"` | With `--typecast`; without: `[{"id":"recXXX"}]` |
| User | `"name"` or `"email"` | With `--typecast`; without: `{"id":"usrXXX","title":"Name"}` |
| Attachment | `[{"name":"f.png","token":"xxx"}]` | Always array of objects; update **replaces all** |

**Batch limits**: `record create`/`update` max 2000 per call; `record delete` max 1000 IDs per call. `--take` (alias `--limit`) max 1000 per `record get`. For larger datasets, split into multiple calls.

**Attachment handling**: Get tokens via `upload-attachment --file-path /path/to/file`. On update, passing attachments **replaces** all existing — not appends.

**View-relative queries**: `record get --view-id viwXXX` returns rows in view order with view's filter/sort/group applied; group headers excluded — use for positional references ("the 3rd row").

**Record reordering**: `record update --header '["recordId"]' --records '[["recXXX"]]' --order '{"viewId":"viwXXX","anchorId":"recYYY","position":"before"}'`; swap = two calls.

**User fields**: use `get-collaborators --search "name"` to find users, then pass user ID or `--typecast` with display name.

## Sending Email

`teable send-email` sends an email **directly** via the Teable mail sender (system SMTP by default). This is a one-off send — for event-driven emails *inside a workflow*, use the automation SendEmail action instead (see [automation.send-email.md](../api-reference/automation.send-email.md)).

```bash
teable send-email \
  --to "a@example.com,b@example.com" \
  --subject "Weekly report" \
  --body "## Summary\nAll green." \
  --body-type markdown
```

| Flag | Notes |
|------|-------|
| `--subject` | Email subject |
| `--body` | Body string **or a path to a file** |
| `--to` | Comma-separated recipients (required unless `--bcc` given) |
| `--cc` / `--bcc` | Comma-separated; `--bcc` satisfies the recipient requirement on its own |
| `--body-type` | `markdown` (default) or `html` |
| `--reply-to` | Reply-to address |
| `--smtp` | Custom SMTP transport as a JSON string (omit to use system SMTP) |

## Node & Folder Management

Organize nodes (tables, folders, dashboards, etc.) in a project: `get-node-tree`, `folder create`, `folder update` (rename), `folder delete`, `folder move`.

Always `get-node-tree` first to see current structure. Reorder with: `folder move --node-id <nodeId> --parent-id <parentId> --anchor-id <siblingId> --position before|after`.

To create a table directly inside a folder, pass `--folder-id` to `table create` or `import` (also supported by `import-airtable` with `--base-id`, and `app create`).

## Authority Matrix (Advanced Permissions)

Per-table / per-view / per-row / per-field access control for project collaborators via the `authority` command group. All config changes go through export → edit → diff → apply. Read [authority-guide.md](authority-guide.md) before running any `authority` command.

## Multi-Table Relationship Design

> **Required**: `api-reference/field.link.md` — Link field configuration
> **Optional**: `api-reference/field.lookup.md`, `api-reference/field.rollup.md` — Lookup/Rollup configuration

When building multiple related tables, plan relationships before creating anything — retrofitting Link/Lookup/Rollup wastes time and often results in poorly connected data.

**Link relationship type selection:**

| Relationship | Type | Example |
|-------------|------|---------|
| One parent, many children | `oneMany` | Department → Employees |
| Many children, one parent | `manyOne` | Tasks → Project |
| One-to-one | `oneOne` | User ↔ Profile |
| Many-to-many | `manyMany` | Tasks ↔ Tags |

**Computed field type selection:**

| Scenario | Field type | Prerequisite |
|----------|-----------|-------------|
| Display value from linked record | Lookup (`--is-lookup`) | Link field exists |
| Display value from ANY table (no link) | Conditional Lookup (`--is-conditional-lookup`) | None |
| Aggregate linked records (SUM, COUNT) | Rollup (`type: rollup`) | Link field exists |
| Aggregate ANY table (no link) | Conditional Rollup (`type: condRollup`) | None |

**Design-first workflow:**
1. **Map relationships** — identify which tables reference each other and choose Link types from the table above
2. **Build referenced tables first** — create "parent" or "lookup target" tables and populate records before the main table
3. **Create Link fields upfront** — include Link fields from the start instead of using plain text/select fields to simulate relationships
4. **Populate Link values with `--typecast`** — pass the linked table's primary field value and it auto-resolves to the correct record ID

**Common mistake:** Creating a "Category" singleSelect field instead of a Link field to a Categories table. This blocks Rollup aggregation and Lookup cross-referencing later.

## search-api + call-api

Use this pair to access any Teable API not covered by dedicated CLI commands.

1. `search-api --query "duplicate record"` — find the API
2. `call-api --method POST --url "/path" --params '{...}'` — execute it

**Narrowing results**: `--tags '["record"]'` filters by API category; `--limit 10` returns up to 10 results (default 5, max 10).

**Note**: `call-api` can execute any method (GET/POST/PUT/PATCH/DELETE).

## One-Time Data Visualization

For static charts/reports from already-queried data, use HTML code blocks (` ```html `) — no CLI command needed.

- HTML must start with `<!DOCTYPE html>` or `<html>` to enable preview
- Recommended: Tailwind CSS + ECharts CDN
- Only generate when user clearly requests it; may actively recommend
- For live dashboards or interactive UIs that need ongoing data access → use `app create` instead

## Error Troubleshooting

When a command fails, follow this procedure:
1. `teable config show` — check current endpoint, baseId, and token status
2. `teable auth status` — confirms connection and permissions
3. Verify IDs exist: `table get` (for table IDs) or `field get` (for field IDs)
4. Check common errors: **field type mismatch** (passing text to number field), **ID not found** (deleted or from different project), **permission denied** (user lacks write access)
