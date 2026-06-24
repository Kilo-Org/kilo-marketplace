# go

## Suggested Packages

Make sure to use the latest versions of each of these packages.

- github.com/apache/arrow-adbc/go/adbc@latest
- github.com/apache/arrow-adbc/go/adbc/drivermgr@latest
- github.com/apache/arrow-go/v18/arrow@latest
- github.com/apache/arrow-go/v18/arrow/array@latest
- github.com/apache/arrow-go/v18/arrow/memory@latest

Important: Make sure not to mix github.com/apache/arrow/go and github.com/apache/arrow-go.

## Usage

```go
package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/apache/arrow-adbc/go/adbc"
	"github.com/apache/arrow-adbc/go/adbc/drivermgr"
	"github.com/apache/arrow-go/v18/arrow"
	"github.com/apache/arrow-go/v18/arrow/array"
	"github.com/apache/arrow-go/v18/arrow/memory"
	"github.com/apache/arrow-go/v18/parquet/file"
	"github.com/apache/arrow-go/v18/parquet/pqarrow"
)

func main() {
	ctx := context.Background()

	// Load driver
	var drv drivermgr.Driver

	// Connect to database
	db, err := drv.NewDatabase(map[string]string{
		"driver": "sqlite",
		"uri":    ":memory:",
	})
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	conn, err := db.Open(ctx)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	// Execute a query
	stmt, err := conn.NewStatement()
	if err != nil {
		log.Fatal(err)
	}
	defer stmt.Close()

	err = stmt.SetSqlQuery("SELECT 41")
	if err != nil {
		log.Fatal(err)
	}

	reader, _, err := stmt.ExecuteQuery(ctx)
	if err != nil {
		log.Fatal(err)
	}
	for reader.Next() {
		fmt.Println(reader.RecordBatch())
	}
	reader.Release()

	// Execute a query with a bind parameter
	schema := arrow.NewSchema([]arrow.Field{
		{Name: "param1", Type: arrow.PrimitiveTypes.Int64},
	}, nil)

	params, _, err := array.RecordFromJSON(memory.DefaultAllocator, schema,
		strings.NewReader(`[{"param1": 41}]`))
	if err != nil {
		log.Fatal(err)
	}
	defer params.Release()

	err = stmt.SetSqlQuery("SELECT ? + 1 AS the_answer")
	if err != nil {
		log.Fatal(err)
	}

	err = stmt.Prepare(ctx)
	if err != nil {
		log.Fatal(err)
	}

	err = stmt.Bind(ctx, params)
	if err != nil {
		log.Fatal(err)
	}

	reader2, _, err := stmt.ExecuteQuery(ctx)
	if err != nil {
		log.Fatal(err)
	}
	for reader2.Next() {
		fmt.Println(reader2.RecordBatch())
	}
	reader2.Release()

	// Ingest a Parquet file and read it back
	f, err := os.Open("../penguins.parquet")
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	pf, err := file.NewParquetReader(f)
	if err != nil {
		log.Fatal(err)
	}
	defer pf.Close()

	arrowReader, err := pqarrow.NewFileReader(pf, pqarrow.ArrowReadProperties{}, memory.DefaultAllocator)
	if err != nil {
		log.Fatal(err)
	}

	recordReader, err := arrowReader.GetRecordReader(ctx, nil, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer recordReader.Release()

	_, err = adbc.IngestStream(ctx, conn, recordReader, "penguins",
		adbc.OptionValueIngestModeCreateAppend, adbc.IngestStreamOptions{})
	if err != nil {
		log.Fatal(err)
	}

	err = stmt.SetSqlQuery("SELECT COUNT(*) AS total_rows FROM penguins")
	if err != nil {
		log.Fatal(err)
	}

	reader3, _, err := stmt.ExecuteQuery(ctx)
	if err != nil {
		log.Fatal(err)
	}
	for reader3.Next() {
		fmt.Println(reader3.RecordBatch())
	}
	reader3.Release()

	// GetObjects: list catalogs, schemas, and tables

	// List all catalogs
	rdr, err := conn.GetObjects(ctx, adbc.ObjectDepthCatalogs, nil, nil, nil, nil, nil)
	if err != nil {
		log.Fatal(err)
	}
	for rdr.Next() {
		fmt.Println(rdr.RecordBatch())
	}
	rdr.Release()

	// List all schemas in a specific catalog
	catalog := "main"
	rdr, err = conn.GetObjects(ctx, adbc.ObjectDepthDBSchemas, &catalog, nil, nil, nil, nil)
	if err != nil {
		log.Fatal(err)
	}
	for rdr.Next() {
		fmt.Println(rdr.RecordBatch())
	}
	rdr.Release()

	// List all tables in a specific schema
	dbSchema := ""
	rdr, err = conn.GetObjects(ctx, adbc.ObjectDepthTables, &catalog, &dbSchema, nil, nil, nil)
	if err != nil {
		log.Fatal(err)
	}
	for rdr.Next() {
		fmt.Println(rdr.RecordBatch())
	}
	rdr.Release()
}
```

## Connection Profiles

New in version 1.11.0. Not available in older versions.

The Go `drivermgr` package wraps the C++ driver manager and inherits connection profile support. Pass a `profile://` URI as the `"uri"` option value — no `"driver"` key is needed when the profile specifies the driver.

```go
db, err := drv.NewDatabase(map[string]string{
    "uri": "profile://mydb_dev",
})
```

Or via the `"driver"` key:

```go
db, err := drv.NewDatabase(map[string]string{
    "driver": "profile://mydb_dev",
})
```

## More information

See https://pkg.go.dev/github.com/apache/arrow-adbc/go/adbc for more detailed documentation if needed.
