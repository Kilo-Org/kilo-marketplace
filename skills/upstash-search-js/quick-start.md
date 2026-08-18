# Quick Start: Upstash Search

This Skill gives agents a fast, end‑to‑end workflow for creating a Search database, adding documents, and querying them. It also summarizes key concepts like **content vs metadata**, **filters**, and **reranking** so agents can use Search correctly.

---

## Create a Database
1. Open the **Vector** tab → **Create → Search Database**.
2. Provide a name (e.g., `product-search`) and region.
3. Select a plan.

Agents should store:
- `UPSTASH_SEARCH_REST_URL`
- `UPSTASH_SEARCH_REST_TOKEN`

These values are required when constructing a Search client.

---

## Add Documents
Documents consist of:
- **id**: unique identifier
- **content** *(required)*: indexed and searchable
- **metadata** *(optional)*: **not searchable**, but retrievable and filterable

### TypeScript / Python Example
```ts
import { Search } from "@upstash/search";
const client = new Search({ 
  url: process.env.UPSTASH_SEARCH_REST_URL,
  token: process.env.UPSTASH_SEARCH_REST_TOKEN 
});
const index = client.index("movies");
await index.upsert([
  {
    id: "star-wars",
    content: { title: "Star Wars", genre: "sci-fi", category: "classic" },
    metadata: { director: "George Lucas" }
  }
]);
```
```python
from upstash_search import Search
client = Search(url=URL, token=TOKEN)
index = client.index("movies")
index.upsert(documents=[{
  "id": "movie-0",
  "content": {
    "title": "Star Wars",
    "overview": "Sci-fi space opera",
    "genre": "sci-fi",
    "category": "classic",
  },
  "metadata": {"poster": "https://poster.link/starwars.jpg"}
}])
```

---

## Content vs Metadata (Essential Concepts)
- **Content**
  - Required
  - Indexed and searchable
  - Can be used in filters
  - Ideal for textual and semantic data

- **Metadata**
  - Optional
  - Not indexed → **cannot be searched**
  - Still **filterable** using `@metadata.key`
  - Used for contextual / reference fields

Example:
```json
{
  "content": { "title": "Star Wars", "genre": "sci-fi" },
  "metadata": { "director": "George Lucas", "sku": "SW-001" }
}
```

---

## Search
Searching supports semantic + keyword hybrid search, optional reranking, and filters.

### TypeScript / Python Example
```ts
const res = await index.search({ query: "space opera", limit: 2, reranking: true });
```
```python
scores = index.search(query="space opera", limit=2, reranking=True)
```

---

## Filtering
Filters restrict results using SQL‑like syntax or structured filters (TypeScript only). Both **content fields** and **metadata fields** can be used.

**Metadata fields require `@metadata.` prefix**.

### Example (String Filters)
```ts
await index.search({
  query: "sony headphones",
  filter: "warehouse_location = 'A3-15' AND @metadata.supplier_id = 'SUP-123'"
});
```

### Example (Type‑safe Filters, TS SDK)
```ts
await index.search({
  query: "sony headphones",
  filter: {
    AND: [
      { category: { equals: "Electronics" } },
      { "@metadata.count": { greaterThanOrEquals: 3 } }
    ]
  }
});
```

Common operators:
- equals, not equals
- <, <=, >, >=
- glob / not glob
- in / not in
- contains / not contains (arrays)
- has field / has not field

---

## Reranking
Reranking reorders results using a high‑accuracy model.

- Disabled by default (`false`)
- When `true`, improves relevance but costs $1 per 1K reranked items

Example:
```ts
await index.search({ query: "space opera", reranking: true });
```
```python
index.search(query="space opera", reranking=True)
```

Use when:
- Precision is critical
- Results require more semantic depth
- Queries are ambiguous or conceptual

---

## Common Pitfalls
- Missing **content** field → upsert fails.
- Metadata fields are **not searchable**.
- Metadata must be prefixed as `@metadata.key` in filters.
- Filters may return fewer than `topK` results if too selective.
- Indexes are created automatically on first `upsert`.
