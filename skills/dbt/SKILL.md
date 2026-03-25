---
name: dbt
description: "Performs analytics engineering with dbt — building and modifying models, writing tests, querying the Semantic Layer, troubleshooting Cloud job failures, configuring MCP servers, and running CLI commands. Use when doing any dbt analytics engineering work."
license: Apache-2.0
metadata:
  category: development
  author: dbt-labs
  source:
    repository: https://github.com/dbt-labs/dbt-agent-skills
    path: skills/dbt
---

## When to Use

- Building or modifying dbt models and SQL transformations
- Adding unit tests or data tests to a dbt project
- Creating or editing Semantic Layer components (metrics, dimensions, entities)
- Answering business questions with SQL via the Semantic Layer
- Diagnosing dbt Cloud job failures
- Configuring the dbt MCP server for AI tools
- Looking up dbt documentation
- Running dbt CLI commands (build, test, compile, show)

## Included Skills

### using-dbt-for-analytics-engineering
Builds and modifies dbt models using `ref()` and `source()`, writes SQL transformations, creates tests, and validates results with `dbt show`. Use for any core dbt work — modeling, debugging, exploring data sources, or evaluating change impact. See `skills/using-dbt-for-analytics-engineering/references/` for patterns on debugging, data discovery, impact evaluation, and documentation.

### adding-dbt-unit-test
Creates unit test YAML definitions that mock upstream model inputs and validate expected outputs. Use when adding unit tests for a dbt model or practicing TDD. See `skills/adding-dbt-unit-test/references/` for spec details, warehouse-specific data types, and special cases (incremental, ephemeral, versioned models).

### building-dbt-semantic-layer
Creates or modifies Semantic Layer components — semantic models, metrics, dimensions, entities, measures, and time spines. Covers MetricFlow configuration and metric types (simple, derived, cumulative, ratio, conversion). See `skills/building-dbt-semantic-layer/references/` for latest/legacy specs and best practices.

### answering-natural-language-questions-with-dbt
Writes and executes SQL queries against the warehouse using the Semantic Layer or ad-hoc SQL to answer business questions. Use when a user asks about analytics, metrics, KPIs, or data trends.

### troubleshooting-dbt-job-errors
Diagnoses dbt Cloud/platform job failures by analyzing run logs, querying the Admin API, reviewing git history, and investigating data issues. See `skills/troubleshooting-dbt-job-errors/references/investigation-template.md` for the structured investigation workflow.

### configuring-dbt-mcp-server
Generates MCP server configuration JSON, resolves authentication, and validates connectivity. Use when setting up or troubleshooting the dbt MCP server. See `skills/configuring-dbt-mcp-server/references/` for environment variables, credentials, and troubleshooting.

### fetching-dbt-docs
Retrieves and searches dbt documentation in LLM-friendly markdown. Use when looking up dbt features or answering questions about dbt Cloud, dbt Core, or the Semantic Layer.

### running-dbt-commands
Formats and executes dbt CLI commands, selects the correct executable, and structures parameters. Use when running `dbt build`, `dbt test`, `dbt compile`, or `dbt show`.

## Source

- **Repository**: https://github.com/dbt-labs/dbt-agent-skills
- **License**: Apache-2.0
- **Author**: dbt Labs
