# Incremental Load Pattern Catalog

Complete incremental load patterns for Qlik Sense. Each pattern includes working code, anti-patterns with specific failure modes, and edge cases. For the ready-to-use SCD Type 2 template, see `script-templates/dual-timestamp-incremental.qvs`.

---

## QVD State Management

All incremental patterns require tracking the last successful load time. Store this in a state QVD:

```qlik
// At script start -- load previous execution time
LET vThisExecTime = Now();

IF NOT IsNull(FileTime('lib://QVDs/ReloadState.qvd')) THEN
    [_State]:
    LOAD LastExecTime
    FROM [lib://QVDs/ReloadState.qvd] (qvd);
    LET vLastExecTime = Peek('LastExecTime', 0, '_State');
    DROP TABLE [_State];
ELSE
    // First load -- set to earliest possible date
    LET vLastExecTime = '1900-01-01 00:00:00';
END IF

// At script end (after successful STORE) -- persist state.
// Uses = 0 as a conservative end-of-script guard. For per-operation
// checks, use the pre-error comparison pattern (see error-handling.qvs).
IF ScriptErrorCount = 0 THEN
    [_State]:
    LOAD '$(vThisExecTime)' AS LastExecTime AUTOGENERATE 1;
    STORE [_State] INTO [lib://QVDs/ReloadState.qvd] (qvd);
    DROP TABLE [_State];
END IF
```

### State File Strategy

Projects with multiple source tables need a state management strategy. Two approaches:

**Per-table state files** (`ReloadState_Customers.qvd`, `ReloadState_Orders.qvd`): Each table tracks its own last-load timestamp independently. Simpler to debug, no contention if multiple scripts run concurrently, and works naturally when tables reload on different schedules or in different apps. This is the recommended default.

**Single state table** with columns `[TableName, LastExecTime]`: One QVD holding timestamps for all tables. More compact and provides a single monitoring point. Best when all tables reload together in the same script and you want one place to check reload status.

### Periodic Full-Refresh Cycle

Every incremental load pattern should include a periodic full-refresh as a safety net. Incremental logic can silently drift from truth due to source key resets, missed edge cases in change detection, retroactive updates that fall outside the timestamp window, or bugs in source system change tracking. Schedule a full-refresh cycle (e.g., weekly or monthly) that replaces the entire QVD from a complete source extract. Track the last full-refresh date in the state QVD and force a full load when the interval expires. This catches any accumulated drift without requiring you to identify the specific failure mode.

### Timezone and Source Timestamp Compatibility

