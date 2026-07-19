# snowflake

## Installing the Driver

Install the Snowflake ADBC driver with dbc by running:

```sh
dbc install snowflake
```

## Before Connecting: Determine the Auth Method and Parameters

Snowflake supports several authentication methods, each with different required parameters. Before writing code:

1. **Check for a connection profile.** If the user has one (see `resources/connection-profiles.md`), prefer `profile://<name>` and skip the rest.
2. **Check the environment** for common Snowflake variables (listed below), including a `.env` file if present. If enough are set to satisfy one auth method unambiguously, read them at runtime (e.g., `os.environ`) — do not hardcode values.
3. **Ask the user** for any missing required parameters, and ask which auth method to use if still ambiguous. Never invent or use placeholder values for accounts, usernames, passwords, keys, or tokens.

### Common Environment Variables (Snowflake convention; not read automatically by the driver)

- `SNOWFLAKE_ACCOUNT` — account identifier
- `SNOWFLAKE_URL` — full account URL (alternative to `SNOWFLAKE_ACCOUNT`)
- `SNOWFLAKE_USER` — username
- `SNOWFLAKE_PASSWORD` — password
- `SNOWFLAKE_AUTHENTICATOR` — auth method override
- `SNOWFLAKE_PRIVATE_KEY_PATH` — PEM-encoded RSA private key path (JWT auth)
- `SNOWFLAKE_PAT` or `SNOWFLAKE_AUTH_TOKEN` — programmatic access token (PAT auth)
- `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`, `SNOWFLAKE_ROLE`

## Connection Styles

Prefer picking **one** style and using it consistently. Mixing them (setting `uri` plus additional `adbc.snowflake.sql.*` options) is technically possible but discouraged — it splits the connection config across two places and makes it easy to set the auth info ambiguously (e.g., `authenticator` in the URI *and* `adbc.snowflake.sql.auth_type` as an option).

### URI style

Set the `uri` option:

```text
snowflake://[user[:password]@]<host>/[database][?param1=value1&...]
```

The `<host>` may be either the bare account identifier (e.g., `myorg-account123`) or the full hostname (e.g., `myorg-account123.snowflakecomputing.com`). The bare form is recommended.

URI query parameters: `warehouse`, `role`, `authenticator`, `token` (for PAT), plus the `adbc.snowflake.sql.*` options below as `&key=value` pairs. The auth method goes in `?authenticator=<value>` (see table below).

### Options style

Omit `uri` and pass these keys directly:

| Key | Purpose |
| --- | --- |
| `adbc.snowflake.sql.account` | Account identifier |
| `username` | Username |
| `password` | Password (secret) |
| `adbc.snowflake.sql.auth_type` | Auth method (see table below) |
| `adbc.snowflake.sql.client_option.jwt_private_key` | Path to a PEM-encoded RSA private key file (JWT auth) |
| `adbc.snowflake.sql.client_option.jwt_private_key_pkcs8_value` | Inline PEM private key contents (secret; JWT auth) |
| `adbc.snowflake.sql.client_option.jwt_private_key_pkcs8_password` | Passphrase for an encrypted PKCS8 private key (secret; JWT auth) |
| `adbc.snowflake.sql.client_option.auth_token` | Token value (PAT, OAuth, and other token-based auth methods) |
| `adbc.snowflake.sql.client_option.okta_url` | Okta endpoint URL (Okta auth) |
| `adbc.snowflake.sql.client_option.identity_provider` | Identity provider for Workload Identity Federation (`auth_wif`) |
| `adbc.snowflake.sql.client_option.ocsp_fail_open_mode` | OCSP fail-open behavior (certificate revocation checks) |
| `adbc.snowflake.sql.db` | Default database |
| `adbc.snowflake.sql.schema` | Default schema |
| `adbc.snowflake.sql.warehouse` | Default warehouse |
| `adbc.snowflake.sql.role` | Default role |
| `adbc.snowflake.sql.client_option.tls_skip_verify` | `"true"` to disable TLS verification (not for production) |

The following keys are rarely needed — only set them when you have to override the default host construction (for example, to reach a non-standard region endpoint or a private/proxy URL):

| Key | Purpose |
| --- | --- |
| `adbc.snowflake.sql.region` | Region override |
| `adbc.snowflake.sql.uri.protocol` | `http` or `https` override |
| `adbc.snowflake.sql.uri.port` | Port override |
| `adbc.snowflake.sql.uri.host` | Host override |

### Auth method value mapping

The two styles use different value names for the same auth methods:

