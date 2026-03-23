---
name: cicd-expert
description: >-
  Expert in CI/CD workflows and Git hooks. Use when users want to set up continuous integration,
  create pre-commit or pre-push hooks, generate pipeline configurations, or run local validation
  before committing or pushing code.
license: Apache-2.0
metadata:
  category: development
---

# CI/CD Expert

Expert in CI/CD workflows and Git hooks for automating quality checks and deployment processes.

## When to Use This Skill

Use this skill when users want to:

- Set up continuous integration for their projects
- Create pre-commit or pre-push Git hooks
- Generate CI/CD pipeline configurations
- Run local validation before committing or pushing code
- Implement automated testing and linting workflows

## What This Skill Does

The CI/CD Expert provides the following capabilities:

1. **Git Hooks** - Create, configure, and manage pre-commit and pre-push hooks for automated quality checks
2. **Pipeline Generation** - Generate CI/CD configurations for GitHub Actions, GitLab CI, and Azure DevOps
3. **Local Validation** - Run linting, formatting, type checking, and unit tests locally before committing
4. **Best Practices** - Provide recommendations for CI/CD workflows and industry best practices

> **Critical Principle: Local/CI Parity**
> Pre-commit hooks MUST match CI/CD workflows 1:1. Jobs should never pass locally but fail in the cloud. This means:
> - The same commands run in hooks must run in CI pipelines
> - The same tool versions and configurations
> - The same environment settings
> - Never skip checks locally that run in CI

## How to Use

### Basic Usage

```text
# Create a pre-commit hook
"Create a pre-commit hook that runs linting"

# Set up CI/CD
"Set up CI/CD for my project"

# Generate a workflow
"Create a GitHub Actions workflow for my Node.js project"

# Run local checks
"Run all checks before I push"
```

### Before Creating New Configurations

The skill will check for existing CI/CD configurations before creating new ones:

1. **Check for existing workflows**: Look in `.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`
2. **Check for existing hooks**: Look in `.git/hooks/`, `.pre-commit-config.yaml`
3. **Check for CI/CD in package.json**: Look for `scripts.test`, `scripts.lint` entries
4. **Check for configuration files**: Look for `eslint.config.*`, `pyproject.toml`, `Gemfile`, etc.

If existing configurations are found, the skill will:
- Offer to update/modify the existing configuration
- Ask before overwriting
- Suggest improvements to existing setup

### Ensure 1:1 Matching

When creating or updating configurations, the skill MUST ensure:

1. **Command Parity**: Pre-commit hooks run the exact same commands as CI jobs
2. **Config Parity**: Same linter/formatter configs, same eslint config, same rules
3. **Version Parity**: Same tool versions (use lockfiles where possible)
4. **Environment Parity**: Same Node.js/Python versions, same dependencies

Example of CORRECT 1:1 matching:
```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test

# .pre-commit-config.yaml (MUST match exactly)
repos:
  - repo: local
    hooks:
      - id: lint
        name: Lint
        entry: npm run lint
        language: system
        stages: [commit]
      - id: typecheck
        name: TypeCheck
        entry: npm run typecheck
        language: system
        stages: [commit]
      - id: test
        name: Test
        entry: npm test
        language: system
        stages: [commit]
```

Example of WRONG (causes local pass/cloud fail):
```yaml
# CI runs lint + typecheck + test
# But pre-commit only runs lint (WRONG!)
```

### Advanced Configuration

For custom pipeline requirements, the skill will prompt you for:

- **Operating System**: ubuntu-latest, windows-latest, macos-latest, or custom
- **Programming Language**: Node.js, Python, Ruby, Go, Rust, Java, etc.
- **Version**: Specific version(s) to test against (e.g., '20.x', '3.10-3.12')
- **Package Manager**: npm, yarn, pnpm, pip, bundler, etc.
- **Testing Frameworks**: Jest, Vitest, pytest, rspec, etc.
- **Linting Tools**: ESLint, Prettier, flake8, rubocop, etc.
- **Deployment Target**: GitHub Pages, Vercel, Netlify, AWS, custom
- **Additional Tools**: Docker, container registries, cloud providers

The skill generates flexible configurations that can be customized for any combination of these tools.

## Git Hooks Setup

### Pre-commit Hooks

Pre-commit hooks run before a commit is created. Common use cases:

- Running linters (ESLint, Prettier, RuboCop, etc.)
- Running unit tests
- Checking code formatting
- Validating commit messages

Example `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks:
      - id: flake8
```

### Pre-push Hooks

Pre-push hooks run before code is pushed to a remote. Common use cases:

- Running full test suites
- Running integration tests
- Building the project to verify compilation

## Pipeline Templates

The skill generates CI/CD configurations that work with any platform. When requesting a pipeline, specify your preferences or let the skill prompt you.

### GitHub Actions

Basic workflow template (customizable OS and versions):

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest] # Customize this
        node-version: ["18.x", "20.x", "22.x"] # Customize versions

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm test
```

### GitLab CI

```yaml
stages:
  - test
  - build

test:
  stage: test
  image: node:20 # Customize this
  script:
    - npm ci
    - npm run lint
    - npm test

build:
  stage: build
  image: node:20 # Customize this
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
```

### Azure DevOps

```yaml
trigger:
  - main

pool:
  vmImage: "ubuntu-latest" # Customize: ubuntu-latest, windows-latest, macOS-latest

steps:
  - task: NodeTool@0
    inputs:
      versionSpec: "20.x" # Customize version
    displayName: "Install Node.js"

  - script: |
      npm ci
      npm run lint
      npm test
    displayName: "Install, lint, and test"

  - script: |
      npm run build
    displayName: "Build"
```

## Local Validation

Run these commands locally before committing or pushing:

### Linting

```bash
# JavaScript/TypeScript
npm run lint

# Python
flake8 .
pylint .

# Ruby
rubocop
```

### Type Checking

```bash
# TypeScript
npx tsc --noEmit

# Python (with mypy)
mypy .
```

### Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- path/to/test.spec.ts
```

### Full Pre-push Check

```bash
# Run lint, type-check, and tests
npm run check
```

## Tips

1. **Local/CI Parity First** - ALWAYS match pre-commit hooks 1:1 with CI workflows. Never skip checks locally that run in CI
2. **Start with pre-commit hooks** - They're faster and catch issues early
3. **Keep hooks fast** - Long-running checks belong in CI pipelines, not pre-commit
4. **Use caching** - Configure cache in your CI pipelines to speed up builds
5. **Fail fast** - Configure pipelines to fail early on linting errors before running tests
6. **Environment parity** - Use Docker containers to ensure consistent environments

## Common Use Cases

| Scenario                        | Solution                                     |
| ------------------------------- | -------------------------------------------- |
| Catch lint errors before commit | Set up pre-commit hooks with ESLint/Prettier |
| Run full test suite before push | Create pre-push hook or local npm script     |
| Automate deployments            | Configure GitHub Actions workflow            |
| Ensure code quality             | Add required checks to pull request reviews  |
| Multi-environment deployments   | Use matrix strategy in CI pipelines          |

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [Azure DevOps Pipelines](https://docs.microsoft.com/en-us/azure/devops/pipelines/)
- [Pre-commit Hooks](https://pre-commit.com/)
