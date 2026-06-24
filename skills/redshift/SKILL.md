---
name: "redshift"
description: "This skill should be used for read-only Amazon Redshift exploration and business analysis via the AWS Data API."
metadata:
  category: data
  source:
    repository: "https://github.com/onsen-ai/redshift-skill"
    path: "."
    license_path: "LICENSE"
---

# Redshift Skill

Use this skill for read-only Redshift exploration and business analysis via the AWS Data API. It applies to both provisioned Redshift clusters and Redshift Serverless.

All scripts in the canonical skill are expected under `${CLAUDE_SKILL_DIR}/scripts/` and require Python 3 plus the AWS CLI.

## Python Command

Read `~/.redshift-skill/config.json` and use the `python` key as the Python command. If config does not exist yet, try `python3 --version` first, falling back to `python --version`. Throughout this skill, `PYTHON` means the detected Python command.

## First-Time Setup

Do not run an interactive setup wizard directly from the agent. Check whether `~/.redshift-skill/config.json` exists.

If it exists, read it to confirm the connection details.

If it does not exist, tell the user to run the setup wizard in their terminal.

## Source

Canonical source: https://skills.sh/onsen-ai/redshift-skill/redshift
