# View Statistics Functions

Grid view columns can display aggregate statistics. Supported functions depend on field type and `isMultipleCellValue`.

## By Cell Value Type

### Number Fields
```
"sum" | "average" | "min" | "max" | "count" | "empty" | "filled" | "unique" | "percentEmpty" | "percentFilled" | "percentUnique"
```
**Applies to**: number, rating, autoNumber, formula (number result)

### String Fields
```
"count" | "empty" | "filled" | "unique" | "percentEmpty" | "percentFilled" | "percentUnique"
```
**Applies to**: singleLineText, longText, singleSelect, multipleSelect, formula (string result)

### DateTime Fields
```
"count" | "empty" | "filled" | "unique" | "percentEmpty" | "percentFilled" | "percentUnique" | "earliestDate" | "latestDate" | "dateRangeOfDays" | "dateRangeOfMonths"
```
**Applies to**: date, createdTime, lastModifiedTime, formula (datetime result)

### Boolean Fields
```
"count" | "checked" | "unChecked" | "percentChecked" | "percentUnChecked"
```
**Applies to**: checkbox, formula (boolean result)

## Special Field Types

### Link Fields
```
"count" | "empty" | "filled" | "percentEmpty" | "percentFilled"
```
Note: No "unique" functions (links always treated as multiple values)

### User Fields (Single User)
```
"count" | "empty" | "filled" | "unique" | "percentEmpty" | "percentFilled" | "percentUnique"
```
**Applies to**: user, createdBy, lastModifiedBy (when `isMultipleCellValue: false`)

### User Fields (Multiple Users)
```
"count" | "empty" | "filled" | "percentEmpty" | "percentFilled"
```
**Applies to**: user (when `isMultipleCellValue: true`)
Note: "unique" functions removed for multiple values

### Attachment Fields
```
"count" | "empty" | "filled" | "percentEmpty" | "percentFilled" | "totalAttachmentSize"
```
Note: Has special "totalAttachmentSize" function; "unique" functions removed

## Dynamic Fields (Formula, Rollup, Lookup)

**Functions depend on their cellValueType**:

- **Formula/Rollup with Number result** → Use Number functions (sum, average, min, max, etc.)
- **Formula/Rollup with String result** → Use String functions (count, unique, etc.)
- **Formula/Rollup with DateTime result** → Use DateTime functions (earliestDate, latestDate, etc.)
- **Formula/Rollup with Boolean result** → Use Boolean functions (checked, unChecked, etc.)
- **Lookup** → Depends on looked-up field's type and `isMultipleCellValue`

Example:
```typescript
{
  columnMeta: {
    // Formula: {Price} * {Quantity} (Number result)
    "fldTotal": { order: 0, statisticFunc: "sum" },
    
    // Rollup: CONCATENATE(values) from links (String result, multiple)
    "fldNames": { order: 1, statisticFunc: "count" }  // No "unique" for multiple
  }
}
```

## Key Rules

1. **Multiple values**: Fields with `isMultipleCellValue: true` typically lose "unique" and "percentUnique" functions
2. **Number-only**: "sum", "average", "min", "max" only for number fields
3. **DateTime-only**: "earliestDate", "latestDate", "dateRangeOfDays/Months" only for datetime fields
4. **Boolean-only**: "checked", "unChecked", "percentChecked/UnChecked" only for checkbox fields
5. **Attachment-only**: "totalAttachmentSize" only for attachment fields
6. **Formula/Rollup/Lookup**: Check their `cellValueType` and `isMultipleCellValue` to determine available functions

## Example

```typescript
{
  columnMeta: {
    "fldAmount": { order: 0, statisticFunc: "sum" },
    "fldQuantity": { order: 1, statisticFunc: "average" },
    "fldStatus": { order: 2, statisticFunc: "unique" },
    "fldDueDate": { order: 3, statisticFunc: "earliestDate" }
  }
}
```
