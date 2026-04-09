# Skills Documentation

This document describes how skills should be structured in this repository.

## What is a Skill?

Skills are modular, self-contained packages that extend an agent's capabilities by providing specialized knowledge, workflows, and tools. They transform a general-purpose agent into a specialized agent equipped with procedural knowledge for specific domains or tasks.

## Skill Directory Structure

Every skill consists of a required `SKILL.md` file and optional bundled resources:

```
skill-name/
├── SKILL.md              # Required - Main skill definition
├── LICENSE               # Recommended - License terms
├── scripts/              # Optional - Executable code (Python/Bash/etc.)
├── references/           # Optional - Documentation loaded into context as needed
├── assets/               # Optional - Files used in output (templates, icons, fonts)
└── examples/             # Optional - Example files demonstrating usage
```

## SKILL.md Structure

### Note on Contributed Skills

All contributed skills must reference an external repository in the `metadata.source` section of the SKILL.md frontmatter. The Kilo Marketplace does not host the source code for third-party skills directly. See [CONTRIBUTING.md](CONTRIBUTING.md#skills-must-be-hosted-externally) for details and examples.

### Frontmatter (Required)

Every `SKILL.md` file must begin with YAML frontmatter containing metadata:

```yaml
---
name: skill-name
description: A clear description of what the skill does and when it should be used. Use third-person (e.g., "This skill should be used when...").
license: MIT # Either license or license_path is required, not both
metadata:
  category: development # or business-marketing, etc.
  author: author-name # Optional - who created the skill
  source: # Optional - for skills from external sources
    repository: https://github.com/org/repo
    path: path/to/skill/in/repo
    license_path: path/to/LICENSE # Path to LICENSE in source repo (alternative to license)
---
```

#### Frontmatter Fields

| Field                        | Required | Description                                                           |
| ---------------------------- | -------- | --------------------------------------------------------------------- |
| `name`                       | Yes      | Unique identifier for the skill (kebab-case)                          |
| `description`                | Yes      | Clear description of what the skill does and when to use it           |
| `license`                    | Yes*     | SPDX license identifier. Either `license` or `metadata.source.license_path` is required, not both |
| `metadata`                   | No       | Container for additional metadata                                     |
| `metadata.category`          | No       | Category for organization (e.g., `development`, `business-marketing`) |
| `metadata.author`            | No       | Author or organization name                                           |
| `metadata.version`           | No       | Semantic version string                                               |
| `metadata.source`            | No       | Source information for external skills                                |
| `metadata.source.repository` | No       | URL to the source repository                                          |
| `metadata.source.path`       | No       | Path within the repository                                            |
| `metadata.source.license_path` | Yes*  | Path to LICENSE in source repo (alternative to `license`)             |

### Markdown Body (Required)

After the frontmatter, include the skill's documentation in Markdown format.

If you need more information, checkout https://agentskills.io/llms.txt

## Adding a remote skill

when asked to add a skill from a github url
use the instructions in .kilocode/skills/add-remote-skill/SKILL.md
