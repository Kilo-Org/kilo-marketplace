# ADF Expression Functions - Complete Reference

## Expression Syntax

Expressions in ADF use `@` prefix and can appear in:
- Parameter values
- Activity typeProperties
- Dynamic content fields

```json
{
  "value": "@concat('prefix_', pipeline().parameters.Name)",
  "type": "Expression"
}
```

String interpolation: `@{expression}` within strings
```json
"sqlReaderQuery": "SELECT * FROM dbo.@{pipeline().parameters.TableName}"
```

---

## String Functions

### concat
Combines multiple strings.
```text
@concat('Hello', ' ', 'World')           → 'Hello World'
@concat(pipeline().parameters.Prefix, '_', item().name)
```

### substring
Extracts part of a string.
```text
@substring('Hello World', 0, 5)          → 'Hello'
@substring(variables('FileName'), 0, indexOf(variables('FileName'), '.'))
```

### replace
Replaces occurrences in a string.
```text
@replace('Hello World', 'World', 'ADF')  → 'Hello ADF'
@replace(item().path, '/', '_')
```

### split
Splits string into array.
```text
@split('a,b,c', ',')                     → ['a', 'b', 'c']
@split(activity('Lookup').output.firstRow.Values, ';')
```

### join
Joins array elements into string.
```text
@join(variables('Names'), ', ')          → 'Alice, Bob, Charlie'
```

### toLower / toUpper
```text
@toLower('Hello')                        → 'hello'
@toUpper('Hello')                        → 'HELLO'
```

### trim / trimStart / trimEnd
```text
@trim('  Hello  ')                       → 'Hello'
@trimStart('  Hello')                    → 'Hello'
@trimEnd('Hello  ')                      → 'Hello'
```

### indexOf / lastIndexOf
```text
@indexOf('Hello World', 'o')             → 4
@lastIndexOf('Hello World', 'o')         → 7
@indexOf('Hello', 'x')                   → -1 (not found)
```

### startsWith / endsWith
```text
@startsWith('Hello World', 'Hello')      → true
@endsWith('file.csv', '.csv')            → true
```

### length
```text
@length('Hello')                         → 5
@length(pipeline().parameters.Items)     → array length
```

### guid
Generates a unique identifier.
```text
@guid()                                  → 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
@guid('N')                               → 'a1b2c3d4e5f67890abcdef1234567890'
```

---

## Collection Functions

### first / last
```text
@first(variables('Items'))               → first element
@last(pipeline().parameters.List)        → last element
```

### take / skip
```text
@take(variables('Items'), 5)             → first 5 elements
@skip(variables('Items'), 10)            → elements after first 10
```

### contains
```text
@contains('Hello World', 'World')        → true (string)
@contains(variables('List'), 'item')     → true (array)
```

### empty
```text
@empty(variables('Items'))               → true if empty/null
@not(empty(activity('Lookup').output.value))
```

### union / intersection
```text
@union(variables('List1'), variables('List2'))
@intersection(variables('Set1'), variables('Set2'))
```

### length (array)
```text
@length(activity('Lookup').output.value) → number of rows
@length(pipeline().parameters.Tables)
```

### range
Creates an array of integers.
```text
@range(1, 10)                            → [1,2,3,4,5,6,7,8,9,10]
@range(0, length(variables('Items')))
```

---

## Logical Functions

### if
```text
@if(equals(variables('Status'), 'Active'), 'Yes', 'No')
@if(greater(activity('Count').output.firstRow.Total, 0), 'HasData', 'Empty')
```

### equals / not
```text
@equals(pipeline().parameters.Env, 'prod')
@not(equals(variables('Status'), 'Failed'))
```

### and / or
```bash
@and(greater(variables('Count'), 0), less(variables('Count'), 100))
@or(equals(item().status, 'New'), equals(item().status, 'Pending'))
```

### greater / greaterOrEquals / less / lessOrEquals
```bash
@greater(variables('Count'), 10)
@greaterOrEquals(activity('Lookup').output.firstRow.Total, 1000)
@less(dayOfWeek(utcnow()), 6)            → is weekday?
@lessOrEquals(length(variables('Items')), 50)
```

