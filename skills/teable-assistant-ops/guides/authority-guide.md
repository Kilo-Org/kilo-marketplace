# Authority Matrix Guide (Advanced Permissions)

Per-table / per-view / per-row / per-field access control for project collaborators. All `authority` commands require project Owner/Creator permission — reads included.

## When to Use

- Restrict collaborators to specific tables, views, rows, or fields
- Different teams see different slices of the same project (e.g. Sales sees only their region's rows)
- Read-only or comment-only access to selected tables

## Concepts

- A role grants access **table by table** — a table without a grant is completely **invisible** to the role's members.
- Inside a granted table the ceiling is platform **Editor** level: matrix roles can never create/delete tables or fields, or share views.
- Once enabled, the matrix applies to **every collaborator except the project Owner and matrix admin users**.
- A user in multiple roles gets the **union** of their grants (most permissive wins).
- `defaultRole` is the fallback for collaborators not assigned to any role.

## Command Overview

| Command | Purpose |
|---------|---------|
| `authority get` | Current config + on/off status |
| `authority export` | Write config as JSON (`--file`; `--role` for one role) — start of every edit |
| `authority diff` | Preview what an edited config file would change (does NOT model `--prune` deletions) |
| `authority apply` | Reconcile live state to match the file; `--dry-run` = full preflight incl. prune preview; `--prune` also deletes roles absent from the file |
| `authority enable` / `disable` | Turn the matrix on/off (config is kept on disable) |
| `authority role-list` | List roles with assigned users/departments |
| `authority role-get` | One role's members + per-table grants (`--role-id`; `--raw` for API form) |
| `authority role-delete` | Delete a role and its permission config (`--role-id`) |
| `authority role-duplicate` | Duplicate a role (`--role-id`; `--name`, `--include-users`, `--include-departments`) |

## Workflow

**ALL config changes (roles, grants, members, default role, admins) go through the config-file flow** — export → edit → diff → apply:

```bash
teable authority get -b bseXXXX                                      # current config + on/off status
teable authority export -b bseXXXX --file authority.json             # 1. export full matrix
teable authority export -b bseXXXX --role "Sales" --file sales.json  #    or scoped to one role (small, safe edits)
# 2. edit the JSON file
teable authority diff -b bseXXXX --file authority.json               # 3. preview changes (dry run)
teable authority apply -b bseXXXX --file authority.json              # 4. reconcile live state to the file
# Pruning? diff does NOT model prune deletions — always preview them first:
teable authority apply -b bseXXXX --file authority.json --dry-run --prune
teable authority apply -b bseXXXX --file authority.json --prune
teable authority enable -b bseXXXX                                   # on/off state is NOT part of the file
```

## Config File Shape

```jsonc
{
  "version": 1,
  "baseId": "bseXXXX",
  "scope": "role",           // written by `export --role`; such a file can never --prune.
                             // Omit for a full-matrix file
  "defaultRole": "<role id or name>",   // or null — fallback for unassigned collaborators
  "admins": ["usrXXXX"],                // users that bypass the matrix
  "roles": [{
    "id": "aurXXXX",          // from export. An entry WITHOUT an id matches an existing role
                              // by name and only creates a new role when no live role has that name
    "name": "Sales",
    "description": "...",
    "enabled": true,
    "members": { "users": ["usrXXXX"], "departments": [] },
    "permissions": [ /* table grants, see below */ ],
    "nodes": [{ "nodeType": "workflow", "nodeId": "...", "enabled": true }]  // workflow | app
  }]
}
```

**Managed-key rule** (applies to every top-level key, including `roles` itself): a key **absent** from the file is left unchanged by diff/apply; an explicitly empty value (`[]` / `null`) is **enforced**. A full `export` writes every key; `export --role` writes a partial file that manages only that role. A hand-written file with only `defaultRole`/`admins` and no `roles` key manages just those.

**Member IDs**: user ids via `teable get-collaborators`; departments need an enterprise organization — resolve ids via `teable call-api` on GET /organization/department (find it with `teable search-api --query department`).

## Table Grants

One entry per table the role may access — a table the role should NOT access is simply **omitted** (there is no "none" value):

```jsonc
{
  "tableId": "tblXXXX",
  "access": "editor",               // capability preset (required): editor | commenter | viewer
  "deny": ["record|delete"],        // optional: take away actions on top of the preset
  "views": ["viwXXXX"],             // optional whitelist; omit = all views, [] = none
  "rowFilter": { /* ... */ },       // optional: members only see matching rows (view-filter JSON syntax)
  "fields": { "fldXXXX": "hidden" } // optional per-field restriction
}
```

**Access presets:**

| Preset | Capabilities |
|--------|-------------|
| `editor` | Full table access: record CRUD + comment + copy, manage views, import + export (the matrix ceiling; trim it with `deny`) |
| `commenter` | Read + comment + copy + export; cannot change records or views |
| `viewer` | Read + copy + export only |

**`fields` values**: `"hidden"` = field invisible to members; `"read-only"` = visible, not editable; an action array (e.g. `["record|create"]`) disables exactly those record actions. Fields added to the table AFTER a field restriction set was stored stay inaccessible to the role — grant one explicitly with `"fldXXXX": []`.

**`rowFilter`**: same JSON syntax as view filters — see [view.filter.md](../api-reference/view.filter.md). For user fields the dynamic current-user token is the literal `"Me"` (capital M) — lowercase `"me"` is a plain string and matches nothing.

A table grant may carry `"enabled": false` — stored but not in effect (round-tripped faithfully by export/apply).

For the authoritative full reference (including the exact `deny` action values), run `teable authority export --help`.
