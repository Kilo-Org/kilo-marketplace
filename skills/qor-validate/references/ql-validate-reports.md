# QL Validate Reports

This reference contains report templates used by /ql-validate.

## Chain Valid Report

```markdown
# Merkle Chain Validation Report

**Timestamp**: [ISO 8601]
**Auditor**: The QoreLogic Judge

---

## Chain Status: VALID OK

The cryptographic integrity of the Meta Ledger has been verified.

### Summary

| Metric        | Value              |
| ------------- | ------------------ |
| Total Entries | [count]            |
| Genesis Hash  | [first 8 chars]... |
| Latest Hash   | [first 8 chars]... |
| Chain Length  | [count] links      |

### Entry-by-Entry Verification

| Entry | Phase   | Timestamp | Hash Prefix | Status |
| ----- | ------- | --------- | ----------- | ------ |
| #1    | GENESIS | [date]    | [8 chars]   | OK     |
| #2    | [phase] | [date]    | [8 chars]   | OK     |
| ...   | ...     | ...       | ...         | OK     |

### Chain Visualization

```
GENESIS -+- > #1 (bootstrap)
         |    hash: [prefix]...
         |
         +-> #2 (audit)
         |    hash: [prefix]...
         |    prev: [#1 prefix]...
         |
         `-> #[N] (latest)
              hash: [prefix]...
              prev: [#N-1 prefix]...
```

---

_Chain integrity confirmed. All decisions are traceable._
```

## Chain Broken Report

```markdown
# Merkle Chain Validation Report

**Timestamp**: [ISO 8601]
**Auditor**: The QoreLogic Judge

---

## Chain Status: BROKEN FAIL

**CRITICAL**: The cryptographic integrity has been compromised.

### Break Location

| Attribute | Value |
|-----------|-------|
| Broken At | Entry #[X] |
| Last Valid | Entry #[X-1] |
| Break Type | [HASH_MISMATCH / MISSING_ENTRY / SEQUENCE_GAP] |

### Discrepancy Details

**Entry #[X]**:
- Recorded Chain Hash: `[recorded]`
- Expected Chain Hash: `[calculated]`
- Content Hash: `[content_hash]`
- Previous Hash: `[previous_hash]`

### Possible Causes

1. **Manual Edit**: The ledger file was modified outside the A.E.G.I.S. workflow
2. **Corruption**: File system corruption or incomplete write
3. **Tampering**: Deliberate modification of decision history
4. **Sync Conflict**: Multiple sessions modified the ledger concurrently

### Required Action

**DATASET LOCKED**

No implementation may proceed until integrity is restored.

Options:
1. **Restore from Backup**: If a clean backup exists, restore docs/META_LEDGER.md
2. **Rebuild Chain**: Re-run all phases from the broken point with new hashes
3. **Manual Audit**: Investigate the discrepancy and document the resolution

### Entry-by-Entry Verification

| Entry | Phase | Hash Prefix | Status |
|-------|-------|-------------|--------|
| #1 | GENESIS | [8 chars] | OK |
| #2 | [phase] | [8 chars] | OK |
| #[X] | [phase] | [8 chars] | FAIL BREAK |
| #[X+1] | [phase] | [8 chars] | OK (unverified) |

---

*Chain integrity compromised. Manual intervention required.*
```

## Referenced Document Status

```markdown
### Referenced Document Status

| Document                       | Exists | Last Modified |
| ------------------------------ | ------ | ------------- |
| docs/CONCEPT.md                | OK/FAIL | [date]        |
| docs/ARCHITECTURE_PLAN.md      | OK/FAIL | [date]        |
| .agent/staging/AUDIT_REPORT.md | OK/FAIL | [date]        |
```

## Deep Content Verification

```markdown
### Deep Content Verification

| Entry | Document               | Content Match |
| ----- | ---------------------- | ------------- |
| #1    | CONCEPT + ARCHITECTURE | OK/FAIL       |
| #2    | AUDIT_REPORT           | OK/FAIL       |
| ...   | ...                    | ...           |
```

## Final Report Summary

```markdown
## Validation Complete

| Check             | Result                   |
| ----------------- | ------------------------ |
| Chain Integrity   | [VALID / BROKEN at #X]   |
| Total Entries     | [count]                  |
| Documents Present | [count]/[expected]       |
| Content Integrity | [VERIFIED / DRIFT at #X] |

### Disposition

[Chain is trustworthy / Chain requires repair before proceeding]

---

_Validation performed by The QoreLogic Judge_
```
