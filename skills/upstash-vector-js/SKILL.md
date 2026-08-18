---
name: upstash-vector-js
description: >-
  Skills for Upstash Vector features, TypeScript/JavaScript SDK usage, and
  integrations. Use when users ask how to work with Vector, its TS SDK,
  features, or supported frameworks.
metadata:
  category: data
  author: upstash
  source:
    repository: 'https://github.com/upstash/skills'
    path: skills/upstash-vector-js
    license_path: LICENSE
    ref: main
    commit: fb4e6019638d5746b86a54f1bb7144dbb324480a
---

# Vector Documentation Skill

## Quick Start

Vector is a high‑performance vector database for storing, querying, and managing vector embeddings.

Basic workflow:

- Install the Vector TS SDK.
- Connect to a Vector instance.
- Upsert vectors, query them, and manage namespaces.

Example (TypeScript):

```ts
import { Index } from "@upstash/vector";
const index = new Index({
  url: process.env.UPSTASH_VECTOR_REST_URL!,
  token: process.env.UPSTASH_VECTOR_REST_TOKEN!,
});

await index.upsert([{ id: "1", vector: [0.1, 0.2], metadata: { tag: "example" } }]);

const results = await index.query({
  vector: [0.1, 0.2],
  topK: 5,
});
```

For full usage, refer to the linked skill files below.

## Other Skill Files

### TS SDK Reference

- `sdk-methods`: Explains SDK commands: delete, fetch, info, query, range, reset, resumable-query, upsert

### Features

- `features/namespaces`: Explains namespaces and dataset organization.
- `features/index-structure`: Covers hybrid and sparse index structures.
- `features/filtering-and-metadata`: Details metadata storage and server-side filtering.

Use these files for deeper guidance on SDK usage, advanced configurations, algorithms, and integrations.
