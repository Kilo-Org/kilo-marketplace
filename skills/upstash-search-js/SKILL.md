---
name: upstash-search-js
description: >-
  Skills covering Upstash Search quick starts, core concepts, and
  TypeScript/JavaScript SDK usage. Use when a user asks how to get started, how
  indexing works, or how to use the TS client.
metadata:
  category: data
  author: upstash
  source:
    repository: 'https://github.com/upstash/skills'
    path: skills/upstash-search-js
    license_path: LICENSE
    ref: main
    commit: fb4e6019638d5746b86a54f1bb7144dbb324480a
---

# Upstash Search Documentation

## Quick Start

Install the TS SDK:

```
npm install @upstash/search
```

Create a client and perform a simple upsert + search:

```
import { Search } from "@upstash/search";

const client = new Search({ url: process.env.UPSTASH_SEARCH_REST_URL, token: process.env.UPSTASH_SEARCH_REST_TOKEN });
const index = client.index("my-index");

await index.upsert({ id: "1", content: { text: "hello world" } });
const results = await index.search({ query: "hello" });
```

Basic steps:
- Create an index
- Insert or update documents
- Run searches or filtered queries

## Other Skill Files

### sdk-overview
Provides detailed documentation for all TypeScript SDK commands. Includes:
- delete: Deleting documents
- fetch: Retrieving a document
- info: Index info
- range: Range queries
- reset: Clearing an index
- search: Search queries
- upsert: Adding/updating documents
- getting-started: Setup steps for the SDK

### quick-start
Provides a fast, end-to-end workflow for creating a Search database, adding documents, and querying them. Covers essential concepts including:
- Creating a database and storing credentials
- Adding documents with content and metadata
- Understanding content vs metadata (searchability and filterability)
- Performing searches with optional reranking
- Filtering syntax with SQL-like or structured filters
- Common pitfalls and best practices
