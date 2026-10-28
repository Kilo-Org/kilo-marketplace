# QVD Operations

Canonical syntax and mechanics for Qlik QVD files: STORE, LOAD FROM (qvd), optimized vs standard read, NoConcatenate around QVD loads, multi-QVD concatenation, file-list iteration, partial reload prefixes, binary load.

For decision framing — when to use optimized read, when to layer QVDs, when to split a generator/consumer architecture — see `qlik-performance` SKILL.md. This file owns the mechanics; that file owns the decisions.

---

## STORE Syntax

Write the contents of an in-memory table to a QVD file.

```qlik
// Write all fields, one table per STORE:
STORE * FROM [TableName] INTO [lib://Connection/path/file.qvd] (qvd);

// Write a subset of fields by name:
STORE Field1, Field2 FROM [TableName] INTO [lib://Connection/file.qvd] (qvd);

// CSV is also supported by the same syntax — file extension and format spec change:
STORE * FROM [TableName] INTO [lib://Connection/file.csv] (txt, delimiter is ',');
```

Rules:
- One table per STORE. To write two tables, write two STORE statements.
- The `(qvd)` format specifier is required for QVD output.
- The target connection (`lib://...`) must be writable from the reload context.
- If the file already exists, STORE overwrites it. There is no append mode; for append-style incremental output, see the patterns in `incremental-load-patterns.md` (sibling reference file).
- **Concurrent-write hazard.** Per the Qlik knowledge base, STORE opens its target file exclusively, denying other tasks both read and write access while it writes. Two reload tasks scheduled to STORE the same QVD path at overlapping times will collide — one acquires the exclusive lock and the other fails. A reload reading the QVD while another reload is writing it can also fail. The script does not retry on its own. Schedule generator reloads so writes to the same QVD path never overlap, or stage each generator's output to a per-task path and promote to the canonical name only after the writers finish. Reference: Qlik Community KB — "Concurrent Read and Write from/to a QVD file may result in one of the tasks failing." https://community.qlik.com/t5/Knowledge-Base/Concurrent-Read-and-Write-from-to-a-QVD-file-may-result-in-one/ta-p/1711386

Reference: help.qlik.com Cloud — Store statement.

---

## LOAD FROM (qvd) Syntax

Read a QVD file back into an in-memory table.

```qlik
// Full load — all fields:
[Customers]:
LOAD * FROM [lib://QVDs/Customers.qvd] (qvd);

// Field-list load — only the named fields:
[Customers]:
LOAD customer_id AS [Customer.Key],
     customer_name AS [Customer.Name]
FROM [lib://QVDs/Customers.qvd] (qvd);
```

The `(qvd)` format specifier tells Qlik to treat the source as a QVD; without it the engine falls back to file-extension detection, which is fragile if the path is variable-driven.

Reference: help.qlik.com Cloud — LOAD statement, QVD format.

---

## Optimized vs Standard Read Modes

QVDs support two read modes. **Optimized read** copies pre-serialized symbol tables and bit-stuffed pointers directly into memory. **Standard read** unpacks every value before applying the LOAD logic. Optimized read is roughly an order of magnitude faster than standard QVD read, which is itself roughly an order of magnitude faster than re-querying a database. (Exact ratios are practitioner figures; Qlik does not publish them.)

### What preserves optimized read

Per Qlik help, only specific operations disable optimized read. Anything not on the disable list is optimized.

