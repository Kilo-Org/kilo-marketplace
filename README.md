<h1 align="center">Kilo Marketplace</h1>

A curated collection of **Skills**, **MCP Servers**, and **Modes** for enhancing AI agent capabilities across the Kilo ecosystem—including Kilo Code (VS Code extension), Kilo CLI, and compatible AI agents.

---

## What is the Kilo Marketplace?

The Kilo Marketplace is a community-driven repository of agent tooling prompts and configurations. It provides three types of resources that extend what AI agents can do:

| Resource | Description |
|----------|-------------|
| **[Skills](#skills)** | Modular workflows and domain expertise that teach agents how to perform specific tasks |
| **[MCP Servers](#mcp-servers)** | Standardized integrations that connect agents to external tools and services |
| **[Modes](#modes)** | Custom agent personalities and behaviors with tailored tool access |

---

## Contents

- [Skills](#skills)
  - [What Are Skills?](#what-are-skills)
  - [Skill Structure](#skill-structure)
  - [Creating Skills](#creating-skills)
- [MCP Servers](#mcp-servers)
  - [What Are MCP Servers?](#what-are-mcp-servers)
- [Modes](#modes)
  - [What Are Modes?](#what-are-modes)
- [Contributing](#contributing)
- [License](#license)

---

## Skills

### What Are Skills?

Skills are self-contained packages that extend an agent's capabilities with specialized knowledge and repeatable workflows. At their core, a skill is a folder containing a `SKILL.md` file with metadata and instructions that tell an agent how to perform a specific task.

Skills follow the open [Agent Skills specification](https://agentskills.io/), making them interoperable across any compatible AI agent—not just Kilo.

**Key benefits:**
- **Self-documenting**: Easy to read, audit, and improve
- **Interoperable**: Works across any agent implementing the Agent Skills spec
- **Extensible**: Can include scripts, templates, and reference materials
- **Shareable**: Portable between projects and developers

### Skill Structure

Each skill is a folder containing a `SKILL.md` file with YAML frontmatter:

```
skill-name/
├── SKILL.md          # Required: Skill instructions and metadata
├── scripts/          # Optional: Helper scripts
├── references/       # Optional: Documentation
├── assets/           # Optional: Templates, resources
└── examples/         # Optional: Example files
```

### Creating Skills

**Basic Skill Template:**

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it.
---

# My Skill Name

Detailed description of the skill's purpose and capabilities.

## When to Use This Skill

- Use case 1
- Use case 2
- Use case 3

## Instructions

[Detailed instructions for the agent on how to execute this skill]

## Examples

[Real-world examples showing the skill in action]
```

**Best Practices:**
- Focus on specific, repeatable tasks
- Include clear examples and edge cases
- Write instructions for the agent, not end users
- Document prerequisites and dependencies
- Include error handling guidance

---

## MCP Servers

### What Are MCP Servers?

MCP (Model Context Protocol) is a standardized communication protocol that allows AI agents to interact with external tools and services. Think of it as a universal adapter—any compatible agent can connect to any MCP server to access its functionality.

MCP servers provide capabilities like:
- File system access
- Database queries
- API integrations
- External service connections

**How it works:**
1. The AI agent (client) connects to MCP servers
2. Each server provides specific capabilities
3. The agent uses these capabilities through a standardized interface
4. Communication occurs via JSON-RPC 2.0 messages

MCP servers can run locally on your machine or remotely as cloud services, depending on security requirements.

Browse available MCP servers in the [`mcps/`](./mcps/) directory.

---

## Modes

### What Are Modes?

Modes are custom agent configurations that define specialized behaviors, personalities, and tool access. They allow you to create purpose-built agents for specific tasks like documentation writing, code review, or security analysis.

A mode defines:
- **Role Definition**: The agent's identity and expertise
- **Available Tools**: Which tool groups the agent can access
- **File Restrictions**: Which files the agent can read or edit
- **Custom Instructions**: Behavioral guidelines and rules

**Example use cases:**
- A "Documentation Writer" mode that can only edit Markdown files
- A "Security Reviewer" mode with read-only access for auditing
- A "Test Engineer" mode focused on test files

Modes can be shared as YAML configurations and imported into Kilo Code or other compatible tools.

Browse available modes in the [`modes/`](./modes/) directory.

---

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- How to submit new skills, MCP servers, or modes
- Quality standards
- Pull request process
- Code of conduct

### Quick Contribution Steps

1. Ensure your contribution is based on a real use case
2. Check for duplicates in existing resources
3. Follow the appropriate structure template
4. Test your contribution across platforms
5. Submit a pull request with clear documentation

---

## License

This repository is licensed under the Apache License 2.0.
