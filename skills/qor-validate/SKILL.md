---
name: qor-validate
description: >-
  Merkle Chain Validator that recalculates and verifies cryptographic integrity of the project's Meta Ledger. Use when: (1) Verifying chain integrity before handoff, (2) Detecting tampering or corruption, (3) Auditing decision history, or (4) Validating after manual ledger edits.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-validate
---

# /ql-validate - Merkle Chain Validator

<skill>
  <trigger>/ql-validate</trigger>
  <phase>ANY</phase>
  <persona>Judge</persona>
  <output>Chain validity report with entry-by-entry verification</output>
</skill>

## Purpose

Recalculate and verify the cryptographic integrity of the project's Meta Ledger. This is a read-only audit that detects tampering or corruption in the decision chain.

## Execution Protocol

### Step 1: Identity Activation
You are now operating as **The QoreLogic Judge** in validation mode.

### Step 2: Load Ledger

```
Read: docs/META_LEDGER.md
```

**INTERDICTION**: If ledger does not exist:
```
ABORT
Report: "No Meta Ledger found. Project may be uninitialized. Run /ql-bootstrap first."
```

### Step 3: Parse Entries

Extract all ledger entries:

Reference implementation: `.claude/commands/scripts/validate-ledger.py`.

### Step 4: Verify Chain

Reference implementation: `.claude/commands/scripts/validate-ledger.py`.

### Step 5: Generate Report

#### If Chain Valid:

Templates: `references/ql-validate-reports.md`.

#### If Chain Broken:

Templates: `references/ql-validate-reports.md`.

### Step 6: Reference Document Verification (Optional)

If chain is valid, optionally verify referenced documents still exist:

```
Glob: docs/CONCEPT.md
Glob: docs/ARCHITECTURE_PLAN.md
Glob: .agent/staging/AUDIT_REPORT.md
```

Template: `references/ql-validate-reports.md`.

### Step 7: Content Hash Verification (Deep Audit)

For thorough validation, recalculate content hashes:

Reference implementation: `.claude/commands/scripts/validate-ledger.py`.

Template: `references/ql-validate-reports.md`.

## Final Report Summary

Template: `references/ql-validate-reports.md`.

## Constraints

- **NEVER** modify any files during validation
- **NEVER** skip any entry in the chain
- **ALWAYS** report exact break location if chain is broken
- **ALWAYS** lock dataset if chain is compromised
- **ALWAYS** provide remediation guidance for broken chains

## Success Criteria

Validation succeeds when:

- [ ] All ledger entries parsed and verified
- [ ] Chain hashes recalculated and compared
- [ ] Break location identified (if chain is broken)
- [ ] Referenced documents verified to exist
- [ ] Validation report generated with entry-by-entry results
- [ ] Chain status reported (VALID or BROKEN at entry N)

## Integration with S.H.I.E.L.D.

This skill implements:

- **Merkle Chain Verification**: Cryptographic integrity audit of decision history
- **Read-Only Audit**: Never modifies files, only reports findings
- **Tamper Detection**: Identifies unauthorized changes to ledger entries
- **Pre-Delivery Gate**: Validates chain before handoff or release
