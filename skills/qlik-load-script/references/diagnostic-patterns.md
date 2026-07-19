# Diagnostic and Validation Patterns

TRACE statement templates, row count logging, post-load validation queries, and data quality check patterns for Qlik Sense load scripts.

---

## TRACE Statement Templates

TRACE writes a message to the script execution log. Use it for milestone tracking, variable inspection, and row count logging. TRACE output is visible in the reload dialog and in the script execution log file.

**Critical syntax rule: `;` terminates a TRACE statement unless the whole text is quoted.** Qlik treats `;` as the statement terminator outside any quoted string, and TRACE accepts an unquoted argument by default — so a bare `;` in the message ends the statement early. Anything after that `;` parses as a separate (and usually invalid) statement, causing a reload error. Two safe options: (a) use commas, periods, or dashes as in-text separators; (b) wrap the entire trace text in single quotes so the `;` sits inside a string literal.

```qlik
// WRONG -- the embedded semicolon ends the TRACE early;
// "See diagnostics" then parses as an unknown statement
TRACE Loaded $(vRows); see diagnostics for detail;

// RIGHT (option a) -- comma, period, or dash separator
TRACE Loaded $(vRows). See diagnostics for detail;
TRACE Loaded $(vRows) -- see diagnostics for detail;
TRACE Loaded $(vRows), see diagnostics for detail;

// RIGHT (option b) -- wrap the whole text in single quotes
TRACE 'Loaded $(vRows); see diagnostics for detail';
```

Treat TRACE text the way you'd treat any other Qlik string argument — when in doubt, quote it.

### Phase Milestone Tracing

```qlik
TRACE === Starting Phase: Extract ===;
TRACE === Starting Phase: Transform ===;
TRACE === Starting Phase: Model Load ===;
TRACE === Starting Phase: Calendar ===;
TRACE === Starting Phase: Diagnostics ===;
TRACE === Reload Complete ===;
```

### Row Count Tracing After LOAD

```qlik
// After every significant LOAD, capture and trace the row count:
[Customers]:
LOAD * FROM [lib://QVDs/Customers.qvd] (qvd);
LET vRowCount = NoOfRows('Customers');
TRACE Customers loaded: $(vRowCount) rows;

// After incremental merge:
LET vNewRows = NoOfRows('_Changed');
TRACE Changed records from source: $(vNewRows);
CONCATENATE([_Changed])
LOAD * FROM [lib://QVDs/data.qvd] (qvd) WHERE NOT EXISTS(key_field);
LET vTotalRows = NoOfRows('_Changed');
TRACE Total records after merge: $(vTotalRows);
```

### Variable Value Tracing

```qlik
TRACE vLastExecTime = $(vLastExecTime);
TRACE vThisExecTime = $(vThisExecTime);
TRACE vFiscalYearStartMonth = $(vFiscalYearStartMonth);
```

### Conditional Tracing for Debugging

```qlik
// Only trace when debugging is enabled
SET vDebug = 1;

IF $(vDebug) = 1 THEN
    // $(=expr) inside TRACE forces dollar-sign expansion to evaluate
    // the expression at TRACE time. Without the = sign, $(NoOfRows(...))
    // would look for a variable named "NoOfRows(...)" and expand to nothing.
    TRACE [DEBUG] _TempTable row count: $(=NoOfRows('_TempTable'));
    TRACE [DEBUG] Total fields in model: $(=NoOfFields());
END IF
```

### Timestamp Tracing for Performance Measurement

```qlik
LET vPhaseStart = Now();
// ... expensive operation ...
LET vPhaseEnd = Now();
LET vPhaseDuration = Interval($(vPhaseEnd) - $(vPhaseStart), 'hh:mm:ss');
TRACE Extract phase duration: $(vPhaseDuration);
```

---

## Row Count Logging Table

Capture row counts after every significant LOAD into a persistent log table. This enables post-load comparison of expected vs. actual row counts.

**If using `error-handling.qvs`:** Use the `LogRowCount` subroutine from that framework instead of this standalone pattern. The error-handling framework logs to `_ReloadLog` with severity levels and integrates with CheckError. Do NOT include both, as the duplicate SUB name will cause a collision.

