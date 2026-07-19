# Error Handling and Logging

Canonical reference for script-layer error detection, halt/continue control, milestone logging, and field-value inspection at script time. Covers TRACE statement mechanics (including the semicolon trap), the `ScriptError` vs `ScriptErrorCount` distinction, `ErrorMode` semantics, file-existence guards, and how the production `error-handling.qvs` framework relates to standalone diagnostic patterns.

## TRACE — Milestone Logging

`TRACE === Phase: Extract ===;` for milestones. `TRACE Rows loaded: $(vRowCount);` for row counts.

### Semicolon trap inside the message

Semicolons inside the message text are consumed by the parser unless the whole text is quoted. Qlik treats `;` as the statement terminator outside any quoted string, and TRACE accepts an unquoted argument by default — so a bare `;` in the message ends the statement early and the words that follow parse as an unknown statement.

Two safe options:

- **(a) Use commas, periods, or dashes as in-text separators:**
  ```qlik
  // WRONG -- embedded ; terminates the statement early:
  TRACE Loaded $(vRows); see diagnostics for detail;

  // RIGHT (a) -- period or dash as separator:
  TRACE Loaded $(vRows). See diagnostics for detail;
  TRACE Loaded $(vRows) -- see diagnostics for detail;
  ```

- **(b) Wrap the entire trace text in single quotes** so the `;` sits inside a string literal:
  ```qlik
  // RIGHT (b) -- quoted argument tolerates embedded ;
  TRACE 'Loaded $(vRows); see diagnostics for detail';
  ```

Treat TRACE text the way you'd treat any other Qlik string argument — when in doubt, quote it.

## ScriptError vs ScriptErrorCount

Do not confuse these two variables — they have different semantics and lifetimes.

- **`ScriptError`** is a **dual value** (numeric error code + text component) reflecting only the **most recent statement**. It is reset to 0 after every successfully executed statement. Because it resets, it cannot detect errors across multiple operations — only the immediately preceding one.
- **`ScriptErrorCount`** is an **integer counter** that is **cumulative** across the entire reload. It increments with each failed statement and is never reset mid-reload.

### Snapshot pattern for per-operation error detection

For per-operation error detection across multiple statements, snapshot the count: `LET vPreErrors = ScriptErrorCount;` before an operation and compare `IF ScriptErrorCount > $(vPreErrors)` after.

A plain `IF ScriptErrorCount > 0` check after the second operation returns true even if only the first operation failed. See `script-templates/error-handling.qvs` for the correct pattern.

```qlik
LET vPreErrors = ScriptErrorCount;

[Orders]:
SQL SELECT order_id, customer_id, order_date, amount
FROM orders;

IF ScriptErrorCount > $(vPreErrors) THEN
    LET vLastError = ScriptError;
    TRACE [CRITICAL] Failed to load Orders. Error: $(vLastError);
    // Do NOT store to QVD on error -- preserve previous good data
ELSE
    STORE [Orders] INTO [lib://QVDs/Orders.qvd] (qvd);
    TRACE [OK] Orders loaded successfully;
END IF
```

### ScriptErrorList

Concatenated list of all errors, line-feed separated. Use for logging at end-of-reload summary.

## Dollar-Sign Apostrophe-Expansion Trap

Dollar-sign expansion happens **before** the script statement is parsed (help.qlik.com: "The replacement is made just before the script statement or the expression is evaluated" — [Use of variables in the script](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/use-variables-in-script.htm)). Embedding `$(varname)` inside a single-quoted string literal — the common `'$(varname)' AS Field` or `'$(varname)'` CALL-argument shape — produces broken script when the variable's value contains an apostrophe: the expanded text terminates the literal early and the parser fails.

This trap routinely surfaces in error logging because `ScriptError` text from databases contains apostrophes (e.g., `"Can't open file"`), the variable lands inside a literal that the LET or CALL or LOAD then fails to parse, and the failure happens inside the very subroutine designed to capture errors.

**Canonical fixes:**

