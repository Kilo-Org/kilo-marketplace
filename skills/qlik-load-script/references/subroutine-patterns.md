# Subroutine Integration

Canonical reference for incorporating external `.qvs` libraries into a Qlik script: include directives, `CALL` syntax, variable scoping rules (the single biggest scoping trap in Qlik), `FOR EACH` iteration patterns, phantom-field detection after subroutine return, and composite key workarounds.

## Including External Files

`$(Must_Include=lib://Connection/path/file.qvs);` fails the reload if the file is missing.

`$(Include=lib://Connection/path/file.qvs);` silently skips a missing file. Useful for optional includes (e.g., environment-specific overrides) but unsafe for any include the script actually depends on.

**Rule:** Use `Must_Include` for required includes. Use `Include` only for genuinely optional ones, and pair it with a `TRACE` warning so a silent skip is visible in the reload log.

## Calling Subroutines

```qlik
$(Must_Include=lib://Shared/standard-libs.qvs);
CALL MySub(param1, param2);
```

`CALL` invokes a subroutine declared between `SUB` and `END SUB`. Arguments are positional. The `END SUB` keyword must appear on its own logical statement — missing it is the most common reason for a "subroutine not found" error elsewhere in the script.

## Variable Scoping — The Critical Gotcha

Qlik variables are primarily global. The single exception, documented by help.qlik.com:

- **Variables created inside a SUB with `LET` or `SET`** are global. They persist after the subroutine returns and will overwrite any caller variable of the same name.
- **Formal parameters declared in the SUB signature** (e.g., `SUB MySub(pArg1, pArg2)`) are locally scoped during execution. However, their behavior at `END SUB` depends on whether a matching actual argument was supplied:
  - **No matching actual argument (extra formal parameter):** initialized to NULL at SUB entry, value is discarded at `END SUB`. Truly local — safe working variable, no leak.
  - **Matching actual argument supplied as a variable name:** copy-out semantics apply. Per help.qlik.com Sub statement: "If a variable is used as parameter in a CALL, ... the parameter is copied back to the calling variable upon return." The parameter's value at `END SUB` is written back to the caller's variable. NOT purely local.

### Practical rule

Use extra formal parameters (declared beyond the CALL arguments) as purely local working variables — they are the only way to get true locality. Use matching parameters intentionally when you need a SUB to return computed values to the caller. Use naming prefixes (e.g., `vSub_MySub_Counter`) for `LET`/`SET` variables that intentionally stay global. **Never rely on a bare `LET` inside a SUB for local state** — it pollutes the caller's variable space.

```qlik
// WRONG -- vCounter leaks to caller and overwrites any global of the same name:
SUB CountRows(pTable)
    LET vCounter = NoOfRows('$(pTable)');
    TRACE Table $(pTable) has $(vCounter) rows;
END SUB

// CASE A -- pCounter declared but no second argument passed:
// pCounter is initialized to NULL at SUB entry, used locally, and discarded at END SUB.
// Nothing leaks to the caller. Truly local working variable.
CALL CountRows('Customers');           // only one actual argument

SUB CountRows(pTable, pCounter)
    LET pCounter = NoOfRows('$(pTable)');
    TRACE Table $(pTable) has $(pCounter) rows;
END SUB

// CASE B -- caller supplies a variable name as the second argument:
// Per help.qlik.com Sub statement: "If a variable is used as parameter in a CALL,
// ... the parameter is copied back to the calling variable upon return."
// pCounter's value at END SUB is assigned back to vMyCounter in the caller.
// This is copy-out semantics -- NOT purely local.
LET vMyCounter = 0;
CALL CountRows('Customers', vMyCounter);
// After the call, vMyCounter = NoOfRows('Customers') in the caller's scope.
```

**Rule (source: help.qlik.com Sub..End Sub):**
- Extra formal parameters with NO matching actual argument → NULL-initialized, truly local, discarded at `END SUB`. Safe working variables.
- Formal parameters with a matching actual argument passed as a variable name → value is **copied back** to the caller's variable at `END SUB`. The SUB effectively returns a value through that parameter.

