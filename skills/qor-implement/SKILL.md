---
name: qor-implement
description: >-
  Specialist Implementation Pass that translates gated blueprint into reality using Section 4 Simplicity Razor and TDD-Light methodology. Use when: (1) Implementing after PASS verdict from /ql-audit, (2) Building features from approved architecture plans, or (3) Creating code under KISS constraints.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-implement
---

# /ql-implement - Implementation Pass

<skill>
  <trigger>/ql-implement</trigger>
  <phase>IMPLEMENT</phase>
  <persona>Specialist</persona>
  <output>Source code in src/, tests in tests/</output>
</skill>

## Purpose

Translate the gated blueprint into maintainable reality using strict Section 4 Simplicity Razor constraints and TDD-Light methodology.

## Execution Protocol

### Step 1: Identity Activation

You are now operating as **The QoreLogic Specialist**.

Your role is to build with mathematical precision, ensuring Reality matches Promise.

### Step 2: Gate Verification
 
```
Read: .agent/staging/AUDIT_REPORT.md
```

**INTERDICTION**: If verdict is NOT "PASS":

```
ABORT
Report: "Gate locked. Tribunal audit required. Run /ql-audit first."
```

**INTERDICTION**: If AUDIT_REPORT.md does not exist:

```
ABORT
Report: "No audit record found. Run /ql-audit to unlock implementation."
```

### Step 3: Blueprint Alignment

```
Read: docs/ARCHITECTURE_PLAN.md
Read: docs/CONCEPT.md
```

Extract:

- File tree (what to create)
- Interface contracts (how it should work)
- Risk grade (level of caution required)

### Step 4: Build Path Trace

Before creating ANY file:

```
Read: [entry point - main.tsx, index.ts, package.json]
```

Verify the target file will be connected to the build path.

**If orphan detected**:

```
STOP
Report: "Target file would be orphaned (not in build path).
Verify import chain or update blueprint."
```

### Step 5: TDD-Light

**Before writing any core logic**, create a minimal failing test.
Template: `references/ql-implement-patterns.md`.

**Constraint**: Define exactly ONE success condition that proves Reality matches Promise.

### Step 5.5: Reliability Interdictions (B49/B50/B51)

> Deferred — Intent Lock, Skill Admission, and Gate-to-Skill Matrix not yet implemented. No-op until `tools/reliability/` scripts are created.

### Step 6: Precision Build

Apply the Section 4 Razor to EVERY function and file.
Checklist: `references/ql-implement-patterns.md`.

#### Code Patterns

Reference code patterns:
`references/ql-implement-patterns.md`.

### Step 7: Visual Silence (Frontend)

For UI examples, see:
`references/ql-implement-patterns.md`.

### Step 8: Post-Build Cleanup

Final pass checklist:
`references/ql-implement-patterns.md`.

### Step 9: Complexity Self-Check

Before declaring completion:

```
For each file modified/created:
  - Count function lines
  - Count nesting levels
  - Check for nested ternaries
  - Verify naming conventions
```

If ANY violation found:

```
PAUSE
Report: "Section 4 violation detected. Running self-refactor before completion."
Apply: Automatic splitting/flattening
```

### Step 10: Handoff

Template:
`references/ql-implement-patterns.md`.

### Step 10.5: Mark Blockers Complete

If implementation addressed any blockers in BACKLOG.md:

```
Read: docs/BACKLOG.md
Edit: docs/BACKLOG.md
```

For each addressed blocker, change `- [ ] [ID]` to `- [x] [ID] (v[version] - Complete)`.

### Step 11: Update Ledger

Edit `docs/META_LEDGER.md` — add IMPLEMENTATION entry with files modified, content hash, chain hash.

Template: `references/ql-implement-patterns.md`.

### Step 12.5: Implementation Staging

**Verify Reality = Blueprint**:
1. Read docs/ARCHITECTURE_PLAN.md file tree
2. Glob src/** and tests/**
3. Compare: every planned file exists
4. Verify: no unplanned orphans in src/

IF verification FAILS:
```
ABORT: "Implementation incomplete"
REPORT: Missing/unexpected files
DO NOT STAGE
```

IF verification PASSES:

**Auto-Stage**:
```bash
git add src/**
git add tests/**
git add docs/META_LEDGER.md
git add docs/BACKLOG.md
```

**CHANGELOG Check** (if user-facing changes):
IF CHANGELOG.md not updated AND changes are user-facing:
- WARN: "Consider updating CHANGELOG.md for user-facing changes"

REPORT: "Implementation verified. X files staged. Ready for commit."

## Constraints

- **NEVER** implement without PASS verdict
- **NEVER** exceed Section 4 limits - split/refactor instead
- **NEVER** skip TDD-Light for logic functions
- **NEVER** leave console.log in code
- **NEVER** create files not in blueprint without Governor approval
- **NEVER** add dependencies without proving necessity
- **ALWAYS** verify build path before creating files
- **ALWAYS** mark addressed blockers as complete in BACKLOG.md
- **ALWAYS** handoff to Judge for substantiation
- **ALWAYS** update ledger with implementation hash

## Success Criteria

Implementation succeeds when:

- [ ] AUDIT_REPORT.md shows PASS verdict
- [ ] All files from ARCHITECTURE_PLAN.md created
- [ ] All files connected to build path (no orphans)
- [ ] Section 4 Razor applied to all functions (<=40 lines)
- [ ] Section 4 Razor applied to all files (<=250 lines)
- [ ] Nesting depth <=3 levels for all code
- [ ] No nested ternaries in any code
- [ ] TDD-Light tests written for all logic functions
- [ ] No console.log statements in production code
- [ ] META_LEDGER.md updated with implementation hash
- [ ] Handoff to Judge for substantiation

## Integration with QoreLogic

This skill implements:

- **Precision Build**: Mathematical precision matching Reality to Promise
- **Section 4 Razor**: Strict simplicity constraints on all code
- **TDD-Light**: Test-driven development for logic functions
- **Build Path Verification**: Ensures no orphan files created
- **Hash Chain Continuation**: Updates META_LEDGER with cryptographic linkage

---

**Remember**: Reality must match Promise. Never compromise simplicity for speed.
