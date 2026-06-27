# flightsql

## Installing the Driver

Install the Flight SQL ADBC driver with dbc by running:

```sh
dbc install flightsql
```

## Connecting

Connect by supplying a `uri` option with a gRPC URI:

```text
grpc://host:port
grpc+tls://host:port
```

Use `grpc://` for unencrypted connections and `grpc+tls://` for TLS-encrypted connections.

## Authentication

The driver supports several authentication methods:

- **Username/Password**: Set `username` and `password` options on the database.
- **Bearer Token**: Set the `adbc.flight.sql.authorization_header` option to `Bearer <token>`.
- **Custom Headers**: Set options with the prefix `adbc.flight.sql.rpc.call_header.<header_name>` (header names must be lowercase).

## TLS Options

- `adbc.flight.sql.client_option.tls_skip_verify` - Set to `true` to skip server certificate verification.
- `adbc.flight.sql.client_option.tls_root_certs` - Override root certificates for server verification.
- `adbc.flight.sql.client_option.tls_override_hostname` - Override hostname for TLS verification.
- `adbc.flight.sql.client_option.mtls_cert_chain` - Client certificate for mTLS.
- `adbc.flight.sql.client_option.mtls_private_key` - Client private key for mTLS.

## More Information

See https://arrow.apache.org/adbc/current/driver/flight_sql.html for more detailed documentation if needed.
