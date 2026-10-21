# View Filter Configuration

Filters show only records matching conditions. Supported operators depend on field type and `isMultipleCellValue`.

## Filter Structure

```typescript
{
  filterSet: [
    { fieldId: "fldXXX", operator: "is", value: "Active" }
  ],
  conjunction: "and"  // "and" | "or"
}
```

## Operators by Cell Value Type

### String Fields
```typescript
"is" | "isNot" | "contains" | "doesNotContain" | "isEmpty" | "isNotEmpty"
```
**Applies to**: singleLineText, longText

### Number Fields
```typescript
"is" | "isNot" | "isGreater" | "isGreaterEqual" | "isLess" | "isLessEqual" | "isEmpty" | "isNotEmpty"
```
**Applies to**: number, rating, autoNumber

### DateTime Fields
```typescript
"is" | "isNot" | "isWithIn" | "isBefore" | "isAfter" | "isOnOrBefore" | "isOnOrAfter" | "isEmpty" | "isNotEmpty"
```
**Applies to**: date, createdTime, lastModifiedTime

### Boolean Fields
```typescript
"is"
```
**Applies to**: checkbox

## Operators by Special Field Type

### SingleSelect (Single Value)
```typescript
"is" | "isNot" | "isAnyOf" | "isNoneOf" | "isEmpty" | "isNotEmpty"
```
**When `isMultipleCellValue: false`** (normal singleSelect)

### SingleSelect (Multiple Values)
```typescript
"hasAnyOf" | "hasAllOf" | "isExactly" | "isNotExactly" | "hasNoneOf" | "isEmpty" | "isNotEmpty"
```
**When `isMultipleCellValue: true`** (lookup of singleSelect)  
Note: Uses "hasAnyOf", "hasAllOf", "isExactly" instead of "is", "contains"

### MultipleSelect
```typescript
"hasAnyOf" | "hasAllOf" | "isExactly" | "isNotExactly" | "hasNoneOf" | "isEmpty" | "isNotEmpty"
```
Note: Always uses "has" operators for array matching

### User (Single)
```typescript
"is" | "isNot" | "isAnyOf" | "isNoneOf" | "isEmpty" | "isNotEmpty"
```
**When `isMultipleCellValue: false`**
Applies to: user, createdBy, lastModifiedBy
**Values**: a user id (`usrXXXX`), or the literal `"Me"` — the dynamic "current user" token. Case-sensitive: lowercase `"me"` is treated as a plain string and matches nothing.

### User (Multiple)
```typescript
"hasAnyOf" | "hasAllOf" | "isExactly" | "hasNoneOf" | "isNotExactly" | "isEmpty" | "isNotEmpty"
```
**When `isMultipleCellValue: true`**
Note: Uses "has" operators instead of "is" operators
**Values**: array-wrapped — `["usrXXXX"]` or `["Me"]`. The "has" operators
(`hasAnyOf`, `hasAllOf`, `isExactly`) reject scalar values.

### Link (Single)
```typescript
"is" | "isNot" | "isAnyOf" | "isNoneOf" | "contains" | "doesNotContain" | "isEmpty" | "isNotEmpty"
```
**When `isMultipleCellValue: false`** (OneOne, ManyOne relationships)

### Link (Multiple)
```typescript
"hasAnyOf" | "hasAllOf" | "isExactly" | "hasNoneOf" | "isNotExactly" | "contains" | "doesNotContain" | "isEmpty" | "isNotEmpty"
```
**When `isMultipleCellValue: true`** (OneMany, ManyMany relationships)  
Note: Includes "contains" for title text search

### Attachment
```typescript
"isEmpty" | "isNotEmpty"
```

## Dynamic Fields (Formula, Rollup, Lookup)

**Operators depend on their cellValueType**:

- **Formula/Rollup with Number result** → Use Number operators
- **Formula/Rollup with String result** → Use String operators
- **Formula/Rollup with DateTime result** → Use DateTime operators
- **Formula/Rollup with Boolean result** → Use Boolean operators
- **Lookup** → Depends on looked-up field's type and `isMultipleCellValue`

Example:
```typescript
// Formula field: {Price} * {Quantity} (returns number)
{ fieldId: "fldTotal", operator: "isGreater", value: 100 }

// Rollup field: CONCATENATE(values) (returns string)
{ fieldId: "fldNames", operator: "contains", value: "John" }
```

## Key Rules

1. **`isMultipleCellValue` impact**: 
   - `false`: Uses "is", "isNot", "isAnyOf", "isNoneOf"
   - `true`: Uses "hasAnyOf", "hasAllOf", "isExactly", "hasNoneOf", "isNotExactly"

