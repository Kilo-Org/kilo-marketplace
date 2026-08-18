# Vector Feature: Namespaces

Namespaces partition a single Upstash Vector index into fully isolated subsets. Each request executes only within its specified namespace.

## Key Concepts

- Every index has a default namespace named "" (empty string).
- Additional namespaces are created automatically on first upsert.
- If no namespace is provided, all operations use the default.

## Using Namespaces

Upsert and query operations scoped to a namespace automatically create it if missing.

```ts
import { Index } from "@upstash/vector";
const index = new Index({ url: "URL", token: "TOKEN" });
const ns = index.namespace("ns");
await ns.upsert({ id: "id-0", vector: [0.1, 0.2] });
await ns.query({ vector: [0.1, 0.2], topK: 5 });
```

## Operations

```ts
await index.deleteNamespace("ns");
await index.listNamespaces();
```

## Common Pitfalls

- Forgetting to specify `namespace` causes writes to go into the default namespace.
