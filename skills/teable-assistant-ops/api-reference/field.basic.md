# Basic Fields Configuration

Basic field types for storing text, numbers, dates, and other primitive data. Most fields support `defaultValue` option.

## Field Types

### singleLineText / longText
```typescript
{
  type: "singleLineText",  // or "longText"
  options: {
    defaultValue: "text"     // optional
  }
}
```
URLs inside text values are detected and rendered as clickable links automatically. For email or phone columns add `showAs: { type: "email" | "phone" }` (see `field.show-as` topic).

---

### checkbox
```typescript
{
  type: "checkbox",
  options: {
    defaultValue: false      // optional
  }
}
```

---

### number
Supports formatting and visualization.

```typescript
{
  type: "number",
  options: {
    defaultValue: 0,         // optional
    formatting: {            // optional, see field.formatting
      type: "decimal",       // "decimal" | "percent" | "currency"
      precision: 2,
      symbol: "$"            // for currency
    },
    showAs: {                // optional, see field.show-as
      type: "bar",           // "bar" | "ring"
      color: "blue",
      showValue: true,
      maxValue: 100
    }
  }
}
```
See `field.formatting` and `field.show-as` topics for details.

---

### date
Supports time and timezone.

```typescript
{
  type: "date",
  options: {
    defaultValue: "now",     // optional: "now" or ISO date string
    formatting: {            // optional, see field.formatting
      date: "YYYY-MM-DD",
      time: "HH:mm",         // "None" for date only
      timeZone: "Asia/Shanghai"
    }
  }
}
```
Stored as ISO 8601 UTC string. See `field.formatting` topic for details.

---

### rating
Displays as icons (1-10 scale).

```typescript
{
  type: "rating",
  options: {
    max: 5,                  // required: 1-10
    icon: "star",            // optional: "star", "heart", "thumbsUp", "flag"
    color: "yellow"          // optional
  }
}
```

---

### user
References collaborators.

```typescript
{
  type: "user",
  options: {
    isMultiple: false,       // optional: allow multiple users
    shouldNotify: true       // optional: notify on assignment
  }
}
```

---

### attachment
Supports multiple file uploads.

```typescript
{
  type: "attachment",
  options: {}                // no required options
}
```
Image preview and file download supported.

---

## Common Notes

- **Optional by default**: All fields are optional. Use table-level validation for required fields.
- **Type conversion**: Field types can be changed, but incompatible data may be lost.
- **Usage**: Can be used in formulas, lookups, rollups, view filters, sorts, and groups.
