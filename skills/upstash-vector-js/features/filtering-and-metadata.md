# Vector Feature: Filtering and Metadata

Upstash Vector supports attaching metadata and optional data to vectors. Metadata is structured JSON used for filtering; data is unstructured content returned in responses but not filterable.

Filtering uses a SQL‑like syntax and supports nested objects, array indexing, glob patterns, and boolean logic. The system applies both in‑filtering and post‑filtering according to a filtering budget, so highly selective filters may return fewer results than `topK`.

## Setting Metadata and Data

You can upsert vectors with metadata and optional data. Metadata is any JSON structure; data is typically raw text.

```ts
import { Index } from "@upstash/vector";

const index = new Index({ url: "...", token: "..." });

await index.upsert([
  {
    id: "v0",
    vector: [0.1, 0.2],
    metadata: { city: "Istanbul", population: 15460000 },
    data: "Istanbul info",
  },
  {
    id: "v1",
    data: "Upstash is a serverless data platform.",
  },
]);
```

## Querying with Metadata Filters

Include metadata in results and apply filters using SQL‑like expressions.

```ts
await index.query({
  vector: [0.9, 0.3],
  topK: 5,
  includeMetadata: true,
  filter: "population >= 1000000 AND geography.continent = 'Asia'",
});
```

### Supported Operators

- Equality: `=`, `!=`
- Numeric comparators: `<`, `<=`, `>`, `>=`
- Set membership: `IN`, `NOT IN`
- Array tests: `CONTAINS`, `NOT CONTAINS`
- Field existence: `HAS FIELD`, `HAS NOT FIELD`
- Glob string matching: `GLOB`, `NOT GLOB`

Glob wildcards: `*`, `?`, `[]`, `[^]`.

### Boolean Logic

Use `AND` and `OR`, with parentheses for grouping. `AND` has higher precedence than `OR`.

### Nested Objects and Arrays

- Access nested fields: `economy.currency`, `geography.coordinates.latitude`.
- Index arrays: `industries[0]` or from end: `industries[#-1]`.

Example:

```SQL
economy.major_industries CONTAINS 'Tourism' AND geography.coordinates.latitude >= 35
```

## Retrieving Metadata and Data

```ts
// query
await index.query({
  vector: [0.9, 0.3],
  topK: 5,
  includeMetadata: true,
  includeData: true,
});

// range
await index.range({ cursor: "0", limit: 3, includeMetadata: true });
```
