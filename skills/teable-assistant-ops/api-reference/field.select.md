# Select Fields

Select fields allow choosing from predefined options.

## ⚡ SIMPLIFIED SYNTAX (Recommended)

**Colors are AUTO-ASSIGNED!** Just provide choice names as strings:

```typescript
// ✅ SIMPLE: Just string array - colors auto-assigned
{
  name: "Status",
  type: "sel",  // or "singleSelect"
  options: {
    choices: ["Todo", "In Progress", "Done"]
  }
}

// ✅ SIMPLE: Multiple select with string array
{
  name: "Tags",
  type: "multi",  // or "multipleSelect"
  options: {
    choices: ["Bug", "Feature", "Enhancement"]
  }
}
```

## Full Syntax (Optional - for custom colors)

```typescript
{
  name: "Status",
  type: "singleSelect",
  options: {
    choices: [
      { name: "Todo", color: "gray" },
      { name: "In Progress", color: "blue" },
      { name: "Done", color: "green" }
    ]
  }
}
```

## Choice Configuration

Each choice accepts:
- `name`: Choice label (required)
- `color`: Color from Colors enum (optional, **AUTO-ASSIGNED** if omitted)

For available colors, see `field.colors` topic.

## Examples

```typescript
// Priority with semantic colors
{
  name: "Priority",
  type: "singleSelect",
  options: {
    choices: [
      { name: "Low", color: "grayLight1" },
      { name: "Medium", color: "yellow" },
      { name: "High", color: "orangeBright" },
      { name: "Critical", color: "redBright" }
    ]
  }
}

// Department tags
{
  name: "Departments",
  type: "multipleSelect",
  options: {
    choices: [
      { name: "Engineering", color: "blue" },
      { name: "Design", color: "purple" },
      { name: "Marketing", color: "pink" },
      { name: "Sales", color: "green" }
    ]
  }
}
```

## Notes

- Choices are required (cannot be empty)
- Choice names must be unique within the field
- Limit to 10-15 choices for better usability
- Colors are optional but recommended for visual clarity
- Single select: one choice per record
- Multiple select: multiple choices per record
