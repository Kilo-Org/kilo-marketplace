# rust

## Suggested Packages

Important: Getting the right set of crates requires extra care. If you don't, you'll get errors and the following note:

> note: two different versions of crate `arrow_array` are being used; two types coming from two different versions of the same crate are different types even if they look the same

Follow this two-step process to get the right versions of dependencies.

First cargo add `adbc_core` and `adbc_driver_manager`:

```sh
cargo add adbc_core adbc_driver_manager
```

And then use cargo tree to find out which versions of the arrow crate those crates use:

```console
$ cargo tree | grep arrow
    │   ├── arrow-array v57.3.0
```

And then add arrow and parquet crates using the same major version:

```sh
cargo add 'arrow@57' 'parquet@57'
```

## Usage

```rust
use std::fs::File;
use std::sync::Arc;

use adbc_core::options::{AdbcVersion, IngestMode, ObjectDepth, OptionDatabase, OptionStatement};
use adbc_core::{Connection, Database, Driver, Optionable, Statement, LOAD_FLAG_DEFAULT};
use adbc_driver_manager::ManagedDriver;
use arrow::datatypes::{DataType, Field, Schema};
use arrow::util::pretty;
use arrow_array::{Int64Array, RecordBatch};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load driver
    let mut driver = ManagedDriver::load_from_name(
        "sqlite",
        None,
        AdbcVersion::default(),
        LOAD_FLAG_DEFAULT,
        None,
    )?;

    // Connect to database
    let opts = [(OptionDatabase::Uri, ":memory:".into())];
    let db = driver.new_database_with_opts(opts)?;
    let mut conn = db.new_connection()?;

    // Execute a query
    let mut stmt = conn.new_statement()?;
    stmt.set_sql_query("SELECT 41")?;
    let reader = stmt.execute()?;
    let batches: Vec<RecordBatch> = reader.collect::<Result<_, _>>()?;
    pretty::print_batches(&batches)?;

    // Execute a query with a bind parameter
    let mut stmt = conn.new_statement()?;
    stmt.set_sql_query("SELECT ? + 1 AS the_answer")?;
    let schema = Arc::new(Schema::new(vec![Field::new("x", DataType::Int64, true)]));
    let batch = RecordBatch::try_new(schema, vec![Arc::new(Int64Array::from(vec![41]))])?;
    stmt.bind(batch)?;
    let reader = stmt.execute()?;
    let batches: Vec<RecordBatch> = reader.collect::<Result<_, _>>()?;
    pretty::print_batches(&batches)?;

    // Ingest a Parquet file and read it back
    let file = File::open("../penguins.parquet")?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
    let reader = builder.build()?;

    let mut stmt = conn.new_statement()?;
    stmt.set_option(OptionStatement::TargetTable, "penguins".into())?;
    stmt.set_option(OptionStatement::IngestMode, IngestMode::Create.into())?;
    stmt.bind_stream(Box::new(reader))?;
    stmt.execute_update()?;

    let mut stmt = conn.new_statement()?;
    stmt.set_sql_query("SELECT COUNT(*) AS total_rows FROM penguins")?;
    let reader = stmt.execute()?;
    let batches: Vec<RecordBatch> = reader.collect::<Result<_, _>>()?;
    pretty::print_batches(&batches)?;

    // List all catalogs
    let reader = conn.get_objects(ObjectDepth::Catalogs, None, None, None, None, None)?;
    let batches: Vec<RecordBatch> = reader.collect::<Result<_, _>>()?;
    pretty::print_batches(&batches)?;

    // List all schemas in a specific catalog
    let reader = conn.get_objects(ObjectDepth::Schemas, Some("main"), None, None, None, None)?;
    let batches: Vec<RecordBatch> = reader.collect::<Result<_, _>>()?;
    pretty::print_batches(&batches)?;

    // List all tables in a specific schema
    let reader = conn.get_objects(ObjectDepth::Tables, Some("main"), Some(""), None, None, None)?;
    let batches: Vec<RecordBatch> = reader.collect::<Result<_, _>>()?;
    pretty::print_batches(&batches)?;

    Ok(())
}
```

## Connection Profiles

New in version 0.23.0. Not available in older versions.

Use `ManagedDatabase::from_uri` with a `profile://` URI to connect via a named profile:

```rust
use adbc_core::options::AdbcVersion;
use adbc_core::LOAD_FLAG_DEFAULT;
use adbc_driver_manager::ManagedDatabase;

let database = ManagedDatabase::from_uri(
    "profile://mydb_dev",
    None,
    AdbcVersion::V100,
    LOAD_FLAG_DEFAULT,
    None,
)?;
```

To override options from the profile, use `from_uri_with_opts`:

```rust
use adbc_core::options::{AdbcVersion, OptionDatabase, OptionValue};
use adbc_core::LOAD_FLAG_DEFAULT;

let overrides = vec![(
    OptionDatabase::Uri,
    OptionValue::String("file::memory:".to_string()),
)];

let database = ManagedDatabase::from_uri_with_opts(
    "profile://mydb_dev",
    None,
    AdbcVersion::V100,
    LOAD_FLAG_DEFAULT,
    None,
    overrides,
)?;
```

## More information

See https://arrow.apache.org/adbc/current/rust/index.html for more detailed documentation if needed.
