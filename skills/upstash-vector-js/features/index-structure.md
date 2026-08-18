# Vector Feature: Index Structure

## Overview

Upstash Vector supports three major index structures:

- **Dense indexes**: semantic matching via dense embeddings.
- **Sparse indexes**: exact/near-exact token and feature matching.
- **Hybrid indexes**: combine dense + sparse results, optionally reranked.

---

## Key Concepts

### Sparse Vectors

- High‑dimensional, mostly‑zero representations.
- Represented as two equal‑length arrays:
  - `indices`: int32 positions of non‑zero elements
  - `values`: float32 values
- Upstash limit: **max 1,000 non‑zero entries per sparse vector**.
- Useful for exact token/word matching (BM25, SPLADE, etc.).

### Hybrid Vectors

- Combine dense semantic vectors with sparse exact‑match vectors.
- Hybrid queries run both dense + sparse search and fuse results.
- Require **both** components (`vector` and `sparseVector`).

### Fusion Algorithms

- **RRF (default)**: ranking‑based, simple, robust, ignores score magnitudes.
- **DBSF**: normalizes scores using distribution statistics; more sensitive to score ranges.

---

## Common Pitfalls

- **Hybrid upserts require both dense and sparse vectors**; omitting either fails.
- **Indexes with embedding models (dense, sparse or both)** let you upsert/query using text; indexes without embedding models do not.
- In Hybrin indexes, dense‑only or sparse‑only querying is allowed, but **fusion happens only when both are provided**.

---

## Usage with Embedding Models

```ts
await index.upsert([
  {
    id: "t1",
    data: "Upstash Vector provides sparse models.",
  },
]);

const results = await index.query({
  data: "Upstash Vector",
  topK: 5,
});

import { WeightingStrategy } from "@upstash/vector";
await index.query({
  data: "Upstash Vector",
  weightingStrategy: WeightingStrategy.IDF,
});
```

## Sparse Index Usage

### Upserting Sparse Vectors

```ts
await index.upsert([
  {
    id: "x1",
    sparseVector: {
      indices: [1, 2, 3],
      values: [0.1, 0.2, 0.3],
    },
  },
]);

const results = await index.query({
  sparseVector: {
    indices: [3, 5],
    values: [0.3, 0.5],
  },
  topK: 5,
  includeMetadata: true,
});
```

- Scores use **inner product**, matching only overlapping indices.
- Results may be fewer than `top_k` if no overlapping dims exist.

## Hybrid Index Usage

### Upserting Dense + Sparse

```ts
await index.upsert([
  {
    id: "h1",
    vector: [0.1, 0.5],
    sparseVector: {
      indices: [1, 2],
      values: [0.1, 0.2],
    },
  },
]);

const results = await index.query({
  vector: [0.5, 0.4],
  sparseVector: {
    indices: [3, 5],
    values: [0.3, 0.5],
  },
  topK: 5,
});

import { FusionAlgorithm } from "@upstash/vector";
await index.query({
  vector: [0.5, 0.4],
  sparseVector: {
    indices: [2, 3],
    values: [0.1, 0.2],
  },
  fusionAlgorithm: FusionAlgorithm.RRF, // or FusionAlgorithm.DBSF
});
```

---

## Custom Reranking

Sometimes RRF/DBSF is insufficient (e.g., using bge‑reranker-v2-m3). Query dense and sparse portions separately and rerank in your own model.

### Custom Rerank (vector input)

```ts
// Dense-only
const dense = await index.query({
  vector: [0.5, 0.4],
  topK: 5,
});

// Sparse-only
const sparse = await index.query({
  sparseVector: {
    indices: [3, 5],
    values: [0.3, 0.5],
  },
  topK: 5,
});

// Custom rerank dense + sparse...
```

### Custom Rerank (text input with hosted models)

```ts
import { QueryMode } from "@upstash/vector";

const dense = await index.query({
  data: "Upstash Vector",
  queryMode: QueryMode.DENSE,
});

const sparse = await index.query({
  data: "Upstash Vector",
  queryMode: QueryMode.SPARSE,
});

// Rerank...
```

---

## Agent Implementation Notes

- Always check whether the index supports **hosted embeddings** before using `data=` fields.
  - Use `await index.info()` to check: if `denseIndex?.embeddingModel` or `sparseIndex?.embeddingModel` exists, the index supports text-based embeddings via the `data` field.
  - Example:
    ```ts
    const info = await index.info();
    const hasDenseEmbedding = !!info.denseIndex?.embeddingModel;
    const hasSparseEmbedding = !!info.sparseIndex?.embeddingModel;
    ```
- For hybrid indexes:
  - Always provide _both_ `vector` and `sparseVector` unless intentionally querying only one modality.
- For reranking workflows:
  - Use dense-only + sparse-only queries, never hybrid queries (as fusion is already applied).
- When building sparse vectors manually:
  - Ensure indices are sorted, unique, and below the model dimension.
