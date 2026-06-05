---
name: qor-organize
description: >-
  Adaptive workspace organization that detects project type, analyzes existing conventions, and proposes context-aware restructuring. Supports software repos, monorepos, data science, documentation, and hybrid workspaces.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-organize
---

# /ql-organize - Adaptive Workspace Organization

<skill>
  <trigger>/ql-organize</trigger>
  <phase>ORGANIZE</phase>
  <persona>Governor</persona>
  <output>Context-aware reorganization proposal, optional execution, FILE_INDEX.md audit trail</output>
</skill>

## Purpose

Intelligently organize workspaces by detecting project archetype, analyzing conventions, and proposing adaptive restructuring. Detects, doesn't assume. Proposes, doesn't prescribe.

## Core Philosophy

1. **Detect, Don't Assume** — Analyze before proposing
2. **Conventions Over Configuration** — Follow ecosystem standards
3. **Propose, Don't Prescribe** — User approves before execution
4. **Incremental Over Wholesale** — Targeted changes beat full restructuring
5. **Preserve Intent** — Existing meaningful structure is signal
6. **ISOLATION MANDATORY** — `.agent/`, `.claude/`, `.qorelogic/`, `.failsafe/` are NEVER reorganized

## Execution Protocol

### Phase -1: Workspace Isolation Enforcement

Before ANY analysis, establish protected paths. Workspace governance directories are forbidden from reorganization.

Isolation rules: `references/ql-organize-templates.md`.

### Phase 0: Archetype Cache Check

```
Glob: .qorelogic/workspace.json
```

If cache exists, load and verify key indicators still present. If indicators changed, prompt user: keep current, re-detect, or manual override.

If no cache, proceed to Phase 1.

### Phase 1: Workspace Detection

**Step 1.1**: Scan for archetype indicators (package.json, Cargo.toml, go.mod, pyproject.toml, etc.).

**Step 1.2**: Classify workspace against archetype table.

Archetype definitions: `references/ql-organize-templates.md`.

**Step 1.3**: Report detection with confidence level.

**Step 1.4**: Cache archetype to `.qorelogic/workspace.json` after user confirmation.

### Phase 2: Convention Analysis

**Step 2.1**: Map how well workspace follows conventions for detected archetype.

Convention checks: `references/ql-organize-templates.md`.

**Step 2.2**: Identify deviations — files/directories that don't match archetype conventions.

### Phase 3: Organization Proposal

**Step 3.1**: Generate targeted proposals (high/medium/low priority) based on deviations.

Proposal template: `references/ql-organize-templates.md`.

**Step 3.2**: User confirmation required before execution.

Options: Execute all, high priority only, review individually, or cancel.

### Phase 4: Execution (After Approval)

**Step 4.1**: Initialize movement log.

**Step 4.2**: For each approved change: verify source, create destination, execute move, log with timestamp, verify.

**Step 4.3**: Generate `FILE_INDEX.md` with movement log and rollback instructions.

Template: `references/ql-organize-templates.md`.

### Phase 5: Privacy Configuration Review

**Step 5.1**: Ask repository visibility (public/private).

**Step 5.2**: Audit `.gitignore` for required privacy patterns.

**Step 5.3**: Report privacy gaps.

**Step 5.4**: Present modification options (apply all, selective, review, skip).

**Step 5.5**: Apply approved updates to `.gitignore`.

**Step 5.6**: Log privacy config to `.qorelogic/workspace.json`.

Privacy patterns: `references/ql-organize-templates.md`.

## Constraints

- **NEVER** move files without user approval
- **NEVER** delete directories unless explicitly requested
- **NEVER** touch `.git/`, `node_modules/`, `__pycache__/`, `venv/`
- **NEVER** reorganize workspace governance directories (`.agent/`, `.claude/`, `.qorelogic/`, `.failsafe/`)
- **NEVER** override detected conventions with personal preference
- **NEVER** assume archetype without evidence
- **ALWAYS** detect before proposing
- **ALWAYS** explain reasoning for each change
- **ALWAYS** provide rollback instructions
- **ALWAYS** preserve existing meaningful structure
- **ALWAYS** log every movement with source and destination

## Success Criteria

Organization succeeds when:

- [ ] Archetype correctly detected
- [ ] Proposals align with archetype conventions
- [ ] User approved changes before execution
- [ ] All movements logged in FILE_INDEX.md
- [ ] No data loss
- [ ] Rollback instructions provided
- [ ] Privacy configuration reviewed (public repos require acknowledgment)
- [ ] Gitignore patterns verified for governance directories

## Integration with S.H.I.E.L.D.

This skill implements:

- **Adaptive Intelligence**: Detects and adapts to workspace type
- **Convention Compliance**: Follows ecosystem-specific standards
- **Audit Trail**: Complete movement logging
- **Safe Defaults**: Proposal-first, execute-after-approval
- **Privacy Enforcement**: Protects governance state from public exposure
