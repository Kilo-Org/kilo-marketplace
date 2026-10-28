# ADF Datasets - Complete JSON Reference

## Azure Blob Storage

### Delimited Text (CSV)
```json
{
  "name": "DS_Blob_CSV",
  "type": "Microsoft.DataFactory/factories/datasets",
  "properties": {
    "type": "DelimitedText",
    "linkedServiceName": {
      "referenceName": "LS_AzureBlobStorage",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "AzureBlobStorageLocation",
        "container": "data",
        "folderPath": "raw/sales",
        "fileName": "sales.csv"
      },
      "columnDelimiter": ",",
      "rowDelimiter": "\n",
      "encodingName": "UTF-8",
      "escapeChar": "\\",
      "quoteChar": "\"",
      "firstRowAsHeader": true,
      "nullValue": "",
      "compressionCodec": "none"
    },
    "schema": []
  }
}
```

### Parquet
```json
{
  "name": "DS_Blob_Parquet",
  "properties": {
    "type": "Parquet",
    "linkedServiceName": {
      "referenceName": "LS_AzureBlobStorage",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "AzureBlobStorageLocation",
        "container": "curated",
        "folderPath": "sales/year=2025/month=01"
      },
      "compressionCodec": "snappy"
    },
    "schema": []
  }
}
```

### JSON
```json
{
  "name": "DS_Blob_JSON",
  "properties": {
    "type": "Json",
    "linkedServiceName": {
      "referenceName": "LS_AzureBlobStorage",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "AzureBlobStorageLocation",
        "container": "data",
        "folderPath": "events",
        "fileName": "events.json"
      },
      "encodingName": "UTF-8"
    }
  }
}
```

### Excel
```json
{
  "name": "DS_Blob_Excel",
  "properties": {
    "type": "Excel",
    "linkedServiceName": {
      "referenceName": "LS_AzureBlobStorage",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "AzureBlobStorageLocation",
        "container": "uploads",
        "fileName": "report.xlsx"
      },
      "sheetName": "Sheet1",
      "firstRowAsHeader": true,
      "range": "A1:Z1000"
    }
  }
}
```

### Binary (Any File)
```json
{
  "name": "DS_Blob_Binary",
  "properties": {
    "type": "Binary",
    "linkedServiceName": {
      "referenceName": "LS_AzureBlobStorage",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "AzureBlobStorageLocation",
        "container": "files",
        "folderPath": "uploads"
      }
    }
  }
}
```

---

## Azure Data Lake Storage Gen2

### Parquet with Partitioning
```json
{
  "name": "DS_ADLS_Parquet_Partitioned",
  "properties": {
    "type": "Parquet",
    "linkedServiceName": {
      "referenceName": "LS_ADLS",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "AzureBlobFSLocation",
        "fileSystem": "datalake",
        "folderPath": {
          "value": "@concat('curated/sales/year=', formatDateTime(pipeline().parameters.ProcessDate, 'yyyy'), '/month=', formatDateTime(pipeline().parameters.ProcessDate, 'MM'))",
          "type": "Expression"
        }
      },
      "compressionCodec": "snappy"
    },
    "parameters": {
      "ProcessDate": { "type": "String" }
    }
  }
}
```

### Delta Lake
```json
{
  "name": "DS_ADLS_Delta",
  "properties": {
    "type": "Parquet",
    "linkedServiceName": {
      "referenceName": "LS_ADLS",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "AzureBlobFSLocation",
        "fileSystem": "datalake",
        "folderPath": "bronze/orders"
      }
    }
  }
}
```

---

## Azure SQL Database

```json
{
  "name": "DS_AzureSql_Table",
  "properties": {
    "type": "AzureSqlTable",
    "linkedServiceName": {
      "referenceName": "LS_AzureSql",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "schema": "dbo",
      "table": "Customers"
    },
    "schema": [
      { "name": "CustomerID", "type": "int" },
      { "name": "CustomerName", "type": "nvarchar" },
      { "name": "Email", "type": "nvarchar" },
      { "name": "CreatedDate", "type": "datetime2" }
    ]
  }
}
```

### Parameterized Table
```json
{
  "name": "DS_AzureSql_Parameterized",
  "properties": {
    "type": "AzureSqlTable",
    "linkedServiceName": {
      "referenceName": "LS_AzureSql",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "schema": {
        "value": "@dataset().SchemaName",
        "type": "Expression"
      },
      "table": {
        "value": "@dataset().TableName",
        "type": "Expression"
      }
    },
    "parameters": {
      "SchemaName": { "type": "String", "defaultValue": "dbo" },
      "TableName": { "type": "String" }
    }
  }
}
```

---

## Azure Synapse Analytics

```json
{
  "name": "DS_Synapse_Table",
  "properties": {
    "type": "AzureSqlDWTable",
    "linkedServiceName": {
      "referenceName": "LS_Synapse",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "schema": "staging",
      "table": "FactSales"
    }
  }
}
```

---

## Microsoft Fabric

