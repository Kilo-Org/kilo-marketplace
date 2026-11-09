# Rollup Field

Rollup fields aggregate data from other tables. There are two types:

⚠️ **CRITICAL**: Rollup is NOT Lookup! Do NOT use `isLookup: true` for rollup fields.
- **Lookup**: Mirrors a single value from linked record (uses `isLookup: true`)
- **Rollup**: Aggregates multiple values using functions like sum/count (uses `type: "rollup"`)

## Core Differences

### Basic Rollup (type: "rollup")
- **Essence**: Aggregates records that are already linked to the current record
- **Prerequisite**: Must have an existing Link field establishing the relationship
- **SQL Analogy**: `SELECT SUM(...) FROM linked_records WHERE id IN (current_record.link_ids)`

### Conditional Rollup (type: "conditionalRollup")
- **Essence**: Automatically links to foreign table with dynamic filter conditions and aggregates
- **Prerequisite**: No Link field needed, directly specify foreign table
- **SQL Analogy**: `SELECT SUM(...) FROM foreign_table WHERE <dynamic_conditions>`
- **Key Feature**: Filter can reference current record's field values (dynamic JOIN conditions)

---

## Business Scenario

Using a project management system to demonstrate both types:

### Table Structure

```typescript
// 1. Employees Table
{
  tableId: "tblEmployees",
  fields: [
    { fieldId: "fldEmpName", name: "Name", type: "text" },
    { fieldId: "fldEmpDept", name: "Department", type: "singleSelect" }
  ]
}

// 2. Projects Table
{
  tableId: "tblProjects",
  fields: [
    { fieldId: "fldProjName", name: "Project Name", type: "text" },
    { fieldId: "fldProjManager", name: "Manager", type: "link",
      options: { foreignTableId: "tblEmployees" }
    },
    // Link field to tasks
    { fieldId: "fldProjTasks", name: "Tasks", type: "link",
      options: { foreignTableId: "tblTasks", relationship: "manyMany" }
    }
  ]
}

// 3. Tasks Table
{
  tableId: "tblTasks",
  fields: [
    { fieldId: "fldTaskName", name: "Task Name", type: "text" },
    { fieldId: "fldTaskAssignee", name: "Assignee", type: "link",
      options: { foreignTableId: "tblEmployees" }
    },
    { fieldId: "fldTaskStatus", name: "Status", type: "singleSelect",
      options: { choices: [
        { name: "Pending" }, { name: "In Progress" }, { name: "Done" }
      ]}
    },
    { fieldId: "fldTaskHours", name: "Hours", type: "number" },
    { fieldId: "fldTaskProject", name: "Project", type: "link",
      options: { foreignTableId: "tblProjects" }
    }
  ]
}
```

---

## Basic Rollup Example

**Use Case**: Sum total hours of all linked tasks in a project

**Prerequisites**:
- Projects table has Link field `fldProjTasks` to Tasks table
- Each project record explicitly links to specific tasks

```typescript
// Create field in Projects table
{
  name: "Total Hours",
  type: "rollup",
  options: {
    expression: "sum({values})"  // Aggregation function
  },
  lookupOptions: {
    linkFieldId: "fldProjTasks",      // Link field in current table
    lookupFieldId: "fldTaskHours",    // Field to aggregate in foreign table
    foreignTableId: "tblTasks"        // Foreign table ID
  }
}
```

**SQL Equivalent**:
```sql
SELECT 
  p.project_name,
  SUM(t.hours) as total_hours
FROM projects p
LEFT JOIN project_tasks_junction j ON j.project_id = p.id
LEFT JOIN tasks t ON t.id = j.task_id
GROUP BY p.id
```

**Result**:
- Project A links to Task 1 (5h) and Task 2 (3h) → Total Hours = 8h
- Project B links to Task 3 (10h) → Total Hours = 10h

**Key Point**: Only aggregates tasks that are **already linked** to the current project.

---

## Conditional Rollup Example

**Use Case**: Count tasks in projects managed by each employee

**Challenge**:
- No direct Link field between Employees and Tasks
- Relationship path: Employee ← Project.Manager ← Task.Project

**Solution**: Use Conditional Rollup with dynamic linking

```typescript
// Create field in Employees table
{
  name: "Managed Project Tasks",
  type: "conditionalRollup",
  options: {
    expression: "countall({values})",
    foreignTableId: "tblTasks",        // Target table
    lookupFieldId: "fldTaskName",      // Field to aggregate (any field works for counting)
    filter: {  // Filter: task.project.manager = current employee
      conjunction: "and",
      filterSet: [{
        fieldId: "fldTaskProject",  // Task's project field
        operator: "isAnyOf",
        value: {
          type: "field",
          fieldId: "fldProjManager",  // References current employee record
          // Effect: WHERE task.project_id IN (
          //   SELECT id FROM projects WHERE manager_id = current_employee.id
          // )
        }
      }]
    }
  }
}
```

