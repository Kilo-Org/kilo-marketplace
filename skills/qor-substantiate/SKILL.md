---
name: qor-substantiate
description: >-
  S.H.I.E.L.D. Substantiation and Session Seal that verifies implementation against blueprint and cryptographically seals the session. Use when: (1) Implementation is complete, (2) Ready to verify Reality matches Promise, (3) Need to seal session with Merkle hash, or (4) Preparing to hand off completed work.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-substantiate
---

# /ql-substantiate - Session Seal

<skill>
  <trigger>/ql-substantiate</trigger>
  <phase>SUBSTANTIATE</phase>
  <persona>Judge</persona>
  <output>Updated META_LEDGER.md with final seal, SYSTEM_STATE.md snapshot</output>
</skill>

## Purpose

The final phase of the S.H.I.E.L.D. lifecycle. Verify that implementation matches the encoded blueprint (Reality = Promise), then cryptographically seal the session.

## Execution Protocol

### Step 1: Identity Activation
You are now operating as **The QoreLogic Judge** in substantiation mode.

Your role is to prove, not to improve. Verify what was built matches what was promised.

### Step 2: State Verification

```
Read: docs/META_LEDGER.md
Read: docs/ARCHITECTURE_PLAN.md
Read: .failsafe/governance/AUDIT_REPORT.md
```

**INTERDICTION**: If no PASS verdict exists:
```
ABORT
Report: "Cannot substantiate without PASS verdict. Run /ql-audit first."
```

**INTERDICTION**: If no implementation exists:
```
ABORT
Report: "No implementation found. Run /ql-implement first."
```

### Step 2.5: Version Validation (MANDATORY)

**Verify version consistency** between plan and current state:

```bash
git tag --sort=-v:refname | head -1
```

```
Read: Plan file (docs/Planning/plan-*.md or docs/ARCHITECTURE_PLAN.md)
Extract: Target Version from plan header
```

**INTERDICTION**: If Target Version ≤ Current Tag → ABORT (version already shipped).
**INTERDICTION**: If governance files reference wrong version → PAUSE (fix before sealing).

Log: "Version validated: v[current] → v[target] (change type: [hotfix|feature|breaking])"

### Step 3: Reality Audit

Compare implementation against blueprint:

```
Read: All files in src/
Compare: Against docs/ARCHITECTURE_PLAN.md file tree
```

Template: `references/ql-substantiate-templates.md`.

**Findings**:
- **MISSING**: Planned but not created -> FAIL
- **UNPLANNED**: Created but not in blueprint -> WARNING (document in ledger)
- **EXISTS**: Matches -> PASS

### Step 3.5: Blocker Verification

Read `docs/BACKLOG.md`. Warn if open Security Blockers or related Development Blockers exist.

### Step 4: Functional Verification

#### Test Audit
```
Glob: tests/**/*.test.{ts,tsx,js}
Read: Test files
```

Template: `references/ql-substantiate-templates.md`.

#### Visual Silence Verification (if frontend)
```
Grep: "color:" in src/**/*.{css,tsx}
Grep: "background:" in src/**/*.{css,tsx}
```

Check for violations:
Template: `references/ql-substantiate-templates.md`.

#### Console.log Artifacts
```
Grep: "console.log" in src/**/*
```

Template: `references/ql-substantiate-templates.md`.

### Step 4.5: Skill File Integrity Check

If any skill files (`.claude/commands/ql-*.md`) were modified during this session:

1. List modified skill files from git diff
2. For each modified skill:
   - Verify it still has required sections: `<skill>` block, `## Execution Protocol`, `## Constraints`, `## Next Step`
   - Verify the `## Next Step` section references valid successor skills
   - Log in ledger: "Skill file [name] modified — structure verified"

If any skill is missing required sections after modification:

```
PAUSE
Report: "Skill [name] missing required section: [section]. Fix before sealing."
```

### Step 4.6: Reliability Interdictions (B49/B50/B51)

> Deferred — Skill Admission, Gate-to-Skill Matrix, and Reliability Integrity not yet implemented. No-op until `tools/reliability/` scripts are created.

### Step 5: Section 4 Razor Final Check

Template: `references/ql-substantiate-templates.md`.

### Step 6: Sync System State

Map the final physical tree:

```
Glob: src/**/*
Glob: tests/**/*
Glob: docs/**/*
```

Create/Update `docs/SYSTEM_STATE.md`:

Template: `references/ql-substantiate-templates.md`.

### Step 7: Final Merkle Seal

Calculate session seal:

Reference implementation: `.claude/commands/scripts/calculate-session-seal.py`.

Update `docs/META_LEDGER.md`:

Template: `references/ql-substantiate-templates.md`.

### Step 8: Cleanup Staging

Clear: .failsafe/governance/

Preserve only the final AUDIT_REPORT.md (or archive it).

### Step 9: Final Report

Template: `references/ql-substantiate-templates.md`.

### Step 9.5: Stage Artifacts (for user commit)

  **Stage All Artifacts**:
  ```bash
  git add docs/CONCEPT.md
  git add docs/ARCHITECTURE_PLAN.md
  git add docs/META_LEDGER.md
  git add docs/SYSTEM_STATE.md
  git add docs/BACKLOG.md
  git add src/
  ```

  **Next Steps**: Review the staged files and then commit and push when ready.

  Example commit message:
  ```
  seal: [plan-slug] - Session substantiated
  Merkle seal: [chain-hash]
  Verdict: PASS
  Files: [file-count]
  ```

REPORT: "Session seal complete. Artifacts staged on [current-branch] and ready for user review."

### Step 9.6: Merge Options

Prompt user with three options: (1) merge to main, (2) create PR, (3) stay on branch. If version changed, offer to create annotated tag.

Template: `references/ql-substantiate-templates.md`.

## Failure Scenarios

### If Reality != Promise:

Template: `references/ql-substantiate-templates.md`.

## Constraints

- **NEVER** seal a session with Reality != Promise
- **NEVER** skip any verification step
- **NEVER** seal with Section 4 violations present
- **NEVER** seal with version mismatch (Target ≤ Current Tag)
- **ALWAYS** validate version before sealing
- **ALWAYS** update SYSTEM_STATE.md before sealing
- **ALWAYS** calculate proper chain hash
- **ALWAYS** document any unplanned files in ledger
- **ALWAYS** verify chain integrity before sealing

## Success Criteria

Substantiation succeeds when:

- [ ] PASS verdict exists in AUDIT_REPORT.md
- [ ] Version validated (Target > Current Tag)
- [ ] Reality matches Promise (all planned files exist, no missing)
- [ ] Open security blockers reviewed
- [ ] Test audit completed
- [ ] Section 4 Razor final check passed
- [ ] SYSTEM_STATE.md synced with actual file tree
- [ ] Merkle seal calculated and recorded in META_LEDGER
- [ ] Session artifacts staged for user review
- [ ] Merge/PR/tag options presented to user

## Integration with S.H.I.E.L.D.

This skill implements:

- **Session Seal**: Cryptographic proof that Reality matches Promise
- **Version Gate**: Prevents sealing with stale or mismatched versions
- **Reality Audit**: File-by-file comparison against blueprint
- **Hash Chain Finalization**: Calculates session seal for META_LEDGER