### coalesce
Returns first non-null value.
```text
@coalesce(pipeline().parameters.Override, 'default')
@coalesce(activity('Lookup').output.firstRow.Value, variables('Default'))
```

---

## Conversion Functions

### int / float / string / bool
```text
@int('42')                               → 42
@float('3.14')                           → 3.14
@string(42)                              → '42'
@bool('true')                            → true
@bool(1)                                 → true
```

### json
Parses JSON string.
```text
@json(activity('WebActivity').output.Response)
@json('{"name":"test"}').name            → 'test'
```

### xml
Parses XML string.
```text
@xml('<root><item>value</item></root>')
```

### base64 / base64ToString
```text
@base64('Hello')                         → 'SGVsbG8='
@base64ToString('SGVsbG8=')              → 'Hello'
```

### decodeBase64 / encodeUriComponent / decodeUriComponent
```text
@encodeUriComponent('hello world')       → 'hello%20world'
@decodeUriComponent('hello%20world')     → 'hello world'
```

### array
Creates array from value.
```text
@array('single')                         → ['single']
@array(activity('Lookup').output.firstRow)
```

### createArray
Creates array from multiple values.
```text
@createArray('a', 'b', 'c')              → ['a', 'b', 'c']
@createArray(item().table1, item().table2)
```

---

## Math Functions

### add / sub / mul / div / mod
```text
@add(10, 5)                              → 15
@sub(10, 5)                              → 5
@mul(10, 5)                              → 50
@div(10, 5)                              → 2
@mod(10, 3)                              → 1
```

### min / max
```text
@min(10, 5, 8)                           → 5
@max(activity('Lookup').output.value)    → max in array
```

### rand
Random number (32-bit signed integer).
```text
@rand(-100, 100)                         → random between -100 and 100
```

---

## Date/Time Functions

### utcnow
```text
@utcnow()                                → '2026-03-07T14:30:45.1234567Z'
@utcnow('yyyy-MM-dd')                    → '2026-03-07'
@utcnow('yyyyMMddHHmmss')                → '20260307143045'
```

### adddays / addhours / addminutes / addseconds
```text
@adddays(utcnow(), -1)                   → yesterday
@adddays(utcnow(), 7)                    → next week
@addhours(utcnow(), -6)                  → 6 hours ago
@addminutes(utcnow(), 30)                → 30 min from now
@addseconds(utcnow(), -3600)             → 1 hour ago
```

### formatDateTime
```text
@formatDateTime(utcnow(), 'yyyy-MM-dd')
@formatDateTime(utcnow(), 'yyyy/MM/dd')
@formatDateTime(utcnow(), 'yyyyMMdd')
@formatDateTime(utcnow(), 'yyyy-MM-ddTHH:mm:ss')
@formatDateTime(utcnow(), 'MMMM dd, yyyy')
@formatDateTime(utcnow(), 'dddd')        → 'Wednesday'
```

**Format Specifiers:**
| Specifier | Output | Example |
|-----------|--------|---------|
| yyyy | 4-digit year | 2026 |
| yy | 2-digit year | 26 |
| MM | 2-digit month | 03 |
| M | Month (no leading zero) | 3 |
| MMMM | Full month name | March |
| dd | 2-digit day | 07 |
| d | Day (no leading zero) | 7 |
| dddd | Full day name | Saturday |
| HH | 24-hour (00-23) | 14 |
| hh | 12-hour (01-12) | 02 |
| mm | Minutes | 30 |
| ss | Seconds | 45 |
| tt | AM/PM | PM |
| fff | Milliseconds | 123 |

### startOfDay / startOfMonth / startOfHour
```text
@startOfDay(utcnow())                    → midnight today
@startOfMonth(utcnow())                  → first of month
@startOfHour(utcnow())                   → start of current hour
```

### dayOfMonth / dayOfWeek / dayOfYear
```text
@dayOfMonth(utcnow())                    → 7
@dayOfWeek(utcnow())                     → 6 (0=Sunday)
@dayOfYear(utcnow())                     → 66
```

### month / year
```text
@month(utcnow())                         → 3
@year(utcnow())                          → 2026
```

### ticks
Converts to ticks (100-nanosecond intervals since 1/1/0001).
```text
@ticks(utcnow())                         → 638723523451234567
```