2. **Operator meanings**:
   - "is/isNot": Single value exact match
   - "isAnyOf/isNoneOf": Single value in/not in array
   - "hasAnyOf/hasAllOf/hasNoneOf": Array contains any/all/none
   - "isExactly/isNotExactly": Array exact match/mismatch
   - "contains/doesNotContain": Text or title search

3. **Formula/Rollup/Lookup fields**: Check their `cellValueType` and `isMultipleCellValue` to determine available operators

## Examples

### Basic Filter
```typescript
{ filterSet: [{ fieldId: "fldStatus", operator: "is", value: "Active" }] }
```

### Multiple Conditions (AND)
```typescript
{
  filterSet: [
    { fieldId: "fldStatus", operator: "is", value: "Active" },
    { fieldId: "fldPriority", operator: "isGreater", value: 3 }
  ],
  conjunction: "and"
}
```

### Multiple Select Field
```typescript
{ filterSet: [{ fieldId: "fldTags", operator: "hasAnyOf", value: ["Bug", "Feature"] }] }
```

### DateTime Value Format

**ALL date/time operators require an object value** with a `mode` field. Never pass a plain date string.

```typescript
{ mode: string, numberOfDays?: number, exactDate?: string, exactDateEnd?: string, timeZone?: string }
```

**Valid modes by operator:**

- **Standard operators** (`isBefore`, `isAfter`, `isOnOrBefore`, `isOnOrAfter`):
  `today`, `tomorrow`, `yesterday`, `currentWeek`, `lastWeek`, `nextWeekPeriod`, `currentMonth`, `lastMonth`, `nextMonthPeriod`, `currentYear`, `lastYear`, `nextYearPeriod`, `oneWeekAgo`, `oneWeekFromNow`, `oneMonthAgo`, `oneMonthFromNow`, `daysAgo`, `daysFromNow`, `exactDate`, `exactDateTime`, `exactFormatDate`
- **`is` operator** (also supports `dateRange`):
  `today`, `tomorrow`, `yesterday`, `currentWeek`, `lastWeek`, `nextWeekPeriod`, `currentMonth`, `lastMonth`, `nextMonthPeriod`, `currentYear`, `lastYear`, `nextYearPeriod`, `oneWeekAgo`, `oneWeekFromNow`, `oneMonthAgo`, `oneMonthFromNow`, `daysAgo`, `daysFromNow`, `exactDate`, `exactDateTime`, `exactFormatDate`, `dateRange`
- **`isWithIn` operator** (all standard modes plus):
  `pastWeek`, `pastMonth`, `pastYear`, `nextWeek`, `nextMonth`, `nextYear`, `pastNumberOfDays`, `nextNumberOfDays`

**Mode-specific required fields:**
- `daysAgo`, `daysFromNow` → `numberOfDays` (integer)
- `pastNumberOfDays`, `nextNumberOfDays` → `numberOfDays` (integer, isWithIn only)
- `exactDate` → `exactDate` (ISO 8601 string; matches the selected day range)
- `exactDateTime` → `exactDate` (ISO 8601 string; exact timestamp match)
- `exactFormatDate` → `exactDate` (ISO 8601 string, e.g. "2024-01-01T00:00:00.000Z")
- `dateRange` → `exactDate` and `exactDateEnd` (ISO 8601 strings, `is` only)
- All other modes (e.g. `today`, `pastWeek`) → no extra fields needed

```typescript
// isBefore today
{ fieldId: "fldDate", operator: "isBefore", value: { mode: "today", timeZone: "UTC" } }

// isWithIn pastWeek
{ fieldId: "fldDate", operator: "isWithIn", value: { mode: "pastWeek", timeZone: "Asia/Shanghai" } }

// isAfter 7 days ago
{ fieldId: "fldDate", operator: "isAfter", value: { mode: "daysAgo", numberOfDays: 7, timeZone: "UTC" } }

// is dateRange
{ fieldId: "fldDate", operator: "is", value: { mode: "dateRange", exactDate: "2026-01-01T00:00:00.000Z", exactDateEnd: "2026-12-31T23:59:59.999Z", timeZone: "UTC" } }

// isWithIn pastNumberOfDays
{ fieldId: "fldDate", operator: "isWithIn", value: { mode: "pastNumberOfDays", numberOfDays: 30, timeZone: "UTC" } }
```

### Empty Check
```typescript
{ filterSet: [{ fieldId: "fldAssignee", operator: "isEmpty" }] }
```