Use Case A (declare extra params beyond the CALL arguments) for purely local state. Use Case B intentionally when you want the SUB to return a computed value to the caller through a parameter.

## FOR EACH Loops

Iterate over file lists or value lists:

```qlik
FOR EACH vFile IN FileList('lib://Data/*.qvd')
    [_AllData]:
    LOAD * FROM [$(vFile)] (qvd);
NEXT vFile
```

**Cloud caveat:** Two specific behaviors in Qlik Cloud differ from on-prem:

1. **Connection type.** `FileList()` in Cloud must target a Data Files connection (`lib://<Space>:DataFiles/...`). Web storage and some third-party connectors do not support wildcard filter masks, so the function returns only individually addressable files or fails outright on those connections.
2. **Recursion semantics.** Cloud `FileList('lib://Space:Folder/*.qvd')` includes files in subfolders of the named folder, not only the immediate folder — the opposite of on-prem behavior, where the wildcard matches only the immediate folder. This is a documented behavioral difference (community-confirmed, undocumented as of mid-2026) and routinely surprises scripts ported from Qlik Sense on Windows. Reference: https://community.qlik.com/t5/Move-to-Qlik-Cloud-Analytics/FileList-works-differently-between-Sense-and-Cloud/td-p/2520108

If you need immediate-folder-only iteration in Cloud, either filter the returned paths (count `/` separators in the returned filename and skip any beyond the expected depth) or maintain an explicit file manifest. For nested directory trees, iterate one level at a time with `DirList` plus `FileList`, recursing explicitly rather than relying on a single wildcard.

For value lists:

```qlik
FOR EACH vSource IN 'orders', 'shipments', 'returns'
    [$(vSource)]:
    LOAD * FROM [lib://RawData/$(vSource).qvd] (qvd);
NEXT vSource
```

## Phantom Field Prevention

Some shared subroutines initialize empty inline tables. If column parameters are wildcards or improperly specified, phantom fields appear in results. Always verify subroutine output contains only expected fields.

After calling a subroutine, check by iterating fields in script:

```qlik
FOR vFldIdx = 1 TO NoOfFields('$(vResultTable)')
    LET vFldName = FieldName($(vFldIdx), '$(vResultTable)');
    TRACE Field $(vFldIdx): $(vFldName);
NEXT vFldIdx
```

If a phantom field appears, `DROP FIELD [PhantomFieldName] FROM [$(vResultTable)];` after the subroutine returns. Document the workaround near the CALL site so future maintainers understand why the explicit DROP exists.

## Composite Key Workaround

When a subroutine handles only single keys but you need composite keys, two options:

- **Concatenate before, split after.** Build a composite string with a safe delimiter (`'|'` is conventional), pass it as a single key, and split back into parts on the return path.
- **Bypass the subroutine.** If the composite logic is simple enough, implement it inline rather than fighting the single-key signature.

```qlik
// Concatenate before call:
[Orders_Pre]:
LOAD
    [Region] & '|' & [Product] AS [%CompositeKey],
    [Amount]
RESIDENT [Orders];

CALL StandardKeyEnrichment('Orders_Pre', '%CompositeKey');

// Split after call (if the subroutine preserved the key):
[Orders_Final]:
LOAD
    SubField([%CompositeKey], '|', 1) AS [Region],
    SubField([%CompositeKey], '|', 2) AS [Product],
    [Amount]
RESIDENT [Orders_Pre];
DROP TABLE [Orders_Pre];
```

The delimiter must be a character that cannot appear in either source field. `|` is conventional; use a different character (or a multi-character separator) if `|` is a valid data value.

## See Also

- `../SKILL.md` § 18 — overview entry point that links here
- For brownfield platforms with shared subroutine libraries, document the contract (signatures, side effects, phantom fields) before relying on subroutines in new scripts
