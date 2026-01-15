<h1 align="center">Kilo Marketplace</h1>

A curated list of practical Skills for enhancing productivity across the Kilo extensions, Kilo CLI, and the whole Kilo ecosystem.

---

## Contents

- [What Are Skills?](#what-are-skills)
- [Creating Skills](#creating-skills)
  - [Skill Structure](#skill-structure)
  - [Basic Skill Template](#basic-skill-template)
  - [Skill Best Practices](#skill-best-practices)
- [Contributing](#contributing)
  - [Quick Contribution Steps](#quick-contribution-steps)
- [License](#license)

## What Are Skills?

Skills are customizable workflows that teach Kilo how to perform specific tasks according to your unique requirements. Skills enable Kilo to execute tasks in a repeatable, standardized manner across all Kilo platforms.

## Creating Skills

### Skill Structure

Each skill is a folder containing a `SKILL.md` file with YAML frontmatter:

```
skill-name/
├── SKILL.md          # Required: Skill instructions and metadata
├── scripts/          # Optional: Helper scripts
├── templates/        # Optional: Document templates
└── resources/        # Optional: Reference files
```

### Basic Skill Template

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

[Detailed instructions for Kilo on how to execute this skill]

## Examples

[Real-world examples showing the skill in action]
```

### Skill Best Practices

- Focus on specific, repeatable tasks
- Include clear examples and edge cases
- Write instructions for Kilo, not end users
- Test across Kilo VS Code extension, Kilo CLI, and API
- Document prerequisites and dependencies
- Include error handling guidance

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- How to submit new skills
- Skill quality standards
- Pull request process
- Code of conduct

### Quick Contribution Steps

1. Ensure your skill is based on a real use case
2. Check for duplicates in existing skills
3. Follow the skill structure template
4. Test your skill across platforms
5. Submit a pull request with clear documentation

## License

This repository is licensed under the Apache License 2.0.
