# Link Field

Link fields create relationships between tables.

## Basic Link Field
```typescript
{
  name: "Related Tasks",
  type: "link",
  options: {
    foreignTableId: "tblXXXXXXXXX",  // REQUIRED: The ID of the table to link to OR use foreignTableName: "Tasks"
    relationship: "manyMany"          // optional: oneOne | oneMany | manyOne | manyMany
  }
}
```

## Advanced Options

### Visible Fields (`visibleFieldIds`)

Control which fields display in the link field selector.

```typescript
{
  name: "Assigned Tasks",
  type: "link",
  options: {
    foreignTableId: "tblTasks",
    relationship: "manyMany",
    visibleFieldIds: ["fldTitle", "fldStatus", "fldPriority"]  // show these fields
  }
}
```

**Notes:**
- `null` or empty array: shows all fields (default)
- Primary field is always shown

### Filter by View (`filterByViewId`)

Limit linkable records to those visible in a specific view.

```typescript
{
  name: "Active Projects",
  type: "link",
  options: {
    foreignTableId: "tblProjects",
    relationship: "manyOne",
    filterByViewId: "viwActiveOnly"  // only show records from this view
  }
}
```

### Filter (`filter`)

Apply custom filter conditions to limit linkable records. **Supports field reference variables** from current record.

```typescript
{
  name: "Team Projects",
  type: "link",
  options: {
    foreignTableId: "tblProjects",
    relationship: "manyMany",
    filter: {
      conjunction: "and",
      filterSet: [
        {
          fieldId: "fldStatus",
          operator: "is",
          value: "Active"
        },
        // 🎯 Reference current record's field
        {
          fieldId: "fldDepartment",
          operator: "is",
          value: { type: "field", fieldId: "fldUserDepartment" }
        }
      ]
    }
  }
}
```

**For detailed filter syntax and operators**, see `view.filter` topic.

## Relationship Types

- `oneOne`: Each record links to at most one (User ↔ Profile)
- `oneMany`: One links to many in foreign table (User → Tasks)
- `manyOne`: Many link to one in foreign table (Tasks → User)
- `manyMany`: Multiple links in both directions (Tasks ↔ Tags)

## Complete Example

```typescript
{
  name: "Assigned Tasks",
  type: "link",
  options: {
    foreignTableId: "tblTasks",
    relationship: "manyMany",
    visibleFieldIds: ["fldTitle", "fldStatus", "fldDueDate"],
    filter: {
      conjunction: "and",
      filterSet: [
        { fieldId: "fldStatus", operator: "isNot", value: "Completed" },
        { fieldId: "fldAssignee", operator: "is", value: { type: "field", fieldId: "fldCurrentUser" } }
      ]
    }
  }
}
```

## Notes

- Link field automatically creates symmetric field in foreign table
- Advanced options control the link selection UI experience
- Filters can reference current record's fields for dynamic behavior
