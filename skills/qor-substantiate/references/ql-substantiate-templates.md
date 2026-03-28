# QL Substantiate Templates

This reference contains report templates used by /ql-substantiate.

## Reality vs Promise Comparison

```markdown
### Reality vs Promise Comparison

| Planned (Blueprint) | Actual (src/) | Status |
|---------------------|---------------|--------|
| src/index.ts | src/index.ts | OK EXISTS |
| src/utils/helpers.ts | src/utils/helpers.ts | OK EXISTS |
| src/components/Button.tsx | [missing] | FAIL MISSING |
| [not planned] | src/temp.ts | WARN UNPLANNED |
```

## Test Coverage

```markdown
### Test Coverage

| Component | Test File | Status |
|-----------|-----------|--------|
| [component] | [test file] | OK EXISTS |
| [component] | [missing] | FAIL NO TEST |
```

## Visual Silence Audit

```markdown
### Visual Silence Audit

| File | Line | Violation |
|------|------|-----------|
| [file] | [line] | Hardcoded color: #ff0000 |
```

## Debug Artifacts

```markdown
### Debug Artifacts

| File | Line | Content |
|------|------|---------|
| [file] | [line] | console.log('debug') |
```

## Simplicity Compliance

```markdown
### Simplicity Compliance

| File | Lines | Max Function | Max Nesting | Status |
|------|-------|--------------|-------------|--------|
| [file] | [X]/250 | [X]/40 | [X]/3 | OK/FAIL |
```

## System State Template

```markdown
# System State

**Sealed**: [ISO 8601]
**Sealed By**: Judge (substantiation)
**Session ID**: [hash prefix]

## File Tree (Reality)

```
project/
|-- docs/
|   |-- CONCEPT.md
|   |-- ARCHITECTURE_PLAN.md
|   |-- META_LEDGER.md
|   `-- SYSTEM_STATE.md
|-- src/
|   `-- [actual tree]
|-- tests/
|   `-- [actual tree]
`-- .agent/
    `-- staging/
        `-- AUDIT_REPORT.md
```

## Metrics

| Metric | Value |
|--------|-------|
| Total Source Files | [count] |
| Total Test Files | [count] |
| Total Lines of Code | [count] |
| Section 4 Violations | 0 |
| Test Coverage | [estimate]% |

## Blueprint Compliance

| Promised | Delivered | Match |
|----------|-----------|-------|
| [count] files | [count] files | [100%/%] |
```

## Session Seal Ledger Entry

```markdown
---

### Entry #[N]: SESSION SEAL

**Timestamp**: [ISO 8601]
**Phase**: SUBSTANTIATE
**Author**: Judge
**Type**: FINAL_SEAL

**Session Summary**:
- Files Created: [count]
- Files Modified: [count]
- Tests Added: [count]
- Blueprint Compliance: [percentage]%

**Content Hash**:
```
SHA256(all_artifacts)
= [content_hash]
```

**Previous Hash**: [from entry N-1]

**Session Seal**:
```
SHA256(content_hash + previous_hash)
= [session_seal]
```

**Verdict**: SUBSTANTIATED. Reality matches Promise.

---

_Chain Status: SEALED_
_Next Session: Run /ql-bootstrap for new feature or /ql-status to review_
```

## Substantiation Report Template

```markdown
# Substantiation Report

**Timestamp**: [ISO 8601]
**Session Seal**: [session_seal prefix]...

---

## Verdict: SUBSTANTIATED OK

Reality matches Promise. Session cryptographically sealed.

---

### Verification Summary

| Check | Result |
|-------|--------|
| Blueprint Compliance | [count]/[count] files |
| Test Coverage | [count] test files |
| Visual Silence | [PASS/violations found] |
| Debug Artifacts | [none/count found] |
| Section 4 Razor | COMPLIANT |
| Merkle Chain | VALID |

### Session Artifacts

| Artifact | Status | Hash Prefix |
|----------|--------|-------------|
| docs/CONCEPT.md | Sealed | [8 chars] |
| docs/ARCHITECTURE_PLAN.md | Sealed | [8 chars] |
| docs/META_LEDGER.md | Updated | [8 chars] |
| docs/SYSTEM_STATE.md | Updated | [8 chars] |
| .agent/staging/AUDIT_REPORT.md | Archived | [8 chars] |

### Disposition

```
Session: SEALED
Ledger: UPDATED
State: SYNCHRONIZED
```

---

*Substantiated. Reality matches Promise. Session Sealed at [seal_prefix]...*

**Next Actions**:
- New feature: `/ql-bootstrap`
- Check status: `/ql-status`
- Validate chain: `/ql-validate`
```

## Failure Report Template

```markdown
## Verdict: SUBSTANTIATION FAILED FAIL

Implementation does not match blueprint.

### Discrepancies

| Type      | Details                 | Required Action               |
| --------- | ----------------------- | ----------------------------- |
| MISSING   | [file] not created      | Implement or update blueprint |
| UNPLANNED | [file] not in blueprint | Remove or update blueprint    |
| VIOLATION | Section 4 breach in [file]     | Run /ql-refactor              |

### Disposition

Session NOT sealed. Address discrepancies and re-run substantiation.
```
