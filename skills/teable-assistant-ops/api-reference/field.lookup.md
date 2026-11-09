# Lookup Field

Lookup fields display values from other tables.

⚠️ **Critical:** Lookup does NOT have its own FieldType. Use the **exact type** of the foreign field and set `isLookup: true`.

## Core Differences

### Basic Lookup (isLookup: true)
- **Essence**: Displays field values from records that are already linked to the current record
- **Prerequisite**: Must have an existing Link field establishing the relationship
- **SQL Analogy**: `SELECT foreign_field FROM foreign_table WHERE id IN (current_record.link_ids)`

### Conditional Lookup (isConditionalLookup: true)
- **Essence**: Displays field values from foreign table records matching dynamic filter conditions
- **Prerequisite**: No Link field needed, directly specify foreign table
- **SQL Analogy**: `SELECT foreign_field FROM foreign_table WHERE <dynamic_conditions>`
- **Key Feature**: Filter can reference current record's field values (dynamic WHERE conditions)

---

## Business Scenario

Using the same project management system:

### Table Structure

```typescript
// 1. Projects Table
{
  tableId: "tblProjects",
  fields: [
    { fieldId: "fldProjName", name: "Project Name", type: "singleLineText" },
    { fieldId: "fldProjBudget", name: "Budget", type: "number" },
    { fieldId: "fldProjManager", name: "Manager", type: "link",
      options: { foreignTableId: "tblEmployees" }
    },
    { fieldId: "fldProjTasks", name: "Tasks", type: "link",
      options: { foreignTableId: "tblTasks" }
    }
  ]
}

// 2. Tasks Table
{
  tableId: "tblTasks",
  fields: [
    { fieldId: "fldTaskName", name: "Task Name", type: "singleLineText" },
    { fieldId: "fldTaskStatus", name: "Status", type: "singleSelect" },
    { fieldId: "fldTaskAssignee", name: "Assignee", type: "link",
      options: { foreignTableId: "tblEmployees" }
    },
    { fieldId: "fldTaskProject", name: "Project", type: "link",
      options: { foreignTableId: "tblProjects" }
    }
  ]
}

// 3. Employees Table
{
  tableId: "tblEmployees",
  fields: [
    { fieldId: "fldEmpName", name: "Name", type: "singleLineText" },
    { fieldId: "fldEmpEmail", name: "Email", type: "singleLineText" }
  ]
}
```

---

## Basic Lookup Example

**Use Case**: Display project name in Tasks table by following the existing link

**Prerequisites**:
- Tasks table has Link field `fldTaskProject` to Projects table
- Each task record links to one project

```typescript
// Create field in Tasks table to display project name
{
  name: "Project Name",
  type: "singleLineText",  // MUST match Projects.fldProjName type
  isLookup: true,
  lookupOptions: {
    linkFieldId: "fldTaskProject",    // Link field in current table (Task → Project)
    lookupFieldId: "fldProjName",     // Field to display from foreign table
    foreignTableId: "tblProjects"     // Foreign table ID
  }
}
```

**SQL Equivalent**:
```sql
SELECT 
  t.task_name,
  p.project_name
FROM tasks t
LEFT JOIN projects p ON t.project_id = p.id
```

**Result**:
- Task "Design UI" links to Project "Website Redesign" → Shows "Website Redesign"
- Task "Write Tests" links to Project "API v2" → Shows "API v2"

**Key Point**: Displays values from the **already linked** project record.

---

## Conditional Lookup Example

**Use Case**: Display task names assigned to the current employee (without direct link)

**Challenge**:
- Employees table has no direct Link field to Tasks table
- Relationship exists: Employee ← Task.Assignee, but we want to show task names

**Solution**: Use Conditional Lookup with dynamic filter

```typescript
// Create field in Employees table to show assigned task names
{
  name: "My Task Names",
  type: "singleLineText",  // MUST match Tasks.fldTaskName type
  isLookup: true,
  isConditionalLookup: true,
  lookupOptions: {
    foreignTableId: "tblTasks",       // Target table
    lookupFieldId: "fldTaskName",     // Field to display
    filter: {  // Filter: task.assignee = current employee
      conjunction: "and",
      filterSet: [{
        fieldId: "fldTaskAssignee",  // Task's assignee field
        operator: "is",
        value: {
          type: "field",
          fieldId: "fldEmpName",  // References current employee record
          // Effect: WHERE task.assignee_id = current_employee.id
        }
      }]
    },
    sort: { fieldId: "fldTaskStatus", order: "asc" },
    limit: 50
  }
}
```

**SQL Equivalent**:
```sql
SELECT 
  e.name,
  GROUP_CONCAT(t.task_name) as my_task_names
FROM employees e
LEFT JOIN tasks t ON t.assignee_id = e.id
GROUP BY e.id
ORDER BY t.status ASC
LIMIT 50
```

**Result**:
- Employee "Alice" is assigned tasks "Design UI", "Review PR" → Shows ["Design UI", "Review PR"]
- Employee "Bob" has no tasks assigned → Shows []

**Key Point**: Dynamically queries foreign table using filter with field reference, similar to SQL WHERE clause.

---

## Comparison Table