### Lakehouse Table
```json
{
  "name": "DS_Fabric_LakehouseTable",
  "properties": {
    "type": "LakehouseTable",
    "linkedServiceName": {
      "referenceName": "LS_FabricLakehouse",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "table": "sales_facts"
    }
  }
}
```

### Warehouse Table
```json
{
  "name": "DS_Fabric_WarehouseTable",
  "properties": {
    "type": "WarehouseTable",
    "linkedServiceName": {
      "referenceName": "LS_FabricWarehouse",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "schema": "dbo",
      "table": "DimCustomer"
    }
  }
}
```

---

## REST API

```json
{
  "name": "DS_REST_API",
  "properties": {
    "type": "RestResource",
    "linkedServiceName": {
      "referenceName": "LS_REST",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "relativeUrl": {
        "value": "@concat('/api/v2/orders?date=', dataset().QueryDate)",
        "type": "Expression"
      },
      "requestMethod": "GET",
      "additionalHeaders": {
        "Accept": "application/json"
      },
      "paginationRules": {
        "AbsoluteUrl": "$.nextLink"
      }
    },
    "parameters": {
      "QueryDate": { "type": "String" }
    }
  }
}
```

---

## HTTP

```json
{
  "name": "DS_HTTP_CSV",
  "properties": {
    "type": "DelimitedText",
    "linkedServiceName": {
      "referenceName": "LS_HTTP",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "HttpServerLocation",
        "relativeUrl": "/data/export.csv"
      },
      "columnDelimiter": ",",
      "firstRowAsHeader": true
    }
  }
}
```

---

## SFTP

```json
{
  "name": "DS_SFTP_CSV",
  "properties": {
    "type": "DelimitedText",
    "linkedServiceName": {
      "referenceName": "LS_SFTP",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "location": {
        "type": "SftpLocation",
        "folderPath": "/incoming/sales",
        "fileName": {
          "value": "@concat('sales_', formatDateTime(utcnow(), 'yyyyMMdd'), '.csv')",
          "type": "Expression"
        }
      },
      "columnDelimiter": ",",
      "firstRowAsHeader": true
    }
  }
}
```

---

## Snowflake

```json
{
  "name": "DS_Snowflake_Table",
  "properties": {
    "type": "SnowflakeTable",
    "linkedServiceName": {
      "referenceName": "LS_Snowflake",
      "type": "LinkedServiceReference"
    },
    "typeProperties": {
      "schema": "PUBLIC",
      "table": "ORDERS"
    }
  }
}
```

---

## Common Patterns

### Parameterized Folder Path (Date Partitioning)
```json
{
  "typeProperties": {
    "location": {
      "type": "AzureBlobStorageLocation",
      "container": "data",
      "folderPath": {
        "value": "@concat('year=', formatDateTime(dataset().ProcessDate, 'yyyy'), '/month=', formatDateTime(dataset().ProcessDate, 'MM'), '/day=', formatDateTime(dataset().ProcessDate, 'dd'))",
        "type": "Expression"
      }
    }
  },
  "parameters": {
    "ProcessDate": { "type": "String" }
  }
}
```

### Wildcard File Name
```json
{
  "typeProperties": {
    "location": {
      "type": "AzureBlobStorageLocation",
      "container": "data",
      "folderPath": "raw",
      "fileName": "*.csv"
    }
  }
}
```

### Compression Options
```json
{
  "compressionCodec": "gzip",
  "compressionLevel": "Optimal"
}
```

Valid compression codecs:
- `none`
- `gzip`
- `snappy` (Parquet only)
- `lzo`
- `bzip2`
- `deflate`
- `zstd`
- `tar`
- `targzip`

---

## Schema Definition

### Explicit Schema
```json
{
  "schema": [
    { "name": "Id", "type": "Int32" },
    { "name": "Name", "type": "String" },
    { "name": "Amount", "type": "Decimal", "precision": 18, "scale": 2 },
    { "name": "CreatedAt", "type": "DateTime" },
    { "name": "IsActive", "type": "Boolean" }
  ]
}
```

### Import Schema from Source
Set `"schema": []` and use "Import schema" in the UI, or define mappings in the Copy activity translator.

---

## Dataset Parameters Usage

In pipeline Copy activity:
```json
{
  "inputs": [
    {
      "referenceName": "DS_Blob_Parameterized",
      "type": "DatasetReference",
      "parameters": {
        "FolderPath": "@pipeline().parameters.SourceFolder",
        "FileName": "@pipeline().parameters.SourceFile"
      }
    }
  ]
}
```

---

## Inline Datasets (Data Flows)

For Mapping Data Flows, inline datasets avoid creating separate dataset objects:

```json
{
  "source": {
    "type": "DelimitedTextSource",
    "dataset": {
      "type": "DelimitedText",
      "linkedService": { "referenceName": "LS_Blob", "type": "LinkedServiceReference" },
      "typeProperties": {
        "location": { "type": "AzureBlobStorageLocation", "container": "data", "fileName": "*.csv" },
        "columnDelimiter": ",",
        "firstRowAsHeader": true
      }
    }
  }
}
```
