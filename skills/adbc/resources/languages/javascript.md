# javascript

## Supported Environments

The JavaScript ADBC driver manager requires Node.js 22+, Bun 1.1+, or Deno 2.0+. It does not work in browser environments.

## Suggested Packages

- @apache-arrow/adbc-driver-manager
- apache-arrow
- Optional: `parquet-wasm` for Arrow-compatible Parquet reading

## TypeScript Support

@apache-arrow/adbc-driver-manager is compatible with TypeScript and the package includes TypeScript type definitions by default so a separate types package is not needed.

## Usage

```javascript
import { AdbcDatabase, ObjectDepth } from "@apache-arrow/adbc-driver-manager";
import { tableFromArrays, tableFromIPC } from "apache-arrow";
import { readFileSync } from "node:fs";
import { readParquet } from "parquet-wasm/node";

const db = new AdbcDatabase({
  driver: "sqlite",
  databaseOptions: { uri: ":memory:" },
});
const connection = await db.connect();

// Execute a query
const table = await connection.query("SELECT 41");
console.log(table.toArray());

// For large result sets, stream record batches instead
const reader = await connection.queryStream("SELECT 41");
for await (const batch of reader) {
  console.log(`Received batch with ${batch.numRows} rows`);
}

//  Execute a query with a bind parameter
const stmt = await connection.createStatement();
await stmt.setSqlQuery("SELECT * FROM my_table WHERE id = ?");
await stmt.bind(tableFromArrays({ id: [2] }));
const result = await stmt.executeQuery();
for await (const batch of result) {
  console.log(batch.toArray());
}
await stmt.close();

// DML — returns the number of affected rows
await connection.execute("CREATE TABLE my_table (id INTEGER)");
await connection.execute("INSERT INTO my_table VALUES (1), (2), (3)");
const affected = await connection.execute("DELETE FROM my_table WHERE id = 1");
console.log(`Deleted ${affected} row(s)`);

// Ingest a Parquet file and read it back
const parquetBuf = readFileSync(
  new URL("../penguins.parquet", import.meta.url),
);
const penguins = tableFromIPC(readParquet(parquetBuf).intoIPCStream());
await connection.ingest("penguins", penguins);
const countResult = await connection.query(
  "SELECT COUNT(*) AS total_rows FROM penguins",
);
console.log(countResult.toArray());

// List all catalogs
console.log(
  (await connection.getObjects({ depth: ObjectDepth.Catalogs })).toArray(),
);

// List all schemas in a specific catalog
console.log(
  (
    await connection.getObjects({ depth: ObjectDepth.Schemas, catalog: "main" })
  ).toArray(),
);

// List all tables in a specific schema
console.log(
  (
    await connection.getObjects({
      depth: ObjectDepth.Tables,
      catalog: "main",
      dbSchema: "",
    })
  ).toArray(),
);


await connection.close();
await db.close();
```

## Connection Profiles

Pass a `profile://` URI as the `driver` field:

```javascript
import { AdbcDatabase } from "@apache-arrow/adbc-driver-manager";

const db = new AdbcDatabase({
  driver: "profile://mydb_dev",
});
const connection = await db.connect();
```

## More information

See https://arrow.apache.org/adbc/main/javascript/index.html for more detailed documentation if needed.
