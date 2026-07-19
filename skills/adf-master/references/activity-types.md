# ADF Activity Types - Complete JSON Reference

## Copy Activity

The Copy Activity moves data between supported data stores.

### Basic Structure
```json
{
  "name": "CopyData",
  "type": "Copy",
  "dependsOn": [],
  "policy": {
    "timeout": "0.12:00:00",
    "retry": 2,
    "retryIntervalInSeconds": 30,
    "secureOutput": false,
    "secureInput": false
  },
  "typeProperties": {
    "source": { },
    "sink": { },
    "enableStaging": false,
    "parallelCopies": 4,
    "dataIntegrationUnits": 4,
    "translator": { }
  },
  "inputs": [{ "referenceName": "SourceDataset", "type": "DatasetReference" }],
  "outputs": [{ "referenceName": "SinkDataset", "type": "DatasetReference" }]
}
```

### Source Types

**AzureSqlSource:**
```json
{
  "source": {
    "type": "AzureSqlSource",
    "sqlReaderQuery": "SELECT * FROM dbo.TableName WHERE Date >= '@{pipeline().parameters.StartDate}'",
    "queryTimeout": "02:00:00",
    "partitionOption": "None",
    "isolationLevel": "ReadCommitted"
  }
}
```

**DelimitedTextSource:**
```json
{
  "source": {
    "type": "DelimitedTextSource",
    "storeSettings": {
      "type": "AzureBlobStorageReadSettings",
      "recursive": true,
      "wildcardFolderPath": "raw/2025",
      "wildcardFileName": "*.csv",
      "enablePartitionDiscovery": false
    },
    "formatSettings": {
      "type": "DelimitedTextReadSettings",
      "skipLineCount": 0,
      "compressionProperties": null
    }
  }
}
```

**ParquetSource:**
```json
{
  "source": {
    "type": "ParquetSource",
    "storeSettings": {
      "type": "AzureBlobStorageReadSettings",
      "recursive": true,
      "wildcardFileName": "*.parquet"
    }
  }
}
```

**JsonSource:**
```json
{
  "source": {
    "type": "JsonSource",
    "storeSettings": {
      "type": "AzureBlobStorageReadSettings",
      "recursive": true
    },
    "formatSettings": {
      "type": "JsonReadSettings"
    }
  }
}
```

**RestSource:**
```json
{
  "source": {
    "type": "RestSource",
    "httpRequestTimeout": "00:01:40",
    "requestInterval": "00.00:00:00.010",
    "requestMethod": "GET",
    "additionalHeaders": {
      "Authorization": "Bearer @{pipeline().parameters.Token}"
    },
    "paginationRules": {
      "AbsoluteUrl": "$.nextLink"
    }
  }
}
```

### Sink Types

**ParquetSink:**
```json
{
  "sink": {
    "type": "ParquetSink",
    "storeSettings": {
      "type": "AzureBlobStorageWriteSettings",
      "copyBehavior": "FlattenHierarchy"
    },
    "formatSettings": {
      "type": "ParquetWriteSettings",
      "maxRowsPerFile": 100000,
      "fileNamePrefix": "output_"
    }
  }
}
```

**AzureSqlSink:**
```json
{
  "sink": {
    "type": "AzureSqlSink",
    "writeBatchSize": 10000,
    "writeBatchTimeout": "00:30:00",
    "preCopyScript": "TRUNCATE TABLE staging.TableName",
    "sqlWriterStoredProcedureName": "usp_UpsertData",
    "sqlWriterTableType": "DataTableType",
    "storedProcedureTableTypeParameterName": "DataTable",
    "tableOption": "autoCreate",
    "disableMetricsCollection": false
  }
}
```

**WarehouseSink (Fabric):**
```json
{
  "sink": {
    "type": "WarehouseSink",
    "writeBehavior": "upsert",
    "upsertSettings": {
      "useTempDB": true,
      "keys": ["Id"],
      "interimSchemaName": "staging"
    },
    "writeBatchSize": 10000,
    "tableOption": "autoCreate"
  }
}
```

**LakehouseTableSink:**
```json
{
  "sink": {
    "type": "LakehouseTableSink",
    "tableActionOption": "overwrite"
  }
}
```

### Translator (Schema Mapping)

```json
{
  "translator": {
    "type": "TabularTranslator",
    "mappings": [
      {
        "source": { "name": "CustomerID", "type": "Int32" },
        "sink": { "name": "customer_id", "type": "Int64" }
      },
      {
        "source": { "name": "CustomerName" },
        "sink": { "name": "customer_name" }
      },
      {
        "source": { "path": "$['nested']['value']" },
        "sink": { "name": "nested_value" }
      }
    ],
    "collectionReference": "$['items']",
    "mapComplexValuesToString": true
  }
}
```

---

## ForEach Activity

Iterates over a collection and executes activities for each item.

