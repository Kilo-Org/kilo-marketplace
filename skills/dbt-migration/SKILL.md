---
name: dbt-migration
description: Skills for migrating dbt projects - moving from dbt Core to the Fusion engine or across data platforms. Use when migrating dbt projects between platforms or to dbt Fusion.
license: Apache-2.0
metadata:
  category: development
  author: dbt-labs
  source:
    repository: https://github.com/dbt-labs/dbt-agent-skills
    path: skills/dbt-migration
---

# dbt Migration Skills

A collection of skills for migrating dbt projects - moving from dbt Core to the Fusion engine or across data platforms.

## Included Skills

### migrating-dbt-core-to-fusion
Classifies dbt-core to Fusion migration errors into actionable categories (auto-fixable, guided fixes, needs input, blocked). Use when a user needs help triaging migration errors to understand what they can fix vs what requires Fusion engine updates.

### migrating-dbt-project-across-platforms
Use when migrating a dbt project from one data platform or data warehouse to another (e.g., Snowflake to Databricks, Databricks to Snowflake) using dbt Fusion's real-time compilation to identify and fix SQL dialect differences.

## Source

- **Repository**: https://github.com/dbt-labs/dbt-agent-skills
- **License**: Apache-2.0
- **Author**: dbt Labs
