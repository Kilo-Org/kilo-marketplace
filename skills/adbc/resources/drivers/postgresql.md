# postgresql

## Installing the Driver

Install the PostgreSQL ADBC driver with dbc by running:

```sh
dbc install postgresql
```

## Connecting

Connect with a standard PostgreSQL [connection URI](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING):

```text
postgresql://[user[:password]@][host[:port]][/dbname][?param1=value1&...]
```

Examples:

- `postgresql://localhost:5432/mydb`
- `postgresql://user:pass@localhost:5432/mydb`
- `postgresql://user:pass@localhost/mydb?sslmode=require`

## Selecting a database

The database is specified in the connection URI. To change databases, establish a new connection with a different URI.

List available databases using `AdbcConnectionGetObjects` with `depth` set to "catalogs".

## More Information

See https://arrow.apache.org/adbc/current/driver/postgresql.html for more detailed documentation if needed.
