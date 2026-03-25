---
name: vercel-react-best-practices
description: "Applies Vercel Engineering's 62 React and Next.js performance optimization rules across 8 priority categories — from eliminating async waterfalls and reducing bundle size to server-side caching and re-render prevention. Use when writing, reviewing, or refactoring React/Next.js components, pages, data fetching, or bundle optimization."
license: MIT
metadata:
  author: vercel
  version: 1.0.0
  category: development
  source:
    repository: 'https://github.com/vercel-labs/agent-skills'
    path: skills/react-best-practices
---

# Vercel React Best Practices

62 performance optimization rules for React and Next.js, organized by impact priority. Each rule has a detailed file in `rules/` with explanations and code examples. The full compiled guide is in `AGENTS.md`.

## Rule Categories by Priority

| Priority | Category | Impact | Prefix | Key rules |
|----------|----------|--------|--------|-----------|
| 1 | Eliminating Waterfalls | CRITICAL | `async-` | `Promise.all()` for independent ops, defer `await` into branches, Suspense streaming |
| 2 | Bundle Size | CRITICAL | `bundle-` | Direct imports (no barrel files), `next/dynamic` for heavy components, defer third-party scripts |
| 3 | Server-Side Performance | HIGH | `server-` | `React.cache()` deduplication, LRU cross-request cache, parallel fetching, `after()` for non-blocking ops |
| 4 | Client-Side Data Fetching | MEDIUM-HIGH | `client-` | SWR deduplication, passive event listeners, versioned localStorage |
| 5 | Re-render Optimization | MEDIUM | `rerender-` | Defer reads, memoize expensive components, functional `setState`, no inline component definitions |
| 6 | Rendering Performance | MEDIUM | `rendering-` | `content-visibility` for long lists, hoist static JSX, conditional render with ternary, resource hints |
| 7 | JavaScript Performance | LOW-MEDIUM | `js-` | Map/Set for O(1) lookups, combine iterations, cache property access, early exits |
| 8 | Advanced Patterns | LOW | `advanced-` | Event handler refs, `useLatest` for stable callbacks, one-time initialization |

## How to Use

Read individual rule files for detailed explanations and before/after code examples:

```
rules/async-parallel.md
rules/bundle-barrel-imports.md
rules/rerender-memo.md
```

Each rule file contains: why it matters, incorrect code with explanation, correct code with explanation, and additional context.

For the complete guide with all rules expanded, see `AGENTS.md`.
