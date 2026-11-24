---
name: gleann-code-intelligence
description: >-
  Answers codebase questions and plans safe changes using Gleann MCP — semantic
  search, graph impact analysis, and persistent memory. Use when searching or
  understanding a codebase, before renaming or refactoring a symbol, when a
  gleann index exists for the project, or when the user mentions gleann, code
  intelligence, blast radius, or indexed knowledge.
license: MIT
compatibility: >-
  Requires the gleann binary (https://github.com/tevfik/gleann) connected as an
  MCP server and at least one indexed codebase. Falls back to shell CLI when MCP
  tools are unavailable.
metadata:
  category: development
  author: tevfik
  source:
    repository: 'https://github.com/tevfik/gleann'
    path: skills/gleann-code-intelligence
    ref: main
    commit: ddf938446633e1d765c36e9e8f7b6902884cce8b
---

# Gleann Code Intelligence

Gleann is a local code-intelligence engine: hybrid semantic + lexical search
over indexed code and docs, a dependency graph (callers, callees, blast
radius), and a persistent memory store. Prefer it over grep/find when working
in an indexed project.

## Check what is indexed

Call `gleann://indexes` (MCP resource) or run `gleann index list`. Each index
shows passage count, backend, and tags. If no index covers the current
project, build one first: `gleann index build <path>`.

## Core MCP tools

- `gleann_search` — hybrid semantic + lexical search over code and docs
- `gleann_def` — go-to-definition for a symbol name
- `gleann_read` — read a file by path in compact mode (map / signatures / lines / task)
- `gleann_graph_neighbors` — direct callers and callees of a symbol (FQN or partial name)
- `gleann_impact` — transitive callers and affected files (blast radius) before changing a symbol
- `gleann_sync` — refresh the index after editing code
- `memory_context` / `memory_search` / `memory_remember` / `memory_forget` — persistent cross-session memory

## Typical workflows

- **Understand a repo**: `gleann_search` for concepts, `gleann_read` (map mode) for file skeletons.
- **Before editing a symbol**: `gleann_impact` to see blast radius; report affected files to the user when the change is risky.
- **Trace a flow**: `gleann_def` then `gleann_graph_neighbors` hop by hop.
- **After edits**: `gleann_sync` so later searches reflect the change.
- **Scoping**: filter by index tags (`gleann index tag <name> --add work`, then search scoped to the tag).

## CLI fallback

When MCP tools are not connected, use the `gleann` binary:

```bash
gleann search <index> <query>                 # semantic search
gleann graph map --index <index>              # compact repo map
gleann graph explain <fqn> --index <index>    # callers, callees, blast radius
gleann graph callers <fqn> --index <index>    # who calls it
gleann graph deps <fqn> --index <index>       # what it calls
gleann index sync <index>                     # refresh after edits
```

## Rules

- Search before reading blindly; read with `gleann_read` compact modes before opening whole files.
- Always run `gleann_impact` before renames, signature changes, or deletions of public symbols.
- Never delete or move files under the gleann model/index storage directories; manage indexes only through `gleann index` commands.
- `gleann_gain` reports tokens saved by `gleann_shell`/`gleann_read` since server start — useful when the user asks about context savings.
