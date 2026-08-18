# Vector TS SDK

## Upsert

Add or update vectors. Also accepts raw text (`data`) to embed automatically.

**Pitfalls**

- Vector dimension must match index dimension.
- Passing both `vector` and `data` is invalid.
- Metadata is optional but recommended for filtering.

**Example (single + batch, mix of vector/data)**

```ts
// Single vector
await index.upsert({ id: "1", vector: [0.1, 0.2], metadata: { type: "doc" } });

// Multiple vectors
await index.upsert(
  [
    { id: "2", vector: [0.2, 0.3] },
    { id: "3", vector: [0.3, 0.4], metadata: { tag: "a" } },
  ],
  { namespace: "ns" }
);

// Using data (auto‑embedding. Only works if the vector index has an embedding model)
await index.upsert({ id: "4", data: "A fantasy movie" });
```

---

## Fetch

Retrieve vectors by exact ID or prefix.

**Example**

```ts
// Exact
const out = await index.fetch(["1", "2"], { includeMetadata: true });
// → [{ id: "1", metadata: {...} }, null]

// Prefix
await index.fetch({ prefix: "user-" });
```

---

## Delete

Remove vectors by IDs, prefix, or metadata filter.

**Pitfalls**

- Only one of `ids`, `prefix`, or `filter` can be used.
- Using `filter` triggers an O(N) scan.

**Example**

```ts
await index.delete(["1", "2"]);
await index.delete({ prefix: "user-" });
await index.delete({ filter: "status = 'expired'" });
```

---

## Query

Find the top‑K most similar vectors. Supports dense, sparse, hybrid, and embedded-on-demand queries.

**Pitfalls**

- Query vector dimension must match index.
- Scores are normalized 0–1 no matter the similarity metric.

**Example**

```ts
// Dense vector
const results = await index.query({
  vector: [0.1, 0.2],
  topK: 3,
  includeMetadata: true,
  filter: "genre = 'fantasy'",
});

// Data (auto‑embedding)
await index.query({ data: "epic fantasy adventure", topK: 2 });
```

---

## Resumable Query

Long-running, chunked queries with server-side state.

**Pitfalls**

- Remember to call `stop()` to free resources.
- `fetchNext(k)` retrieves N more results.

**Example**

```ts
const { result, fetchNext, stop } = await index.resumableQuery({
  vector: [0.1, 0.2],
  topK: 50,
  maxIdle: 3600,
});

const next = await fetchNext(10);
await stop();
```

---

## Range

Paginated, stateless scanning of vectors; recommended for large prefix fetches.

**Pitfalls**

- Always pass `cursor`; set to `0` initially.

**Example**

```ts
let cursor = 0;
while (cursor !== null) {
  const page = await index.range({ cursor, limit: 100, includeMetadata: true });
  console.log(page.vectors);
  cursor = page.nextCursor;
}
```

---

## Info

Retrieve index statistics.

**Example**

```ts
const info = await index.info();
/* Returns:
{
  vectorCount: number;
  pendingVectorCount: number;
  indexSize: number;
  dimension: number;
  similarityFunction: "COSINE" | "EUCLIDEAN" | "DOT_PRODUCT";
  denseIndex?: {
    dimension: number;
    similarityFunction: "COSINE" | "EUCLIDEAN" | "DOT_PRODUCT";
    embeddingModel?: string;
  };
  sparseIndex?: {
    embeddingModel?: string;
  };
  namespaces: Record<string, {
    vectorCount: number;
    pendingVectorCount: number;
  }>;
}
*/
```

---

## Reset

Clear a namespace or the entire index.

**Pitfalls**

- `{ all: true }` must be explicit.

**Example**

```ts
await index.reset(); // default namespace
await index.reset({ namespace: "my-namespace" });
await index.reset({ all: true });
```

---

## Advanced

### Request Timeout

```ts
const index = new Index({
  url,
  token,
  signal: () => AbortSignal.timeout(1000),
});
```

### Telemetry

Disable with env variable:

```sh
UPSTASH_DISABLE_TELEMETRY=1
```
