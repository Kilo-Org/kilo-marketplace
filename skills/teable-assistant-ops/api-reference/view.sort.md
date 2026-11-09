# View Sort Configuration

Controls record display order.

## Structure

```typescript
{
  sort: {
    sortObjs: [
      { fieldId: "fldXXX", order: "asc" | "desc" }
    ],
    manualSort: false  // optional: manual reordering mode
  }
}
```

## Order Values

- `asc`: Ascending (A-Z, 0-9, oldest→newest, false→true)
- `desc`: Descending (Z-A, 9-0, newest→oldest, true→false)

## Sorting by Field Type

### String (singleLineText, longText, select)
- Alphabetical (case-insensitive)
- Empty values last

### Number (number, rating, autoNumber)
- Numerical order
- Empty values last

### DateTime (date, createdTime, lastModifiedTime)
- Chronological order
- Empty values last

### Boolean (checkbox)
- `asc`: unchecked → checked
- `desc`: checked → unchecked

### User/Link
- By title/name alphabetically
- Empty values last

### Formula/Rollup/Lookup
- Sort behavior depends on their `cellValueType`
- Number result → numerical sort
- String result → alphabetical sort
- DateTime result → chronological sort
- Boolean result → false before true (asc)

## Examples

### Single Sort
```typescript
{ sort: { sortObjs: [{ fieldId: "fldCreatedTime", order: "desc" }] } }
```

### Multiple Sorts (priority order)
```typescript
{
  sort: {
    sortObjs: [
      { fieldId: "fldPriority", order: "desc" },  // Primary
      { fieldId: "fldDueDate", order: "asc" },    // Secondary
      { fieldId: "fldTitle", order: "asc" }       // Tertiary
    ]
  }
}
```

### Manual Sort Mode
```typescript
{
  sort: {
    sortObjs: [{ fieldId: "fldOrder", order: "asc" }],
    manualSort: true  // User can drag to reorder
  }
}
```

## Key Notes

- Sort order matters: first is primary, subsequent are tie-breakers
- All field types are sortable
- Empty/null values always appear last regardless of order
