# cpp

## Suggested Packages

Pre-compiled packages for ADBC are only available through conda. Use the following conda packages:

- libadbc-driver-manager
- libarrow
- cmake (optional, for CMake builds)
- compilers

## Usage

## Building

ADBC packages provide CMake targets so a CMakeLists.txt like this will work:

```cmake
cmake_minimum_required(VERSION 3.15)
project(adbc_sqlite_example)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(Arrow REQUIRED)
find_package(Parquet REQUIRED)
find_package(AdbcDriverManager REQUIRED)

add_executable(main main.cpp)

target_link_libraries(main
    PRIVATE
        Arrow::arrow_shared
        Parquet::parquet_shared
        AdbcDriverManager::adbc_driver_manager_shared
)
```

Alternatively, with pkg-config, use `-larrow -lparquet -ladbc_driver_manager`.

## Code

```cpp
#include <cstdlib>
#include <iostream>
#include <memory>

#include <arrow-adbc/adbc.h>
#include <arrow-adbc/adbc_driver_manager.h>
#include <arrow/builder.h>
#include <arrow/c/bridge.h>
#include <arrow/record_batch.h>
#include <arrow/table.h>
#include <parquet/arrow/reader.h>
#include <parquet/file_reader.h>

#define CHECK_ADBC(EXPR)                                                       \
  if (AdbcStatusCode status = (EXPR); status != ADBC_STATUS_OK) {              \
    if (error.message != nullptr) {                                            \
      std::cerr << "ADBC Error: " << error.message << std::endl;               \
    }                                                                          \
    return EXIT_FAILURE;                                                       \
  }

void print_stream(struct ArrowArrayStream *stream) {
  auto maybe_reader = arrow::ImportRecordBatchReader(stream);
  if (!maybe_reader.ok()) {
    std::cerr << "Failed to import reader: " << maybe_reader.status().message()
              << std::endl;
    return;
  }
  auto reader = maybe_reader.ValueOrDie();
  while (true) {
    auto maybe_batch = reader->Next();
    if (!maybe_batch.ok()) {
      std::cerr << "Error: " << maybe_batch.status().message() << std::endl;
      return;
    }
    auto batch = maybe_batch.ValueOrDie();
    if (!batch) break;
    std::cout << batch->ToString() << std::endl;
  }
}

int main() {
  AdbcError error = {};
  int64_t rows_affected = -1;

  // Load driver
  AdbcDatabase database = {};
  CHECK_ADBC(AdbcDatabaseNew(&database, &error));
  CHECK_ADBC(AdbcDatabaseSetOption(&database, "driver", "sqlite", &error));
  CHECK_ADBC(AdbcDatabaseSetOption(&database, "uri", ":memory:", &error));
  CHECK_ADBC(AdbcDriverManagerDatabaseSetLoadFlags(
      &database, ADBC_LOAD_FLAG_DEFAULT, &error));
  CHECK_ADBC(AdbcDatabaseInit(&database, &error));

  // Connect to database
  AdbcConnection connection = {};
  CHECK_ADBC(AdbcConnectionNew(&connection, &error));
  CHECK_ADBC(AdbcConnectionInit(&connection, &database, &error));

  // Execute a query
  AdbcStatement stmt1 = {};
  CHECK_ADBC(AdbcStatementNew(&connection, &stmt1, &error));
  CHECK_ADBC(AdbcStatementSetSqlQuery(&stmt1, "SELECT 41", &error));
  struct ArrowArrayStream stream1 = {};
  CHECK_ADBC(
      AdbcStatementExecuteQuery(&stmt1, &stream1, &rows_affected, &error));
  print_stream(&stream1);
  CHECK_ADBC(AdbcStatementRelease(&stmt1, &error));

  // Execute a query with a bind parameter
  AdbcStatement stmt2 = {};
  CHECK_ADBC(AdbcStatementNew(&connection, &stmt2, &error));
  CHECK_ADBC(
      AdbcStatementSetSqlQuery(&stmt2, "SELECT ? + 1 AS the_answer", &error));

  arrow::Int64Builder bind_builder;
  if (!bind_builder.Append(41).ok()) {
    std::cerr << "Failed to create bind data" << std::endl;
    return EXIT_FAILURE;
  }

  std::shared_ptr<arrow::Array> bind_array;
  if (!bind_builder.Finish(&bind_array).ok()) {
    std::cerr << "Failed to finish bind array" << std::endl;
    return EXIT_FAILURE;
  }

  auto bind_schema = arrow::schema({arrow::field("x", arrow::int64())});
  auto bind_batch = arrow::RecordBatch::Make(bind_schema, 1, {bind_array});

  struct ArrowSchema c_bind_schema;
  struct ArrowArray c_bind_array;
  if (!arrow::ExportRecordBatch(*bind_batch, &c_bind_array, &c_bind_schema)
           .ok()) {
    std::cerr << "Failed to export bind batch" << std::endl;
    return EXIT_FAILURE;
  }

  CHECK_ADBC(AdbcStatementBind(&stmt2, &c_bind_array, &c_bind_schema, &error));

  struct ArrowArrayStream stream2 = {};
  CHECK_ADBC(
      AdbcStatementExecuteQuery(&stmt2, &stream2, &rows_affected, &error));
  print_stream(&stream2);
  CHECK_ADBC(AdbcStatementRelease(&stmt2, &error));

  // Ingest a Parquet file and read it back
  auto pq_reader =
      parquet::ParquetFileReader::OpenFile("../penguins.parquet", false);
  auto arrow_reader_result = parquet::arrow::FileReader::Make(
      arrow::default_memory_pool(), std::move(pq_reader));
  if (!arrow_reader_result.ok()) {
    std::cerr << "Failed to open parquet: "
              << arrow_reader_result.status().message() << std::endl;
    return EXIT_FAILURE;
  }
  auto arrow_reader = std::move(arrow_reader_result).ValueOrDie();

  std::shared_ptr<arrow::Table> table;
  auto status = arrow_reader->ReadTable(&table);
  if (!status.ok()) {
    std::cerr << "Failed to read table: " << status.message() << std::endl;
    return EXIT_FAILURE;
  }

  AdbcStatement stmt3 = {};
  CHECK_ADBC(AdbcStatementNew(&connection, &stmt3, &error));
  CHECK_ADBC(AdbcStatementSetOption(&stmt3, ADBC_INGEST_OPTION_TARGET_TABLE,
                                    "penguins", &error));
  CHECK_ADBC(AdbcStatementSetOption(&stmt3, ADBC_INGEST_OPTION_MODE,
                                    ADBC_INGEST_OPTION_MODE_CREATE, &error));

  auto combined = table->CombineChunks();
  if (!combined.ok()) {
    std::cerr << "Failed to combine chunks: " << combined.status().message()
              << std::endl;
    return EXIT_FAILURE;
  }
  auto flat_table = combined.ValueOrDie();

  arrow::TableBatchReader table_reader(*flat_table);
  std::shared_ptr<arrow::RecordBatch> batch;
  status = table_reader.ReadNext(&batch);
  if (!status.ok() || !batch) {
    std::cerr << "Failed to read batch" << std::endl;
    return EXIT_FAILURE;
  }

  struct ArrowSchema c_schema;
  struct ArrowArray c_array;
  status = arrow::ExportRecordBatch(*batch, &c_array, &c_schema);
  if (!status.ok()) {
    std::cerr << "Failed to export batch: " << status.message() << std::endl;
    return EXIT_FAILURE;
  }

  CHECK_ADBC(AdbcStatementBind(&stmt3, &c_array, &c_schema, &error));
  CHECK_ADBC(
      AdbcStatementExecuteQuery(&stmt3, nullptr, &rows_affected, &error));
  CHECK_ADBC(AdbcStatementRelease(&stmt3, &error));

  AdbcStatement stmt4 = {};
  CHECK_ADBC(AdbcStatementNew(&connection, &stmt4, &error));
  CHECK_ADBC(AdbcStatementSetSqlQuery(
      &stmt4, "SELECT COUNT(*) AS total_rows FROM penguins", &error));
  struct ArrowArrayStream stream4 = {};
  CHECK_ADBC(
      AdbcStatementExecuteQuery(&stmt4, &stream4, &rows_affected, &error));
  print_stream(&stream4);
  CHECK_ADBC(AdbcStatementRelease(&stmt4, &error));

  // List all catalogs
  struct ArrowArrayStream objects1 = {};
  CHECK_ADBC(AdbcConnectionGetObjects(&connection, ADBC_OBJECT_DEPTH_CATALOGS,
                                      NULL, NULL, NULL, NULL, NULL, &objects1,
                                      &error));
  print_stream(&objects1);

  // List all schemas in a specific catalog
  struct ArrowArrayStream objects2 = {};
  CHECK_ADBC(AdbcConnectionGetObjects(&connection, ADBC_OBJECT_DEPTH_DB_SCHEMAS,
                                      "main", NULL, NULL, NULL, NULL, &objects2,
                                      &error));
  print_stream(&objects2);

  // List all tables in a specific schema
  struct ArrowArrayStream objects3 = {};
  CHECK_ADBC(AdbcConnectionGetObjects(&connection, ADBC_OBJECT_DEPTH_TABLES,
                                      "main", "", NULL, NULL, NULL, &objects3,
                                      &error));
  print_stream(&objects3);

  // Clean up
  CHECK_ADBC(AdbcConnectionRelease(&connection, &error));
  CHECK_ADBC(AdbcDatabaseRelease(&database, &error));

  return EXIT_SUCCESS;
}
```

## Connection Profiles

New in version 1.11.0. Not available in older versions.

Set the `"uri"` or `"driver"` option to a `profile://` URI before calling `AdbcDatabaseInit`. The driver manager loads the profile and applies its options automatically — do not also set a `"driver"` option when using `profile://`:

```cpp
AdbcDatabase database = {};
AdbcDatabaseNew(&database, &error);
AdbcDatabaseSetOption(&database, "uri", "profile://mydb_dev", &error);
AdbcDatabaseInit(&database, &error);
```

Alternatively, use the `"profile"` option to pass a profile name (without the `profile://` prefix):

```cpp
AdbcDatabaseNew(&database, &error);
AdbcDatabaseSetOption(&database, "profile", "mydb_dev", &error);
AdbcDatabaseSetOption(&database, "additional_profile_search_path_list",
                      "/path/to/profiles", &error);
AdbcDatabaseInit(&database, &error);
```

## More information

See https://arrow.apache.org/adbc/current/cpp/index.html for more detailed documentation if needed.
