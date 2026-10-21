# Field Formatting

Formatting controls display without changing stored values. Available for number and datetime fields (including formula/rollup/lookup with Number or DateTime cellValueType).

## Number Formatting

### Decimal
```typescript
{
  type: "number",
  options: {
    formatting: {
      type: "decimal",
      precision: 2  // 0-5 decimal places
    }
  }
}
```

### Percent
```typescript
{
  type: "number",
  options: {
    formatting: {
      type: "percent",
      precision: 1  // 0-5, value × 100%
    }
  }
}
// Value 0.1234 → displays as "12.3%"
```

### Currency
```typescript
{
  type: "number",
  options: {
    formatting: {
      type: "currency",
      precision: 2,
      symbol: "$"  // "$", "€", "¥", "£", "₹", etc.
    }
  }
}
// Value 1234.56 → displays as "$1,234.56"
```

## DateTime Formatting

```typescript
{
  type: "date",
  options: {
    formatting: {
      date: "YYYY-MM-DD",  // date format preset or custom
      time: "HH:mm",    // "HH:mm" | "hh:mm A" | "None"
      timeZone: "Asia/Shanghai"  // IANA timezone
    }
  }
}
```

### Date Format Presets
- `M/D/YYYY` - US
- `D/M/YYYY` - European
- `YYYY/MM/DD` - Asian
- `YYYY-MM-DD` - ISO
- `YYYY-MM` - YM
- `MM-DD` - MD
- `YYYY` - Y
- `MM` - M
- `DD` - D

Custom formats also supported using YYYY, MM, DD tokens.

### Time Formats
- `HH:mm` - Hour24
- `hh:mm A` - Hour12
- `None` - No time display

### Common Timezones
**Americas:** `America/New_York`, `America/Chicago`, `America/Los_Angeles`, `America/Sao_Paulo`
**Europe:** `Europe/London`, `Europe/Paris`, `Europe/Berlin`, `Europe/Moscow`
**Asia:** `Asia/Shanghai`, `Asia/Tokyo`, `Asia/Seoul`, `Asia/Kolkata`, `Asia/Dubai`
**Oceania:** `Australia/Sydney`, `Pacific/Auckland`

## Examples

```typescript
// Formula field with currency formatting
{
  type: "formula",
  options: {
    expression: "{Price} * {Quantity}",
    formatting: { type: "currency", symbol: "€", precision: 2 }
  }
}

// Date field with US format
{
  type: "date",
  options: {
    formatting: {
      date: "M/D/YYYY",
      time: "hh:mm A",
      timeZone: "America/New_York"
    }
  }
}
```

## Notes

- Formatting only affects display, not stored values
- Number precision: 0-5 decimal places
- DateTime always stores as ISO 8601 UTC internally
- Formatting applies to computed fields based on cellValueType
