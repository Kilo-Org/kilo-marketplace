# Workflow Invocation

This documentation covers how to invoke one workflow from another using `context.invoke`, along with how to define and expose multiple workflows using `createWorkflow` and `serveMany`.

---

## Invoking Another Workflow

A workflow can start another workflow run and wait for it to finish before continuing. This enables orchestration and dependency chains across workflows.

Use `context.invoke` to trigger another workflow:

```ts
const result = await context.invoke("analyze content", {
  workflow: analyzeContent, // workflow object or function
  body: "input payload", // request body passed to invoked workflow
  headers: { "x-user": "123" }, // optional headers
  retries: 5, // optional, default 3
  flowControl: {
    /* ... */
  },
  workflowRunId: "optional-custom-id",
});

const {
  body, // response returned by invoked workflow
  isFailed, // true if invoked workflow failed
  isCanceled, // true if invoked workflow was canceled
} = result;
```

### Returning a Value

A workflow may return any serializable value, which becomes `body` for the caller.

### Depth Limitation

Workflow invocation depth is limited to 100. Any recursive or cyclic chain exceeding this will fail.

---

## Defining Workflows Without Exposing Endpoints

Use `createWorkflow` to define workflows as objects. These are not automatically exposed as HTTP endpoints.

```ts
const analyzeContent = createWorkflow(async (context) => {
  await context.sleep("delay", 1);
  return { message: "processed" };
});

const processUser = createWorkflow(async (context) => {
  const { body } = await context.invoke("invoke analyze", {
    workflow: analyzeContent, // type‑safe invocation
    body: "user-1",
  });

  return { result: body };
});
```

---

## Exposing Multiple Workflows With `serveMany`

To allow workflows to invoke each other without requiring explicit URLs, define all related workflows under a shared parent path.

```ts
// app/workflows/[...any]/route.ts
export const { POST } = serveMany({
  analyze: analyzeContent,
  process: processUser,
});
```

- Keys become route names.
- All workflows that need to invoke each other must appear in the same `serveMany` call.
- Requests are routed based on the key names.

### Triggering a Workflow

```ts
import { Client } from "@upstash/workflow";

const client = new Client({ token: "<QSTASH_TOKEN>" });

await client.trigger({
  url: "https://your-app/workflows/analyze",
});
```

---

## Common Pitfalls

- **Missing workflow in `serveMany`**: If a workflow invokes another that was not included in the same `serveMany` definition, the call will fail.
- **Infinite invocation loops**: Depth limit of 100 prevents runaway recursive chains.
