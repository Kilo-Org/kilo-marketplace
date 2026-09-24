# Skills Documentation

This document describes how skills should be structured in this repository. For plugins, see [Plugins](#plugins) below and [plugins/README.md](plugins/README.md).

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
  category: development # or business, etc.
  author: author-name # Optional - who created the skill
  source: # Optional - for skills from external sources
    repository: https://github.com/org/repo
    path: path/to/skill/in/repo
    license_path: path/to/LICENSE # Path to LICENSE in source repo (alternative to license)
    commit: 0123456789abcdef0123456789abcdef01234567 # Imported revision
---
```

#### Frontmatter Fields

| Field                        | Required | Description                                                           |
| ---------------------------- | -------- | --------------------------------------------------------------------- |
| `name`                       | Yes      | Unique identifier for the skill (kebab-case)                          |
| `description`                | Yes      | Clear description of what the skill does and when to use it           |
| `license`                    | Yes*     | SPDX license identifier. Either `license` or `metadata.source.license_path` is required, not both |
| `metadata`                   | No       | Container for additional metadata                                     |
| `metadata.category`          | No       | Category for organization (e.g., `development`, `business`) |
| `metadata.author`            | No       | Author or organization name                                           |
| `metadata.version`           | No       | Semantic version string                                               |
| `metadata.source`            | No       | Source information for external skills                                |
| `metadata.source.repository` | No       | URL to the source repository                                          |
| `metadata.source.path`       | No       | Path within the repository                                            |
| `metadata.source.license_path` | Yes*  | Path to LICENSE in source repo (alternative to `license`)             |
| `metadata.source.commit`    | New      | Full 40-character Git SHA for new imports and updates                  |

### Markdown Body (Required)

After the frontmatter, include the skill's documentation in Markdown format.

If you need more information, checkout https://agentskills.io/llms.txt

## Adding a remote skill

when asked to add a skill from a github url
use the instructions in .kilocode/skills/add-remote-skill/SKILL.md

## Plugins

Plugins extend Kilo with hooks, custom tools, auth providers, model providers, and runtime behavior. Each plugin lives in one directory named after its `id` and contains one `PLUGIN.yaml` file:

```
plugins/
  my-plugin/PLUGIN.yaml
  @scope/package/PLUGIN.yaml
  git/github.com/owner/repo/PLUGIN.yaml
  git/github.com/owner/repo/plugins/x/PLUGIN.yaml
```

Required `PLUGIN.yaml` fields: `id`, `name`, `description`, `category`, `author`, `url`, and `content`. Do not set `tags`; the generator derives `tags` from `category`. Valid categories are `business`, `data`, `development`, `observability`, `productivity`, `providers`, `search`, and `web-automation`.

The directory path must equal `id`. For a registry plugin, `id` is the exact npm package name and `content` is a registry specifier for that same package with an optional version, range, or tag. For a git plugin, `id` is the normalized git identity `git/` plus the repo without scheme or trailing `.git`, plus the subpath when present, and `content` is `git:<repo>[@ref][#subpath]`.

Git plugins must be self-contained. Kilo clones the repository and loads the plugin directly, and it does not install npm dependencies for git plugins. The `package.json` must declare at least one target supported by the Kilo client, such as a server or TUI entry. This repository's generator validates catalog fields and content specifiers only, not the remote package manifest, so see [plugins/README.md](plugins/README.md#package-requirements) for the target rules.

After adding or changing a plugin, regenerate the catalog and run the checks from `bin/`:

```bash
cd bin
pnpm install
pnpm exec tsx generate-plugins-marketplace.ts
pnpm test
pnpm run typecheck:plugins
```

Do not edit `plugins/marketplace.yaml` manually. Submit plugins through a pull request; direct pushes are not accepted. See [plugins/README.md](plugins/README.md) for the full rules.
