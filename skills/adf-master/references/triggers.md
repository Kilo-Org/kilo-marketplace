# ADF Triggers - Complete JSON Reference

## Schedule Trigger

Runs pipelines on a recurring schedule.

```json
{
  "name": "TR_Daily_0600",
  "type": "Microsoft.DataFactory/factories/triggers",
  "properties": {
    "type": "ScheduleTrigger",
    "typeProperties": {
      "recurrence": {
        "frequency": "Day",
        "interval": 1,
        "startTime": "2025-01-01T06:00:00Z",
        "endTime": "2030-12-31T23:59:59Z",
        "timeZone": "UTC"
      }
    },
    "pipelines": [
      {
        "pipelineReference": {
          "referenceName": "PL_DailyLoad",
          "type": "PipelineReference"
        },
        "parameters": {
          "ProcessDate": "@trigger().scheduledTime"
        }
      }
    ]
  }
}
```

### Frequency Options

| Frequency | Interval | Result |
|-----------|----------|--------|
| Minute | 15 | Every 15 minutes |
| Hour | 1 | Every hour |
| Day | 1 | Daily |
| Week | 1 | Weekly |
| Month | 1 | Monthly |

### Weekly Schedule
```json
{
  "recurrence": {
    "frequency": "Week",
    "interval": 1,
    "startTime": "2025-01-01T08:00:00Z",
    "timeZone": "Eastern Standard Time",
    "schedule": {
      "weekDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "hours": [8],
      "minutes": [0]
    }
  }
}
```

### Monthly Schedule
```json
{
  "recurrence": {
    "frequency": "Month",
    "interval": 1,
    "startTime": "2025-01-01T00:00:00Z",
    "schedule": {
      "monthDays": [1, 15],
      "hours": [6],
      "minutes": [0]
    }
  }
}
```

### Multiple Runs Per Day
```json
{
  "recurrence": {
    "frequency": "Day",
    "interval": 1,
    "schedule": {
      "hours": [6, 12, 18],
      "minutes": [0, 30]
    }
  }
}
```

---

## Tumbling Window Trigger

Processes data in fixed-time windows with built-in retry and dependency support.

### Basic Tumbling Window
```json
{
  "name": "TR_TumblingWindow_Hourly",
  "properties": {
    "type": "TumblingWindowTrigger",
    "typeProperties": {
      "frequency": "Hour",
      "interval": 1,
      "startTime": "2025-01-01T00:00:00Z",
      "endTime": "2030-12-31T23:59:59Z",
      "delay": "00:05:00",
      "maxConcurrency": 10,
      "retryPolicy": {
        "count": 3,
        "intervalInSeconds": 30
      }
    },
    "pipeline": {
      "pipelineReference": {
        "referenceName": "PL_HourlyProcess",
        "type": "PipelineReference"
      },
      "parameters": {
        "WindowStart": "@trigger().outputs.windowStartTime",
        "WindowEnd": "@trigger().outputs.windowEndTime"
      }
    }
  }
}
```

**Key Properties:**
- `delay`: Wait time after window ends before starting (allows late data)
- `maxConcurrency`: Number of parallel windows (1-50)
- Window times available via `@trigger().outputs.windowStartTime/windowEndTime`

### Tumbling Window with Dependencies
```json
{
  "name": "TR_TumblingWindow_Dependent",
  "properties": {
    "type": "TumblingWindowTrigger",
    "typeProperties": {
      "frequency": "Hour",
      "interval": 1,
      "startTime": "2025-01-01T00:00:00Z",
      "maxConcurrency": 5,
      "retryPolicy": {
        "count": 3,
        "intervalInSeconds": 60
      },
      "dependsOn": [
        {
          "type": "TumblingWindowTriggerDependencyReference",
          "referenceTrigger": {
            "referenceName": "TR_TumblingWindow_Upstream",
            "type": "TriggerReference"
          },
          "offset": "00:00:00",
          "size": "01:00:00"
        }
      ]
    },
    "pipeline": {
      "pipelineReference": {
        "referenceName": "PL_DependentProcess",
        "type": "PipelineReference"
      }
    }
  }
}
```

### Self-Dependency (Sequential Processing)
```json
{
  "dependsOn": [
    {
      "type": "SelfDependencyTumblingWindowTriggerReference",
      "offset": "-01:00:00",
      "size": "01:00:00"
    }
  ]
}
```

---

## Event Triggers

### Blob Storage Event Trigger
```json
{
  "name": "TR_BlobCreated",
  "properties": {
    "type": "BlobEventsTrigger",
    "typeProperties": {
      "blobPathBeginsWith": "/container/raw/",
      "blobPathEndsWith": ".csv",
      "ignoreEmptyBlobs": true,
      "events": ["Microsoft.Storage.BlobCreated"],
      "scope": "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage>"
    },
    "pipelines": [
      {
        "pipelineReference": {
          "referenceName": "PL_ProcessNewFile",
          "type": "PipelineReference"
        },
        "parameters": {
          "FileName": "@trigger().outputs.body.fileName",
          "FolderPath": "@trigger().outputs.body.folderPath"
        }
      }
    ]
  }
}
```

