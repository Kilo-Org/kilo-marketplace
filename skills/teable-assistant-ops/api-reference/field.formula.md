# Formula Field

Formula fields compute values dynamically based on expressions.

## Basic Configuration

```typescript
{
  name: "Full Name",
  type: "formula",
  options: {
    expression: "CONCATENATE({First Name}, ' ', {Last Name})"
  }
}
```

## Available Functions

All 80 available functions:

```
  SUM(number1, [number2, ...])                             → number
  AVERAGE(number1, [number2, ...])                         → number
  MAX(number1, [number2, ...])                             → number
  MIN(number1, [number2, ...])                             → number
  ROUND(value, [precision])                                → number
  ROUNDUP(value, [precision])                              → number
  ROUNDDOWN(value, [precision])                            → number
  CEILING(value, [significance])                           → number
  FLOOR(value, [significance])                             → number
  EVEN(value)                                              → number
  ODD(value)                                               → number
  INT(value)                                               → number
  ABS(value)                                               → number
  SQRT(value)                                              → number
  POWER(value)                                             → number
  EXP(value)                                               → number
  LOG(number, [base=10])                                   → number
  MOD(value, divisor)                                      → number
  VALUE(text)                                              → number
  CONCATENATE(text1, [text2, ...])                         → string
  FIND(stringToFind, whereToSearch, [startFromPosition])   → number
  SEARCH(stringToFind, whereToSearch, [startFromPosition])  → number
  MID(text, whereToStart, count)                           → string
  LEFT(text, count)                                        → string
  RIGHT(text, count)                                       → string
  REPLACE(text, whereToStart, count, replacement)          → string
  REGEXP_REPLACE(text, regular_expression, replacement)    → string
  SUBSTITUTE(text, oldText, newText, [index])              → string
  TEXTBEFORE(text, delimiter)                              → string
  TEXTSPLIT(text, delimiter)                               → array
  LOWER(text)                                              → string
  UPPER(text)                                              → string
  REPT(text, number)                                       → string
  TRIM(text)                                               → string
  LEN(text)                                                → number
  T(value)                                                 → string
  ENCODE_URL_COMPONENT(value)                              → string
  IF(logical, value1, value2)                              → string
  SWITCH(expression, [pattern, result]..., [default])      → string
  AND(logical1, [logical2, ...])                           → boolean
  OR(logical1, [logical2, ...])                            → boolean
  XOR(logical1, [logical2, ...])                           → boolean
  NOT(boolean)                                             → boolean
  BLANK()                                                  → string
  ERROR(message)                                           → string
  IS_ERROR(expr)                                           → boolean
  TODAY()                                                  → dateTime
  NOW()                                                    → dateTime
  YEAR(date)                                               → number
  MONTH(date)                                              → number
  WEEKNUM(date)                                            → number
  WEEKDAY(date, [startDayOfWeek])                          → number
  DAY(date, [startDayOfWeek])                              → number
  HOUR(date, [startDayOfWeek])                             → number
  MINUTE(date, [startDayOfWeek])                           → number
  SECOND(date, [startDayOfWeek])                           → number
  FROMNOW(date, unit)                                      → number
  TONOW(date, unit)                                        → dateTime
  DATETIME_DIFF(endDate, startDate, [unit])                → number
  WORKDAY(date, count, [holidayStr])                       → dateTime
  WORKDAY_DIFF(startDate, endDate, [holidayStr])           → number
  IS_SAME(date1, date2, [unit])                            → boolean
  IS_AFTER(date1, date2, [unit])                           → boolean
  IS_BEFORE(date1, date2, [unit])                          → boolean
  DATE_ADD(date, count, units)                             → dateTime
  DATESTR(date)                                            → string
  TIMESTR(date)                                            → string
  DATETIME_FORMAT(date, [specified_output_format])         → string
  DATETIME_PARSE(date, [input_format])                     → dateTime
  CREATED_TIME()                                           → dateTime
  LAST_MODIFIED_TIME([field])                              → dateTime
  COUNTALL(value1, [value2, ...])                          → number
  COUNTA(value1, [value2, ...])                            → number
  COUNT(value1, [value2, ...])                             → number
  ARRAY_JOIN(array, [separator])                           → string
  ARRAY_UNIQUE(array)                                      → array
  ARRAY_FLATTEN(array)                                     → array
  ARRAY_COMPACT(array)                                     → array
  RECORD_ID()                                              → string
  AUTO_NUMBER()                                            → number
```

## Examples

```typescript
// Basic arithmetic
{ expression: "{Quantity} * {Unit Price}" }

// With formatting
{
  expression: "{Quantity} * {Price}",
  formatting: { type: "currency", symbol: "$", precision: 2 }
}

// Conditional logic
{ expression: "IF({Status} = 'Done', 'Complete', 'Incomplete')" }

// Date operations (note singular 'month', not 'months')
{ expression: "DATE_ADD({Start Date}, 3, 'month')" }
```

## Key Rules

- **Field references**: `{Field Name}` with exact name and braces
- **Functions**: Case-sensitive uppercase (`SUM` not `sum`)
- **Date/time units**: Singular - `'day'`, `'month'`, `'year'`, `'hour'`, `'minute'`, `'second'`, `'week'`
- **Result type**: Determined by expression, affects formatting (see `field.formatting` topic)
- Formula fields are read-only (computed automatically)
