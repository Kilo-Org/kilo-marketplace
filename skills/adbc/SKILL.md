---
name: adbc
description: >-
  Connect to and work with databases using Arrow Database Connectivity (ADBC).
  Use whenever the user needs to use a database.
metadata:
  category: data
  source:
    repository: 'https://github.com/columnar-tech/skills'
    path: skills/adbc
    license_path: LICENSE
    commit: 8add65001dfb37b423e31124a0749d7879557723
---

## Find a driver for a database

Use the dbc command line tool to find available drivers for a database.
It's possible no driver may exist for the user's database of choice as not all databases have ADBC drivers.

## Install dbc

If the user does not have `dbc` available, try to install it for them.

Prefer installing it with these commands, in order of preference, if the tool is available:

- If `uv` is available: `uv tool install dbc`
- If `pipx` is available: `pipx install dbc`
- If `brew` is available: `brew install columnar-tech/tap/dbc`
- On Windows, if `winget` is available: `winget install dbc`
- Otherwise, direct the user to the installation docs: https://docs.columnar.tech/dbc/getting_started/installation/

### Search for a driver

```sh
dbc search
```

### Install a driver

Install a driver by running `dbc install <DRIVER>`. This is idempotent — if the driver is already installed, it is a no-op that simply reports the existing installation — so there is no need to check first before running it.
Prefer to install drivers using dbc over installing driver packages from PyPI or Conda Forge.

For anything beyond a one-shot `dbc install <DRIVER>` — reproducible `dbc.toml` / `dbc sync` workflows, version pinning, or any other `dbc` subcommand — invoke the `dbc` skill rather than guessing at commands. In particular, note that **there is no `dbc list` command**.

### Referring to drivers

Refer to drivers by their dbc short name and avoid specifying drivers with absolute paths.

Example: After running `dbc install sqlite`, refer to that driver as `sqlite`. For example:

```python
from adbc_driver_manager import dbapi
dbapi.connect(driver="sqlite", db_kwargs={"uri": "foo.db"})
```

Don't use `dbc info` to find where drivers are installed and find their absolute paths on disk.

## Programming Language

See the resources below depending on which language or languages the user wants to use:

- C++: `resources/languages/cpp.md`
- Go: `resources/languages/go.md`
- JavaScript: `resources/languages/javascript.md`
- Python: `resources/languages/python.md`
- R: `resources/languages/r.md`
- Rust: `resources/languages/rust.md`

Prefer any language the user has already said they're using or can use.
Each of these examples use the "sqlite" driver, connect to an in-memory database, and load a "penguins.parquet" file. This is done just for explanatory purposes and the code should be adapted to the user's problem.

## Using a Driver

See the resources below depending on which database the user wants to use:

- DuckDB: `resources/drivers/duckdb.md`
- FlightSQL: `resources/drivers/flightsql.md`
- MySQL: `resources/drivers/mysql.md`
- PostgreSQL: `resources/drivers/postgresql.md`
- Snowflake: `resources/drivers/snowflake.md`
- SQLite: `resources/drivers/sqlite.md`

## Connection Profiles

Connection profiles are TOML files that store a driver name and connection options, referenced by a `profile://profile_name` URI. They decouple credentials and environment-specific config from application code.

Suggest connection profiles when the user:

- Has multiple environments (dev/staging/prod) to switch between
- Wants to keep credentials out of source code
- Wants a shared, reusable connection config

All language bindings that wrap the C++ or Rust driver manager support connection profiles, including Python, Go, R, Java, GLib/Ruby, C++, and Rust. JavaScript (`@apache-arrow/adbc-driver-manager`) also supports connection profiles via the `profileSearchPaths` option.

See `resources/connection-profiles.md` for the TOML format, file locations, and environment variable substitution syntax. See the relevant language resource for the binding-specific API.

## More Resources

- Official Apache Arrow ADBC documentation: https://arrow.apache.org/adbc/current/index.html
- ADBC Quickstarts. Minimal but well-documented examples for each language and many databases: https://github.com/columnar-tech/adbc-quickstarts
- Documentation for many dbc-installable drivers: https://docs.adbc-drivers.org
