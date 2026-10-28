# organizations list

List the organizations that the authenticated principal has access to.

## Usage

```bash
airbyte-agent organizations list --json '{}'
```

## Filtering output

```bash
airbyte-agent organizations list --fields id,organization_name --json '{}'              # short form
airbyte-agent organizations list --fields data.id,data.organization_name --json '{}'    # long form

# Mixed top-level and row-level paths — use the long form for the row paths
airbyte-agent organizations list --fields data.id,next --json '{}'
```

## When to use

Most workflows do not need the organization ID directly — `workspace` is the primary identifier passed to other commands. Use this command when:

- You need to confirm which organization the credentials belong to.
- You are setting `AIRBYTE_ORGANIZATION_ID` and want to verify the value.
- You are debugging multi-org credential setups.

## Hints

- Output is paginated automatically by the CLI; you do not need to handle cursors.
- The organization ID is a UUID; it is rarely needed at the command line.