```json
{
  "name": "ForEach_Tables",
  "type": "ForEach",
  "dependsOn": [],
  "typeProperties": {
    "items": {
      "value": "@pipeline().parameters.TableList",
      "type": "Expression"
    },
    "isSequential": false,
    "batchCount": 20,
    "activities": [
      {
        "name": "CopyTable",
        "type": "Copy",
        "typeProperties": {
          "source": {
            "type": "AzureSqlSource",
            "sqlReaderQuery": "@concat('SELECT * FROM ', item().schemaName, '.', item().tableName)"
          },
          "sink": { "type": "ParquetSink" }
        }
      }
    ]
  }
}
```

**Key Properties:**
- `isSequential`: false = parallel, true = sequential
- `batchCount`: 1-50 (only when isSequential=false)
- Use `@item()` to access current iteration item

**Limitations:**
- Cannot nest ForEach inside ForEach
- Cannot nest Until inside ForEach
- Max 100,000 items

---

## If Condition Activity

Conditional branching based on expression evaluation.

```json
{
  "name": "IfDataExists",
  "type": "IfCondition",
  "dependsOn": [
    { "activity": "LookupCount", "dependencyConditions": ["Succeeded"] }
  ],
  "typeProperties": {
    "expression": {
      "value": "@greater(activity('LookupCount').output.firstRow.RecordCount, 0)",
      "type": "Expression"
    },
    "ifTrueActivities": [
      {
        "name": "ProcessData",
        "type": "Copy",
        "typeProperties": { }
      }
    ],
    "ifFalseActivities": [
      {
        "name": "LogNoData",
        "type": "WebActivity",
        "typeProperties": { }
      }
    ]
  }
}
```

**Limitations:**
- Cannot nest ForEach, If, Switch, Until, or Validation inside branches
- Use Execute Pipeline for complex nested logic

---

## Switch Activity

Multi-way branching based on expression value.

```json
{
  "name": "SwitchByEnvironment",
  "type": "Switch",
  "dependsOn": [],
  "typeProperties": {
    "on": {
      "value": "@pipeline().parameters.Environment",
      "type": "Expression"
    },
    "cases": [
      {
        "value": "development",
        "activities": [
          { "name": "DevProcess", "type": "Copy" }
        ]
      },
      {
        "value": "production",
        "activities": [
          { "name": "ProdProcess", "type": "Copy" }
        ]
      }
    ],
    "defaultActivities": [
      { "name": "DefaultProcess", "type": "Copy" }
    ]
  }
}
```

---

## Until Activity

Loops until condition is true or timeout is reached.

```json
{
  "name": "UntilComplete",
  "type": "Until",
  "dependsOn": [],
  "typeProperties": {
    "expression": {
      "value": "@equals(variables('IsComplete'), true)",
      "type": "Expression"
    },
    "timeout": "0.01:00:00",
    "activities": [
      {
        "name": "CheckStatus",
        "type": "WebActivity",
        "typeProperties": {
          "url": "@pipeline().parameters.StatusUrl",
          "method": "GET"
        }
      },
      {
        "name": "SetComplete",
        "type": "SetVariable",
        "dependsOn": [{ "activity": "CheckStatus", "dependencyConditions": ["Succeeded"] }],
        "typeProperties": {
          "variableName": "IsComplete",
          "value": "@equals(activity('CheckStatus').output.status, 'Complete')"
        }
      },
      {
        "name": "WaitBeforeRetry",
        "type": "Wait",
        "dependsOn": [{ "activity": "SetComplete", "dependencyConditions": ["Succeeded"] }],
        "typeProperties": {
          "waitTimeInSeconds": 30
        }
      }
    ]
  }
}
```

---

## Lookup Activity

Retrieves data from a source for use in expressions.

```json
{
  "name": "LookupConfig",
  "type": "Lookup",
  "dependsOn": [],
  "policy": {
    "timeout": "0.00:10:00",
    "retry": 2
  },
  "typeProperties": {
    "source": {
      "type": "AzureSqlSource",
      "sqlReaderQuery": "SELECT * FROM dbo.Configuration WHERE IsActive = 1"
    },
    "dataset": {
      "referenceName": "DS_AzureSql_Config",
      "type": "DatasetReference"
    },
    "firstRowOnly": false
  }
}
```

**Output Access:**
- `firstRowOnly: true` → `@activity('LookupConfig').output.firstRow.ColumnName`
- `firstRowOnly: false` → `@activity('LookupConfig').output.value` (array)

**Limits:**
- Max 5,000 rows
- Max 4 MB response size

---

## Execute Pipeline Activity

Calls another pipeline, enabling modular design.

```json
{
  "name": "ExecuteChildPipeline",
  "type": "ExecutePipeline",
  "dependsOn": [],
  "typeProperties": {
    "pipeline": {
      "referenceName": "PL_Child_Process",
      "type": "PipelineReference"
    },
    "waitOnCompletion": true,
    "parameters": {
      "TableName": {
        "value": "@item().tableName",
        "type": "Expression"
      },
      "ProcessDate": {
        "value": "@pipeline().parameters.ProcessDate",
        "type": "Expression"
      }
    }
  }
}
```

---

## Web Activity

Calls REST endpoints for integration.