- `LOAD *`
- Field subsetting (loading only some of the QVD's fields by name)
- Field renaming with `AS` (e.g., `source_col AS [New.Name]`)
- Field reordering relative to the QVD's stored order
- `LOAD DISTINCT` — the QVD read itself stays optimized; DISTINCT processing happens after the fast read
- `CONCATENATE` prefix
- Single-parameter `EXISTS(field)` / `NOT EXISTS(field)` in a WHERE clause — the standard incremental-filter pattern — **only when `field` exactly matches a field name in the QVD being loaded**. If the QVD stores the field under one name (e.g., `customer_id`) but this LOAD aliases it to a different name (e.g., `[Customer.Key]`), an `EXISTS([Customer.Key])` check forces standard read because the engine cannot match the EXISTS name to a stored symbol before unpacking. Either reference the stored QVD name in EXISTS, or alias upstream so the symbol space already contains the target name
- A preceding LOAD above the QVD LOAD — the inner QVD read stays optimized; the outer transformation processes in-memory after

### What forces standard read

- Any function or expression applied to a loaded field — `Upper(name)`, `Date#(date_field)`, `Num(id_field)`, etc.
- Derived fields built from multiple source fields — `field1 & '-' & field2 AS CompositeKey`
- Two-parameter `EXISTS(field, expression)` — the expression form
- WHERE clauses that aren't a single-parameter `EXISTS(field)` — e.g., `WHERE amount > 0`
- `MAP ... USING` applied to a field being loaded

```qlik
// Optimized — field rename, subset, single-parameter NOT EXISTS:
LOAD customer_id AS [Customer.Key], name AS [Customer.Name]
FROM [lib://QVDs/Customers.qvd] (qvd)
WHERE NOT EXISTS([Order.Key]);

// Standard — transformation breaks it:
LOAD Upper(name) AS [Customer.Name]
FROM [lib://QVDs/Customers.qvd] (qvd);

// Standard — two-parameter EXISTS forces unpack:
LOAD * FROM [lib://QVDs/Customers.qvd] (qvd)
WHERE NOT EXISTS([Existing.Key], [Order.Key]);
```

**Folklore correction:** Field renaming via `AS` and field reordering relative to the QVD's stored order do NOT break optimized load. Earlier QlikView-era guidance to the contrary is wrong for current Sense/Cloud behavior.

**Preceding LOAD for transformations:** When transformations are needed, load to a temp via an inner optimized LOAD, then transform in the outer preceding LOAD:

```qlik
[Dimension.Customer]:
LOAD *, Upper([Customer.Name]) AS [Customer.Name];   // outer — in-memory transform
LOAD * FROM [lib://QVDs/Customer.qvd] (qvd);         // inner — optimized read
```

The inner read remains optimized. The outer LOAD reads the in-memory rows and applies the transform.

Reference: help.qlik.com Cloud — Working with QVD files (`work-with-QVD-files.htm`); Exists() (`InterRecordFunctions/Exists.htm`).

---

## EXISTS Against a QVD Load

The single-parameter `EXISTS(field)` form is the canonical pattern for filtering a QVD load while preserving optimized read. It checks the named field's symbol space (all previously loaded values across all tables containing that field).

```qlik
// Step 1 — load the set of allowed keys into a prior table.
[AllowedCustomers]:
LOAD customer_id FROM [lib://QVDs/AllowedKeys.qvd] (qvd);

// Step 2 — optimized load that filters by membership.
[Fact.Orders]:
LOAD *
FROM [lib://QVDs/Orders.qvd] (qvd)
WHERE EXISTS(customer_id);
```

**Self-referencing dedup behavior:** Single-parameter `EXISTS(field)` also checks values already loaded *during the current statement*. The symbol table updates row-by-row as the load progresses, so the second occurrence of a value sees the first as already existing. This is documented Qlik behavior — usually beneficial for incremental patterns (it skips QVD rows whose keys were already loaded from source), but it means `WHERE NOT EXISTS(field)` on a fresh load loads only the first occurrence of each value.

To avoid both the self-reference and cross-table contamination (where another table also containing `field` pollutes the check), alias the lookup field and use the two-parameter form — at the cost of forcing standard mode:

```qlik
[_Existing]:
LOAD DISTINCT customer_id AS _existing_cust RESIDENT [Customers];

LOAD * FROM [lib://QVDs/Orders.qvd] (qvd)
WHERE NOT EXISTS(_existing_cust, customer_id);   // standard read

DROP TABLE [_Existing];
```

Reference: help.qlik.com Cloud — Exists() (`InterRecordFunctions/Exists.htm`); see SKILL.md Section 15 for the full symbol-space discussion.

---

## NoConcatenate Around QVD Loads

When a new LOAD produces a field set identical to an existing table's (same names AND same count), Qlik silently concatenates the rows into the existing table. The new table name is never registered.

This trap hits QVD-based patterns frequently because two QVDs in the same processing layer often share the same column structure (e.g., two raw extracts of the same shape, or a temp table that mirrors the QVD it loads from).

```qlik
[Customers]:
LOAD * FROM [lib://QVDs/Customers.qvd] (qvd);

// WITHOUT NoConcatenate, this silently merges into [Customers]:
[CustomersBackup]:
NoConcatenate
LOAD * RESIDENT [Customers];
```

Apply `NoConcatenate` defensively to any temp table that dedups, filters, or pivots data with the same shape as its source. Full treatment in `references/sql-constructs.md` Section 2.1.

**Explicit CONCATENATE prefix:** `CONCATENATE([TargetTable])` forces concatenation even when field sets differ. Mismatched fields receive NULL in the target. Use when intentionally merging tables with partially overlapping schemas — common in multi-source extracts that union into one fact.

---

## Multi-QVD Concatenation

Two common patterns load multiple QVDs into a single table.

### Pattern 1: Explicit CONCATENATE per file

```qlik
[Sales]:
LOAD * FROM [lib://QVDs/Sales_2024.qvd] (qvd);

CONCATENATE([Sales])
LOAD * FROM [lib://QVDs/Sales_2025.qvd] (qvd);

CONCATENATE([Sales])
LOAD * FROM [lib://QVDs/Sales_2026.qvd] (qvd);
```

Each CONCATENATE load stays optimized (CONCATENATE preserves it). Use when the file list is short and known at script time.

### Pattern 2: FOR EACH over FileList

```qlik
[Sales]:
LOAD * FROM [lib://QVDs/Sales_2024.qvd] (qvd);   // seed the target

FOR EACH vFile IN FileList('lib://QVDs/Sales_*.qvd')
    IF '$(vFile)' <> 'lib://QVDs/Sales_2024.qvd' THEN
        CONCATENATE([Sales])
        LOAD * FROM [$(vFile)] (qvd);
    END IF
NEXT vFile
```

Use when the file list is dynamic. Notes:
- The first load creates the target; subsequent loads must use `CONCATENATE([Sales])`. Without it, the auto-concatenation rule still merges identically structured QVDs — but only if the field set matches exactly. Explicit CONCATENATE is safer.
- `FileList('lib://Path/*.qvd')` wildcards may not work for all Qlik Cloud connection types. If the wildcard fails, switch to an explicit file list or a directory listing.
- The seed-then-loop pattern shown above avoids loading the seed file twice.

### Pattern 3: Auto-concatenation in a loop

If every QVD in the list has the identical field set, the auto-concatenation rule does the work — no `CONCATENATE` prefix needed:

```qlik
FOR EACH vFile IN FileList('lib://QVDs/Sales_*.qvd')
    [Sales]:
    LOAD * FROM [$(vFile)] (qvd);
NEXT vFile
```

Each iteration's `[Sales]:` is silently merged into the running `[Sales]` because the field sets match. This is concise but fragile — one stray column in one QVD and the merge breaks. Prefer explicit CONCATENATE in production scripts.

---

## Load Once, Map Many

Never read the same QVD from disk twice. Each disk read is the expensive part; once the data is resident, subsequent operations are free by comparison.

```qlik
// WRONG — two disk reads:
[Map_ProductName]:
MAPPING LOAD product_id, product_name FROM [lib://QVDs/Product.qvd] (qvd);
[Map_ProductCategory]:
MAPPING LOAD product_id, product_category FROM [lib://QVDs/Product.qvd] (qvd);

// RIGHT — one disk read, multiple maps from resident:
[_ProductTemp]:
LOAD * FROM [lib://QVDs/Product.qvd] (qvd);

[Map_ProductName]:
MAPPING LOAD product_id, product_name RESIDENT [_ProductTemp];
[Map_ProductCategory]:
MAPPING LOAD product_id, product_category RESIDENT [_ProductTemp];

DROP TABLE [_ProductTemp];
```

Rule: every QVD should be read from disk exactly once per reload. If a downstream step needs the same QVD, load to a temp and serve all consumers from resident.

---

## Narrow Before STORE

When writing intermediate or output QVDs, write only the fields downstream consumers need. Storing fields that nothing reads costs disk space, QVD read time, and downstream memory.

```qlik
// WRONG — store all 20 fields of the working table:
STORE [_AllOrderData] INTO [lib://QVDs/orders.qvd] (qvd);

// RIGHT — narrow to a downstream-only table, then store:
[_OrdersSubset]:
LOAD order_id, order_date, customer_id, amount, region
RESIDENT [_AllOrderData];

STORE [_OrdersSubset] INTO [lib://QVDs/orders.qvd] (qvd);
DROP TABLE [_OrdersSubset];
```

This is especially worthwhile in QVD generator/consumer architectures: a narrow generator output reduces every consumer's load time.

---

## Partial Reload and QVD Loads

Partial reload runs only LOAD/SELECT statements marked with `ADD`, `REPLACE`, or `MERGE` prefixes — every other statement is skipped. This interacts with QVD operations:

| Prefix | Behavior on partial reload | Behavior on full reload |
|---|---|---|
| `ADD` | Runs; rows append to existing table (or new table is created) | Runs |
| `REPLACE` | Runs; existing table is dropped before the load | Runs |
| `MERGE` | Runs; uses operation markers to insert/update/delete rows | Runs |
| (no prefix) | Skipped | Runs |

The implication for QVDs: a script that builds QVDs from sources and is meant to support partial reload must use `ADD LOAD` / `ADD CONCATENATE LOAD` for the source-to-table-to-STORE chain, otherwise partial reload skips it entirely and nothing happens.

```qlik
// Partial-reload-friendly extract:
[Sales]:
ADD CONCATENATE LOAD * FROM [lib://QVDs/Sales.qvd] (qvd);          // load existing

ADD CONCATENATE SQL SELECT * FROM sales WHERE modified > '$(vLast)'; // append new

ADD STORE * FROM [Sales] INTO [lib://QVDs/Sales.qvd] (qvd);          // overwrite QVD
```

`MERGE LOAD` in particular reads a change-log-style table where each row has an operation marker (insert / update / delete) and applies the right action to the target. Useful when the source provides change events; less applicable when the source is a snapshot.

Reference: help.qlik.com Cloud — Partial reload; ADD, REPLACE, and MERGE load prefixes.

---

## Binary Load

`binary [app];` copies the entire data model (and section access) from another app. Rules:

- Must be the **first statement** in the script — before SET statements.
- Only one binary statement per script.
- Loads data tables and section access only. Does NOT copy variables, sheets, master items, or visualizations.
- Does NOT cascade reloads — the consumer is a snapshot of the generator's last-saved state at the moment the consumer reloads.

Syntax depends on platform:

```qlik
// Qlik Cloud — app GUID:
binary [a1b2c3d4-5e6f-7890-abcd-ef1234567890];

// Client-managed — .qvf via folder data connection:
binary [lib://Apps/Generator.qvf];
```

Decision framing — when binary load is the right choice versus generator/consumer with QVDs — is in `qlik-data-modeling` → `references/multi-app-architecture.md`.

Reference: help.qlik.com Cloud — Binary statement.

---

## Cross-References

- **`incremental-load-patterns.md`** (sibling reference file) — full working code for insert-only, insert/update, insert/update/delete, and dual-timestamp SCD2 patterns; all use the QVD mechanics described here.
- **`references/sql-constructs.md` Section 2.1** — NoConcatenate failure modes including the INLINE auto-concatenation trap.
- **`qlik-performance` SKILL.md** — decision framing for optimized load, redundant-disk-read elimination, narrow-before-STORE rationale, memory-aware QVD layer design.
- **`qlik-data-modeling` → `references/multi-app-architecture.md`** — when to split a single app into generator/consumer (or further), reload chaining between apps, binary load tradeoffs.
- **`SKILL.md` Section 15** — EXISTS symbol-space behavior (cross-table contamination, self-referencing dedup) with worked examples.

---

## Tier-1 References

- help.qlik.com Cloud — Working with QVD files: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/work-with-QVD-files.htm
- help.qlik.com Cloud — Exists() function: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/InterRecordFunctions/Exists.htm
- help.qlik.com Cloud — Store, LOAD, Binary statements and ADD/REPLACE/MERGE load prefixes (Script statements and keywords section).