**Available Trigger Outputs:**
```text
@trigger().outputs.body.fileName
@trigger().outputs.body.folderPath
@trigger().outputs.body.uri
```

### Custom Event Trigger (Event Grid)
```json
{
  "name": "TR_CustomEvent",
  "properties": {
    "type": "CustomEventsTrigger",
    "typeProperties": {
      "scope": "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.EventGrid/topics/<topic>",
      "events": ["DataReady", "ProcessComplete"],
      "subjectBeginsWith": "/orders/",
      "subjectEndsWith": ""
    },
    "pipelines": [
      {
        "pipelineReference": {
          "referenceName": "PL_ProcessEvent",
          "type": "PipelineReference"
        },
        "parameters": {
          "EventData": "@trigger().outputs.body.data",
          "Subject": "@trigger().outputs.body.subject"
        }
      }
    ]
  }
}
```

---

## Storage Event Trigger (ADLS Gen2)

```json
{
  "name": "TR_ADLSEvent",
  "properties": {
    "type": "BlobEventsTrigger",
    "typeProperties": {
      "blobPathBeginsWith": "/filesystem/landing/",
      "blobPathEndsWith": ".parquet",
      "ignoreEmptyBlobs": true,
      "events": ["Microsoft.Storage.BlobCreated"],
      "scope": "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<adls-account>"
    },
    "pipelines": [
      {
        "pipelineReference": {
          "referenceName": "PL_ProcessLanding",
          "type": "PipelineReference"
        },
        "parameters": {
          "FilePath": "@concat(trigger().outputs.body.folderPath, '/', trigger().outputs.body.fileName)"
        }
      }
    ]
  }
}
```

---

## Rerun Triggers

### Tumbling Window Rerun Trigger
```json
{
  "name": "TR_Rerun_January",
  "properties": {
    "type": "RerunTumblingWindowTrigger",
    "typeProperties": {
      "parentTrigger": {
        "referenceName": "TR_TumblingWindow_Daily",
        "type": "TriggerReference"
      },
      "requestedStartTime": "2025-01-01T00:00:00Z",
      "requestedEndTime": "2025-01-31T23:59:59Z",
      "rerunConcurrency": 5
    }
  }
}
```

---

## Multiple Pipelines per Trigger

```json
{
  "name": "TR_MultiplePipelines",
  "properties": {
    "type": "ScheduleTrigger",
    "typeProperties": {
      "recurrence": {
        "frequency": "Day",
        "interval": 1,
        "startTime": "2025-01-01T06:00:00Z"
      }
    },
    "pipelines": [
      {
        "pipelineReference": {
          "referenceName": "PL_ExtractData",
          "type": "PipelineReference"
        },
        "parameters": { "Source": "Sales" }
      },
      {
        "pipelineReference": {
          "referenceName": "PL_ExtractData",
          "type": "PipelineReference"
        },
        "parameters": { "Source": "Inventory" }
      },
      {
        "pipelineReference": {
          "referenceName": "PL_ExtractData",
          "type": "PipelineReference"
        },
        "parameters": { "Source": "Customers" }
      }
    ]
  }
}
```

---

## Common Trigger Expressions

### Access Trigger Properties in Pipeline
```text
@trigger().name                          → Trigger name
@trigger().scheduledTime                 → Scheduled time (schedule trigger)
@trigger().startTime                     → Actual start time
@trigger().outputs.windowStartTime       → Window start (tumbling window)
@trigger().outputs.windowEndTime         → Window end (tumbling window)
@trigger().outputs.body.fileName         → File name (blob trigger)
@trigger().outputs.body.folderPath       → Folder path (blob trigger)
```

### Dynamic Date from Tumbling Window
```json
{
  "ProcessDate": {
    "value": "@formatDateTime(trigger().outputs.windowStartTime, 'yyyy-MM-dd')",
    "type": "Expression"
  }
}
```

---

## Time Zones

Supported time zone values:
- `UTC`
- `Eastern Standard Time`
- `Pacific Standard Time`
- `Central Standard Time`
- `Mountain Standard Time`
- `GMT Standard Time`
- `W. Europe Standard Time`
- `Tokyo Standard Time`
- `India Standard Time`
- `China Standard Time`
- `AUS Eastern Standard Time`

**Example with Time Zone:**
```json
{
  "recurrence": {
    "frequency": "Day",
    "interval": 1,
    "startTime": "2025-01-01T08:00:00",
    "timeZone": "Eastern Standard Time"
  }
}
```

---

## Trigger States

| State | Description |
|-------|-------------|
| Started | Trigger is active and firing |
| Stopped | Trigger is disabled |

**Start/Stop via REST API:**
```text
POST /triggers/{triggerName}/start
POST /triggers/{triggerName}/stop
```

---

## Limitations

- Schedule trigger: Max 5 executions per minute
- Tumbling window: maxConcurrency 1-50
- Event trigger: Subject max 1024 characters
- Blob trigger: Doesn't fire for folder creation
- Rerun trigger: Cannot exceed original trigger window range
