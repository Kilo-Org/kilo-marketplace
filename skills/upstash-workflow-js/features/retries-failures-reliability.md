# Workflow Reliability Features

This documentation provides a consolidated reference for reliability mechanisms in Upstash Workflow, focusing on retries, failure handling, and the Dead Letter Queue (DLQ). It is optimized for AI‑driven execution but remains clear for developers.

---

## Core Reliability Concepts

Upstash Workflow ensures that workflow runs are durable, recoverable, and traceable. Reliability is achieved through:

- Automatic retries for transient failures
- Failure handling via `failureFunction` or `failureUrl`
- DLQ for storing permanently failed runs
- Manual recovery actions: restart, resume, rerun failure function
- Mechanisms to prevent retries when failure is intentional

These mechanisms work together to guarantee that no failed execution is lost and that failures can be observed and handled.

---

## Automatic Retries

Workflow steps automatically retry when they fail, using configurable retry count and delay.

### Retry Parameters

- `retries`: How many times the step will retry
- `retryDelay`: A math expression (string) returning delay in milliseconds; can use `retried` variable

### Common Pitfalls

- The delay expression must be a _string_; raw numbers disable dynamic calculation.
- A workflow only moves to DLQ after **all** retries fail.

### Example: Configure Retry Count + Delay

```ts
import { Client, WorkflowNonRetryableError, serve } from "@upstash/workflow";

// Trigger with custom retry settings
const client = new Client({ token: process.env.WORKFLOW_TOKEN! });
await client.trigger({
  url: "https://example.com/workflow",
  retries: 5,
  retryDelay: "(1 + retried) * 2000", // 2s, 4s, 6s...
});

// Workflow with steps that may intentionally skip retries
export const { POST } = serve(async (context) => {
  const shouldFail = await context.run("check", () => true);

  if (shouldFail) {
    // Skips retry cycle and sends directly to failure handling
    throw new WorkflowNonRetryableError("Bad state");
  }

  await context.run("process", () => doWork());
});
```

---

## Preventing Retries

### When to Stop Retries

Use these when failure is expected or should halt execution immediately:

- `WorkflowNonRetryableError` → Fail fast, trigger failure function, enter DLQ
- `context.cancel()` → Stop workflow intentionally, no DLQ, no failure function
- Conditional returns → Graceful early exit without error

### Pitfalls

- `context.cancel()` marks the run as **canceled**, not failed — no failure handling executes.
- Throwing any error _other than_ `WorkflowNonRetryableError` will still trigger retries.

---

## Failure Handling

You can handle workflow failures using either:

- `failureFunction` (runs in your workflow environment)
- `failureUrl` (external callback endpoint)

Only **one** can be configured — they are mutually exclusive.

### Failure Function Behavior

- Runs after all retries fail
- Receives failure metadata and workflow context
- Cannot create new workflow steps; `context` is read‑only
- Is retried if it fails
- Can be manually retried from the DLQ

### Failure Function Parameters

- `context.workflowRunId`
- `context.url`
- `context.requestPayload`
- `context.headers`
- `context.env`
- `failStatus`
- `failResponse`
- `failHeaders`

### Example: Workflow + Failure Function + Prevent‑Retry Logic

```ts
export const { POST } = serve(
  async (context) => {
    const ok = await context.run("verify", () => verifySomething());

    if (!ok) {
      throw new WorkflowNonRetryableError("Verification failed");
    }

    const shouldAbort = await context.run("check", () => false);
    if (shouldAbort) {
      await context.cancel();
      return;
    }

    await context.run("execute", () => doWork());
  },
  {
    failureFunction: async ({ context, failStatus, failResponse }) => {
      // Logging / cleanup / alerts
      await logFailure(context.workflowRunId, failStatus, failResponse);
    },
  }
);
```

---

## Dead Letter Queue (DLQ)

A workflow enters the DLQ when:

- A step fails _after all retries_
- A `WorkflowNonRetryableError` is thrown
- `failureFunction` also fails (visible as failed in DLQ)

### Retention

- Free: 3 days
- Pay‑as‑you‑go: 1 week
- Fixed: Up to 3 months

After retention expires, items cannot be recovered.

---

## DLQ Recovery Actions

You may perform these actions from the dashboard or programmatically.

### 1. Resume

Continue from the failed step while keeping previous step results.

### 2. Restart

Start the entire workflow from scratch, discarding previous results.

### 3. Rerun Failure Function

Retry the failure handler **only if it previously failed**.

### Example: All DLQ Actions

```ts
import { Client } from "@upstash/workflow";
const client = new Client({ token: process.env.WORKFLOW_TOKEN! });

await client.dlq.resume({ dlqId: "dlq-1", retries: 3 }); // Continue run
await client.dlq.restart({ dlqId: "dlq-2", retries: 3 }); // Restart
await client.dlq.retryFailureFunction({ dlqId: "dlq-3" }); // Retry failure handler
```

### Pitfalls

- `retryFailureFunction` is only allowed when the failure function failed.
- `resume` cannot be used if workflow code changed before the failure point.
- `restart` re-executes everything, including expensive steps.

---

## Failure URL (Advanced Option)

Use when failure must be handled by a separate service.

### Notes

- Use **either** `failureFunction` **or** `failureUrl`.
- Recommended only when your primary app might be offline.
- Failure URL receives a structured JSON payload about the failed request.

### Example

```ts
export const { POST } = serve(
  async (context) => {
    await context.run("work", () => doWork());
  },
  {
    failureUrl: "https://example.com/failure-handler",
  }
);
```

---

## Debugging Failed Runs

DLQ entries store:

- Request + response headers
- Payloads
- Failure metadata
- Failure function state

Use the dashboard filters (workflow run ID, URL, failure function state) to identify and debug root causes.

---

## Summary

This skill unifies all Workflow reliability controls:

- Retries (automatic, configurable)
- Failure handling (`failureFunction`, `failureUrl`)
- DLQ retention + recovery
- Fast‑fail mechanisms (`WorkflowNonRetryableError`, `cancel`, conditional exits)
- Manual recovery operations (resume, restart, retry failure function)

Together these features ensure workflows are resilient, debuggable, and recoverable under all failure scenarios.
