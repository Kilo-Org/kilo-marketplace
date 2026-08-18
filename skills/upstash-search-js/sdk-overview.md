# SDK Overview

This skill provides a concise but complete reference for using the Upstash Search TypeScript SDK. It focuses on practical usage patterns, common pitfalls, and efficient examples that combine multiple commands. Use this skill whenever interacting with the Upstash Search SDK, generating agents that must query, mutate, or paginate search indexes.

---

## Client Initialization

You must configure a Search client using either environment variables or a config object.

```ts
import { Search } from "@upstash/search";

// Option 1: with explicit config
const client = new Search({ 
  url: process.env.UPSTASH_SEARCH_REST_URL!,
  token: process.env.UPSTASH_SEARCH_REST_TOKEN! 
});
const index = client.index("movies");

// Option 2: using fromEnv (Node.js platform only)
// The constructor will automatically read from process.env if url/token not provided
const client2 = new Search({}); // reads UPSTASH_SEARCH_REST_URL and UPSTASH_SEARCH_REST_TOKEN
const index2 = client2.index("movies");
```

Type-safe usage:
```ts
type Content = { title: string, genre: string };
type Metadata = { year: number };
const indexTyped = client.index<Content, Metadata>("movies");
```

---

## Upsert (add or update documents)

Pitfalls:
- Document structure must match the index schema.
- Content/metadata types are enforced when using generics.

```ts
// Single
await index.upsert({
  id: "star-wars",
  content: { title: "Star Wars", genre: "sci-fi" },
  metadata: { year: 1977 }
});

// Multiple
await index.upsert([
  { id: "inception", content: { title: "Inception", genre: "action" }, metadata: { year: 2010 } },
  { id: "matrix", content: { title: "The Matrix", genre: "sci-fi" }, metadata: { year: 1999 } },
]);

// Update
await index.upsert({ id: "star-wars", content: { title: "A New Hope" } });
```

---

## Fetch (retrieve documents)

Pitfalls:
- Returns null for IDs not found.
- Supports prefix matching.

```ts
// By IDs
const docs = await index.fetch({ ids: ["star-wars", "inception"] });

// By prefix
const sciFi = await index.fetch({ prefix: "star-" });
```

---

## Delete (IDs, prefix, or filter)

Pitfalls:
- **Filter deletion is O(N)** and slow on large indexes.
- Prefix deletion removes *all* matching documents.

```ts
// ID list
await index.delete(["star-wars", "inception"]);

// Single ID
await index.delete("star-wars");

// Prefix
await index.delete({ prefix: "star-" });

// Filter — expensive
await index.delete({ filter: "age > 30" });
```

---

## Search (AI‑powered)

Pitfalls:
- Default `limit = 5`.
- Scores are 0–1.
- Use filters to restrict by document fields.

```ts
// Basic
const results = await index.search({ query: "space opera", limit: 3 });

// With reranking
await index.search({ query: "space opera", limit: 3, reranking: true });

// With filter
await index.search({ query: "space", filter: "category = 'classic'" });

// Adjust semantic vs keyword weighting
await index.search({ query: "robots", semanticWeight: 0.2 });
```

---

## Range (cursor pagination)

Pitfalls:
- Stateless: you must pass all parameters every call.
- `cursor = "0"` for the first request.

```ts
let cursor = "0";
while (cursor !== "") {
  const res = await index.range({ cursor, limit: 2, prefix: "test-" });
  cursor = res.nextCursor;
  console.log(res.documents);
}
```

---

## Reset (delete all documents)

```ts
await index.reset(); // "Success"
```

---

## Info (index or database level)

```ts
// Index-level
const indexInfo = await index.info();
// { documentCount, pendingDocumentCount }

// Database-level
const dbInfo = await client.info();
// { documentCount, pendingDocumentCount, diskSize, indexes: {...} }
```