| Feature | Basic Lookup | Conditional Lookup |
|---------|--------------|-------------------|
| **Requires Link Field** | ✅ Yes (pre-established relationship) | ❌ No (direct foreign table reference) |
| **Configuration** | `linkFieldId` in lookupOptions | No `linkFieldId`, uses `filter` |
| **Filtering** | Optional static filter | Required filter (at least one condition) |
| **Dynamic Field Reference** | ❌ Not supported | ✅ Supported (`{type: "field"}` in filter value) |
| **Sort/Limit** | ❌ Not supported | ✅ Supported |
| **Field Flag** | `isLookup: true` | `isLookup: true` + `isConditionalLookup: true` |
| **Typical Use Case** | Display linked record's field | Cross-table dynamic field display |
| **SQL Analogy** | `JOIN ON link_table` | `WHERE dynamic_condition` |

---

## Type Inheritance Rule

⚠️ **Critical:** Lookup type MUST exactly match the foreign field type. Mismatch causes validation error.

```typescript
// Foreign field: { fieldId: "fldProjName", type: "singleLineText" }
// Lookup field MUST be:
{
  type: "singleLineText",  // ✅ Exact match
  isLookup: true,
  lookupOptions: { ... }
}

// ❌ Wrong: type: "longText" (even though both are text types)
// ❌ Wrong: type: "lookup" (no such type exists)
```

**Type matching examples:**
- Foreign = `singleLineText` → Lookup = `singleLineText`
- Foreign = `number` → Lookup = `number`
- Foreign = `date` → Lookup = `date`
- Foreign = `user` → Lookup = `user`

---

## Complete Examples

```typescript
// ==================== Basic Lookup ====================

// Display project name from linked project
{
  name: "Project Name",
  type: "singleLineText",
  isLookup: true,
  lookupOptions: {
    linkFieldId: "fldTaskProject",
    lookupFieldId: "fldProjName",
    foreignTableId: "tblProjects"
  }
}

// Display project budget with formatting
{
  name: "Project Budget",
  type: "number",
  isLookup: true,
  lookupOptions: {
    linkFieldId: "fldTaskProject",
    lookupFieldId: "fldProjBudget",
    foreignTableId: "tblProjects"
  },
  options: {
    formatting: { type: "currency", symbol: "$", precision: 2 }
  }
}


// ==================== Conditional Lookup ====================

// Display task names assigned to current employee
{
  name: "My Task Names",
  type: "singleLineText",
  isLookup: true,
  isConditionalLookup: true,
  lookupOptions: {
    foreignTableId: "tblTasks",
    lookupFieldId: "fldTaskName",
    filter: {
      conjunction: "and",
      filterSet: [{
        fieldId: "fldTaskAssignee",
        operator: "is",
        value: { type: "field", fieldId: "fldEmpName" }
      }]
    },
    sort: { fieldId: "fldTaskStatus", order: "asc" },
    limit: 50
  }
}

// Display in-progress task names with static + dynamic filters
{
  name: "My Active Tasks",
  type: "singleLineText",
  isLookup: true,
  isConditionalLookup: true,
  lookupOptions: {
    foreignTableId: "tblTasks",
    lookupFieldId: "fldTaskName",
    filter: {
      conjunction: "and",
      filterSet: [
        {
          fieldId: "fldTaskAssignee",
          operator: "is",
          value: { type: "field", fieldId: "fldEmpName" }  // Dynamic
        },
        {
          fieldId: "fldTaskStatus",
          operator: "is",
          value: "In Progress"  // Static
        }
      ]
    },
    limit: 20
  }
}
```

---

## Common Mistakes

❌ **Using `type: "lookup"`**
- No such type exists
- ✅ Use: `type: "singleLineText"` (or foreign field's type) + `isLookup: true`

❌ **Missing `isLookup: true`**
- ✅ Always set: `isLookup: true`

❌ **Type mismatch with foreign field**
- ✅ Use: **Exact same type** as foreign field

❌ **Missing `foreignTableId` in lookupOptions**
- ✅ Always include: `foreignTableId`

❌ **Conditional lookup missing `isConditionalLookup: true`**
- ✅ Set both: `isLookup: true` AND `isConditionalLookup: true`

❌ **Including `linkFieldId` in conditional lookup**
- Validation will reject this
- ✅ Conditional lookup uses `filter`, not `linkFieldId`

---

## Important Notes

### Basic Lookup
1. **Link field required**: Must have existing Link field
2. **Configure linkFieldId**: Points to the Link field in current table
3. **Type must match**: Foreign field's type exactly
4. **Read-only**: Synced from linked records

### Conditional Lookup
1. **No Link field needed**: Direct foreignTableId reference
2. **filter required**: Must contain at least one valid condition (validation checks non-empty filterSet)
3. **Dynamic field reference**: `value: { type: "field", fieldId: "xxx" }` references current record's field
4. **Both flags required**: `isLookup: true` AND `isConditionalLookup: true`
5. **limit range**: 1-5000 (CONDITIONAL_QUERY_MAX_LIMIT)

### General Rules
- All Lookup fields are read-only (synced from foreign table)
- Type inheritance is strictly enforced (validation will fail on mismatch)
- Support formatting/showAs options based on field type
- For detailed filter syntax, see `view.filter` topic
- For detailed formatting options, see `field.formatting` topic
