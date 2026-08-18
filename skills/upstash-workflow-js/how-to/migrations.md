# Migration Guide for Upstash Workflow (TypeScript)

This document provides a clear, task-focused overview of migrations between Workflow versions. It highlights breaking changes, how to update your code, and common pitfalls to avoid. Code samples combine multiple parameters in each example to reduce redundancy.

## January 2026 – Major Release 1.0.0

### Agents API → moved to a separate package

The Agents API was removed from the core workflow package and placed into `@upstash/workflow-agents` so the base SDK no longer depends on large AI-related libraries.

**Key changes**:

- Must install and import `agentWorkflow` from the new package.
- Agents access now happens through an `agents` helper created per workflow invocation.

```ts
// Before
import { serve } from "@upstash/workflow/nextjs";
export const { POST } = serve(async (context) => {
  const model = context.agents.openai("gpt-3.5-turbo");
  const agent = context.agents.agent({
    /* ... */
  });
  const task = context.agents.task({
    /* ... */
  });
});

// After
import { serve } from "@upstash/workflow/nextjs";
import { agentWorkflow } from "@upstash/workflow-agents";
export const { POST } = serve(async (context) => {
  const agents = agentWorkflow(context);
  const model = agents.openai("gpt-3.5-turbo");
  const agent = agents.agent({
    /* ... */
  });
  const task = agents.task({
    /* ... */
  });
});
```

---

### `keepTriggerConfig` and `useFailureFunction` removed

These fields were redundant—both behaviors are now always enabled.

```ts
// Before
await client.trigger({
  url: "...",
  retries: 3,
  keepTriggerConfig: true,
  useFailureFunction: true,
});

// After
await client.trigger({ url: "...", retries: 3 });
```

---

### Configuration moved from `serve()` → `client.trigger()`

Options such as `retries`, `flowControl`, `retryDelay`, and `failureUrl` no longer belong in `serve()`.

```ts
// Before
export const { POST } = serve(
  async (context) => {
    /* ... */
  },
  {
    retries: 3,
    retryDelay: "1000 * (1 + retried)",
    flowControl: { key: "my-key", rate: 10 },
  }
);
await client.trigger({ url: "..." });

// After
export const { POST } = serve(async (context) => {
  /* ... */
});
await client.trigger({
  url: "...",
  retries: 3,
  retryDelay: "1000 * (1 + retried)",
  flowControl: { key: "my-key", rate: 10 },
});
```

---

### `stringifyBody` removed from `context.call` and `context.invoke`

Bodies must now be strings.

```ts
// Before
await context.call("step", {
  url: "https://api.example.com",
  method: "POST",
  body: { key: "value" },
  stringifyBody: true,
});

// After
await context.call("step", {
  url: "https://api.example.com",
  method: "POST",
  body: JSON.stringify({ key: "value" }),
});

// Same change applies to invoke
await context.invoke("other", {
  workflow: otherWorkflow,
  body: JSON.stringify({ key: "value" }),
});
```

---

### Logger removed → middleware system added

Removed `WorkflowLogger` class and added `WorkflowMiddleware`. Updated `verbose` param to only allow `true` (in this case, `loggingMiddleware` will be used which prints to console).

```ts
import { loggingMiddleware, WorkflowMiddleware } from "@upstash/workflow";

const stepFinish = new WorkflowMiddleware({
  name: "step-finish",
  callbacks: {
    afterExecution: async ({ stepName, result }) =>
      console.log(`Step ${stepName} finished`, result),
  },
});

export const { POST } = serve(
  async (context) => {
    /* ... */
  },
  {
    middlewares: [loggingMiddleware, stepFinish],
  }
);
```

---

## October 2024 – Migration from `@upstash/qstash`

### Install the new package

Replace all workflow usage from `@upstash/qstash` with `@upstash/workflow`.

### Serve import and return shape changed

Most environments now require destructuring `{ POST }`.

```ts
// Before
import { serve } from "@upstash/qstash/nextjs";
export const POST = serve(...);

// After
import { serve } from "@upstash/workflow/nextjs";
export const { POST } = serve(...);
```

### `context.call` updated

Now returns `{ status, headers, body }` and **does not fail** the workflow if the HTTP call fails.

```ts
const { status, headers, body } = await context.call("call-step", {
  url: "https://example.com/api",
  method: "POST",
});
```

**Pitfall**: Old runs may not contain `status` or `headers` until fully migrated.

### Errors renamed

- `QStashWorkflowError` → `WorkflowError`
- `QStashWorkflowAbort` → `WorkflowAbort`

---

## Summary of Common Mistakes

- Using `context.agents` instead of the new `agentWorkflow()` helper.
- Leaving old serve-config options (`retries`, `flowControl`, etc.).
- Forgetting to `JSON.stringify` bodies.
- Assuming `context.call` failures stop workflow execution.
- Mix-and-matching `@upstash/qstash` and `@upstash/workflow` imports.

This guide ensures smooth migration with minimal friction while highlighting where behavioral changes may break existing workflows.
