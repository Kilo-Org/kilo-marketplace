---
name: qor-debug
description: >
  Two-phase diagnostic system combining rapid root-cause identification with
  residual sweep verification. Prevents cascading AI debugging damage by
  enforcing four mandatory analysis layers before any code change.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-debug
user-invocable: true
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /ql-debug - Diagnostic Fixer

<skill>
  <trigger>/ql-debug</trigger>
  <phase>IMPLEMENT / SUBSTANTIATE / GATE</phase>
  <persona>Fixer</persona>
  <dispatch>
    <phase1>general — Rapid root-cause (4-layer analysis on reported symptoms)</phase1>
    <phase2>general — Residual sweep (4-layer analysis on fixed state)</phase2>
  </dispatch>
  <output>Two-phase diagnosis: root-cause fix + residual sweep report</output>
</skill>

## Purpose

Bring surgical precision to debugging. AI coding agents typically pull a thread and watch the codebase unravel — guessing at fixes, introducing regressions, chasing cascading failures. The Fixer enforces a formal methodology: **prove the root cause first, then propose the minimal fix.** No code changes until the cause-effect chain is established with evidence.

## When to Use

- Runtime errors with unclear origin or misleading stack traces
- Non-deterministic failures (works sometimes, fails others)
- Cascading failures after refactoring
- Proactive verification after significant logic changes
- Test failures requiring formal root-cause analysis
- Structural defects blocking phase transitions

## Execution Protocol

### Step 1: Describe the Problem

Provide the Fixer with:

- **Symptom**: What is failing? Error message, unexpected behavior, test output.
- **Context**: What changed recently? Which files are involved?
- **Reproduction**: How to trigger the failure (if known).

If invoking proactively (no specific failure), state which files or logic paths were changed.

### Step 2: Two-Phase Agent Dispatch

**Phase 1 — Rapid Root-Cause (general agent)**

Launch the `general` agent (use `subagent_type: "general"`) with the problem description. The fixer runs all four layers (Dijkstra, Hamming/Shannon, Turing/Hopper, Zeller) focused on the REPORTED symptoms. It identifies root causes and proposes fixes.

Apply the proposed fixes.

**Phase 2 — Residual Sweep (general agent, resumed)**

After Phase 1 fixes are applied, launch the `general` agent again to:
- Verify the fixes are complete and correct
- Sweep for residual issues introduced or exposed by the fixes
- Check for similar patterns elsewhere in the codebase
- Validate build artifacts match source (dist/out staleness check)

Phase 2 uses the same four-layer methodology but scoped to the FIXED state, not the original symptoms.

### Step 3: Diagnosis & Handoff

The Fixer produces a final diagnosis with:

- Root cause location and explanation
- Cause-effect chain
- Recommended fix with regression risk assessment
- Related issues discovered during analysis

**Handoff rules:**

- Straightforward fix: Fixer proposes exact code changes
- Architectural changes needed: hand off to `/ql-plan` for Governor review
- Implementation ready: hand off to `/ql-implement` for the Specialist
- Test validation needed: hand off to `/ql-substantiate` for the Judge

## Constraints

- **NEVER** apply a fix without completing at least Layers 1-3
- **NEVER** propose a fix that only addresses the symptom
- **ALWAYS** distinguish symptom from root cause
- **ALWAYS** check for similar patterns elsewhere in the codebase
- **ALWAYS** document findings with line numbers and evidence
- **ALWAYS** use `subagent_type: "general"` (not `ultimate-debugger`)

## Integration with QoreLogic

This skill implements:

- **S.H.I.E.L.D. Diagnostic Service**: On-demand across IMPLEMENT, SUBSTANTIATE, and GATE phases
- **Two-Phase Architecture**: Root-cause first, then residual sweep
- **Four-Layer Methodology**: Dijkstra, Hamming/Shannon, Turing/Hopper, Zeller
- **Evidence-Based Fixes**: Every conclusion backed by code evidence
- **Cross-Agent Handoff**: Routes results to appropriate next agent/skill

## Success Criteria

Debug succeeds when:

- [ ] Root cause identified with evidence (not just symptom)
- [ ] Cause-effect chain documented with line numbers
- [ ] Phase 1 fix applied and verified
- [ ] Phase 2 residual sweep completed
- [ ] No regressions introduced by fix
- [ ] Handoff to appropriate next skill provided
