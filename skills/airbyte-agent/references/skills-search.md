# skills search

Search connector and static skill docs by task, connector, or keyword.

## Usage

```bash
airbyte-agent skills search --json '{"workspace": "default", "query": "post a slack message", "limit": 20}'
airbyte-agent skills search --json '{"workspace": "default", "query": "hubspot contacts", "cursor": "<next_cursor>"}'
```

`query` is required. `workspace` is optional and defaults to the configured workspace, then `default`.

## When to use

- Finding relevant docs when you do not know the connector or skill ID yet.
- Discovering static agent docs by task.
- Narrowing from many installed connectors to the likely target.

## Do NOT

- Do NOT execute based only on search snippets. Open `skills docs` for the exact skill and section first.
- Do NOT use search instead of `connectors inspect` when you already have the connector instance.