`vThisExecTime` and `vLastExecTime` are both produced by `Now()` in the Qlik load script. In Qlik Cloud, `Now()` returns the current time in **UTC** (the reload pod's system clock). On-premises Qlik Sense returns the time in the **server's local timezone**.

When the source database stores timestamps in a different timezone — for example, SQL Server `DATETIME` columns recorded in America/New_York with no UTC offset — the WHERE clause comparison silently drifts by the timezone offset (5–8 hours for US Eastern). On a 1-hour reload schedule, this can cause up to 8 hours of changed records to be missed entirely or re-extracted on every reload.

**This is silent.** No error is raised. Row counts look plausible. The drift accumulates undetected until a periodic full-refresh corrects it.

**Resolution — normalize before comparison. Choose one approach:**

*Option A: Normalize at the source (SQL Server `AT TIME ZONE`)*

Convert the stored timestamp to UTC inside the SQL SELECT. This is the preferred approach because it keeps all timezone logic in one place and does not require changes to state management.

```sql
-- SQL Server: convert a DATETIME stored in Eastern time to UTC
WHERE CONVERT(DATETIME,
      SWITCHOFFSET(
          CONVERT(DATETIMEOFFSET, modified_date) AT TIME ZONE 'Eastern Standard Time',
          '+00:00'))
    >= '$(vLastExecTime)'
```

Note: `AT TIME ZONE` in SQL Server requires SQL Server 2016 or later and a named Windows Time Zone identifier (e.g., `'Eastern Standard Time'`), not an IANA name. The named zone handles DST transitions automatically.

*Option B: Normalize on the Qlik side*

Shift `vLastExecTime` and `vThisExecTime` into the source timezone using `ConvertToLocalTime()` before the SQL is issued. This keeps the SQL simple but requires knowing the source offset at script time.

```qlik
// Add the source-timezone offset before issuing the SQL
// Example: source is UTC-5 (US Eastern Standard Time)
LET vLastExecTime_Source  = ConvertToLocalTime(vLastExecTime,  'Eastern Standard Time');
LET vThisExecTime_Source  = ConvertToLocalTime(vThisExecTime,  'Eastern Standard Time');

// Then use the adjusted variables in the WHERE clause:
// WHERE modified_date >= '$(vLastExecTime_Source)'
//   AND modified_date < '$(vThisExecTime_Source)'
```

`ConvertToLocalTime()` is documented in Qlik help (help.qlik.com) and accepts the same Windows Time Zone identifiers as SQL Server `AT TIME ZONE`. It handles DST shifts automatically.

**If you cannot determine the source timezone**, add a reconciliation query to your diagnostic run that compares the MAX(modified_date) from the source against `vLastExecTime` in UTC. A consistent gap matching the suspected offset confirms the drift.

**Qlik Cloud reload timezone reference:** Qlik Cloud reload pods run in UTC. This is documented on qlik.dev (developer portal, Reload task scheduling). On-premises Qlik Sense inherits the Windows Server timezone; confirm with your infrastructure team before assuming UTC.

### How to Use These Patterns

**Patterns 1-3 are building blocks.** They assume `vLastExecTime` and `vThisExecTime` already exist. You must combine each pattern with the state management block above (or equivalent) to get a complete incremental script. Without state management, the pattern loads new records but never persists the timestamp, so the next reload re-extracts everything.

**The dual-timestamp template** (`script-templates/dual-timestamp-incremental.qvs`) is self-contained. It includes its own state management, configuration variables, and STORE guards. Use it directly for SCD Type 2 sources.

---

## Pattern 1: Insert-Only (Append)

### Scenario
Append-only transaction tables where records are never updated or deleted. Examples: log tables, event streams, financial transaction journals.

### Prerequisite
A monotonically increasing key or a reliable creation timestamp that is never backdated.

### Working Code

```qlik
// ============================================================
// INSERT-ONLY INCREMENTAL: Append new records to existing QVD
// ============================================================

LET vQvdPath = 'lib://QVDs/Transactions.qvd';

IF NOT IsNull(FileTime('$(vQvdPath)')) THEN
    // --- Incremental load ---

    // 1. Load new records from source
    [_NewRecords]:
    SQL SELECT
        transaction_id,
        customer_id,
        transaction_date,
        amount,
        created_at
    FROM transactions
    WHERE created_at >= '$(vLastExecTime)'
      AND created_at < '$(vThisExecTime)';

    LET vNewRows = NoOfRows('_NewRecords');
    TRACE New records from source: $(vNewRows);

    // 2. Load existing QVD (optimized read -- no WHERE, no transforms).
    //    LOAD * avoids maintenance burden: if source SQL changes columns,
    //    this load automatically matches without a separate field list update.
    CONCATENATE([_NewRecords])
    LOAD * FROM [$(vQvdPath)] (qvd);

    LET vTotalRows = NoOfRows('_NewRecords');
    TRACE Total records after merge: $(vTotalRows);

    // 3. Store combined result (guard against any errors during reload)
    IF ScriptErrorCount = 0 THEN
        STORE [_NewRecords] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [_NewRecords];

ELSE
    // --- First load (full extract) ---
    TRACE First load -- full extract from source;

    [_NewRecords]:
    SQL SELECT
        transaction_id,
        customer_id,
        transaction_date,
        amount,
        created_at
    FROM transactions
    WHERE created_at < '$(vThisExecTime)';

    IF ScriptErrorCount = 0 THEN
        STORE [_NewRecords] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [_NewRecords];
END IF
```

### Anti-Pattern: Using Insert-Only on Mutable Tables

```qlik
// WRONG -- source table allows updates but we only capture new records:
SQL SELECT * FROM orders WHERE created_at >= '$(vLastExecTime)';
// Result: If order #1234 was created yesterday (already in QVD) and its
// amount was corrected today, the QVD still has the old amount.
// This is SILENT STALE DATA -- no error, no warning.
```

**Failure mode:** Records updated after initial capture are never refreshed. The QVD permanently contains stale versions. Use the insert/update pattern instead when records can change.

### Edge Case: Source Key Reset

If the source system resets keys (e.g., database restore, table rebuild), the incremental key comparison breaks. The QVD contains records with keys that no longer exist or now point to different data.

**Mitigation:** Include a periodic full-refresh cycle (e.g., weekly) that replaces the entire QVD. Track the last full-refresh date in the state QVD and force a full load when the interval expires.

### QVD Read Mode

The CONCATENATE load of the existing QVD uses an **optimized read** (no WHERE clause, no transforms). This is the fastest incremental pattern.

---

## Pattern 2: Insert/Update

### Scenario
Mutable dimension or fact tables with a reliable modification timestamp. Records can be inserted or updated but not deleted.

### Prerequisite
A `ModifiedDate` or equivalent column that is updated on every change. If the timestamp has date-only granularity (no time component), use `>=` not `>` to avoid missing same-day updates.

### Working Code

```qlik
// ============================================================
// INSERT/UPDATE INCREMENTAL: Merge new and updated records
// ============================================================

LET vQvdPath = 'lib://QVDs/Customers.qvd';

IF NOT IsNull(FileTime('$(vQvdPath)')) THEN
    // --- Incremental load ---

    // 1. Load new and updated records from source
    [Customers]:
    SQL SELECT
        customer_id,
        customer_name,
        email,
        status,
        modified_date
    FROM customers
    WHERE modified_date >= '$(vLastExecTime)'
      AND modified_date < '$(vThisExecTime)';

    LET vChangedRows = NoOfRows('Customers');
    TRACE Changed records from source: $(vChangedRows);

    // 2. Load existing QVD, EXCLUDING records already loaded from source.
    //    WHERE NOT EXISTS forces standard mode -- acceptable tradeoff.
    //    LOAD * is safe here (already standard mode) and avoids a real
    //    production bug: if you add a column to the SQL SELECT above but
    //    forget to update an explicit field list here, every existing
    //    record loses that field after merge. Silent data loss.
    CONCATENATE([Customers])
    LOAD *
    FROM [$(vQvdPath)] (qvd)
    WHERE NOT EXISTS(customer_id);

    LET vTotalRows = NoOfRows('Customers');
    TRACE Total records after merge: $(vTotalRows);

    // 3. Store merged result
    IF ScriptErrorCount = 0 THEN
        STORE [Customers] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [Customers];

ELSE
    // --- First load ---
    [Customers]:
    SQL SELECT customer_id, customer_name, email, status, modified_date
    FROM customers;

    IF ScriptErrorCount = 0 THEN
        STORE [Customers] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [Customers];
END IF
```

### How the Merge Works

1. Load changed records first (they go into the `Customers` table).
2. Load the existing QVD with `WHERE NOT EXISTS(customer_id)`. Since the changed records are already loaded, EXISTS sees their customer_id values. The QVD load skips those rows (old versions).
3. Result: changed records from source + unchanged records from QVD = complete, current dataset.

### Anti-Pattern: Forgetting to Remove Old Versions

```qlik
// WRONG -- loads ALL QVD records including old versions of updated records:
[Customers]:
SQL SELECT * FROM customers WHERE modified_date >= '$(vLastExecTime)';
CONCATENATE([Customers])
LOAD * FROM [lib://QVDs/Customers.qvd] (qvd);
// NO WHERE NOT EXISTS -- old versions of updated records remain!
// Result: DUPLICATE ROWS for every updated record (old + new version).
// Aggregations double-count. Row counts grow on every reload.
```

### Anti-Pattern: Wrong Comparison for Date-Only Granularity

```qlik
// WRONG when modified_date has no time component:
WHERE modified_date > '$(vLastExecTime)'
// If last load ran at 2026-03-01 and a record modified on 2026-03-01,
// the > comparison misses it (2026-03-01 is NOT > 2026-03-01).

// RIGHT -- use >= to include same-day modifications:
WHERE modified_date >= '$(vLastExecTime)'
```

**Failure mode:** Records modified on the same calendar day as the last load are permanently missed. Intermittent and hard to debug.

---

## Pattern 3: Insert/Update/Delete

### Scenario
Tables where records can be inserted, updated, OR deleted. Two approaches depending on whether the source provides a deletion indicator.

### Approach A: Soft Delete Flag

When the source marks deleted records with a flag rather than physically removing them:

```qlik
// ============================================================
// INSERT/UPDATE/DELETE via SOFT DELETE FLAG
// ============================================================

LET vQvdPath = 'lib://QVDs/Products.qvd';

IF NOT IsNull(FileTime('$(vQvdPath)')) THEN
    // 1. Load changed records (includes newly deleted ones)
    [Products]:
    SQL SELECT product_id, product_name, category, price, is_deleted, modified_date
    FROM products
    WHERE modified_date >= '$(vLastExecTime)'
      AND modified_date < '$(vThisExecTime)';

    // 2. Load unchanged records from QVD (LOAD * -- see Pattern 2 note)
    CONCATENATE([Products])
    LOAD *
    FROM [$(vQvdPath)] (qvd)
    WHERE NOT EXISTS(product_id);

    // 3. Remove soft-deleted records before storing
    [Products_Clean]:
    NoConcatenate
    LOAD * RESIDENT [Products]
    WHERE NOT Match(is_deleted, 1, 'Y', 'true');

    DROP TABLE [Products];

    IF ScriptErrorCount = 0 THEN
        STORE [Products_Clean] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [Products_Clean];
ELSE
    // First load -- filter out soft-deleted records at source.
    // Uses same filter logic as the incremental path for consistency.
    [Products]:
    SQL SELECT product_id, product_name, category, price, is_deleted, modified_date
    FROM products
    WHERE is_deleted = 0 OR is_deleted IS NULL;

    // Remove any soft-deleted records using same Match() logic as incremental path
    [Products_Clean]:
    NoConcatenate
    LOAD * RESIDENT [Products]
    WHERE NOT Match(is_deleted, 1, 'Y', 'true');

    DROP TABLE [Products];

    IF ScriptErrorCount = 0 THEN
        STORE [Products_Clean] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [Products_Clean];
END IF
```

### Approach B: Full Key Comparison (INNER JOIN)

When the source physically deletes records (no soft delete flag):

```qlik
// ============================================================
// INSERT/UPDATE/DELETE via FULL KEY COMPARISON
// ============================================================

LET vQvdPath = 'lib://QVDs/Employees.qvd';

IF NOT IsNull(FileTime('$(vQvdPath)')) THEN
    // 1. Load changed records
    [Employees]:
    SQL SELECT employee_id, name, department, hire_date, modified_date
    FROM employees
    WHERE modified_date >= '$(vLastExecTime)'
      AND modified_date < '$(vThisExecTime)';

    // 2. Load unchanged records from QVD (LOAD * -- see Pattern 2 note)
    CONCATENATE([Employees])
    LOAD *
    FROM [$(vQvdPath)] (qvd)
    WHERE NOT EXISTS(employee_id);

    // 3. INNER JOIN against full source key list to remove deleted records
    INNER JOIN([Employees])
    SQL SELECT DISTINCT employee_id FROM employees;

    LET vTotalRows = NoOfRows('Employees');
    TRACE Records after delete check: $(vTotalRows);

    IF ScriptErrorCount = 0 THEN
        STORE [Employees] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [Employees];
ELSE
    [Employees]:
    SQL SELECT employee_id, name, department, hire_date, modified_date
    FROM employees;

    IF ScriptErrorCount = 0 THEN
        STORE [Employees] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [Employees];
END IF
```

### Anti-Pattern: Not Handling Deletes

```qlik
// Using insert/update pattern on a table with physical deletes:
// The QVD retains records that no longer exist in the source.
// These "orphaned" records persist FOREVER across all future loads.
// QVD row count grows unbounded. Deleted entities appear in reports.
```

### Performance Note on INNER JOIN

The `INNER JOIN SQL SELECT DISTINCT key FROM source` loads the full key list on every reload. For very large tables (100M+ rows), this is expensive. Consider running the delete check less frequently (e.g., daily full-key check, hourly insert/update only).

---

## Pattern 4: Dual-Timestamp SCD Type 2 (CRITICAL)

### Scenario
Slowly Changing Dimension Type 2 tables where each record version has `effective_from` and `effective_to` dates. When an entity changes, the old version gets its `effective_to` set, and a new version is created.

### Why This Is the Hardest Pattern

An incremental load must capture TWO categories of changes:

1. **Newly created records:** `effective_from >= last_load_date` (new versions of changed entities, or new entities)
2. **Newly closed records:** `effective_to` changed from NULL/far-future to a real date since last load (previous "current" versions that were superseded)

**Missing condition #2 is silent data loss.** You capture the new version but the QVD still has the old version with `effective_to = NULL` (appearing "current"). The entity shows TWO current versions.

### Working Code

```qlik
// ============================================================
// DUAL-TIMESTAMP SCD TYPE 2 INCREMENTAL LOAD
// Captures BOTH new records AND newly closed records.
// Missing either condition causes silent data loss.
// ============================================================

LET vQvdPath = 'lib://QVDs/Customer_SCD2.qvd';

IF NOT IsNull(FileTime('$(vQvdPath)')) THEN
    // --- Incremental load ---

    // 1. Load ALL changed records using DUAL-TIMESTAMP condition
    [_Changed]:
    SQL SELECT
        surrogate_key,
        business_key,
        customer_name,
        customer_status,
        effective_from,
        effective_to,
        is_current,
        modified_date
    FROM customer_dim
    WHERE effective_from >= '$(vLastExecTime)'
       OR (effective_to IS NOT NULL
           AND effective_to >= '$(vLastExecTime)'
           AND effective_to < '$(vThisExecTime)');

    LET vChangedRows = NoOfRows('_Changed');
    TRACE SCD2 changed records: $(vChangedRows);

    // 2. Load existing QVD, excluding changed surrogate keys.
    //    Must use SURROGATE KEY (unique per row), not business key.
    //    LOAD * -- see Pattern 2 note on field-list maintenance risk.
    CONCATENATE([_Changed])
    LOAD *
    FROM [$(vQvdPath)] (qvd)
    WHERE NOT EXISTS(surrogate_key);

    LET vTotalRows = NoOfRows('_Changed');
    TRACE SCD2 total records after merge: $(vTotalRows);

    // 3. Store merged result
    IF ScriptErrorCount = 0 THEN
        STORE [_Changed] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [_Changed];

ELSE
    // --- First load (full extract) ---
    TRACE SCD2 first load -- full extract;

    [_Changed]:
    SQL SELECT
        surrogate_key,
        business_key,
        customer_name,
        customer_status,
        effective_from,
        effective_to,
        is_current,
        modified_date
    FROM customer_dim;

    IF ScriptErrorCount = 0 THEN
        STORE [_Changed] INTO [$(vQvdPath)] (qvd);
    END IF
    DROP TABLE [_Changed];
END IF
```

### The WHERE Clause Explained

```sql
WHERE effective_from >= '$(vLastExecTime)'              -- Condition 1: new versions
   OR (effective_to IS NOT NULL                          -- Condition 2: closures
       AND effective_to >= '$(vLastExecTime)'            --   closed since last load
       AND effective_to < '$(vThisExecTime)')            --   closed before this load
```

**Condition 1** captures: new entity records, new versions of existing entities.

**Condition 2** captures: the closing of previous "current" versions. When entity X is updated, the old version of X gets its `effective_to` set. Without this condition, the QVD retains the old version with `effective_to = NULL`, making it appear "current."

The `effective_to < vThisExecTime` bound prevents capturing closures during the load window.

### Anti-Pattern: Only Checking effective_from

```qlik
// WRONG -- only captures new records, not closures:
SQL SELECT * FROM customer_dim
WHERE effective_from >= '$(vLastExecTime)';

// When customer "ACME Corp" changes status:
// - New version (effective_from=today) IS captured
// - Old version (effective_to changed to today) is NOT captured
// - QVD still has old version with effective_to=NULL (looks "current")
// - ACME Corp appears TWICE: once Active (wrong) and once Inactive
// This is SILENT DATA LOSS
```

### Anti-Pattern: Using Single MAX Timestamp

```qlik
// WRONG -- many SCD2 implementations only set modified_date on the NEW record,
// not on the closed record. The closed record's modified_date stays unchanged.
SQL SELECT * FROM customer_dim
WHERE modified_date >= '$(vLastExecTime)';
// Same failure: closures missed.
```

**Only use modified_date if you have verified that the source updates it on BOTH the new and closed records.** When in doubt, use the dual-timestamp approach.

### Edge Case: Surrogate Key vs Business Key for EXISTS

```qlik
// WRONG -- business_key has multiple rows in SCD2, EXISTS drops old versions:
WHERE NOT EXISTS(business_key)

// RIGHT -- surrogate_key is unique per row:
WHERE NOT EXISTS(surrogate_key)
```

### Edge Case: Records Created and Closed Between Load Cycles

If a record is created (effective_from = Tuesday) and superseded (effective_to = Wednesday) between Monday and Thursday load cycles, both conditions match but SQL returns the record once. The EXISTS check on the QVD prevents double-loading. No duplication.

---

## QVD Optimized Read Summary

| Pattern | QVD Read Mode | Reason |
|---|---|---|
| Insert-only (CONCATENATE, no WHERE) | **Optimized** | No WHERE clause on QVD load |
| Insert/update (WHERE NOT EXISTS, one-param) | **Optimized** | One-parameter NOT EXISTS preserves optimized read |
| Insert/update/delete (WHERE NOT EXISTS + INNER JOIN) | **Optimized** (QVD load) | One-parameter NOT EXISTS on QVD; INNER JOIN is a separate operation |
| Dual-timestamp SCD2 (WHERE NOT EXISTS, one-param) | **Optimized** | One-parameter NOT EXISTS preserves optimized read |

One-parameter `NOT EXISTS(field)` preserves optimized QVD read. Two-parameter `NOT EXISTS(field1, field2)` forces standard mode. All incremental patterns above use the one-parameter form.

Standard mode is ~10x faster than loading from the database. Optimized mode is ~10x faster than standard QVD read (~100x faster than database).

**NOT EXISTS self-referencing behavior:** One-parameter `NOT EXISTS(field)` checks values already loaded during the current LOAD statement. For incremental patterns, this is actually beneficial: if the source returns a record that also exists in the QVD, the QVD load skips it (the source version was loaded first via CONCATENATE). However, if the source returns duplicate keys, only the first occurrence loads. This is acceptable for key-based incremental patterns where the source key should be unique. See SKILL.md Section 12 for the full explanation and workarounds.

**Strategy for very large QVDs (50M+ rows):** If QVD read performance is the bottleneck and you need the two-parameter EXISTS form (which forces standard mode), split the logic: load the full QVD (optimized, fast), load changed records from source, then deduplicate using RESIDENT LOAD with WHERE NOT EXISTS. The dedup happens in-memory rather than during the QVD file read.