**Standalone pattern** (when NOT using error-handling.qvs):

```qlik
// Initialize log table at script start
[_LoadLog]:
LOAD * INLINE [
    LogTimestamp, TableName, Operation, RowCount
] (delimiter is ',');

// After each significant LOAD, append a log entry:
SUB LogLoadCount(vLogTable, vLogOperation)
    LET vLogRows = NoOfRows('$(vLogTable)');
    LET vLogTime = Timestamp(Now(), 'YYYY-MM-DD hh:mm:ss');

    // Apostrophe-safety: build the row via bracketed INLINE LOAD (with
    // a `|` delimiter), then CONCATENATE-LOAD RESIDENT into _LoadLog.
    // The previous AUTOGENERATE form
    //   '$(vLogOperation)' AS Operation, ...
    // expands the variable INSIDE a single-quoted string literal, so an
    // apostrophe in vLogOperation (or any caller-supplied string field)
    // breaks the parse before the LOAD executes. See
    // `error-handling.md` "Dollar-Sign Apostrophe-Expansion Trap" for
    // the class-level recipe. NoConcatenate forces _LogRow standalone —
    // without it the matching 4-field schema silently auto-merges into
    // _LoadLog and the subsequent DROP TABLE fails.
    [_LogRow]:
    NoConcatenate
    LOAD * INLINE [
    LogTimestamp|TableName|Operation|RowCount
    $(vLogTime)|$(vLogTable)|$(vLogOperation)|$(vLogRows)
    ] (delimiter is '|');

    CONCATENATE([_LoadLog])
    LOAD LogTimestamp, TableName, Operation, RowCount
    RESIDENT [_LogRow];

    DROP TABLE [_LogRow];

    TRACE [LOG] $(vLogTable) | $(vLogOperation) | $(vLogRows) rows;
END SUB

// Usage after each LOAD:
[Customers]:
LOAD * FROM [lib://QVDs/Customers.qvd] (qvd);
CALL LogLoadCount('Customers', 'QVD Load');

[Orders]:
SQL SELECT * FROM orders;
CALL LogLoadCount('Orders', 'SQL Extract');

// At script end -- store the log for post-load inspection
STORE [_LoadLog] INTO [lib://QVDs/Diagnostics/LoadLog.qvd] (qvd);
DROP TABLE [_LoadLog];
```

### Using Row Counts for Validation

Compare actual row counts against expected counts from the source profile:

```qlik
// Expected counts from source profile (set during configuration)
SET vExpectedCustomers = 150000;
SET vExpectedOrders = 2500000;

// After loading
LET vActualCustomers = NoOfRows('Customers');
IF $(vActualCustomers) < $(vExpectedCustomers) * 0.9 THEN
    TRACE [WARNING] Customers row count $(vActualCustomers) is more than 10%% below expected $(vExpectedCustomers);
END IF
IF $(vActualCustomers) > $(vExpectedCustomers) * 1.5 THEN
    TRACE [WARNING] Customers row count $(vActualCustomers) is more than 50%% above expected $(vExpectedCustomers);
END IF
```

Note: `%%` is required in TRACE to output a literal `%` character.

---

## Post-Load Validation Queries

These queries produce diagnostic tables that can be inspected in the data model viewer or exported for review. They run AFTER all data is loaded and before the final model is stored.

### Null Rate Check Per Field

```qlik
// Check null rate for key fields and critical dimensions
[_Diag_NullRate]:
LOAD
    'Customers' AS DiagTable,
    'Customer.Key' AS DiagField,
    Count([Customer.Key]) AS NonNullCount,
    NoOfRows('Customers') AS TotalRows,
    NoOfRows('Customers') - Count([Customer.Key]) AS NullCount,
    Round((NoOfRows('Customers') - Count([Customer.Key])) / NoOfRows('Customers') * 100, 0.01) AS NullPct
RESIDENT [Customers];

// Add more fields to check by concatenating:
CONCATENATE([_Diag_NullRate])
LOAD
    'Customers' AS DiagTable,
    'Customer.Region' AS DiagField,
    Count([Customer.Region]) AS NonNullCount,
    NoOfRows('Customers') AS TotalRows,
    NoOfRows('Customers') - Count([Customer.Region]) AS NullCount,
    Round((NoOfRows('Customers') - Count([Customer.Region])) / NoOfRows('Customers') * 100, 0.01) AS NullPct
RESIDENT [Customers];
```

