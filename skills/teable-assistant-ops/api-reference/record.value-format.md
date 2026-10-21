# Record Value Format Reference

This document defines the exact format for field values when creating or updating records.

## Simple Field Types

### singleLineText
```typescript
// Value: string
{
  "fldTitle": "My Task Title"
}
```

### longText
```typescript
// Value: string (can include newlines)
{
  "fldDescription": "This is a long description\nWith multiple lines"
}
```

### number
```typescript
// Value: number (not string)
{
  "fldAmount": 123.45,
  "fldQuantity": 10
}
```

### checkbox
```typescript
// Value: true or null (false value always be null)
{
  "fldIsCompleted": true,
  "fldIsActive": null
}
```

### date
```typescript
// Value: ISO 8601 date string
{
  "fldDueDate": "2024-01-15T10:30:00.000Z",  // With time
  "fldStartDate": "2024-01-15"                // Date only
}
```

### rating
```typescript
// Value: number (within field's max range)
{
  "fldPriority": 5,
  "fldStars": 3
}
```

## Select Fields

### singleSelect
```typescript
// Value: string (must match choice name exactly)
{
  "fldStatus": "In Progress"  // Must be an existing choice name
}
```

### multipleSelect
```typescript
// Value: array of strings (choice names)
{
  "fldTags": ["Bug", "Feature", "High Priority"]
}
```

## User Fields

```typescript
// Single: user object (id, title required; email, avatarUrl optional)
{ "fldAssignee": { "id": "usrXXXXXXXXX", "title": "John Doe" } }

// Multiple: array of user objects
{ "fldCollaborators": [
  { "id": "usrXXXXXX1", "title": "Alice" },
  { "id": "usrXXXXXX2", "title": "Bob" }
]}
```

## Link Fields

```typescript
// Single (OneOne/ManyOne): link object
{ "fldProject": { "id": "recXXXXXXXXX", "title": "Project Alpha" } }

// Multiple (OneMany/ManyMany): array of link objects
{ "fldRelatedTasks": [
  { "id": "recXXXXXX1", "title": "Task 1" },
  { "id": "recXXXXXX2", "title": "Task 2" }
]}
```

## Attachment Fields

### attachment
```typescript
// Value: array of simplified attachment objects (only name and token required)
// Backend automatically fetches other fields (size, mimetype, path, etc.) from database by token
// Optional id: if provided and exists in DB, the attachment will reuse that id
{
  "fldFiles": [
    {
      "name": "document.pdf",
      "token": "tokenXXXXXXXX"
    },
    {
      "id": "attXXXXXXXXX",  // Optional: reuse existing attachment id
      "name": "image.png",
      "token": "tokenYYYYYYYY"
    }
  ]
}
```

## Read-Only Fields

These fields are computed or system-managed and CANNOT be set:
- **formula, lookup, rollup**: Computed from other fields/records
- **createdTime, lastModifiedTime, createdBy, lastModifiedBy, autoNumber**: System-managed

## Complete Example

```typescript
{
  "records": [{
    "fields": {
      "fldTitle": "Implement user authentication",
      "fldDescription": "Add OAuth2 support\nIntegrate with SSO",
      "fldEstimatedHours": 8,
      "fldDueDate": "2024-02-01T17:00:00.000Z",
      "fldStatus": "In Progress",
      "fldPriority": 5,
      "fldTags": ["Feature", "Security"],
      "fldAssignee": { "id": "usrXXXXXXXXX", "title": "John Doe" },
      "fldProject": { "id": "recProjectXXX", "title": "Q1 Sprint" },
      "fldIsBlocking": true
    }
  }]
}
```

## Important Notes

- Use field IDs (starting with "fld") in API calls
- User and Link fields require objects with `id` and `title` (not simple strings)
- Single link = object, Multiple link = array of objects
- Checkbox: use `true` or `null` (not `false`)
- Date: ISO 8601 format ("2024-01-15T10:30:00.000Z")
- Choice names are case-sensitive

## Common Errors

```typescript
// ❌ Wrong: User/Link as string
{ "fldAssignee": "usrXXXXXXXXX" }
{ "fldProject": "recXXXXXXXXX" }

// ✅ Correct: Use objects
{ "fldAssignee": { "id": "usrXXXXXXXXX", "title": "John" } }
{ "fldProject": { "id": "recXXXXXXXXX", "title": "Project" } }

// ❌ Wrong: Number as string, checkbox as false
{ "fldAmount": "123.45", "fldActive": false }

// ✅ Correct: Proper types
{ "fldAmount": 123.45, "fldActive": null }
```
