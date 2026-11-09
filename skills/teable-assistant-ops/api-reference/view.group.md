# View Group Configuration

Organizes records into collapsible sections.

## Structure

```typescript
{
  group: [
    { fieldId: "fldXXX", order: "asc" | "desc" }
  ]
}
```

**Max 3 levels**: System limits grouping to 3 nested levels

## Order Values

- `asc`: Ascending group order
- `desc`: Descending group order

## Grouping by Field Type

### Select (singleSelect, multipleSelect)
- Groups by choice values
- Empty: "Ungrouped" section

### User (user, createdBy, lastModifiedBy)
- Groups by user
- Empty: "Unassigned" section

### Date (date, createdTime, lastModifiedTime)
- Groups by date ranges (Today, This Week, This Month, etc.)
- Empty: "No Date" section

### Boolean (checkbox)
- Groups: Checked / Unchecked

### Link
- Groups by linked record titles
- Empty: "No Links" section

### Number/Rating
- Groups by value or ranges
- Empty: "Empty" section

### Text (singleLineText, longText)
- Groups alphabetically (creates many groups)
- Not recommended for longText

### Formula/Rollup/Lookup
- Group behavior depends on their `cellValueType`
- Number result → groups by value/range
- String result → groups alphabetically
- DateTime result → smart date range groups
- Boolean result → Checked/Unchecked groups
- Check `isMultipleCellValue` for proper grouping

## Examples

### Single Level
```typescript
{ group: [{ fieldId: "fldStatus", order: "asc" }] }
```
Result: Groups like "Todo", "In Progress", "Done"

### Multi-Level (max 3)
```typescript
{
  group: [
    { fieldId: "fldDepartment", order: "asc" },  // Level 1
    { fieldId: "fldStatus", order: "asc" },      // Level 2
    { fieldId: "fldPriority", order: "desc" }    // Level 3
  ]
}
```

### Combined with Filter and Sort
```typescript
{
  filter: { /* ... */ },
  group: [{ fieldId: "fldAssignee", order: "asc" }],
  sort: { sortObjs: [{ fieldId: "fldPriority", order: "desc" }] }
}
```

## Key Notes

- Group by fields with limited distinct values for best results
- First group is primary, second nests within first, third nests within second
- Empty values create separate "Empty/Ungrouped" sections
- Sorting applies within each group
- Date fields auto-create smart date range groups