### Key Uniqueness Check

```qlik
// Detect duplicate keys (should return 0 rows if keys are unique)
// Uses preceding LOAD: inner aggregates, outer filters (replaces HAVING)
[_Diag_DuplicateKeys]:
LOAD [Customer.Key], KeyCount
WHERE KeyCount > 1;
LOAD [Customer.Key], Count([Customer.Key]) AS KeyCount
RESIDENT [Customers]
GROUP BY [Customer.Key];

LET vDuplicates = NoOfRows('_Diag_DuplicateKeys');
IF $(vDuplicates) > 0 THEN
    TRACE [ERROR] Found $(vDuplicates) duplicate Customer.Key values!;
ELSE
    TRACE [OK] Customer.Key is unique;
    DROP TABLE [_Diag_DuplicateKeys];
END IF
```

### Referential Integrity Check

```qlik
// Find orders referencing non-existent customers (orphaned records)
[_CustomerKeys]:
LOAD DISTINCT [Customer.Key] AS _custkey_lookup RESIDENT [Customers];

[_Diag_OrphanedOrders]:
NoConcatenate
LOAD [Order.Key], [Customer.Key] AS OrphanedCustomerKey
RESIDENT [Orders]
WHERE NOT EXISTS(_custkey_lookup, [Customer.Key]);

DROP TABLE [_CustomerKeys];

LET vOrphans = NoOfRows('_Diag_OrphanedOrders');
IF $(vOrphans) > 0 THEN
    TRACE [WARNING] Found $(vOrphans) orders referencing non-existent customers;
ELSE
    TRACE [OK] All orders reference valid customers;
    DROP TABLE [_Diag_OrphanedOrders];
END IF
```

Note: Uses the aliased EXISTS pattern (`_custkey_lookup`) to avoid symbol space contamination.

### Value Distribution Sample

```qlik
// Top 10 values per dimension field (useful for data discovery)
[_Diag_TopValues]:
LOAD [Customer.Region], Count([Customer.Key]) AS RegionCount
RESIDENT [Customers]
GROUP BY [Customer.Region]
ORDER BY RegionCount DESC;

// Use RowNo() to limit to top 10 in a preceding LOAD if needed:
[_Diag_Top10]:
NoConcatenate
LOAD * WHERE RowNo() <= 10;
LOAD [Customer.Region], RegionCount
RESIDENT [_Diag_TopValues]
ORDER BY RegionCount DESC;

DROP TABLE [_Diag_TopValues];
```

---

## ScriptError Handling

### Checking After Critical Operations

ScriptErrorCount is **cumulative** across the entire reload. Use a pre-operation snapshot to isolate errors to the most recent operation. For the full error-handling framework with CheckError subroutine, see `script-templates/error-handling.qvs`.

```qlik
// After a database connection load:
LET vPreErrors = ScriptErrorCount;

[Orders]:
SQL SELECT order_id, customer_id, order_date, amount
FROM orders;

IF ScriptErrorCount > $(vPreErrors) THEN
    LET vLastError = ScriptError;
    TRACE [CRITICAL] Failed to load Orders from database. Error: $(vLastError);
    // Do NOT store to QVD on error -- preserve previous good data
ELSE
    STORE [Orders] INTO [lib://QVDs/Orders.qvd] (qvd);
    TRACE [OK] Orders loaded and stored successfully;
END IF
```

### Capturing Full Error Details

