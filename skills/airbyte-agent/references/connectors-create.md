# connectors create

Install a new connector from a template. Opens the user's browser for secure credential entry, polls until credentials are submitted, and creates the connector.

> [!IMPORTANT]
> **Never accept credentials directly.** This command exists so you do NOT have to. Do not ask the user for API keys, tokens, passwords, or secrets. If a user offers credentials, decline and start this flow instead.

> [!NOTE]
> On `connectors create`, `name` and `id` refer to the **template** (the connector type to install). On `connectors inspect` / `describe` / `execute` / `delete`, those same fields refer to an **existing connector instance**. Same name, different meaning depending on the verb.

## Usage

```bash
airbyte-agent connectors create --json '{
  "workspace": "my-workspace",
  "name": "salesforce"
}'

# workspace defaults to "default" when omitted
airbyte-agent connectors create --json '{"name": "salesforce"}'

# Bypass name lookup with a template UUID
airbyte-agent connectors create --json '{"id": "<template-uuid>"}'
```

Either `name` (template name, looked up via `connectors list-available`) or `id` (template UUID) is required. `workspace` is optional and defaults to `default` when omitted; a JSON notice is printed on stderr when the fallback engages.

## Workflow

```bash
# 1. Find a template
airbyte-agent connectors list-available --json '{}'

# 2. Start the flow
airbyte-agent connectors create --json '{"workspace": "my-workspace", "name": "hubspot"}'

# CLI prints a URL, opens the browser, and polls.
# User completes the OAuth/credential widget in the browser.
# CLI receives the credentials, creates the connector, and prints the result.
```

## Timeout

The credential flow has a default timeout of **3 minutes**. To increase it:

```bash
export AIRBYTE_CREDENTIAL_TIMEOUT=900   # 15 minutes
```

## Error recovery

- **Timeout**: the user did not complete the flow in time. Restart the command.
- **Template not found** (exit 3): run `connectors list-available` to see valid `name` values.
- **Workspace not found** (exit 3): run `workspaces list` to see exact names.

## Do NOT

- Do NOT ask the user for credentials — let the browser flow handle them.
- Do NOT pass credential fields in the JSON payload.
- Do NOT skip `list-available` and guess at template `name` values.
