---
name: skill-creator
description: "Guides the end-to-end creation and packaging of agent skills, from requirements gathering through SKILL.md authoring, bundled resource setup (scripts, references, assets), validation, and zip distribution. Use when creating a new skill, updating an existing skill, or packaging a skill for distribution."
license: Complete terms in LICENSE.txt
metadata:
  category: development
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: skill-creator
    license_path: skill-creator/LICENSE.txt
---

# Skill Creator

Guides creation of effective agent skills — modular packages that extend agent capabilities with specialized workflows, tool integrations, domain expertise, and bundled resources.

## Skill Structure

```
skill-name/
├── SKILL.md              # Required — metadata + instructions
├── scripts/              # Executable code (deterministic, reusable)
├── references/           # Documentation loaded into context as needed
└── assets/               # Output resources (templates, images, fonts)
```

**Progressive disclosure**: Metadata (~100 words) is always loaded. SKILL.md body (<5k words) loads on trigger. Bundled resources load on demand.

## Creation Workflow

### 1. Understand the Skill (Gather Examples)

Clarify concrete usage examples before writing anything:
- What functionality should the skill support?
- What would a user say to trigger it?
- What are 2-3 representative tasks it handles?

Skip only when usage patterns are already well understood.

### 2. Plan Reusable Contents

For each example, identify what resources would prevent repeated work:

| Resource type | When to include | Example |
|--------------|----------------|---------|
| `scripts/` | Same code rewritten repeatedly; deterministic reliability needed | `scripts/rotate_pdf.py` |
| `references/` | Documentation the agent should consult while working | `references/schema.md` |
| `assets/` | Files used in output (templates, boilerplate, images) | `assets/hello-world/` |

### 3. Initialize the Skill

For new skills, run:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

Creates the skill directory with a SKILL.md template (frontmatter + TODO placeholders) and example `scripts/`, `references/`, `assets/` directories. Skip if iterating on an existing skill.

### 4. Edit the Skill

**Write for another agent instance** — include non-obvious procedural knowledge and domain-specific details.

**SKILL.md authoring rules**:
- Use **imperative/infinitive form** (verb-first instructions), not second person
- Use objective language: "To accomplish X, do Y" — not "You should do X"
- Metadata `description` must be specific about what the skill does and when to use it, in third person ("Generates..." not "Generate...")
- Keep SKILL.md lean: move detailed reference material, schemas, and long examples to `references/`
- For large reference files (>10k words), include grep search patterns in SKILL.md
- Avoid duplicating content between SKILL.md and reference files

**Start implementation with bundled resources** (scripts, references, assets), then write the SKILL.md body. Delete unused example directories from init.

### 5. Package for Distribution

```bash
scripts/package_skill.py <path/to/skill-folder>
```

Validates frontmatter, naming conventions, directory structure, and description quality, then produces a zip file. Fix any validation errors and re-run if needed.

### 6. Iterate

After real usage: notice struggles or inefficiencies, update SKILL.md or bundled resources, and test again.
