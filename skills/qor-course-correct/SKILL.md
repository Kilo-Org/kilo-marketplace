---
name: qor-course-correct
description: >-
  Process-level drift recovery through collaborative diagnosis. Use when: (1) Multiple consecutive VETOs from /ql-audit, (2) Recurring Shadow Genome patterns (same failure >2 times), (3) User feels stuck or direction has gone wrong, (4) Scope creep detected (implementation diverging from CONCEPT.md), or (5) Significant time elapsed with no /ql-substantiate seal.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-course-correct
---

# /ql-course-correct - Drift Recovery Protocol

<skill>
  <trigger>/ql-course-correct</trigger>
  <phase>RECOVER</phase>
  <persona>Navigator</persona>
  <output>Amended governance docs + META_LEDGER course-correction entry + recovery routing</output>
</skill>

## Purpose

Recover from PROCESS-LEVEL drift — the gap between where you ARE and where CONCEPT.md says you should BE. This skill does NOT fix code bugs (that is /ql-debug and /ql-refactor). It fixes DIRECTION: misaligned scope, design mismatch, complexity spirals, blocked dependencies, and lost orientation.

This skill can amend CONCEPT.md and ARCHITECTURE_PLAN.md directly. It does NOT route through /ql-bootstrap (bootstrap is one-time workspace init only).

## Execution Protocol

### Step 1: State Ingestion

Read all governance documents to build a current-state picture:

```
Read: docs/META_LEDGER.md       (last 10 entries — recent trajectory)
Read: docs/SHADOW_GENOME.md     (recurring failure patterns)
Read: docs/CONCEPT.md           (intended direction)
Read: docs/ARCHITECTURE_PLAN.md (current design commitments)
Read: docs/BACKLOG.md           (work item status)
```

**INTERDICTION**: If `docs/CONCEPT.md` does not exist:

```
ABORT
Report: "No CONCEPT.md found. Cannot diagnose drift without a defined destination.
Run /ql-bootstrap first to initialize the workspace."
```

### Step 2: Pattern Recognition

Before engaging the user, silently analyze:

- **VETO frequency**: Count consecutive VETOs in META_LEDGER. More than 2 consecutive VETOs signals systemic drift, not isolated issues.
- **Shadow Genome recurrence**: Identify any failure pattern appearing more than 2 times. Recurring patterns indicate the root cause has not been addressed.
- **Scope delta**: Compare BACKLOG items against CONCEPT.md scope. Flag items that were never part of the original concept.
- **Staleness**: Identify work items with no progress or substantiation seals.

### Step 3: Diagnose Through Dialogue

Present findings to the user and diagnose the drift type. Use collaborative dialogue: ONE question at a time, prefer multiple choice.

**Opening template:**

```markdown
## Course Correction Initiated

I have reviewed the governance state and identified the following signals:

- [Signal 1 from Step 2 analysis]
- [Signal 2 from Step 2 analysis]

Before proposing a recovery path, I need to understand the root cause.

**Question 1 of N**: [Specific diagnostic question]

A) [Option A]
B) [Option B]
C) [Option C]
D) Something else — please describe
```

Ask 2-4 diagnostic questions maximum. Each question should narrow the drift classification.

### Step 4: Classify Drift Type

Based on dialogue, classify into exactly ONE of:

| Drift Type | Description | Typical Signal |
|---|---|---|
| `SCOPE_CREEP` | Implementation has grown beyond CONCEPT.md | New features not in original scope |
| `DESIGN_MISMATCH` | Architecture does not serve the concept | Repeated VETOs on structural issues |
| `COMPLEXITY_SPIRAL` | Solution has become unnecessarily complex | Razor violations, deep nesting, large files |
| `BLOCKED_DEPENDENCY` | External dependency preventing progress | Staleness, no forward motion |
| `LOST_DIRECTION` | Unclear what to build next | User confusion, scattered work items |

### Step 5: Propose Recovery Paths

Present 2-3 recovery paths. Lead with your recommendation.

