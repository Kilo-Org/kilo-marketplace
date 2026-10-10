---
name: codebase-edu-doc-writer
description: This skill creates educational documentation for codebases being learned. Use it when users want beginner guides, class curricula, poems and mnemonics for key concepts, or study materials. It produces well-organized markdown with learning paths, memorization aids, diagrams, and progressive study materials. Useful for college and high-school students or beginners learning complex rendering or game engines.
license: MIT
metadata:
  category: development
  author: yhyu13
---

# Codebase Educational Documentation Writer

This skill creates educational documentation for a codebase being learned, transforming a
complex codebase into approachable study materials for beginners.

## When to Use This Skill

- User says they are a beginner and need guidance on where to start learning a codebase
- User asks for a "learning path," "beginner guide," "curriculum," or "study plan"
- User asks to create mnemonics, poems, or songs to memorize concepts
- User asks to break down documentation into "classes" or lessons
- User asks to create a "mental map" or visual overview of a codebase
- User asks to dump documentation to a specific directory

## Workflow

### Step 1: Analyze the Codebase Structure

Read the top-level architecture files to understand the codebase layout:

1. Read the main README and any architecture overview docs (AGENTS.md, CLAUDE.md, etc.)
2. List the top-level source directories
3. Identify the main entry points and core classes
4. Map the high-level architecture layers

### Step 2: Identify Key Classes and Concepts

For each major section identified:

1. Read the core header files for that section
2. Identify the public interface and key methods
3. Determine the relationships between classes
4. Note any important patterns (factory, singleton, interface, etc.)

### Step 3: Determine Output Structure

Create documentation in the requested directory (e.g., `doc/class/`). The standard structure:

| Document Type | Content | File Pattern |
|---------------|---------|-------------|
| Beginner's Guide | Overall curriculum, 5-6 classes | `doc/class/beginner_guide.md` |
| Class Notes | One file per class (~1hr study each) | `doc/class/XX_section.md` |
| Key Concept Poem | Poem + 中文口诀 + quick reference | `doc/class/kc_XX_concept.md` |
| Mental Map | Architecture overview diagrams | `doc/class/architecture.md` |

### Step 4: Create the Documents

#### Beginner Guide Structure

The guide should be organized into **Classes** (~1 hour each):

1. **Class 1**: Entry point / Main loop
2. **Class 2**: Data layer (scene objects, world)
3. **Class 3**: Abstraction layer (GPU resource creation)
4. **Class 4**: Pipeline / orchestration (render graph)
5. **Class 5**: Core rendering (batches, meshlets, G-buffer)
6. **Class 6**: Advanced effects (lighting, post-processing, ray tracing)

Each class should include:
- Files to read (in order)
- Key concepts (with mermaid diagrams)
- 15-minute exercise
- Mental check quiz

#### Key Concept Poems Structure

Each key concept gets its own file containing:
- English poem (4-8 verses, simple rhyme)
- 中文口诀 (Chinese mnemonic verse)
- Quick reference table
- One-line summary (bilingual)

#### Mermaid Diagrams to Include

Use mermaid for visual memorization:
- `flowchart` for processes and data flow
- `mindmap` for directory structure
- `sequenceDiagram` for call flows (if applicable)
- `flowchart TD` for two-phase operations

### Step 5: Format Rules

- Use Chinese and English together for key concepts (bilingual recall)
- Poems should be simple, 4-8 lines, easy to recite
- Diagrams should fit on one screen (no external references)
- Use ASCII/text diagrams as fallback where mermaid may not render

### Step 6: Output Location

Always write to the user-specified directory. Common patterns:
- User specifies: `dump to /path/to/doc/class` → write to `/path/to/doc/class/`
- Default location: `doc/class/` in the project root

## Reusable Resources

### Templates

See `references/` for reusable document templates:
- `class_template.md` — template for class/lesson notes
- `kc_template.md` — template for key concept poem files
- `beginner_guide_template.md` — template for the main beginner guide

### Assets

The `assets/` directory contains any boilerplate or reference material:
- `glossary_terms.md` — standard glossary terms for graphics engines
- `prerequisite_topics.md` — topics beginners should study first

## Key Patterns to Follow

### Adding a New Class File

```markdown
# Class N: Title
## Goal: Understanding Title after ~1 hour of study

### Files to Read (in order)
1. `source/path/file.h` — Description

### Key Concept: Name

[English poem]
[中文口诀]

[Quick reference table]

### Exercise (15 min)
1. Step one
2. Step two

### Mental Check
- [ ] Question 1
- [ ] Question 2
```

### Adding a New Key Concept File

```markdown
# Key Concept: Name

## English Poem

[4-8 lines of simple verse]

## 中文口诀

[Chinese mnemonic verse]

## Quick Reference

| Question | Answer |
|----------|--------|
| ... | ... |

## One-Line Summary

> [Bilingual summary line]
```

## Quality Checklist

Before completing documentation:

- [ ] All mermaid diagrams render correctly (or have ASCII fallback)
- [ ] Every Key Concept has English poem + 中文口诀
- [ ] Every class has exercise + mental check
- [ ] File names follow XX_name.md pattern for ordering
- [ ] Documents are written to the user-specified directory
- [ ] Bilingual content (Chinese + English) for memorization content
- [ ] No broken links between documents