| Auth method | Options: `adbc.snowflake.sql.auth_type` | URI: `authenticator` |
| --- | --- | --- |
| Username / password (default) | `auth_snowflake` | `snowflake` |
| JWT key pair | `auth_jwt` | `snowflake_jwt` |
| Programmatic access token (PAT) | `auth_pat` | `programmatic_access_token` |
| OAuth | `auth_oauth` | `oauth` |
| External browser (SSO) | `auth_ext_browser` | `externalbrowser` |
| Okta | `auth_okta` | `okta_endpoint` |
| Username / password + MFA | `auth_mfa` | `username_password_mfa` |
| Workload Identity Federation | `auth_wif` | *(consult upstream docs)* |

Auth info must match the chosen style: when `uri` is set, `authenticator` goes in the URI query string; when using options, set `adbc.snowflake.sql.auth_type`.

## Auth Methods and Their Required Parameters

### 1. Username / Password (default)

- `adbc.snowflake.sql.account`
- `username`
- `password`

`auth_snowflake` is the default, so the auth marker is optional. URI equivalent: `snowflake://<user>:<password>@<account>/[database]`.

A programmatic access token (PAT) can also be supplied as the `password` under `auth_snowflake` — the driver will accept it in place of a regular password. This is an alternative to using `auth_pat` below.

### 2. JWT Key Pair (RSA private key)

- `adbc.snowflake.sql.account`
- `username`
- Auth marker: `auth_type=auth_jwt` (options) or `authenticator=snowflake_jwt` (URI)
- Exactly one private key source:
  - `adbc.snowflake.sql.client_option.jwt_private_key` — path to a PEM-encoded RSA private key file, **or**
  - `adbc.snowflake.sql.client_option.jwt_private_key_pkcs8_value` — the PEM contents inline (secret)
- `adbc.snowflake.sql.client_option.jwt_private_key_pkcs8_password` — passphrase to decrypt the private key, if it is encrypted (secret; required only for encrypted keys)

### 3. Programmatic Access Token (PAT)

- `adbc.snowflake.sql.account`
- `username`
- Auth marker: `auth_type=auth_pat` (options) or `authenticator=programmatic_access_token` (URI)
- Token delivery:
  - Options style: `adbc.snowflake.sql.client_option.auth_token` = `<PAT>`
  - URI style: `&token=<url-encoded PAT>` in the query string

### 4. Other Authenticators

`auth_oauth`, `auth_ext_browser` (SSO via browser), `auth_okta`, `auth_mfa`, and `auth_wif` (Workload Identity Federation) have their own required parameters — consult https://docs.adbc-drivers.org/drivers/snowflake/index.html and ask the user for the specific values (e.g., OAuth token, Okta URL) rather than guessing option keys.

## Selecting a Database

If no database was specified via URI or `adbc.snowflake.sql.db`, list available databases with `AdbcConnectionGetObjects` at `depth="catalogs"`, then execute `USE DATABASE <NAME>`. Schema, warehouse, and role can also be switched with `USE SCHEMA`, `USE WAREHOUSE`, and `USE ROLE`.

## Ingesting Data

The Snowflake driver does not support the `catalog_name` / `db_schema_name` kwargs on `adbc_ingest` (it raises `NOT_IMPLEMENTED: Unknown statement option 'adbc.ingest.target_catalog'`). Set the target database and schema on the connection instead — either via `adbc.snowflake.sql.db` / `adbc.snowflake.sql.schema` (or the URI path), or by running `USE DATABASE` / `USE SCHEMA` before the ingest — and pass only the unqualified table name to `adbc_ingest`.

`adbc_ingest` preserves Arrow field names verbatim — it behaves like the double-quoted `CREATE TABLE` exception described in "Identifiers and Case" below. If your Arrow schema has lowercase fields (e.g., `country`, `user_id`), the resulting Snowflake columns are stored as lowercase and **must be referenced with double quotes** in every subsequent query (`SELECT "country" FROM t`, not `SELECT country` or `SELECT COUNTRY`). To get conventional uppercase columns that can be referenced unquoted, rename the Arrow fields to uppercase before calling `adbc_ingest`.

## Identifiers and Case

Snowflake stores and resolves unquoted identifiers as uppercase. Double-quoted identifiers preserve case and are resolved exactly as written, by default. Therefore, names returned by metadata APIs such as `AdbcConnectionGetObjects`, and simple column names in query results, should be treated as the stored Snowflake identifier form.

In typical Snowflake databases, objects and columns are created unquoted, so expect uppercase names such as `C_CUSTKEY`, not `c_custkey`. Do not rely on the case the user typed in SQL; compare against the stored identifier form, or normalize consistently.

Exception: if a table or column was created with double quotes, for example `CREATE TABLE "MyTable" ("id" INT)`, Snowflake stores those names exactly as `MyTable` and `id`, and SQL must reference them with double quotes and the exact case: `SELECT "id" FROM "MyTable"`.

## More Information

See https://docs.adbc-drivers.org/drivers/snowflake/index.html for more detailed documentation if needed.