- **Inside LOAD (bracketed INLINE LOAD).** Replace `'$(varname)' AS Field AUTOGENERATE 1` with a bracketed INLINE LOAD using a delimiter that is uncommon in the data (`|` is conventional). Inside the bracketed block, expanded text is data — apostrophes are literal characters, not string-literal delimiters. CONCATENATE-LOAD RESIDENT into the target log table afterwards. Use `NoConcatenate` on the temp row so a matching-schema target does not auto-merge it ([qlik-load-script § 14](../SKILL.md#14-noconcatenate-and-auto-concatenation)). The fix lives in `script-templates/error-handling.qvs` at `SUB LogMessage` — read it before applying the pattern elsewhere.
- **Inside CALL (bare variable reference).** Replace `CALL Sub('$(varname)')` with `CALL Sub(varname)`. Qlik passes the variable's value to the SUB without re-expanding into a single-quoted literal, so apostrophes survive (help.qlik.com: [Sub statement](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptControlStatements/Sub.htm) — variable arguments have copy-out semantics). Static labels like `'CRITICAL'` stay as plain literals.
- **Inside LET (route through INLINE LOAD + Peek).** Replace `LET vOut = 'prefix: ' & '$(vIn)' & ...;` with a bracketed INLINE LOAD that builds the assembled string inside an AS-expression (data values flow in as fields, prefixes stay as parsed literals), then `Peek` the result into `vOut`. `Chr(39) & vVar & Chr(39)` is occasionally workable in expression contexts but does not solve the upstream `$(...)` expansion-into-literal problem; prefer the INLINE LOAD route.

**Residual limits.** The bracketed INLINE LOAD pattern fails when the variable value contains `]` (closes the bracket early), the chosen delimiter, or a newline. These are uncommon in caller-supplied phase tags and database error text but possible in arbitrary external strings. Document the assumption near the SUB and ask callers to pre-substitute risky characters if their inputs may include them. Worked examples and the verified mechanism are in `script-templates/error-handling.qvs` (`SUB LogMessage`, `SUB CheckError`).

## ErrorMode — Halt vs Continue

`SET ErrorMode = 1;` is the default in Qlik Sense and Qlik Cloud.

| Mode | Behavior | When to Use |
|---|---|---|
| `ErrorMode = 0` | Ignore the failure and continue the script | Non-critical fallback paths; requires careful `ScriptErrorCount` checking to detect problems |
| `ErrorMode = 1` (default) | Halt the script on error. In interactive QlikView this prompts the user; in Qlik Sense/Cloud batch reloads this stops the reload | Production reloads — default behavior is correct |
| `ErrorMode = 2` | Immediately trigger an "Execution of script failed" error and stop, with no user prompt even in interactive contexts | Hard-stop semantics regardless of environment |

`ErrorMode = 0` is the only mode that leaves the burden of error detection on the developer. After every operation that could fail, snapshot `ScriptErrorCount` and check it explicitly.

## File Existence Guards

Check before loading to avoid hard-fails on missing files:

```qlik
IF NOT IsNull(FileTime('lib://path/file.qvd')) THEN
    [Orders]: LOAD * FROM [lib://path/file.qvd] (qvd);
ELSE
    TRACE [WARNING] file.qvd not present -- skipping Orders load;
END IF
```

`FileTime()` returns the last-modified timestamp of a file. NULL means the file does not exist (or the connection cannot reach it). Pairs well with the placeholder pattern for blocked dependencies.

## Field Value Inspection at Script Time

To get min/max of a loaded field, use a Resident LOAD into a temp table and Peek the values:

```qlik
[_Temp]:
LOAD Min(Field) AS _min, Max(Field) AS _max
RESIDENT MyTable;

LET vMin = Peek('_min', 0, '_Temp');
LET vMax = Peek('_max', 0, '_Temp');

DROP TABLE [_Temp];
```

For symbol table iteration, use `FieldValue('Field', n)` with `FieldValueCount('Field')`.

**`fieldvaluelist` is a `FOR EACH` loop keyword** (like `filelist` and `dirlist`), not a general-purpose function — it cannot be used in LET assignments or as an argument to other functions.

## Framework vs Standalone — Pick One

See `script-templates/error-handling.qvs` for the error handling and logging framework (preferred for production scripts). See `diagnostic-patterns.md` (sibling reference file) for standalone TRACE templates and validation queries.

**These are alternatives, not complements.** If using `error-handling.qvs`, use its `LogRowCount` subroutine. The standalone `LogLoadCount` in `diagnostic-patterns.md` is for scripts that don't include the full framework. Mixing them duplicates milestone logs and obscures which subroutine actually fired.

## See Also

- `script-templates/error-handling.qvs` — production framework with `LogRowCount`, error checking, and standard milestone logging
- `diagnostic-patterns.md` § ScriptError Handling — standalone error-check pattern with worked example
- `../SKILL.md` § 13 — overview entry point that links here