**SQL Equivalent**:
```sql
SELECT 
  e.name,
  COUNT(*) as task_count
FROM employees e
LEFT JOIN projects p ON p.manager_id = e.id
LEFT JOIN tasks t ON t.project_id = p.id
GROUP BY e.id
```

**Result**:
- Employee A manages Projects X and Y with 15 total tasks → Shows 15
- Employee B manages no projects → Shows 0

**Key Point**: Dynamically links tables using filter conditions with field references, similar to SQL JOIN with WHERE clause.

---

## Comparison Table

| Feature | Basic Rollup | Conditional Rollup |
|---------|--------------|-------------------|
| **Requires Link Field** | ✅ Yes (pre-established relationship) | ❌ No (direct foreign table reference) |
| **Configuration** | `lookupOptions` | All in `options` |
| **Filtering** | Optional static filter | Required filter (at least one condition) |
| **Dynamic Field Reference** | ❌ Not supported | ✅ Supported (`{type: "field"}` in filter value) |
| **Sort/Limit** | ❌ Not supported | ✅ Supported |
| **Typical Use Case** | Aggregate linked records | Cross-table dynamic aggregation |
| **SQL Analogy** | `JOIN ON link_table` | `JOIN ON dynamic_condition` |

---

## Aggregation Functions

- `countall({values})`
- `counta({values})`
- `count({values})`
- `sum({values})`
- `average({values})`
- `max({values})`
- `min({values})`
- `and({values})`
- `or({values})`
- `xor({values})`
- `array_join({values})`
- `array_unique({values})`
- `array_compact({values})`
- `concatenate({values})`

**IMPORTANT**: `{values}` is a fixed placeholder, do not modify! Functions are enum types and cannot be concatenated!

### Function Descriptions
- `countall({values})`: Count all records (including empty values)
- `counta({values})`: Count non-empty records
- `count({values})`: Count non-empty and unique records
- `sum/average/max/min`: For numeric fields only
- `and/or/xor`: For boolean fields only
- `array_*` / `concatenate`: Array/text processing

---

## Complete Examples

```typescript
// ==================== Basic Rollup ====================

// Sum hours of linked tasks
{
  name: "Total Hours",
  type: "rollup",
  options: {
    expression: "sum({values})",
    formatting: { type: "decimal", precision: 1 }
  },
  lookupOptions: {
    linkFieldId: "fldProjTasks",  // Project's task link field
    lookupFieldId: "fldTaskHours",
    foreignTableId: "tblTasks"
  }
}


// ==================== Conditional Rollup ====================

// Count tasks in employee's managed projects (dynamic linking)
{
  name: "Managed Project Tasks",
  type: "conditionalRollup",
  options: {
    expression: "countall({values})",
    foreignTableId: "tblTasks",
    lookupFieldId: "fldTaskName",
    filter: {
      conjunction: "and",
      filterSet: [{
        fieldId: "fldTaskProject",  // Task's project
        operator: "isAnyOf",
        value: {
          type: "field",
          fieldId: "fldProjManager",  // Project manager = current employee
          tableId: "tblEmployees"
        }
      }]
    }
  }
}

// Sum hours of tasks assigned to current employee with dynamic + static filters
{
  name: "My In-Progress Hours",
  type: "conditionalRollup",
  options: {
    expression: "sum({values})",
    foreignTableId: "tblTasks",
    lookupFieldId: "fldTaskHours",
    filter: {
      conjunction: "and",
      filterSet: [
        {
          fieldId: "fldTaskAssignee",
          operator: "is",
          value: {
            type: "field",
            fieldId: "fldEmpName"  // Dynamic: current employee
          }
        },
        {
          fieldId: "fldTaskStatus",
          operator: "is",
          value: "In Progress"  // Static condition
        }
      ]
    },
    sort: { fieldId: "fldTaskHours", order: "desc" },
    limit: 50,
    formatting: { type: "decimal", precision: 1 }
  }
}
```

---

## Important Notes

### Basic Rollup
1. **Link field required**: Cannot dynamically link across tables
2. **Configure in lookupOptions**: `linkFieldId`, `lookupFieldId`, `foreignTableId`
3. **expression in options**: Don't put it in lookupOptions
4. **filter optional**: Only filters already-linked records

### Conditional Rollup
1. **No Link field needed**: Directly specify foreignTableId
2. **All in options**: Includes foreignTableId, lookupFieldId, filter, sort, limit
3. **filter required**: Must contain at least one valid condition (validation checks non-empty filterSet)
4. **Dynamic field reference**: `value: { type: "field", fieldId: "xxx" }` references current record's field
5. **limit range**: 1-5000 (CONDITIONAL_QUERY_MAX_LIMIT)

### General Rules
- All Rollup fields are read-only (automatically calculated)
- Support formatting/showAs options for display
- For detailed filter syntax, see `view.filter` topic
- For detailed formatting options, see `field.formatting` topic