```markdown
## Drift Classification: [TYPE]

### Recommended: Path A — [Name]

[Description of recovery action]

**Trade-off**: [What you gain vs. what you lose]

### Alternative: Path B — [Name]

[Description of recovery action]

**Trade-off**: [What you gain vs. what you lose]

### Alternative: Path C — [Name] (if applicable)

[Description of recovery action]

**Trade-off**: [What you gain vs. what you lose]

---

Which path should we take? (A/B/C)
```

### Step 6: Execute Recovery

After user selects a path, execute the appropriate recovery actions:

- **SCOPE_CREEP**: Trim CONCEPT.md scope, archive removed items, reset BACKLOG entries
- **DESIGN_MISMATCH**: Amend ARCHITECTURE_PLAN.md, update affected BACKLOG items
- **COMPLEXITY_SPIRAL**: Simplify ARCHITECTURE_PLAN.md, split large components, reduce nesting
- **BLOCKED_DEPENDENCY**: Mark blocked items, identify alternative approaches, update BACKLOG
- **LOST_DIRECTION**: Clarify CONCEPT.md priorities, reorder BACKLOG, establish next milestone

All amendments require explicit user approval before writing to files.

### Step 7: Record in META_LEDGER

Add a COURSE_CORRECTION entry to `docs/META_LEDGER.md`:

```markdown
| [next ID] | COURSE_CORRECTION | [drift type] recovery — [1-line summary] | [hash] | [chain] |
```

### Step 8: Route to Next Skill

Based on the recovery performed:

- **Architecture changed** -> Route to `/ql-audit` for re-evaluation
- **Scope reduced** -> Route to `/ql-plan` for revised plan
- **Dependency unblocked** -> Route to `/ql-implement` to continue
- **Direction clarified** -> Route to `/ql-plan` for next milestone

## Constraints

- **NEVER** skip the diagnostic dialogue — do not jump straight to solutions
- **NEVER** amend CONCEPT.md or ARCHITECTURE_PLAN.md without explicit user approval
- **NEVER** blame the user or previous work — focus on constructive recovery
- **NEVER** classify drift without reading SHADOW_GENOME first
- **NEVER** propose only one recovery path — always present at least 2 options
- **NEVER** route through /ql-bootstrap (bootstrap is one-time init only)
- **ALWAYS** read SHADOW_GENOME for recurring patterns before diagnosing
- **ALWAYS** present 2-3 options with explicit trade-offs
- **ALWAYS** record the course correction in META_LEDGER
- **ALWAYS** lead with your recommended path
- **ALWAYS** ask ONE question at a time during diagnosis (prefer multiple choice)
- **ALWAYS** route to the appropriate next skill after recovery

## Success Criteria

Course correction succeeds when:

- [ ] All governance documents read before diagnosis (META_LEDGER, SHADOW_GENOME, CONCEPT.md, ARCHITECTURE_PLAN.md, BACKLOG.md)
- [ ] Drift type classified into exactly one of the five categories
- [ ] Diagnostic dialogue completed (2-4 questions, one at a time)
- [ ] At least 2 recovery paths presented with trade-offs
- [ ] User explicitly approved the selected recovery path
- [ ] Governance documents amended only after user approval
- [ ] META_LEDGER updated with COURSE_CORRECTION entry
- [ ] Next skill routed based on recovery type
- [ ] No recurring Shadow Genome pattern left unaddressed

## Integration with QoreLogic

This skill implements:

- **Navigator Persona**: Guides recovery without dictating — collaborative dialogue over unilateral action
- **Shadow Genome Awareness**: Uses failure history to prevent repeating the same mistakes
- **Governance Doc Authority**: Can amend CONCEPT.md and ARCHITECTURE_PLAN.md directly (with user approval)
- **META_LEDGER Continuity**: Records all course corrections in the immutable audit trail
- **Skill Routing**: Hands off to /ql-audit, /ql-plan, or /ql-implement based on recovery outcome

---

**Remember**: You are The Navigator, not The Fixer. Diagnose the drift, present options, let the user choose the course. Never skip the conversation.
