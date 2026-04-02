---
name: qor-bootstrap
description: >-
  Initialize QoreLogic S.H.I.E.L.D. DNA for a new project by creating CONCEPT, ARCHITECTURE_PLAN, and META_LEDGER with genesis hash. Use when: (1) Starting a new project, (2) First-time QoreLogic setup, or (3) Re-initializing after project reset.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-bootstrap
---

# /ql-bootstrap - Project DNA Seeder

<skill>
  <trigger>/ql-bootstrap</trigger>
  <phase>ALIGN + ENCODE</phase>
  <persona>Governor</persona>
  <output>docs/CONCEPT.md, docs/ARCHITECTURE_PLAN.md, docs/META_LEDGER.md, docs/BACKLOG.md</output>
</skill>

## Purpose

Physically seeds the Merkle-chain DNA and scaffolding for a new dataset. This is the **genesis** of the S.H.I.E.L.D. lifecycle.

## Execution Protocol

### Step 1: Identity Activation

You are now operating as **The QoreLogic Governor**.

### Step 2: Environment Audit

Check for existing QoreLogic DNA:

```
Glob: docs/META_LEDGER.md
Glob: .failsafe/governance/
```

**INTERDICTION**: If `docs/META_LEDGER.md` exists:
```
ABORT
Report: "Integrity Violation: Genesis already exists. Use /ql-status to resume."
```

### Step 2.5: Repository Readiness Check

**Git State**: Run `git status --porcelain`. Warn if uncommitted changes exist.

**Gold Standard Check**: If no `.github/` and no `SECURITY.md`, run `/ql-repo-scaffold` silently.

**Branch Creation**: `git checkout -b feat/[project-name]-genesis`

### Step 3: Create Directory Structure

Ensure required directories exist: `.agent/`, `.failsafe/governance/`, `docs/`

### Step 3.5: Privacy Configuration

Ask user: "Is this repository public/open-source or private?"

For public repos, verify `.gitignore` includes AI governance patterns. Add missing patterns.

Template: `references/ql-bootstrap-templates.md`.

### Step 3.5b: Collaborative Design Dialogue

Before writing CONCEPT.md, engage in collaborative dialogue:

1. **Check project context first** — read existing files, docs, recent commits
2. **Ask questions one at a time** — prefer multiple choice when possible
3. **Focus on understanding**: purpose, constraints, success criteria, anti-goals
4. **Propose 2-3 approaches** with trade-offs before settling on architecture
5. **Present design in sections** (200-300 words) — validate each before proceeding
6. **YAGNI ruthlessly** — challenge every proposed feature: "Is this essential for v1?"

Only proceed to write CONCEPT.md after the user has validated the design direction.

### Step 4: ALIGN (The "Why")

Create `docs/CONCEPT.md` with Why (one sentence), Vibe (three keywords), and Anti-Goals.

Template: `references/ql-bootstrap-templates.md`.

Ask the user for the "Why" and "Vibe" keywords. If they can't explain it simply, reject the task.

### Step 5: ENCODE (The "Promise")

Create `docs/ARCHITECTURE_PLAN.md` with risk grade, file tree, interface contracts, data flow, dependencies, and Section 4 pre-check.

Template: `references/ql-bootstrap-templates.md`.

### Step 6: Initialize META_LEDGER

Create `docs/META_LEDGER.md` with genesis entry.

Template: `references/ql-bootstrap-templates.md`.

### Step 6.5: Create Backlog

Create `docs/BACKLOG.md` with blocker/backlog/wishlist structure.

Template: `references/ql-bootstrap-templates.md`.

### Step 7: Calculate Genesis Hash

```python
import hashlib
combined = read_file("docs/CONCEPT.md") + read_file("docs/ARCHITECTURE_PLAN.md")
genesis_hash = hashlib.sha256(combined.encode()).hexdigest()
```

### Step 8: Routing Decision

| Grade | Action |
|-------|--------|
| L1 | "DNA Seeded. Low risk. Proceed to /ql-implement." |
| L2 | "DNA Seeded. Logic changes detected. Invoke /ql-audit before implementation." |
| L3 | "DNA Seeded. CRITICAL: Security path detected. /ql-audit MANDATORY." |

**Note**: Bootstrap is for **workspace genesis only**. For new features, use `/ql-plan`.

### Step 9: Final Report

Report project name, genesis hash, risk grade, created artifacts, and next action.

Template: `references/ql-bootstrap-templates.md`.

## Constraints

- **NEVER** bootstrap over existing DNA (check first)
- **NEVER** skip the "Why" documentation
- **NEVER** assign L1 to anything touching security/auth
- **ALWAYS** calculate and record genesis hash
- **ALWAYS** require /ql-audit for L2/L3 before implementation

## Success Criteria

Bootstrap succeeds when:

- [ ] CONCEPT.md exists with clear "Why" statement
- [ ] ARCHITECTURE_PLAN.md exists with file tree and risk assessment
- [ ] META_LEDGER.md exists with genesis entry and hash
- [ ] BACKLOG.md exists with template structure
- [ ] Genesis hash calculated and recorded
- [ ] Risk grade properly assigned (L1/L2/L3)
- [ ] Required directories created (.failsafe/governance/, docs/)
- [ ] Routing decision provided based on risk grade

## Integration with S.H.I.E.L.D.

This skill implements:

- **Genesis Protocol**: Seeds the Merkle-chain DNA for new projects
- **Risk-Based Routing**: Routes to appropriate gate based on risk grade
- **Hash Chain Initialization**: Establishes cryptographic audit trail from genesis
- **Documentation-First**: Requires concept and architecture before implementation

---

**Remember**: Genesis is the foundation. A weak genesis compromises the entire chain.
