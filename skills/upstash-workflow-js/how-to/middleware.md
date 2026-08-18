# Middlewares

This guide explains how to intercept workflow lifecycle and debug events using middleware. It covers how to attach middlewares, define event handlers, initialize resources, and combine functionality into efficient implementations.

## Overview

Middlewares plug into the workflow engine and listen to:

- Lifecycle events such as run start, run completion, and step execution
- Debug messages such as errors, warnings, and informational logs

They are useful for logging, monitoring, instrumentation, and integrating with external systems.

## Using Built‑in Middleware

Add middleware inside the `middlewares` array when serving a workflow:

```ts
import { serve } from "@upstash/workflow/nextjs";
import { loggingMiddleware } from "@upstash/workflow";

export const { POST } = serve(
  async (ctx) => {
    await ctx.run("step-1", () => "Hello World");
  },
  {
    middlewares: [loggingMiddleware], // emits run/step logs
  }
);
```

## Creating Custom Middleware

You define middleware by instantiating `WorkflowMiddleware` with callbacks for the events you want to handle.

### Direct Callback Definitions

All lifecycle and debug events can be defined in one object.

```ts
import { WorkflowMiddleware } from "@upstash/workflow";

const customMiddleware = new WorkflowMiddleware({
  name: "custom-logger",
  callbacks: {
    // Lifecycle events
    runStarted: async ({ context }) => {
      console.log(`Run ${context.workflowRunId} started`);
    },
    beforeExecution: async ({ context, stepName }) => {
      console.log(`→ Executing step: ${stepName}`);
    },
    afterExecution: async ({ context, stepName, result }) => {
      console.log(`✓ Step ${stepName} completed`, result);
    },
    runCompleted: async ({ context, result }) => {
      console.log(`Run ${context.workflowRunId} finished`, result);
    },

    // Debug events
    onError: async ({ workflowRunId, error }) => {
      console.error(`Error in ${workflowRunId}`, error);
    },
    onWarning: async ({ workflowRunId, warning }) => {
      console.warn(`Warning from ${workflowRunId}`, warning);
    },
    onInfo: async ({ workflowRunId, info }) => {
      console.info(`Info from ${workflowRunId}`, info);
    },
  },
});
```

### Initialization With `init`

Use `init` when you need setup logic (connecting to a DB, creating clients, loading configuration). `init` returns an object containing the callbacks.

```ts
import { WorkflowMiddleware } from "@upstash/workflow";

const databaseMiddleware = new WorkflowMiddleware({
  name: "database-logger",
  init: async () => {
    const db = await connectToDatabase();

    return {
      runStarted: async ({ context }) => {
        await db.insert({ workflowRunId: context.workflowRunId, status: "started" });
      },
      runCompleted: async ({ context, result }) => {
        await db.update({ workflowRunId: context.workflowRunId, status: "completed", result });
      },
      onError: async ({ workflowRunId, error }) => {
        await db.insert({ workflowRunId, level: "error", message: error.message });
      },
    };
  },
});
```

## Event Reference

Below is a concise list of supported event handlers and what they receive.

### Lifecycle

- **runStarted**: `{ context }`
- **beforeExecution**: `{ context, stepName }`
- **afterExecution**: `{ context, stepName, result }`
- **runCompleted**: `{ context, result }`

### Debug

- **onError**: `{ workflowRunId?, error }`
- **onWarning**: `{ workflowRunId?, warning }`
- **onInfo**: `{ workflowRunId?, info }`

## Combined Example

Single snippet showing typical usage patterns.

```ts
import { serve } from "@upstash/workflow/nextjs";
import { WorkflowMiddleware } from "@upstash/workflow";

// Error tracking
const errorTrackingMiddleware = new WorkflowMiddleware({
  name: "errors",
  callbacks: {
    onError: async ({ workflowRunId, error }) => {
      await fetch("https://monitoring/errors", {
        method: "POST",
        body: JSON.stringify({ workflowRunId, error: error.message }),
      });
    },
  },
});

// Performance measurement
const timings = new Map();
const performanceMiddleware = new WorkflowMiddleware({
  name: "perf",
  callbacks: {
    beforeExecution: ({ stepName }) => timings.set(stepName, Date.now()),
    afterExecution: ({ stepName }) => {
      const t = timings.get(stepName);
      if (t) console.log(`Step ${stepName} took ${Date.now() - t}ms`);
      timings.delete(stepName);
    },
  },
});

export const { POST } = serve(
  async (ctx) => {
    await ctx.run("task", () => "done");
  },
  {
    middlewares: [errorTrackingMiddleware, performanceMiddleware],
  }
);
```

## Pitfalls and Tips

- Ensure `init` returns all callbacks; missing keys simply mean the event is ignored.
- Debug events may be called without a `workflowRunId` if errors occur before run id is identified.
