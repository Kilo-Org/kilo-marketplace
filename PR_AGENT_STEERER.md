# Pull Request: Add agent-steerer skill

## Title

Add agent-steerer skill

## Description

### What Problem It Solves

Agent-driven software projects often suffer from preventable issues: inverted logic gates, security vulnerabilities discovered post-deployment, swallowed errors, thread safety problems, and massive PRs that are hard to review. This skill captures lessons learned from past agent-built projects to prevent these pitfalls.

### Who Uses This Workflow

- **Developers starting new projects with agents** who want to avoid common mistakes
- **Team leads** reviewing agent-generated architecture decisions
- **DevOps/engineers** establishing agent workflows for their teams
- **Agents** learning best practices for building reliable, maintainable codebases

### Attribution / Inspiration Source

**Inspired by:** Real-world git history analysis of agent-built projects, distilling patterns of what went wrong and how to prevent them.

**Core content:**
- 6 core principles for agent-driven projects
- Anti-pattern checklist for reviewing agent code
- Required agent workflow for building codebases

### Example Output Snippets

**Core Principles (from SKILL.md)**

> ### 1. Define Schema/Contracts FIRST
>
> Before any code is written, establish clear input/output contracts, API schemas, and data models. This prevents issues like inverted logic gates where validation logic was backwards.
>
> **Anti-pattern observed:** T1 gate had inverted logic — pass/fail conditions were reversed because no contract was defined upfront.

> ### 2. Security From Day 1
>
> Security must be built into the initial design, not added later as patches. Agents tend to focus on functionality and defer security.
>
> **Anti-patterns observed:**
> - Path traversal vulnerabilities discovered post-deployment
> - Missing authentication checks
> - `file://` URL handling without validation
> - Hardcoded credentials/secrets

**Anti-Pattern Checklist (from SKILL.md)**

| Anti-Pattern | What to Do Instead |
|--------------|-------------------|
| Hardcoded strings/URLs/paths | Use config/env vars |
| Bare `except:` or `except Exception:` | Catch specific exceptions |
| `await` on sync function | Remove await or make async |
| No input validation | Add validation at boundaries |
| Missing error handling | Propagate errors up |
| Global mutable state | Pass state explicitly |
| No tests for async code | Write explicit async tests |

**Required Agent Workflow (from SKILL.md)**

> For any agent building a codebase:
>
> 1. **Before writing code:** Define schemas, contracts, error types
> 2. **During coding:** Validate inputs, handle errors explicitly, use env vars
> 3. **After each feature:** Run lint, typecheck, tests
> 4. **Before merging:** Security review, concurrency review, error handling review

### Example of How It's Used

**User prompt:**
```
I'm starting a new project with an agent. What guidance should I give it to avoid common pitfalls?
```

**Skill output:**
The skill provides 6 core principles to follow:
1. Define Schema/Contracts FIRST
2. Security From Day 1
3. Error Handling Is Architecture
4. Concurrency Needs Explicit Modeling
5. Incremental Validation Over Giant PRs
6. Validate Before Moving On

Plus an anti-pattern checklist for code review.

### Skill Structure

```
skills/agent-steerer/
└── SKILL.md                              # Skill definition & workflow
```

### Checklist

- [x] Solves a real problem (based on actual agent project lessons learned)
- [x] Well-documented with clear instructions and examples
- [x] Practical guidance for developers and agents
- [x] Includes anti-pattern checklist for code review
- [x] Safe (guidance-only skill; no destructive operations)