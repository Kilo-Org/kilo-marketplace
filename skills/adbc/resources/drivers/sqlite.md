# sqlite

## Installing the Driver

Install the SQLite ADBC driver with dbc by running:

```sh
dbc install sqlite
```

## Connecting

Connect by supplying a `uri` option. This should be a filename, a [SQLite URI filename](https://www.sqlite.org/c3ref/open.html#urifilenamesinsqlite3open), or omitted entirely for an in-memory database.

Valid URIs:

- `:memory:` - in-memory database (shared across connections)
- `/path/to/database.db` - file path
- `file:/path/to/database.db` - URI filename
- `file:/path/to/database.db?mode=ro` - URI filename with parameters

If the `uri` option is omitted, it defaults to an in-memory database that is shared across all connections.

## More Information

See https://arrow.apache.org/adbc/current/driver/sqlite.html for more detailed documentation if needed.
