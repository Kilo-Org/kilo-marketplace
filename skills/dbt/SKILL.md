---
name: dbt
description: Skills for analytics engineering with dbt - building models, writing tests, querying the semantic layer, troubleshooting jobs, and more. Use when doing any dbt analytics engineering work.
license: Apache-2.0
metadata:
  category: development
  author: dbt-labs
  source:
    repository: https://github.com/dbt-labs/dbt-agent-skills
    path: skills/dbt
---

# dbt Analytics Engineering Skills

A comprehensive collection of skills for analytics engineering with dbt. Covers building models, writing tests, querying the semantic layer, troubleshooting jobs, and more.

## Included Skills

### using-dbt-for-analytics-engineering
Builds and modifies dbt models, writes SQL transformations using ref() and source(), creates tests, and validates results with dbt show. Use when doing any dbt work - building or modifying models, debugging errors, exploring unfamiliar data sources, writing tests, or evaluating impact of changes.

### adding-dbt-unit-test
Creates unit test YAML definitions that mock upstream model inputs and validate expected outputs. Use when adding unit tests for a dbt model or practicing test-driven development (TDD) in dbt.

### building-dbt-semantic-layer
Use when creating or modifying dbt Semantic Layer components - semantic models, metrics, dimensions, entities, measures, or time spines. Covers MetricFlow configuration, metric types (simple, derived, cumulative, ratio, conversion), and validation for both latest and legacy YAML specs.

### answering-natural-language-questions-with-dbt
Writes and executes SQL queries against the data warehouse using dbt's Semantic Layer or ad-hoc SQL to answer business questions. Use when a user asks about analytics, metrics, KPIs, or data.

### troubleshooting-dbt-job-errors
Diagnoses dbt Cloud/platform job failures by analyzing run logs, querying the Admin API, reviewing git history, and investigating data issues. Use when a dbt Cloud/platform job fails and you need to diagnose the root cause.

### configuring-dbt-mcp-server
Generates MCP server configuration JSON, resolves authentication setup, and validates server connectivity for dbt. Use when setting up, configuring, or troubleshooting the dbt MCP server for AI tools.

### fetching-dbt-docs
Retrieves and searches dbt documentation pages in LLM-friendly markdown format. Use when fetching dbt documentation, looking up dbt features, or answering questions about dbt Cloud, dbt Core, or the dbt Semantic Layer.

### running-dbt-commands
Formats and executes dbt CLI commands, selects the correct dbt executable, and structures command parameters. Use when running models, tests, builds, compiles, or show queries via dbt CLI.

## Source

- **Repository**: https://github.com/dbt-labs/dbt-agent-skills
- **License**: Apache-2.0
- **Author**: dbt Labs
