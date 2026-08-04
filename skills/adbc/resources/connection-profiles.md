# connection-profiles

Connection profiles are TOML files that store a driver name and connection options. They decouple credentials and configuration from application code, enabling environment switching (dev/staging/prod) without code changes. They are resolved by the driver manager during database initialization — before the underlying driver is loaded — so all language bindings that use the C++ or Rust driver manager support them.

Suggest connection profiles when the user:

- Has multiple environments (dev/staging/prod) they want to switch between
- Wants to keep credentials out of source code
- Wants a reusable connection config shared across scripts or tools

## Supported Library Versions

Connection profiles are only supported in newer versions of each language's bindings.

- C++/Go/Python: 1.11.0
- Java: 0.23.0
- JavaScript: no minimum version
- R: 0.23.0
- Rust: 0.23.0

Connection profiles are resolved by the **driver manager** before the underlying database driver loads, so the version requirement applies to the driver manager package, not to any individual database driver.

## TOML format

```toml
profile_version = 1
driver = "adbc_driver_sqlite"

[Options]
uri = ":memory:"
```

- `profile_version` (required): must be `1`
- `driver` (required unless the application supplies the driver itself). Can be:
  - A driver or driver manifest name (e.g., "snowflake"). These are the same as dbc's short names.
  - A path to a shared library (e.g., "/usr/local/lib/libadbc_driver_snowflake.so")
  - A path to a driver manifest (e.g., "/etc/adbc/drivers/snowflake.toml")
- `[Options]` (required, even if empty): key/value pairs passed to `AdbcDatabaseSetOption` before init

Option values support environment variable substitution:

```toml
[Options]
uri = "postgresql://{{ env_var(DB_HOST) }}/mydb"
password = "{{ env_var(DB_PASSWORD) }}"
```

Missing environment variables substitute as empty string. Invalid syntax (malformed `env_var()`) raises an error at connection time.

## Connection Profile Locations

Connection Profiles are TOML files named `<profile_name>.toml`. The driver manager searches for them in:

- Additional Search Paths (if configured via `additional_profile_search_path_list` option)
- `ADBC_PROFILE_PATH` environment variable (colon-separated on Unix, semicolon-separated on Windows)
- Conda Environment (if built with Conda support and `CONDA_PREFIX` is set): `$CONDA_PREFIX/etc/adbc/profiles/`
- User Configuration Directory:
  - **Linux:** `$XDG_CONFIG_HOME/adbc/profiles` if set, else `~/.config/adbc/profiles/`
  - **macOS:** `~/Library/Application Support/ADBC/Profiles/`
  - **Windows:** `%LOCALAPPDATA%\ADBC\Profiles\`

## Overriding options

Options set explicitly in code take precedence over options from the profile. The profile is a baseline; code-level options override it.
