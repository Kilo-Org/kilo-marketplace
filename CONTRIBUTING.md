# Contributing to Kilo Marketplace

Thank you for your interest in contributing to the Kilo Marketplace! This guide will help you add new skills that benefit the entire community.

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
  source:
    repository: https://github.com/yourname/your-skill-repo
    path: path/to/skill
    license_path: LICENSE
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `metadata.source.repository` | **Yes** (for contributed skills) | URL to the GitHub repository containing your skill |
| `metadata.source.path` | **Yes** (for contributed skills) | Path within the repository to the skill directory |
| `metadata.source.license_path` | **Yes** (for contributed skills) | Path to the LICENSE file in the source repo |

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

## Contributing Custom Modes

Custom modes allow you to tailor Kilo Code's behavior for specific tasks or workflows. You can contribute modes that benefit the community.

### Mode Requirements

All contributed modes must:

1. **Serve a clear purpose** - Optimized for specific tasks like documentation, testing, or security review
2. **Be well-documented** - Include clear descriptions and use cases
3. **Define appropriate permissions** - Use tool groups and file restrictions responsibly
4. **Be tested** - Verify the mode works correctly in Kilo Code

### Mode Structure

Create a new folder with your mode name (use lowercase and hyphens):

```
modes/
└── mode-name/
    └── MODE.yaml
```

The `MODE.yaml` file should contain:

```yaml
id: mode-slug
name: Mode Display Name
description: Brief description of what this mode does
author: "@your-github-username"
tags: [relevant, tags, here]
content: |
  slug: mode-slug
  name: 🎯 Mode Display Name
  roleDefinition: |
    You are a specialist in [domain]. Your expertise includes:
    - Capability 1
    - Capability 2
    - Capability 3
  groups:
    - read
    - edit
    - command
  customInstructions: |
    Specific behavioral guidelines for this mode.
```

### Mode Properties

| Property | Required | Description |
|----------|----------|-------------|
| `id` | Yes | Unique identifier (kebab-case) |
| `name` | Yes | Display name shown in the marketplace |
| `description` | Yes | Brief description of the mode's purpose |
| `author` | Yes | Your GitHub username with @ prefix |
| `tags` | Yes | Array of relevant tags for discovery |
| `content.slug` | Yes | Internal identifier (must match `id`) |
| `content.name` | Yes | Display name with optional emoji |
| `content.roleDefinition` | Yes | Defines the mode's expertise and personality |
| `content.groups` | Yes | Tool groups the mode can access |
| `content.customInstructions` | No | Additional behavioral guidelines |
| `content.whenToUse` | No | Guidance for automated mode selection |

### Available Tool Groups

- `read` - Read files and explore the codebase
- `edit` - Modify files (can include file restrictions)
- `command` - Execute terminal commands
- `browser` - Browser automation capabilities
- `mcp` - Access MCP server tools

### File Restrictions Example

To restrict which files a mode can edit:

```yaml
groups:
  - read
  - - edit
    - fileRegex: \.(md|mdx)$
      description: Markdown files only
  - command
```

### Mode Examples

**Documentation Writer** (`modes/docs-writer/MODE.yaml`):
```yaml
id: docs-writer
name: Documentation Writer
description: Technical documentation expert for clear, comprehensive docs
author: "@your-username"
tags: [documentation, markdown, technical-writing]
content: |
  slug: docs-writer
  name: 📝 Documentation Writer
  roleDefinition: |
    You are a technical writer specializing in clear documentation.
  groups:
    - read
    - - edit
      - fileRegex: \.md$
        description: Markdown files only
  customInstructions: |
    Focus on clarity, proper formatting, and comprehensive examples.
```

**Security Reviewer** (`modes/security-review/MODE.yaml`):
```yaml
id: security-review
name: Security Reviewer
description: Read-only security analysis and vulnerability assessment
author: "@your-username"
tags: [security, audit, code-review]
content: |
  slug: security-review
  name: 🔒 Security Reviewer
  roleDefinition: |
    You are a security specialist reviewing code for vulnerabilities.
  groups:
    - read
    - browser
  customInstructions: |
    Focus on input validation, authentication flaws, and data exposure risks.
```

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
tags:
  - relevant
  - tags
  - here
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
| `tags` | Yes | Array of relevant tags |
| `prerequisites` | No | Required software or accounts |
| `content` | Yes | Installation configuration(s) |
| `parameters` | No | User-configurable parameters |

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

### MCP Example

**Example Service** (`mcps/example-service/MCP.yaml`):

```yaml
id: example-service
name: Example Service
description: Enables AI assistants to interact with Example Service API for data retrieval and automation.
author: example-org
url: https://github.com/example-org/example-mcp
tags:
  - api-integration
  - automation
  - data-retrieval
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

Open an issue if you have questions about contributing or need help structuring your skill, mode, or MCP server.

Thank you for contributing to Kilo Marketplace!
