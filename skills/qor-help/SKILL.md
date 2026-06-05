---
name: qor-help
description: >-
  Quick reference that summarizes the purpose and usage of all QoreLogic commands. Use when: (1) Need to understand available commands, (2) Unsure which command to use, or (3) Looking for command overview.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QoreLogic
    path: processed/skills-output/qor-help
---

# /ql-help - Command Summary

<skill>
  <trigger>/ql-help</trigger>
  <phase>ANY</phase>
  <persona>Governor</persona>
  <output>Concise summary of available QoreLogic commands</output>
</skill>

## Execution Protocol

### Step 1: Display Command Summary

Present the command table and decision tree below. No file reads required.

### Step 2: Route User

If the user asks about a specific command, direct them to invoke it. If unsure, recommend `/ql-status` first.

## Summary

| Command            | Purpose                                                                      | Typical When                                    |
| ------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------- |
| `/ql-bootstrap`    | Initialize QoreLogic DNA for a **new workspace** (CONCEPT, ARCHITECTURE_PLAN, META_LEDGER). | First-time setup only. NOT for new features. |
| `/ql-plan`         | Create implementation plan for a **new feature** (plan-*.md with phases, tests). | Planning a feature in an existing workspace. |
| `/ql-status`       | Diagnose lifecycle stage and next required action.                           | Any time you need current state.                |
| `/ql-audit`        | Judge review for L2/L3 risk work; produces PASS/VETO.                        | Before any high-risk change.                    |
| `/ql-implement`    | Execute work under KISS constraints after a PASS verdict.                    | After `/ql-audit` PASS.                         |
| `/ql-refactor`     | Apply scoped refactors with guardrails.                                      | After initial implementation or when requested. |
| `/ql-validate`     | Verify Merkle chain integrity and artifacts.                                 | Before delivery or handoff.                     |
| `/ql-substantiate` | Seal the session and record evidence.                                        | End of a completed work session.                |

## Quick Decision Tree

```
New workspace?     → /ql-bootstrap
New feature?       → /ql-plan
Check state?       → /ql-status
Ready to build?    → /ql-audit → /ql-implement
Done with session? → /ql-substantiate
```

## Constraints

- **NEVER** execute other skills from within ql-help (display only)
- **ALWAYS** recommend /ql-status when user is uncertain

## Success Criteria

- [ ] Command summary displayed
- [ ] User directed to appropriate next skill

## Integration with S.H.I.E.L.D.

This skill implements:

- **Lifecycle Navigation**: Entry point for discovering available commands
- **Zero-Read Design**: No file reads required, pure reference output
- **Governor Persona**: Routing guidance without execution
