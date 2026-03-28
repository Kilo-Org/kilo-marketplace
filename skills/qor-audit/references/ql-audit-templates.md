# QL Audit Templates

## Audit Report Template

```markdown
# AUDIT REPORT

**Tribunal Date**: [ISO 8601]
**Target**: [project/component name]
**Risk Grade**: [L1 / L2 / L3]
**Auditor**: The QoreLogic Judge

---

## VERDICT: [PASS / VETO]

---

### Executive Summary

[One paragraph explaining the verdict]

### Audit Results

#### Security Pass
**Result**: [PASS / FAIL]
[Specific findings]

#### Ghost UI Pass
**Result**: [PASS / FAIL]
[Specific findings]

#### Section 4 Razor Pass
**Result**: [PASS / FAIL]
[Specific findings]

#### Dependency Pass
**Result**: [PASS / FAIL]
[Specific findings]

#### Orphan Pass
**Result**: [PASS / FAIL]
[Specific findings]

#### Macro-Level Architecture Pass
**Result**: [PASS / FAIL]
[Specific findings]

### Violations Found

| ID  | Category | Location    | Description    |
| --- | -------- | ----------- | -------------- |
| V1  | [type]   | [file/line] | [what's wrong] |

### Required Remediation (if VETO)

1. [Specific action required]

### Verdict Hash

SHA256(this_report) = [hash]

---
_This verdict is binding._
```

## Ledger Entry Template (GATE TRIBUNAL)

```markdown
### Entry #[N]: GATE TRIBUNAL

**Timestamp**: [ISO 8601]
**Phase**: GATE
**Author**: Judge
**Risk Grade**: [L1/L2/L3]
**Verdict**: [PASS / VETO]

**Content Hash**:
SHA256(AUDIT_REPORT.md) = [hash]

**Previous Hash**: [from entry N-1]

**Chain Hash**:
SHA256(content_hash + previous_hash) = [calculated]

**Decision**: [Brief summary of verdict and reason]
```

## Shadow Genome Entry Template (VETO only)

```markdown
## Failure Entry #[N]

**Date**: [ISO 8601]
**Verdict ID**: [from audit report]
**Failure Mode**: [COMPLEXITY_VIOLATION / SECURITY_STUB / GHOST_PATH / HALLUCINATION / ORPHAN]

### What Failed
[Component or pattern that was rejected]

### Why It Failed
[Specific violation details]

### Pattern to Avoid
[Generalized lesson for future work]

### Remediation Attempted
[Was it fixed? How?]
```

## Final Report Template

```markdown
## Tribunal Complete

**Verdict**: [PASS / VETO]
**Risk Grade**: [L1/L2/L3]
**Report Location**: .agent/staging/AUDIT_REPORT.md

### If PASS
Gate cleared. The Specialist may proceed with `/ql-implement`.

### If VETO
Implementation blocked. Address violations and re-submit for audit.
Required actions logged in AUDIT_REPORT.md.
Failure mode recorded in SHADOW_GENOME.md.

---
_Gate [OPEN / LOCKED]. Proceed accordingly._
```
