This documentation explains how to use `serve()` to expose workflows as HTTP endpoints.

## Core Concept

`serve()` turns an async route function into a workflow endpoint. When a request arrives, a workflow run is created, and the route function defines the execution logic using `context.run()`.

### Full Example With Inline Comments

```typescript
import { serve } from "@upstash/workflow/nextjs";
import { z } from "zod";
import { Client, Receiver } from "@upstash/qstash";
import { loggingMiddleware } from "@upstash/workflow";

type InitialPayload = { foo: string; bar: number };

const payloadSchema = z.object({ foo: z.string(), bar: z.number() });

export const { POST } = serve<InitialPayload>(
  async (context) => {
    const payload = context.requestPayload;
    await context.run("step-1", async () => `hello ${payload.foo}`);
  },
  {
    // Runs when the workflow fails after all retries
    failureFunction: async ({ context, failStatus, failResponse, failHeaders, failStack }) =>
      console.error(failResponse),

    // Hooks for step lifecycle, run lifecycle, and debug events
    middlewares: [loggingMiddleware],

    // Manually parse the initial request payload before workflow execution
    initialPayloadParser: (raw) => JSON.parse(raw),

    // Automatically validate + parse the request payload using Zod
    schema: payloadSchema,

    // Override the full URL used to schedule subsequent workflow steps
    url: "https://myapp.com/api/workflow",

    // Override only the base portion of the inferred URL (keeps the route path)
    baseUrl: "https://proxy-url.com",

    // Provide a custom QStash client
    qstashClient: new Client({ token: process.env.QSTASH_TOKEN! }),

    // Provide a custom QStash Receiver for verifying that requests come from QStash
    receiver: new Receiver({
      currentSigningKey: process.env.QSTASH_CURRENT_SIGNING_KEY!,
      nextSigningKey: process.env.QSTASH_NEXT_SIGNING_KEY!,
    }),

    // Override environment variables available inside workflow execution
    env: {
      QSTASH_URL: "https://qstash.upstash.io",
      QSTASH_TOKEN: process.env.QSTASH_TOKEN!,
    },

    // Output detailed execution logs to stdout
    verbose: true,

    // Disable anonymous telemetry for this workflow endpoint
    disableTelemetry: true,
  }
);
```

## Common Pitfalls

- **Incorrect URL inference** behind proxies or local tunnels—set `url` or `baseUrl`.