```json
{
  "name": "CallRestApi",
  "type": "WebActivity",
  "dependsOn": [],
  "policy": {
    "timeout": "0.00:10:00",
    "retry": 3
  },
  "typeProperties": {
    "url": "@concat(pipeline().parameters.ApiBaseUrl, '/process')",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "@concat('Bearer ', activity('GetToken').output.access_token)"
    },
    "body": {
      "data": "@pipeline().parameters.InputData",
      "timestamp": "@utcnow()"
    },
    "authentication": {
      "type": "MSI",
      "resource": "https://management.azure.com/"
    }
  }
}
```

---

## Databricks Job Activity

Orchestrates Databricks Workflow Jobs.

```json
{
  "name": "RunDatabricksJob",
  "type": "DatabricksJob",
  "dependsOn": [],
  "policy": {
    "timeout": "0.12:00:00",
    "retry": 2
  },
  "typeProperties": {
    "jobId": "123456789",
    "jobParameters": {
      "input_path": "@pipeline().parameters.InputPath",
      "output_path": "@pipeline().parameters.OutputPath",
      "process_date": "@pipeline().parameters.ProcessDate"
    }
  },
  "linkedServiceName": {
    "referenceName": "LS_Databricks",
    "type": "LinkedServiceReference"
  }
}
```

---

## Set Variable Activity

Sets pipeline variable values.

```json
{
  "name": "SetCounter",
  "type": "SetVariable",
  "dependsOn": [],
  "typeProperties": {
    "variableName": "Counter",
    "value": {
      "value": "@add(variables('Counter'), 1)",
      "type": "Expression"
    }
  }
}
```

**Note:** Cannot use SetVariable in parallel ForEach. Use AppendVariable or sequential mode.

---

## Append Variable Activity

Appends value to an array variable.

```json
{
  "name": "AppendResult",
  "type": "AppendVariable",
  "dependsOn": [],
  "typeProperties": {
    "variableName": "Results",
    "value": {
      "value": "@activity('ProcessItem').output",
      "type": "Expression"
    }
  }
}
```

---

## Wait Activity

Pauses execution for specified duration.

```json
{
  "name": "WaitForProcessing",
  "type": "Wait",
  "dependsOn": [],
  "typeProperties": {
    "waitTimeInSeconds": 60
  }
}
```

---

## Fail Activity

Explicitly fails the pipeline with custom error.

```json
{
  "name": "FailPipeline",
  "type": "Fail",
  "dependsOn": [
    { "activity": "Validation", "dependencyConditions": ["Failed"] }
  ],
  "typeProperties": {
    "message": "Validation failed: @{activity('Validation').output.error}",
    "errorCode": "VALIDATION_FAILED"
  }
}
```

---

## Get Metadata Activity

Retrieves metadata about datasets or files.

```json
{
  "name": "GetFileList",
  "type": "GetMetadata",
  "dependsOn": [],
  "typeProperties": {
    "dataset": {
      "referenceName": "DS_Blob_Folder",
      "type": "DatasetReference"
    },
    "fieldList": ["childItems", "itemName", "itemType", "lastModified", "size"],
    "storeSettings": {
      "type": "AzureBlobStorageReadSettings",
      "recursive": false
    }
  }
}
```

**Available Fields:**
- `childItems`, `itemName`, `itemType`
- `lastModified`, `created`, `size`
- `exists`, `columnCount`, `structure`

---

## Azure ML Execute Pipeline Activity

Executes an Azure Machine Learning published pipeline. **SDK v1 support ends June 2026.** Migrate to batch endpoints via WebActivity.

```json
{
  "name": "RunMLPipeline",
  "type": "AzureMLExecutePipeline",
  "dependsOn": [],
  "policy": {
    "timeout": "1.00:00:00",
    "retry": 1,
    "retryIntervalInSeconds": 60
  },
  "typeProperties": {
    "mlPipelineId": "<published-pipeline-id>",
    "experimentName": "my-experiment",
    "mlPipelineParameters": {
      "param1": "@pipeline().parameters.Value1"
    },
    "continueOnStepFailure": false
  },
  "linkedServiceName": {
    "referenceName": "LS_AzureML",
    "type": "LinkedServiceReference"
  }
}
```

**Output:**
- `@activity('RunMLPipeline').output.mlPipelineRunId`
- `@activity('RunMLPipeline').output.status`

---

## Execute Data Flow Activity

Runs a Mapping Data Flow for Spark-based transformations.

```json
{
  "name": "RunDataFlow",
  "type": "ExecuteDataFlow",
  "dependsOn": [],
  "policy": {
    "timeout": "1.00:00:00",
    "retry": 0
  },
  "typeProperties": {
    "dataFlow": {
      "referenceName": "DF_Transform",
      "type": "DataFlowReference",
      "parameters": {
        "Param1": "'value1'"
      }
    },
    "compute": {
      "coreCount": 8,
      "computeType": "General"
    },
    "staging": {
      "linkedService": {
        "referenceName": "LS_AzureBlobStorage",
        "type": "LinkedServiceReference"
      },
      "folderPath": "staging/dataflows"
    },
    "traceLevel": "Fine"
  }
}
```

**Compute Types:** `General`, `MemoryOptimized`, `ComputeOptimized`
**Core Counts:** 8, 16, 32, 48, 80, 144, 272
