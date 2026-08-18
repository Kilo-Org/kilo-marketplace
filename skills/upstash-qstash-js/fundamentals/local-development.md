# Local Development

Use the QStash dev server to test publishing and signature verification end-to-end on your machine — no public tunnel, no real QStash account, no real signing keys.

## Automatic dev server (recommended)

Pass `devMode: true` to the `Client` (and the matching verifier). The SDK will download the QStash CLI binary, start it, and wire credentials for you.

```typescript
import { Client } from "@upstash/qstash";

const client = new Client({ devMode: true });

await client.publishJSON({
  url: "https://example.com/webhook",
  body: { hello: "world" },
});
```

When `devMode` is on:

- The SDK downloads the latest `qstash` binary on first use, caches it under the OS cache directory, and reuses it across projects.
- Spawns the dev server on port `8080` (override via `QSTASH_DEV_PORT`).
- Reuses an already-running server on the configured port instead of spawning a duplicate.
- Injects deterministic dev `baseUrl`, `token`, and signing keys. **Any explicit `token` / `baseUrl` / signing keys you pass are ignored** (a warning is printed). To use real credentials, set `devMode: false`.
- Forwards dev server logs to stdout/stderr with a dim `[QStash CLI]` prefix.
- No-ops in production (`NODE_ENV=production`), during `next build`, and in browser/edge runtimes.

### Environment variable

Instead of hard-coding `devMode: true`, leave the option unset and toggle via env:

```bash
QSTASH_DEV=true       # or "1"
QSTASH_DEV_PORT=8080  # optional, default 8080
```

The resolution order is: explicit `devMode` boolean > `QSTASH_DEV` env var > off. Use this so production code never accidentally turns the dev server on.

### Verifying signatures in dev

The receiving side also needs `devMode: true` so it verifies against the dev server's deterministic signing keys instead of your real ones.

```typescript
import { Receiver } from "@upstash/qstash";

const receiver = new Receiver({ devMode: true });

await receiver.verify({
  signature: request.headers.get("upstash-signature")!,
  body: await request.text(),
});
```

For Next.js, the wrappers accept the same flag:

```typescript
// app/api/webhook/route.ts
import { verifySignatureAppRouter } from "@upstash/qstash/nextjs";

export const POST = verifySignatureAppRouter(
  async (request) => new Response("ok"),
  { devMode: true }
);
```

### Next.js: starting the server before edge routes

Edge runtimes cannot spawn child processes. If a route in the Edge Runtime is the first thing to use QStash, the SDK can only check whether the server is reachable — it cannot start it. Call `registerQStashDev()` from `instrumentation.ts` to spawn the server during Next.js startup, before any request hits:

```typescript
// instrumentation.ts
import { registerQStashDev } from "@upstash/qstash/nextjs";

export function register() {
  registerQStashDev();
}
```

`registerQStashDev` is itself a no-op in production and during `next build`.

### Common pitfalls

- **Passing `token` alongside `devMode: true`** — the explicit token is ignored and you get a console warning. Drop the `token` field, or set `devMode: false` to use it.
- **Hitting build-time errors in `next build`** — if a route module is evaluated at build time and instantiates the `Client`, mark the route `export const dynamic = "force-dynamic"` so it isn't pre-rendered.
- **Port 8080 already in use** — the SDK errors with a clear message; either stop the other process or set `QSTASH_DEV_PORT` to a free port (matched on both client and receiver sides).
- **Calling QStash from an edge route without `instrumentation.ts`** — the edge runtime can't spawn the binary. Either move the call to a Node-runtime route or wire `registerQStashDev()` as shown above.

## Manual dev server

If you cannot use the automatic flow (non-Node runtime, CI without internet, custom binary), run the CLI yourself:

```bash
npx @upstash/qstash-cli dev
```

Then construct the client with the printed dev credentials explicitly and **leave `devMode` unset/false**:

```typescript
const client = new Client({
  baseUrl: "http://127.0.0.1:8080",
  token: "eyJVc2VySUQiOiJkZWZhdWx0VXNlciIsIlBhc3N3b3JkIjoiZGVmYXVsdFBhc3N3b3JkIn0=",
});
```

See the [Local Development docs](https://upstash.com/docs/qstash/howto/local-development) for the full list of test users and CLI options.