### convertFromUtc / convertToUtc
```text
@convertFromUtc(utcnow(), 'Pacific Standard Time')
@convertToUtc('2026-03-07T10:00:00', 'Eastern Standard Time')
```

---

## Pipeline & Activity References

### pipeline()
```text
@pipeline().Pipeline                      → pipeline name
@pipeline().DataFactory                   → data factory name
@pipeline().RunId                         → current run ID
@pipeline().TriggerName                   → trigger name
@pipeline().TriggerTime                   → trigger time
@pipeline().TriggerType                   → 'Manual', 'Schedule', 'Tumbling'
@pipeline().TriggeredByPipelineName       → parent pipeline (if nested)
@pipeline().TriggeredByPipelineRunId      → parent run ID
@pipeline().GroupId                       → execution group ID
```

### pipeline().parameters / pipeline().globalParameters
```text
@pipeline().parameters.TableName
@pipeline().parameters.StartDate
@pipeline().globalParameters.Environment
```

### activity()
```text
@activity('ActivityName').output
@activity('ActivityName').output.firstRow.ColumnName
@activity('ActivityName').output.value                  → array from Lookup
@activity('ActivityName').output.rowsCopied
@activity('ActivityName').output.rowsRead
@activity('ActivityName').output.throughput
@activity('ActivityName').output.copyDuration
@activity('ActivityName').output.errors
@activity('ActivityName').status                        → 'Succeeded', 'Failed'
@activity('ActivityName').error.message
@activity('ActivityName').error.errorCode
```

### variables()
```text
@variables('Counter')
@variables('ResultArray')
```

### item()
Inside ForEach loop:
```text
@item()                                   → current item
@item().tableName
@item()['property-with-dash']
```

### trigger()
```text
@trigger().name
@trigger().scheduledTime
@trigger().startTime
@trigger().outputs.windowStartTime        → tumbling window
@trigger().outputs.windowEndTime          → tumbling window
@trigger().outputs.body                   → event trigger payload
@trigger().outputs.body.fileName          → blob trigger
@trigger().outputs.body.folderPath
```

### dataset()
Inside dataset definition:
```text
@dataset().TableName
@dataset().FolderPath
```

### linkedService()
Inside linked service:
```text
@linkedService().Environment
```

---

## Common Expression Patterns

### Yesterday's Date
```text
@formatDateTime(adddays(utcnow(), -1), 'yyyy-MM-dd')
```

### First Day of Month
```text
@formatDateTime(startOfMonth(utcnow()), 'yyyy-MM-dd')
```

### Last Day of Previous Month
```text
@formatDateTime(adddays(startOfMonth(utcnow()), -1), 'yyyy-MM-dd')
```

### Date Partition Path
```text
@concat(
  formatDateTime(utcnow(), 'yyyy'), '/',
  formatDateTime(utcnow(), 'MM'), '/',
  formatDateTime(utcnow(), 'dd')
)
```

### Check if Weekday
```bash
@and(greater(dayOfWeek(utcnow()), 0), less(dayOfWeek(utcnow()), 6))
```

### Safe Property Access (with Default)
```text
@coalesce(activity('Lookup').output.firstRow.Value, 'default')
```

### Conditional SQL Query
```sql
@if(equals(pipeline().parameters.FullLoad, true),
  'SELECT * FROM dbo.Table',
  concat('SELECT * FROM dbo.Table WHERE Date >= ''', pipeline().parameters.LastDate, '''')
)
```

### Dynamic Table Name
```text
@concat(pipeline().parameters.Schema, '.', pipeline().parameters.Table)
```

### Parse JSON Response
```text
@json(activity('WebActivity').output.Response).data.items
```

### File Name from Path
```text
@substring(
  variables('FilePath'),
  add(lastIndexOf(variables('FilePath'), '/'), 1),
  sub(
    length(variables('FilePath')),
    add(lastIndexOf(variables('FilePath'), '/'), 1)
  )
)
```

### Array to Comma-Separated String
```text
@join(activity('Lookup').output.value, ',')
```

### Check Array Not Empty
```text
@not(empty(activity('GetMetadata').output.childItems))
```
