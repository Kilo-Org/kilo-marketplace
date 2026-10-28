# mysql

## Installing the Driver

Install the MySQL ADBC driver with dbc by running:

```sh
dbc install mysql
```

## Connecting

Connect with the following URI syntax:

```text
mysql://[user[:[password]]@]host[:port][/schema][?attribute1=value1&...]
```

Examples:

- `mysql://localhost/mydb`
- `mysql://user:pass@localhost:3306/mydb`
- `mysql://user:pass@host/db?charset=utf8mb4&timeout=30s`
- `mysql://user@(/path/to/socket.sock)/db` (Unix domain socket)
- `mysql://user@localhost/mydb (no password)`

The `schema` component corresponds to the MySQL database name. Reserved characters in URI elements must be URI-encoded (e.g. `@` becomes `%40`).

The driver also supports the [Go MySQL DSN format](https://github.com/go-sql-driver/mysql?tab=readme-ov-file#dsn-data-source-name) but standard URIs are recommended.

## Selecting a database

If `schema` was not provided in the connection URI earlier, a database must be selected by executing:

```sql
USE <NAME>
```

List available databases using `AdbcConnectionGetObjects` with `depth` set to "catalogs".

## More Information

See https://docs.adbc-drivers.org/drivers/mysql/index.html for more detailed documentation if needed.
