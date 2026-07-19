# connectors list-available

List the connector templates available to install in this account. Each template has a `name` (e.g. `salesforce`, `hubspot`) that you pass to `connectors create --json '{"name": "<name>"}'`.

## Usage

```bash
airbyte-agent connectors list-available --json '{}'
```

## When to use

Always run this **before** `connectors create` to discover the exact template `name` to use. Template names are stable identifiers — do not guess them.

## Workflow

```bash
airbyte-agent connectors list-available --json '{}'
airbyte-agent connectors create --json '{"workspace": "my-workspace", "name": "salesforce"}'
```

## Filtering output

```bash
airbyte-agent connectors list-available --fields id,name --json '{}'              # short form
airbyte-agent connectors list-available --fields data.id,data.name --json '{}'    # long form
```

## Hints

- The list is filtered to what your account has access to — it will not show every connector that exists in Airbyte's catalog.
