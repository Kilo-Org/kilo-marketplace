---
name: technical-design-document
description: "Create a Technical Design Document (TDD) for game development projects. Use when the user asks to write, draft, scaffold, structure, or review a Technical Design Document, a TDD, a technical specification for a game, coding standards plus technical overview plus build/release policy for a game project, or a pre-production engineering plan that complements a GDD (Game Design Document). Triggers on phrases like 'write a TDD', 'create a technical design document', 'document the engine/modules/tools for our game', 'what goes into a TDD', or 'draft coding standards and branch policy for our game team'."
license: MIT
metadata:
  category: development
  source:
    repository: 'https://github.com/Siitoo/Technical-Design-Document'
    path: README.md
    license: MIT
---

# Technical Design Document (TDD) Writer

This skill produces a Technical Design Document for a game project. A TDD is the engineering counterpart of the Game Design Document (GDD): it states how the game will be built, not how it will play. It is written by the technical lead / programming lead during pre-production and is updated as production evolves.

The full source guide lives in `references/tdd-guide.md`. Image assets (class diagrams, branch policy, file-type charts, etc.) live in `assets/docs/` and can be embedded when visual references help the team.

## When to Use This Skill

Use this skill when the user wants to:

- Create, draft, or scaffold a new Technical Design Document for a game
- Add or update a section of an existing TDD (e.g. "add a Branches Policy section")
- Review/audit an existing TDD for missing sections
- Translate the high-level content of a GDD into technical specs (classes, modules, libraries, performance budgets)
- Establish coding standards, naming conventions, file-type rules, or branch policy for a game team

Do **not** use this skill for:

- Game Design Documents (GDD) — these describe gameplay and design intent, not engineering implementation
- Pure code reviews or refactors of a single module
- Postmortems / production reports

## TDD Structure (Author This Outline)

A complete TDD contains the following sections. Adapt naming to the team's conventions, but do not skip sections without an explicit reason from the user.

### 0. Cover page / change log

- Game name, team/company name, members, current date
- TDD version number (incremented each time the document is updated)
- A short change-log table: version, date, author, summary of changes

### 1. Table of contents

Introduction, Technical Overview, Game Mechanics, Build Creation, Resource Management and File Formats, Tool Instructions (plus any team-specific sections such as Branches Policy, Performance Budgets, Risk Register).

### 2. Introduction

- Purpose of the game
- Technical goals
- Target platform (hardware + software minimum and recommended specs)
- External tools used in development
- Development team roles
- Development timeline
- Branches policy (high-level pointer; details in §7)

### 3. Technical Overview

- Naming conventions (language-specific: e.g. C++/C# style guides; reference the team's house style)
- Technologies used (engine, languages, libraries, middleware — static vs. dynamic linking decision)
- Data layout (save-game format, persistent player data, config files)
- Libraries (STL, custom engine modules, third-party SDKs, asset pipelines)
- Performance budgets (target FPS, frame-time budgets for logic/audio/graphics/IO in ms)
- Analysis platform (profilers such as Brofiler, Tracy, Superluminal, PIX, RenderDoc — when and how they are used)

### 4. Game Mechanics

For every mechanic identified in the GDD, document:

- Overview of the mechanic
- Game structures: main classes involved (entity, level, UI, IA/AI, factory, observer, etc.)
- UML diagrams to clarify the structure (class diagram, object diagram, composite structure diagram, package diagram for resource layout)
- Main loop (input → simulation → rendering → present)
- Game states (boot, menu, loading, gameplay, pause, cutscene, end) and the state machine that transitions between them
- State functionality: what each state allows and forbids

### 5. Build Creation

- List every release/milestone build the team will cut (alpha, beta, vertical slice, release candidate, gold master)
- Acceptance criteria for each build: features complete, bugs fixed, performance targets met, content lock status
- Who signs off on each build

### 6. Resource Management and File Formats

- File types used in development: images (png/jpg/etc.), UML tools, audio (wav/ogg), documents
- Per-file-type: extension, max size, color depth, compression rules
- Folder layout for source, assets, builds, tools, docs
- Compression policy (per-folder, per-file-type, runtime cache)
- Asset naming conventions

### 7. Branches Policy

Adopt (or adapt) GitFlow-style branching:

- `master` — release production
- `develop` — integration for the next release
- Supporting branches:
  - `feature/*` — work for a distant future release
  - `release/*` — stabilize a release candidate
  - `hotfix/*` — patch a critical bug on master

Document naming, merge rules, code-review requirements, and CI gating per branch.

### 8. Tool Instructions

For every external tool used (engine editor, profiler, asset pipeline, scripting tool, build server):

- Name and version
- How to install / configure
- How to invoke it for this project
- How to update the instructions when the tool changes

### 9. Optional but recommended

- Performance budgets table (per system: target ms, hard ms)
- Risk register (top technical risks + mitigations)
- Coding conventions (file headers, pointer naming, function signature style, class structure)
- UML structure overview (package diagram for resource management, deployment diagram for runtime platforms)

## Workflow

When the user asks for a TDD:

1. **Confirm scope** — what game, what engine, what target platforms, what team size, what deadline. If any of these are missing, ask the user before writing.
2. **Open `references/tdd-guide.md`** for the full reference text and terminology used in this domain.
3. **Author the document** in the structure above. Use headings exactly as listed unless the user has a house template. Keep prose concise — a TDD is a reference, not an essay.
4. **Embed diagrams from `assets/docs/`** when the team needs visuals (class diagrams, branch policy diagram, file-type chart). Reference them with relative paths so the document is portable.
5. **Include a version + change-log block** at the top so future edits are tracked.
6. **Validate** before handing back: every section in §0 through §8 must exist; if a section is intentionally empty, write `TBD` followed by a reason rather than deleting it.
7. **Save** the TDD as a Markdown file (default name: `TDD.md`) in the repository root or wherever the user requests.

## Coding Standards Cheat Sheet

When the user asks specifically for the coding-standards section, draw on:

- **Conventions**: indentation, brace style, line length, comment style (file header, function header, TODO markers).
- **Naming**: classes (`PascalCase`), functions (`camelCase` or `PascalCase` per language), constants (`UPPER_SNAKE_CASE`), member variables (trailing `m_` or trailing `_` per team), pointers (`p` prefix, optional).
- **File headers**: copyright, file purpose, author, last-modified.
- **Functions**: order of params (in, out, in/out), const-correctness, error return policy.
- **Class structure**: public, then protected, then private; rule of five / three / zero as appropriate; explicit constructors; prefer composition.
- **Languages**: for C++ see `geosoft.no/development/cppstyle.html`; for C# see Microsoft's C# Coding Conventions; for TypeScript / Lua / GDScript use the team's engine-specific guide.

## Key References

- Full reference guide: `references/tdd-guide.md` (the source document this skill is based on)
- Diagrams: `assets/docs/` (branches.jpg, classdiagram.jpg, objectdiagram.jpg, packageModel.jpg, conventions.jpg, fpsTarget.jpg, toolsInstructions.jpg, etc.)
- **The Game Production Handbook** — Heather Maxwell Chandler (canonical definition of coding standards, technical design, tool instructions)
- **Game Development and Production** — Erik Bethke
- **Git branching models** — Vincent Driessen (GitFlow)