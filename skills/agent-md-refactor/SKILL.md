---
name: agent-md-refactor
description: "Refactors bloated AGENTS.md, CLAUDE.md, or COPILOT.md files into a minimal root file with linked, categorized sub-files following progressive disclosure principles. Identifies contradictions, extracts essentials, groups instructions by topic, and flags redundant content for deletion. Use when agent instruction files exceed ~50 lines or contain mixed concerns."
license: MIT
metadata:
  category: development
  source:
    repository: 'https://github.com/softaworks/agent-toolkit'
    path: skills/agent-md-refactor
    license_path: LICENSE
---

# Agent MD Refactor

Splits monolithic agent instruction files (AGENTS.md, CLAUDE.md, COPILOT.md) into a minimal root file with linked sub-files, following progressive disclosure principles.

## Workflow

| Phase | Action | Output |
|-------|--------|--------|
| 1 | Find contradictions | Conflicts to resolve with user |
| 2 | Extract essentials | Core instructions for root file |
| 3 | Categorize remaining | Logical topic groupings |
| 4 | Create file structure | Root + linked `.claude/` files |
| 5 | Flag for deletion | Redundant/vague instructions removed |

### Phase 1: Find Contradictions

Scan for conflicting instructions (e.g., "use semicolons" vs. "no semicolons", incompatible tool preferences). For each contradiction, present both instructions and ask the user to resolve before proceeding.

### Phase 2: Extract Essentials

Keep **only** universal content in the root file:

| Keep in root | Move to linked files |
|-------------|---------------------|
| One-sentence project description | Language-specific conventions |
| Non-standard package manager (if not npm) | Testing guidelines |
| Custom build/test/typecheck commands | Code style details |
| Critical overrides of default behavior | Framework patterns |
| Rules that apply to 100% of tasks | Git workflow, docs standards |

### Phase 3: Categorize Remaining Instructions

Group into 3-8 self-contained topic files. Common categories:

`typescript.md`, `testing.md`, `code-style.md`, `git-workflow.md`, `architecture.md`, `api-design.md`, `security.md`, `performance.md`

Each file must be self-contained for its topic with only actionable instructions.

### Phase 4: Create File Structure

```
project-root/
├── CLAUDE.md                  # Minimal root (<50 lines) with links
└── .claude/
    ├── typescript.md
    ├── testing.md
    ├── code-style.md
    └── architecture.md
```

**Root file template**:
```markdown
# Project Name
One-sentence description.

## Commands
- `pnpm dev` — Start development server
- `pnpm test` — Run tests
- `pnpm build` — Production build

## Guidelines
- [Code Style](.claude/code-style.md)
- [Testing](.claude/testing.md)
- [TypeScript](.claude/typescript.md)
```

### Phase 5: Flag for Deletion

Remove instructions that are:

| Criterion | Example |
|-----------|---------|
| Redundant | "Use TypeScript" in a .ts project |
| Too vague | "Write clean code" |
| Default behavior | "Use descriptive variable names" |
| Outdated | References deprecated APIs |

## Verification Checklist

- Root file is under 50 lines with only universal info
- All links point to existing files
- No contradictions remain
- Every instruction is specific and actionable
- No instructions were lost (unless flagged for deletion)
- Each linked file stands alone
