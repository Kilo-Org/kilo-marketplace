---
name: agent-steerer
description: This skill should be used when starting new agent-driven software projects or when steering agents to build codebases. It provides lessons learned from past agent-built projects to prevent common pitfalls around security, architecture, error handling, and incremental validation.
license: MIT
metadata:
  category: development
---

# Agent Steerer

## Overview

This skill provides guidance for steering agents to build software projects correctly the first time. It captures lessons learned from analyzing git history of agent-built projects, distilling patterns of what went wrong and how to prevent them.

## When to Use This Skill

- Starting a new project with an agent
- Giving an agent instructions to build a substantial codebase
- Reviewing agent-generated architecture decisions
- Planning iterative agent workflows

## Core Principles

### 1. Define Schema/Contracts FIRST

Before any code is written, establish clear input/output contracts, API schemas, and data models. This prevents issues like inverted logic gates where validation logic was backwards.

**Anti-pattern observed:** T1 gate had inverted logic — pass/fail conditions were reversed because no contract was defined upfront.

### 2. Security From Day 1

Security must be built into the initial design, not added later as patches. Agents tend to focus on functionality and defer security.

**Anti-patterns observed:**
- Path traversal vulnerabilities discovered post-deployment
- Missing authentication checks
- `file://` URL handling without validation
- Hardcoded credentials/secrets

**What to require upfront:**
- Input validation on all boundaries
- Authentication/authorization hooks in architecture
- No `file://` URL support unless explicitly designed
- All secrets via environment variables from start

### 3. Error Handling Is Architecture

Design error propagation as a first-class concern. Bare `except:` handlers that swallow errors create fragile pipelines impossible to debug.

**Anti-pattern observed:** Pipeline had swallowed errors and bare except handlers, making debugging nearly impossible.

**Required patterns:**
- All exceptions must be caught, logged, and propagated appropriately
- Distinguish between recoverable and fatal errors
- Return structured error responses, never bare `false`/`null`

### 4. Concurrency Needs Explicit Modeling

Async code has subtle pitfalls. Agents often assume sequential execution where concurrent execution happens.

**Anti-patterns observed:**
- Thread safety issues in LLM client
- Deadlocks under concurrent load
- `await` on sync functions (or vice versa)

**Required patterns:**
- Mark async functions explicitly with `async def`
- Never `await` synchronous functions
- Use thread pools for blocking I/O in async context
- Test concurrent access patterns explicitly

### 5. Incremental Validation Over Giant PRs

Ship smaller chunks. Agents that build for too long without validation produce large PRs with tangled issues.

**Anti-pattern observed:** Many fix branches merged at once suggests rushed integration of a large amount of work.

**Required workflow:**
1. Build smallest viable feature
2. Validate it works (tests, lint, typecheck)
3. Only then proceed to next feature
4. Merge frequently, not at the end

### 6. Validate Before Moving On

After each agent task completes, verify before proceeding:
- Run linting (`ruff`, `mypy`, etc.)
- Run type checking
- Run relevant tests
- Review the generated code for anti-patterns

## Anti-Pattern Checklist

When reviewing agent-generated code, check for these warning signs:

| Anti-Pattern | What to Do Instead |
|--------------|-------------------|
| Hardcoded strings/URLs/paths | Use config/env vars |
| Bare `except:` or `except Exception:` | Catch specific exceptions |
| `await` on sync function | Remove await or make async |
| No input validation | Add validation at boundaries |
| Missing error handling | Propagate errors up |
| Global mutable state | Pass state explicitly |
| No tests for async code | Write explicit async tests |

## Required Agent Workflow

For any agent building a codebase:

1. **Before writing code:** Define schemas, contracts, error types
2. **During coding:** Validate inputs, handle errors explicitly, use env vars
3. **After each feature:** Run lint, typecheck, tests
4. **Before merging:** Security review, concurrency review, error handling review

## References

The memory graph contains detailed lessons under:
- `AMG Project Learning` — specific failures observed in past project
- `Agent Steering Best Practices` — derived guidelines

To retrieve these: use `memory_search_nodes` with query "agent steering" or "AMG project learning".