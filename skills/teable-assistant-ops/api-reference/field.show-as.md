# Field Show As

Show As provides enhanced visual representations for field values. Available for number and text fields (including formula/rollup/lookup with compatible cellValueType).

## Number Show As

### Single Value (bar/ring)

For fields with `isMultipleCellValue: false` or undefined.

```typescript
{
  type: "number",
  options: {
    showAs: {
      type: "bar",  // "bar" | "ring"
      color: "blue",           // see field.colors topic
      showValue: true,         // display numeric value
      maxValue: 100           // ⚠️ REQUIRED! The reference value for 100%
    }
  }
}
```

**Bar:** Horizontal progress bar
**Ring:** Circular progress ring
**maxValue:** ⚠️ **REQUIRED** - The reference value for 100% scale (values can exceed it)

### Multiple Values (bar/line)

For fields with `isMultipleCellValue: true` (e.g., rollup with `values` expression).

```typescript
{
  type: "rollup",
  options: {
    expression: "values",
    showAs: {
      type: "line",  // "bar" | "line"
      color: "purple"
    }
  }
}
```

**Bar:** Individual bars for each value
**Line:** Connected line chart

## Text Show As

For single-line text fields. Creates clickable elements for common actions.

```typescript
{
  type: "singleLineText",
  options: {
    showAs: {
      type: "email"  // "email" | "phone"
    }
  }
}
```

**email:** Opens mail client with mailto: link
**phone:** Initiates call with tel: protocol

URLs inside text values are detected and rendered as clickable links automatically, so a URL column needs no show-as at all. The legacy `{ type: "url" }` show-as is deprecated and renders as plain text.

## Color Options

For available colors, see `field.colors` topic.

## Examples

```typescript
// Progress bar
{
  name: "Completion",
  type: "number",
  options: {
    showAs: {
      type: "bar",
      color: "greenBright",
      showValue: true,
      maxValue: 100
    }
  }
}

// Score ring
{
  name: "Rating",
  type: "formula",
  options: {
    expression: "{Stars} * 20",
    showAs: {
      type: "ring",
      color: "yellowBright",
      showValue: true,
      maxValue: 100
    }
  }
}

// Trend line
{
  name: "Daily Sales",
  type: "rollup",
  options: {
    expression: "values",
    showAs: { type: "line", color: "cyan" }
  }
}
```

## Notes

- Show as is optional; without it, values display as plain text/numbers
- Single vs multiple types must match `isMultipleCellValue`
- Text show-as only validates type, not actual value format
- Can be added/removed without affecting stored values
