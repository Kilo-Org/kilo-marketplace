# View Column Configuration

columnMeta is a Record mapping fieldId to column properties. Different view types have different properties.

## Structure

```typescript
{
  columnMeta: {
    "fldXXXXXXXXX": { order: 0, ... },
    "fldYYYYYYYYY": { order: 1, ... }
  }
}
```

## Column Properties by View Type

### Grid View
```typescript
{
  "fldTitle": {
    order: 0,            // required: display order (float)
    width: 300,          // optional: column width in px
    hidden: false,       // optional: hide column
    statisticFunc: null  // optional: aggregate function (see View Statistics doc)
  }
}
```

### Kanban View
```typescript
{
  "fldTitle": {
    order: 0,       // required
    visible: true   // optional: show in card
  }
}
```

### Gallery View
```typescript
{
  "fldTitle": {
    order: 0,       // required
    visible: true   // optional: show in card
  }
}
```

### Calendar View
```typescript
{
  "fldTitle": {
    order: 0,       // required
    visible: true   // optional: show in event
  }
}
```

### Form View
```typescript
{
  "fldTitle": {
    order: 0,        // required: field order in form
    visible: true,   // optional: show in form
    required: false  // optional: required field
  }
}
```

### Plugin View
```typescript
{
  "fldTitle": {
    order: 0,      // required
    hidden: false  // optional: hide column
  }
}
```

## Examples

### Grid with Custom Widths
```typescript
{
  columnMeta: {
    "fldTitle": { order: 0, width: 300 },
    "fldStatus": { order: 1, width: 120 },
    "fldPriority": { order: 2, width: 100, statisticFunc: "average" }
  }
}
```

### Form with Required Fields
```typescript
{
  columnMeta: {
    "fldName": { order: 0, visible: true, required: true },
    "fldEmail": { order: 1, visible: true, required: true },
    "fldNotes": { order: 2, visible: true, required: false },
    "fldInternalId": { order: 3, visible: false }
  }
}
```

### Kanban Card Fields
```typescript
{
  columnMeta: {
    "fldTitle": { order: 0, visible: true },
    "fldAssignee": { order: 1, visible: true },
    "fldPriority": { order: 2, visible: true },
    "fldDescription": { order: 3, visible: false }
  }
}
```

## Notes

- `order` determines display sequence (smaller = earlier)
- Grid uses `hidden`, others use `visible` for visibility control
- Form `required` only validates user input, doesn't affect table schema
