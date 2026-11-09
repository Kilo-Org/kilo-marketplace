# Quick Reference: Smart Field Creation

This guide summarizes all smart features for efficient field creation.

## ⚡ TYPE ALIASES

| Alias | Full Type | Alias | Full Type |
|-------|-----------|-------|-----------|
| text, str | singleLineText | long | longText |
| num, int | number | check, bool | checkbox |
| sel, select | singleSelect | multi, tags | multipleSelect |
| rate, star | rating | date | date |
| user, person | user | file, attach | attachment |
| link, rel | link | rollup | rollup |
| condrollup | conditionalRollup | formula | formula |

## ⚡ TYPE INFERENCE (Omit type!)

```typescript
// Auto-inferred types from options:
{ options: { choices: [...] } }           → singleSelect
{ options: { max: 5 } }                   → rating
{ options: { foreignTableId: "..." } }    → link
{ options: { expression: "..." } }        → formula (if no foreignTableId)
{ options: { expression, foreignTableId, filter } } → conditionalRollup
```

## ⚡ AUTO-SANITIZATION

### Select Fields - Colors AUTO-ASSIGNED!
```typescript
// ✅ SIMPLE: Just strings - colors auto-assigned
{ type: "sel", options: { choices: ["Done", "Pending", "Active"] } }

// ❌ DON'T NEED: Explicit colors
{ type: "singleSelect", options: { choices: [{ name: "Done", color: "green" }] } }
```

### Rating Fields - Defaults AUTO-APPLIED
```typescript
// ✅ SIMPLE: Just max - icon/color auto-added
{ type: "rate", options: { max: 5 } }
// Result: { max: 5, icon: "star", color: "yellow" }

// ✅ SIMPLER: Even simpler
{ type: "rate" }
// Result: { max: 5, icon: "star", color: "yellow" }
```

## ⚡ NAME RESOLUTION (Use Names, Not IDs!)

### Link Fields
```typescript
// ✅ PREFERRED: Use table NAME
{ type: "link", options: { foreignTableName: "Tasks" } }

// Also works
{ type: "link", options: { foreignTableId: "tblXXX" } }
```

### Lookup/Rollup Fields
```typescript
// ✅ PREFERRED: Use field NAMES
lookupOptions: {
  linkFieldName: "Project",      // → resolved to linkFieldId
  lookupFieldName: "Name",       // → resolved to lookupFieldId
  foreignTableId: "tblProjects"
}
```

## ⚡ ERROR HINTS

When something's wrong, errors include:
- Available tables with IDs
- Available link fields with foreign tables
- Suggestions for similar names (fuzzy matching)
- Required parameters for the field type

## 📝 COMPLETE EXAMPLES

### Basic Text Field
```typescript
{ tableId: "tblXXX", name: "Title", type: "text" }
```

### Select with Auto-Colors
```typescript
{ tableId: "tblXXX", name: "Status", type: "sel", options: { choices: ["Todo", "Done"] } }
```

### Link with Name Resolution
```typescript
{ tableId: "tblXXX", name: "Project", type: "link", options: { foreignTableName: "Projects" } }
```

### Lookup with Name Resolution
```typescript
{
  tableId: "tblXXX",
  name: "Project Name",
  type: "text",
  isLookup: true,
  lookupOptions: {
    linkFieldName: "Project",
    lookupFieldName: "Name",
    foreignTableId: "tblProjects"
  }
}
```

### Rollup with Name Resolution
```typescript
{
  tableId: "tblXXX",
  name: "Total Hours",
  type: "rollup",
  options: { expression: "sum({values})" },
  lookupOptions: {
    linkFieldName: "Tasks",
    lookupFieldName: "Hours",
    foreignTableId: "tblTasks"
  }
}
```

## ⚡ TYPE SELECTION GUIDE

Quick Decision Table — pick the type that matches **data semantics**, not just shape:

| Scenario | Recommended Type |
|----------|-----------------|
| Title / name / short text | SingleLineText |
| Description / notes / content | LongText |
| Fixed options (status / priority / category) | SingleSelect |
| Multiple tags / multi-select | MultipleSelect |
| Quantity / amount / price | Number |
| Rating / stars | Rating |
| Date / time | Date |
| Yes-no / toggle | Checkbox |
| Person assignment | User |
| Files / images | Attachment |
| Reference another table | Link |
| Row-level formula calculation | Formula |
| Aggregate linked records | Rollup / ConditionalRollup |
| Mirror a linked field | Lookup |
| Audit fields (who / when) | CreatedTime / LastModifiedTime / CreatedBy / LastModifiedBy |
| Auto-increment ID | AutoNumber |
| Trigger an action | Button |
| Auto-generate content from other fields via AI | AI field (any base type + `aiConfig`; read `field.ai` doc) |

## ⚡ COMMON TYPE MISTAKES

| Mistake | Better Choice |
|---------|---------------|
| Text field to store status/priority | Use **SingleSelect** — enables filtering, coloring, and validation |
| SingleSelect for tags/labels | Use **MultipleSelect** — one record can have many tags |
| Number field for ratings | Use **Rating** — provides star UI and bounded values |
| Text field for dates | Use **Date** — enables date filtering, sorting, and formatting |
| Text field for person names | Use **User** — links to real collaborators, enables mentions and assignment |
| Manually repeating values from another table | Use **Link** + **Lookup** — keeps data in sync automatically |
| Writing a formula to summarize/translate/classify text | Use **AI field** with `aiConfig` — purpose-built for AI generation (read `field.ai` doc) |

## ⚡ NAME-BASED AUTO-SUGGESTION

The `create-field` command has **built-in name → type inference**. You can often omit `type` entirely and let the system pick the right one based on the field name.

Key mapping rules (from `suggestTypeFromName`):

| Name pattern | Inferred type |
|-------------|---------------|
| status, priority, category, type, stage, level | SingleSelect |
| tag, label | MultipleSelect |
| description, notes, comment, content, body | LongText |
| count, amount, price, quantity, total, number, age | Number |
| rating, score, stars | Rating |
| date, time (without "by") | Date |
| is*, has*, active, enabled, done, completed | Checkbox |
| assignee, owner, user | User |
| attachment, file, image, photo, document | Attachment |
| email | SingleLineText |
| created time / created (without "by") | CreatedTime |
| last modified / updated (without "by") | LastModifiedTime |
| created by, author | CreatedBy |
| modified by, updated by | LastModifiedBy |

> **Tip:** If your field name matches one of these patterns, just omit the `type` parameter — the system will infer it automatically.

## 📤 OUTPUT FORMAT

Returns compressed format:
```json
{ "field": "fldXXX:FieldName:type", "hint": "Created singleSelect field" }
```

## 🔗 DETAILED DOCS

For complex fields, check:
- Link fields → `field.link`
- Lookup fields → `field.lookup`
- Rollup fields → `field.rollup`
- AI fields → `field.ai`
