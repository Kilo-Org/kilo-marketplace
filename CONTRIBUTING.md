# Contributing to Kilo Marketplace

Thank you for your interest in contributing to the Kilo Marketplace! This guide will help you add new skills that benefit the entire community.

## Contributing Plugins

To contribute an npm or git plugin, follow the [plugin contribution workflow](plugins/README.md#contribution-workflow). It covers scoped and unscoped package directories, supported registry and git source specifiers, the normalized git identity rule for `id`, server and TUI manifest requirements, and catalog generation and checks.

Registry plugin source code stays in its own repository and is published to npm. Git plugin source code can live in any public git repository, or inside this marketplace repository. Git plugins must be self-contained: Kilo clones the repository and loads the plugin directly, and it does not install npm dependencies for git plugins in this version. Contributions are accepted through pull requests only.

## Before You Start

- Ensure your skill is based on a **real use case**, not a hypothetical scenario.
- Search existing skills to avoid duplicates.
- If possible, attribute the use case to the original person or source.

## Skill Requirements

All skills must:

1. **Solve a real problem** - Based on actual usage, not theoretical applications.
2. **Be well-documented** - Include clear instructions, examples, and use cases.
3. **Be accessible** - Written for non-technical users when possible.
4. **Include examples** - Show practical, real-world usage.
5. **Be tested** - Verify the skill works in Kilo Code
6. **Be safe** - Confirm before destructive operations.

## Skill Structure

Create a new folder with your skill name (use lowercase and hyphens):

```
skills/
└──skill-name/
    └── SKILL.md
```

## SKILL.md Template

Use this template for your skill:

```markdown
---
name: skill-name
description: One-sentence description of what this skill does and when to use it.
---

# Skill Name

Detailed description of the skill and what it helps users accomplish.

## When to Use This Skill

- Bullet point use case 1
- Bullet point use case 2
- Bullet point use case 3

## What This Skill Does

1. **Capability 1**: Description
2. **Capability 2**: Description
3. **Capability 3**: Description

## How to Use

### Basic Usage
```

Simple example prompt

```

### Advanced Usage

```

More complex example prompt with options

```

## Example

**User**: "Example prompt"

**Output**:
```

Show what the skill produces

```

**Inspired by:** [Attribution to original source, if applicable]

## Tips

- Tip 1
- Tip 2
- Tip 3

## Common Use Cases

- Use case 1
- Use case 2
- Use case 3
```

## Skills Must Be Hosted Externally

The Kilo Marketplace does **not** host the source code for contributed skills directly. Instead, the marketplace acts as an index that references skills hosted in external repositories. This design allows skill authors to:

- **Maintain ownership** — you control your skill's repository and can update it at any time
- **Iterate independently** — push fixes and improvements without waiting for marketplace PRs
- **Keep licensing clear** — your repository is the canonical source with its own license

### How It Works

1. **Create a public GitHub repository** for your skill (or a repository containing multiple skills).
2. **Add a `SKILL.md`** file with the standard frontmatter (`name`, `description`, etc.).
3. **Submit a PR to this marketplace** that adds your skill using the `add-remote-skill` tooling (see below). The script automatically pulls in your skill and adds the `metadata.source` reference to the frontmatter.

The marketplace periodically syncs with source repositories to pull in updates, so you don't need to submit a new PR every time you change your skill.

### The `metadata.source` Frontmatter

Every contributed skill in the marketplace must have a `metadata.source` section in its YAML frontmatter. This tells the marketplace where the canonical source lives. **You don't need to add this yourself** — the `add-remote-skill` script (see below) adds it automatically when importing your skill. But for reference, here's what it looks like:

```yaml
---
name: my-skill
description: >-
  A clear description of what this skill does and when to use it.
metadata:
  category: development
  author: your-github-username
  suggest_for:
    filename:
      - "*.component.ts"
  source:
    repository: https://github.com/yourname/your-skill-repo
    path: path/to/skill
    license_path: LICENSE
    commit: 0123456789abcdef0123456789abcdef01234567
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `metadata.suggest_for.filename` | No | Non-empty list of patterns that make this skill highly probable from the filename alone; prefer distinctive forms such as `"*.component.ts"` and omit broad patterns such as `"*.ts"` |
| `metadata.suggest_for.vscode_extension` | No | Non-empty list of VS Code extension objects (`name` + `id`) that strongly indicate this skill is relevant, such as `{ name: "Jupyter", id: "ms-toolsai.jupyter" }` |
| `requirements` | No | Direct skill, VS Code extension, and MCP dependencies; see [Marketplace Requirements](#marketplace-requirements) |
| `metadata.source.repository` | **Yes** (for contributed skills) | URL to the GitHub repository containing your skill |
| `metadata.source.path` | **Yes** (for contributed skills) | Path within the repository to the skill directory |
| `metadata.source.license_path` | **Yes** (for contributed skills) | Path to the LICENSE file in the source repo |
| `metadata.source.commit` | **Yes** (for new imports and updates) | Full 40-character Git SHA of the imported upstream revision; managed by marketplace tooling |

Suggestion patterns are intentionally not exhaustive. A format being supported as input or output is not enough to add it: for example, a generic Markdown or audio file does not imply a writing or meeting-analysis task. Likewise, only list a VS Code extension when its installation strongly indicates the exact skill is relevant. A `suggest_for` object must contain at least one of `filename` or `vscode_extension`.

### Real-World Examples

Here are some existing skills in the marketplace and how they reference their source repositories:

**Angular Component** (from [analogjs/angular-skills](https://github.com/analogjs/angular-skills)):
```yaml
---
name: angular-component
description: Create modern Angular standalone components following v20+ best practices...
metadata:
  category: development
  source:
    repository: 'https://github.com/analogjs/angular-skills'
    path: skills/angular-component
    license_path: LICENSE
---
```

**Frontend Design** (from [anthropics/skills](https://github.com/anthropics/skills)):
```yaml
---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces...
metadata:
  category: development
  source:
    repository: 'https://github.com/anthropics/skills'
    path: skills/frontend-design
    license_path: skills/frontend-design/LICENSE.txt
---
```

**Create Pull Request** (from [cline/cline](https://github.com/cline/cline)):
```yaml
---
name: create-pull-request
description: Create a GitHub pull request following project conventions...
metadata:
  category: development
  source:
    repository: 'https://github.com/cline/cline'
    path: .cline/skills/create-pull-request
    license_path: LICENSE
---
```

### Adding Your Skill to the Marketplace

Once your skill is hosted in its own repository, use the `add-remote-skill` script to add it:

```bash
npx tsx bin/add-remote-skill.ts https://github.com/yourname/your-repo/tree/main/path/to/skill
```

This script will:
1. Clone only the skill directory from your repository
2. Copy it into `skills/<skill-name>/`
3. Update the SKILL.md frontmatter with the correct `metadata.source` fields

Then submit a PR with the result.

> **Note:** Skills submitted without a valid `metadata.source` referencing an external repository will not be accepted unless they are official Kilo skills.

## Pull Request Process

1. Fork the repository
2. Create a branch: `git checkout -b add-skill-name`
3. Host your skill in your own public GitHub repository (see above)
4. Run `npx tsx bin/add-remote-skill.ts <github-url-to-your-skill>` to add it
5. Commit your changes: `git commit -m "Add [Skill Name] skill"`
6. Push to your fork: `git push origin add-skill-name`
7. Open a Pull Request

## Pull Request Guidelines

Your PR should:

- **Title**: "Add [Skill Name] skill"
- **Description**: Explain the real-world use case and include:
  - What problem it solves
  - Who uses this workflow
  - Attribution/inspiration source
  - Example of how it's used

## Code of Conduct

- Be respectful and constructive
- Credit original sources and inspirations
- Focus on practical, helpful skills
- Write clear, accessible documentation
- Test your skills before submitting

## Questions?

Open an issue if you have questions about contributing or need help structuring your skill.

## Attribution

When adding a skill based on someone's workflow or use case, include proper attribution:

```markdown
**Inspired by:** [Person Name]'s workflow
```

or

```markdown
**Credit:** Based on [Company/Team]'s process
```

Examples:

- **Inspired by:** Dan Shipper's meeting analysis workflow
- **Inspired by:** Teresa Torres's content research process
- **Credit:** Based on Notion's documentation workflow

---

## Marketplace Requirements

Agent, skill, and MCP definitions may declare machine-readable dependencies with an optional top-level `requirements` field:

```yaml
requirements:
  skills:
    - jupyter-notebook
  vscode_extensions:
    - name: Jupyter
      id: ms-toolsai.jupyter
  mcps:
    - jupyter
```

The supported subgroups are exactly `skills`, `vscode_extensions`, and `mcps`. Each subgroup that is present must be a non-empty list, and every listed item is a direct required dependency; alternative or OR groups are not supported. Omit `requirements` entirely when the resource has no machine-readable dependencies.

Skill values must be exact marketplace skill IDs, and MCP values must match the `id` in the resource's `MCP.yaml`. Both are checked during marketplace generation. A skill cannot require itself, and an MCP cannot require itself. Dependencies between multiple resources are not expanded or checked for cycles. Each VS Code extension requires a human-readable `name` and a non-empty extension identifier in `id`. Authored values and list ordering are preserved without normalization, sorting, or deduplication.

Declare requirements at the top level of `agents/<id>/AGENT_DEFINITION.md`, `skills/<id>/SKILL.md`, or `mcps/<id>/MCP.yaml`. Generated agent requirements are emitted as `items[].content.requirements` so installation retains them. Generated skill and MCP requirements remain at `items[].requirements`, because skill content is a download URL and MCP content is runtime configuration.

Keep setup instructions that cannot be resolved to marketplace skills, MCPs, or VS Code extensions in `prerequisites`.

---

## Contributing MCP Servers

MCP (Model Context Protocol) servers extend Kilo Code's capabilities by connecting to external tools and services.

### MCP Requirements

All contributed MCP servers must:

1. **Provide real value** - Connect to useful external services or tools
2. **Be well-documented** - Include clear setup instructions and prerequisites
3. **Handle authentication securely** - Use environment variables for sensitive data
4. **Include multiple installation options** - When possible, provide NPX, Docker, and other methods

### MCP Structure

Create a new folder with your MCP server name (use lowercase and hyphens):

```
mcps/
└── service-name/
    └── MCP.yaml
```

The `MCP.yaml` file should contain:

```yaml
id: service-name
name: Service Name
description: Brief description of what this MCP server provides
author: author-name
url: https://github.com/org/repo
category: development
suggest_for:
  filename:
    - "*.i64"
prerequisites:
  - Required software or accounts
content:
  - name: NPX
    prerequisites:
      - Node.js
    content: |
      {
        "command": "npx",
        "args": ["-y", "@package/mcp-server"],
        "env": {
          "API_KEY": "{{API_KEY}}"
        }
      }
parameters:
  - name: API Key
    key: API_KEY
    placeholder: your_api_key_here
```

### MCP Properties

| Property | Required | Description |
|----------|----------|-------------|
| `id` | Yes | Unique identifier (kebab-case) |
| `name` | Yes | Display name for the MCP server |
| `description` | Yes | Clear description of capabilities |
| `author` | Yes | Author or organization name |
| `url` | Yes | Link to the MCP server repository |
| `category` | Yes | Primary category: `business`, `data`, `development`, `observability`, `productivity`, `search`, or `web-automation` |
| `suggest_for.filename` | No | Non-empty list of patterns that make this MCP server highly probable from the filename alone; prefer proprietary formats such as `"*.i64"` and omit broad patterns such as `"*.php"` |
| `suggest_for.vscode_extension` | No | Non-empty list of VS Code extension objects (`name` + `id`) that strongly indicate this MCP server is relevant, such as `{ name: "Jupyter", id: "ms-toolsai.jupyter" }` |
| `requirements` | No | Direct skill, VS Code extension, and MCP dependencies; see [Marketplace Requirements](#marketplace-requirements) |
| `skills` | No | Companion skill IDs installed with this MCP; see [MCP Companion Skills](#mcp-companion-skills) |
| `prerequisites` | No | Required software or accounts |
| `content` | Yes | Installation configuration(s) |
| `parameters` | No | User-configurable parameters |

Choose the single category that best represents how users will discover the MCP. Categories are broad navigation groups, not a list of every capability:

- `business` - Finance, payments, contracts, and other specialized business operations
- `data` - Databases, storage, data engineering, and persistent knowledge
- `development` - Code, repositories, developer platforms, and software tooling
- `observability` - Logs, errors, telemetry, and application or infrastructure monitoring
- `productivity` - Projects, workflows, collaboration, communication, and office tools
- `search` - Web, documentation, knowledge, and other information retrieval
- `web-automation` - Browser control, testing, scraping, and web content extraction

Propose a new category only when several MCPs share a distinct primary purpose that does not fit an existing category.

Suggestion patterns are intentionally not exhaustive. Do not list every format an MCP can open; add only filenames or VS Code extensions that strongly identify that exact MCP, such as `"*.ipynb"` or `{ name: "Jupyter", id: "ms-toolsai.jupyter" }`. A `suggest_for` object must contain at least one of `filename` or `vscode_extension`.

### Transport Types

**STDIO Transport (Local):**
```yaml
content: |
  {
    "command": "npx",
    "args": ["-y", "@package/mcp-server"],
    "env": {
      "API_KEY": "{{API_KEY}}"
    }
  }
```

**Streamable HTTP Transport (Remote):**
```yaml
content: |
  {
    "type": "streamable-http",
    "url": "https://your-server-url.com/mcp",
    "headers": {
      "Authorization": "Bearer {{API_TOKEN}}"
    }
  }
```

### Multiple Installation Options

Provide multiple ways to install when possible:

```yaml
content:
  - name: NPX
    prerequisites:
      - Node.js
    content: |
      {
        "command": "npx",
        "args": ["-y", "@package/mcp-server"]
      }
  - name: Docker
    prerequisites:
      - Docker
    content: |
      {
        "command": "docker",
        "args": ["run", "-i", "--rm", "mcp/server"]
      }
  - name: UVX
    prerequisites:
      - Python and uv
    content: |
      {
        "command": "uvx",
        "args": ["mcp-server-package"]
      }
```

### Parameter Configuration

Define user-configurable parameters:

```yaml
parameters:
  - name: API Key
    key: API_KEY
    placeholder: your_api_key_here
  - name: Optional Setting
    key: OPTIONAL_SETTING
    placeholder: default_value
    optional: true
```

### MCP Companion Skills

Use the optional top-level `skills` field to install workflows with an MCP server. Author a non-empty list of unique marketplace skill IDs, not URLs or descriptor objects. Each ID must be lowercase kebab-case, must not be a reserved device name such as `con`, and must reference `skills/<id>/SKILL.md`. The file must be a regular file with a matching frontmatter `name` and a non-empty `description`. Omit the field when the server has no companions.

When `skills` is present, the MCP's own `id` must also be safe lowercase kebab-case. Device names and prototype-related names such as `constructor`, `prototype`, and `__proto__` are not permitted. This extra validation does not change MCPs without companions.

Companion skills follow the same [external source-hosting requirement](#skills-must-be-hosted-externally) as standalone skills. Keep the canonical source in a public repository and retain `metadata.source` in the imported marketplace copy.

These fields have different purposes:

- `prerequisites` describes setup the user must complete, such as an account, credentials, or a running service. It does not install files.
- `requirements.skills` retains its existing meaning as direct dependency metadata. It is not expanded into companion archives and does not grant ownership of a skill installation.
- `skills` selects companion archives to install with the MCP in the same project or global scope. It does not recursively install a skill's dependencies.

Keep `skills` outside the JSON runtime configuration in `content`. It applies to every installation method for the MCP. Clients with bundle support disclose the companions before installation and manage removal using local installation ownership, not the current catalog's list. A pre-existing skill is not adopted or overwritten.

#### Complete Remote Example

The following definitions are documentation examples, not a published service. Replace the example owner, URLs, and workflow with your actual public source and tested MCP endpoint before submitting a listing.

In the server's public repository, create `skills/example-docs-guide/SKILL.md`:

```markdown
---
name: example-docs-guide
description: Use the Example Docs MCP to find version-specific documentation and cite source pages.
license: Apache-2.0
metadata:
  category: search
---

# Example Docs Guide

1. Confirm the product, version, and question with the user when they are unclear.
2. Use the connected Example Docs MCP's documented tools to search and read relevant pages.
3. Check that the returned pages match the requested product and version.
4. Answer with source URLs. If the tools fail or no matching page exists, state the limitation instead of inventing documentation.

Use read-only tools. Never request credentials in the conversation or include them in an answer.
```

Import the skill with the [remote skill workflow](#adding-your-skill-to-the-marketplace). The imported copy belongs at `skills/example-docs-guide/`; the importer records its canonical repository, path, ref, and commit in `metadata.source`. Review licensing and preserve required license files and notices. Official Kilo skills use [Kilo-Org/skills](https://github.com/Kilo-Org/skills) as their canonical source, not this catalog.

After the skill archive is published, add `mcps/example-docs/MCP.yaml`:

```yaml
id: example-docs
name: Example Docs
description: Search and read version-specific product documentation.
author: example-org
url: https://github.com/example-org/docs-mcp
category: search
prerequisites:
  - An Example Docs account with read access
  - A client version with MCP companion skill support
skills:
  - example-docs-guide
content:
  - name: Remote
    content: |
      {
        "type": "streamable-http",
        "url": "https://mcp.example.com/mcp",
        "headers": {
          "Authorization": "Bearer {{DOCS_TOKEN}}"
        }
      }
parameters:
  - name: Read-only API token
    key: DOCS_TOKEN
    placeholder: your_read_only_token
```

Keep real credentials out of source files. The generator preserves the MCP configuration and replaces only the authored companion references in `mcps/marketplace.yaml`:

```yaml
skills:
  - id: example-docs-guide
    content: https://github.com/Kilo-Org/kilo-marketplace/releases/download/skills-latest/example-docs-guide.tar.gz
```

This optional API field contains only `id` and the archive URL in `content`. Clients do not need a second catalog lookup. The `/api/marketplace/mcps` API passes generated YAML through unchanged. Do not edit generated catalogs manually.

#### Resources And Archives

A companion is the same package as a standalone skill, not just its Markdown text. Keep any `scripts/`, `references/`, `assets/`, `examples/`, and required license files inside the skill directory. Resolve resources relative to the loaded skill directory, not a fixed project path. Review bundled scripts; installation does not execute them.

On a `main` push affecting `skills/**` or `bin/**`, the Package Skills workflow archives each skill with a single outer `<id>/` directory. It includes the resources and excludes `<id>/evals`, `<id>/local.patch`, and `<id>/local.remove`. It creates a timestamped release and updates the mutable `skills-latest` assets used by both catalogs. A change in the canonical source alone does not update a published archive: import or update the marketplace copy, validate it, and merge it first.

#### Validation And Publication

From `bin/`, run the catalog checks:

```sh
pnpm install
pnpm exec tsx generate-skill-marketplace.ts
pnpm exec tsx generate-mcps-marketplace.ts
pnpm test
pnpm run typecheck:mcps
pnpm run typecheck:plugins
```

Validate each new or changed skill with `skills-ref validate skills/<id>` from the repository root, as the Validate Skills workflow does. Test the real MCP endpoint and companion workflow in a supported client, including a skill that has a relative resource file. Check both installation scopes, a conflicting existing skill, and removal. Confirm that unrelated skills remain unchanged.

Publish in this order:

1. Release a Kilo CLI version with the companion install and removal contract. Verify and release each client that exposes the feature. In JetBrains, bump the pinned CLI version only after that CLI release exists, then test and release the plugin. Older clients can ignore `skills` and install only the MCP; do not advertise a complete bundle to those clients.
2. Merge the real skill into its canonical public repository. Import it into this repository, validate its metadata and resources, and merge the skill and generated standalone catalog through a pull request.
3. Wait for Package Skills to finish and verify `https://github.com/Kilo-Org/kilo-marketplace/releases/download/skills-latest/<id>.tar.gz` is downloadable and contains `<id>/SKILL.md` plus the required resources. Generator validation checks local sources, not remote asset availability.
4. Add the MCP's companion IDs, regenerate the MCP catalog, and submit the listing through a pull request. An already published skill can be referenced directly without a separate skill release.
5. After merge, allow for the API's one-hour cache and client cache refresh, then verify installation from the public marketplace.

Do not rely on cache delay to hide a missing archive. Catalog changes and release uploads are separate operations, so merging a new skill and its first MCP reference together can expose a download URL before its asset exists.

### MCP Example

**Example Service** (`mcps/example-service/MCP.yaml`):

```yaml
id: example-service
name: Example Service
description: Enables AI assistants to interact with Example Service API for data retrieval and automation.
author: example-org
url: https://github.com/example-org/example-mcp
category: business
prerequisites:
  - Example Service account
content:
  - name: NPX
    prerequisites:
      - Node.js
    content: |
      {
        "command": "npx",
        "args": ["-y", "@example/mcp-server"],
        "env": {
          "EXAMPLE_API_KEY": "{{EXAMPLE_API_KEY}}"
        }
      }
  - name: Docker
    prerequisites:
      - Docker
    content: |
      {
        "command": "docker",
        "args": ["run", "-i", "--rm", "-e", "EXAMPLE_API_KEY", "example/mcp-server"],
        "env": {
          "EXAMPLE_API_KEY": "{{EXAMPLE_API_KEY}}"
        }
      }
parameters:
  - name: Example API Key
    key: EXAMPLE_API_KEY
    placeholder: your_example_api_key
```

---

## Questions?

Open an issue if you have questions about contributing or need help structuring your skill, agent, or MCP server.

Thank you for contributing to Kilo Marketplace!