```qlik
// End-of-script error summary (cumulative count is fine here since
// we're checking whether ANY errors occurred during the entire reload)
IF ScriptErrorCount > 0 THEN
    LET vErrorCount = ScriptErrorCount;
    LET vLastError = ScriptError;
    LET vAllErrors = ScriptErrorList;

    TRACE [CRITICAL] Reload encountered $(vErrorCount) errors;
    TRACE [CRITICAL] Last error: $(vLastError);
    // ScriptErrorList contains all errors separated by line feeds

    // Apostrophe-safety: vLastError is ScriptError text, which from
    // databases routinely contains apostrophes (e.g., "Can't connect").
    // The previous form
    //   '$(vLastError)' AS LastError
    // expanded the apostrophe into a single-quoted string literal,
    // breaking the LOAD parse inside the error-capture block itself.
    // FIX: route the value through a bracketed INLINE LOAD with `|`
    // delimiter, then CONCATENATE-LOAD RESIDENT into _ErrorLog. See
    // `error-handling.md` "Dollar-Sign Apostrophe-Expansion Trap".
    LET vErrorTimestamp = Timestamp(Now(), 'YYYY-MM-DD hh:mm:ss');
    [_ErrorLogRow]:
    NoConcatenate
    LOAD * INLINE [
    ErrorTimestamp|ErrorCount|LastError
    $(vErrorTimestamp)|$(vErrorCount)|$(vLastError)
    ] (delimiter is '|');

    [_ErrorLog]:
    NoConcatenate
    LOAD ErrorTimestamp, ErrorCount, LastError
    RESIDENT [_ErrorLogRow];

    DROP TABLE [_ErrorLogRow];

    STORE [_ErrorLog] INTO [lib://QVDs/Diagnostics/ErrorLog.qvd] (qvd);
    DROP TABLE [_ErrorLog];
END IF
```

---

## File Existence Checks

### Check QVD Before Loading

```qlik
// FileTime returns NULL if the file does not exist
IF NOT IsNull(FileTime('lib://QVDs/Customers.qvd')) THEN
    [Customers]:
    LOAD * FROM [lib://QVDs/Customers.qvd] (qvd);
    TRACE Loaded existing Customers QVD;
ELSE
    TRACE [WARNING] Customers.qvd does not exist -- performing full extract;
    [Customers]:
    SQL SELECT * FROM customers;
    STORE [Customers] INTO [lib://QVDs/Customers.qvd] (qvd);
END IF
```

### Check Connection Availability

```qlik
// Attempt a lightweight query to test connection
LET vPreConnErrors = ScriptErrorCount;

[_ConnectionTest]:
SQL SELECT 1 AS ConnectionOK;

IF ScriptErrorCount > $(vPreConnErrors) THEN
    TRACE [CRITICAL] Database connection failed -- using cached QVDs;
    // Fall back to QVD-only mode
    LET vUseCachedQVDs = 1;
ELSE
    LET vUseCachedQVDs = 0;
    DROP TABLE [_ConnectionTest];
END IF
```

For a reusable connection test with logging, see TestConnection in `script-templates/error-handling.qvs`.

---

## Complete Diagnostic Script Section

A complete diagnostic section to append at the end of a reload script:

```qlik
// ============================================================
// POST-LOAD DIAGNOSTICS
// ============================================================
TRACE === Starting Phase: Diagnostics ===;

// --- Table summary ---
LET vTableCount = NoOfTables();
TRACE Total tables in data model: $(vTableCount);

FOR vDiagIdx = 0 TO $(vTableCount) - 1
    LET vDiagTableName = TableName($(vDiagIdx));
    LET vDiagRowCount = NoOfRows('$(vDiagTableName)');
    LET vDiagFieldCount = NoOfFields('$(vDiagTableName)');
    TRACE Table: $(vDiagTableName) | Rows: $(vDiagRowCount) | Fields: $(vDiagFieldCount);
NEXT vDiagIdx

// --- Key field null checks ---
// Add null checks for every key field in the model
// (Replace with actual key field names from the data model specification)

// --- Row count validation ---
// Compare against expected counts from source profile
// (Replace with actual expected counts)

// --- Referential integrity ---
// Add orphaned record checks for every fact-to-dimension relationship
// (Replace with actual table and key field references)

TRACE === Diagnostics Complete ===;
TRACE Reload finished at $(=Timestamp(Now(), 'YYYY-MM-DD hh:mm:ss'));
```
