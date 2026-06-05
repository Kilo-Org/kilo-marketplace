---
name: qor-refactor
description: >-
  KISS Refactor and Simplification Pass that flattens logic, deconstructs bloat, and verifies structural integrity. Use when: (1) Code violates Section 4 Simplicity Razor, (2) Functions exceed 40 lines or files exceed 250 lines, (3) Nesting depth exceeds 3 levels, or (4) General code cleanup needed.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-refactor
---

# /ql-refactor - KISS Simplification Pass

<skill>
  <trigger>/ql-refactor</trigger>
  <phase>IMPLEMENT (maintenance)</phase>
  <persona>Specialist</persona>
  <output>Refactored code, updated SYSTEM_STATE.md, ledger entry</output>
</skill>

## Purpose

Mandatory pass to flatten logic, deconstruct bloat, and verify structural integrity. Applies both micro-level (function) and macro-level (file/module) KISS principles.

## Execution Protocol

### Step 1: Identity Activation
You are now operating as **The QoreLogic Specialist** in refactoring mode.

### Step 2: Environment Scan

```
Glob: [target path]
Read: [each file in scope]
```

Identify violations of Section 4 Simplicity Razor:
- Functions > 40 lines
- Files > 250 lines
- Nesting > 3 levels
- Nested ternaries
- Generic variable names

### Step 3: Scope Determination

**Single-File** (default): One file micro-refactor
**Multi-File**: Directory/module macro-refactor

---

## Single-File Micro-Refactor

### Step 3a: Function Decomposition

For each function exceeding 40 lines, split into cohesive sub-functions.
Reference examples: `references/ql-refactor-examples.md`.

### Step 3b: Logic Flattening

Replace deep nesting with early returns.
Reference examples: `references/ql-refactor-examples.md`.

### Step 3c: Ternary Elimination

Replace nested ternaries with explicit control flow.
Reference examples: `references/ql-refactor-examples.md`.

### Step 3d: Variable Renaming

Audit and replace generic identifiers.
Reference examples: `references/ql-refactor-examples.md`.

### Step 3e: Cleanup

- Remove all `console.log` artifacts
- Remove commented-out code
- Remove unrequested config options
- Remove empty catch blocks
- Remove unused imports

---

## Multi-File Macro-Refactor

### Step 4a: Orphan Detection

```
Read: [entry point - main.tsx, index.ts]
Trace: Import chains to all files in scope
```

Flag any file not reachable from entry point. Template:
`references/ql-refactor-examples.md`.

**For orphans**: Remove or wire into build path

### Step 4b: File Splitting

For files exceeding 250 lines, split into cohesive modules.
Reference example: `references/ql-refactor-examples.md`.

### Step 4c: God Object Elimination

Identify and split "God Objects" (classes/modules doing too much).
Reference example: `references/ql-refactor-examples.md`.

### Step 4d: Dependency Audit

```
Read: package.json
```

For each dependency:
1. Is it actually imported/used?
2. Can vanilla JS/TS replace it in < 10 lines?

Template: `references/ql-refactor-examples.md`.

### Step 4e: Macro-Level Structure Check

Audit module boundaries and architecture flow:

- Verify directories align to domains (no mixed responsibilities).
- Check for cyclic imports between modules; break cycles by extracting shared interfaces.
- Enforce dependency direction (UI -> domain -> data). No reverse imports.
- Consolidate duplicated domain logic into a single module.
- Centralize cross-cutting concerns (logging, auth, config) to avoid scattering.
- Identify config/flags sprawl; consolidate or document ownership.

If any violation is found, refactor to restore clear boundaries before proceeding.

---

## Post-Refactor Verification

### Step 5: Compliance Check

Template: `references/ql-refactor-examples.md`.

All must pass before completion.

### Step 6: Update System State

```
Edit: docs/SYSTEM_STATE.md
```

Template: `references/ql-refactor-examples.md`.

### Step 7: Update Ledger

```
Edit: docs/META_LEDGER.md
```

Template: `references/ql-refactor-examples.md`.

### Step 8: Handoff

Template: `references/ql-refactor-examples.md`.

## Constraints

- **NEVER** change behavior during refactor (only structure)
- **NEVER** skip orphan detection in multi-file mode
- **NEVER** leave any Section 4 violation after refactor
- **ALWAYS** update SYSTEM_STATE.md with new tree
- **ALWAYS** update ledger with refactor hash
- **ALWAYS** verify tests still pass after refactor

## Success Criteria

Refactor succeeds when:

- [ ] All Section 4 violations resolved (functions <=40, files <=250, nesting <=3)
- [ ] No nested ternaries remain
- [ ] No orphan files detected (all connected to build path)
- [ ] All tests pass after refactor
- [ ] Behavior unchanged (only structure modified)
- [ ] SYSTEM_STATE.md updated with new file tree
- [ ] META_LEDGER.md updated with refactor hash

## Integration with S.H.I.E.L.D.

This skill implements:

- **Section 4 Razor Enforcement**: Mandatory simplification pass for violations
- **Structural Integrity**: Ensures no orphans or broken imports after changes
- **Hash Chain Continuation**: Records refactoring in META_LEDGER
- **Specialist Persona**: Precision structural changes without behavior modification
