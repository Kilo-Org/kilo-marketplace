# Workflow Client Basics

This skill provides guidance for using the Workflow Client to trigger, cancel, inspect, resume, and manage workflow runs. It focuses on TypeScript usage patterns, argument structures, and common pitfalls.

---

## Core Operations

### Triggering Workflow Runs (`client.trigger`)

Starts one or multiple workflow runs with optional payload, metadata, retry logic, and flow control.

```ts
// Single and multiple triggers
const single = await client.trigger({
  url: "https://your-endpoint/workflow", // required
  body: { msg: "hello" }, // optional payload
  headers: { "x-user": "123" }, // optional headers
  workflowRunId: "custom-id", // custom unique identifier
  retries: 3, // retry count for steps
  retryDelay: "1000 * (1 + retried)", // expression-based retry delay
  delay: "10s", // start later
  notBefore: Math.floor(Date.now() / 1000) + 60, // absolute schedule
  label: "my-run", // dashboard filtering
  disableTelemetry: true, // opt‑out telemetry
  flowControl: {
    // concurrency & rate limiting
    key: "user-key",
    rate: 10,
    parallelism: 5,
    period: "10m",
  },
});

const multiple = await client.trigger([
  { url: "https://api/runA", body: { a: 1 } },
  { url: "https://api/runB", retries: 5 },
]);
```

**Pitfalls**:

- `workflowRunId` must be unique; collisions cause errors.
- `delay` is ignored if `notBefore` is provided.
- Using `url` incorrectly (missing protocol or dynamic segments) leads to invalid workflow endpoints.

---

### Canceling Workflow Runs (`client.cancel`)

Cancel runs by ID, by URL prefix, or all active/pending runs.

```ts
await client.cancel({ ids: ["wfr_123", "wfr_456"] });
await client.cancel({ urlStartingWith: "https://your-endpoint.com" });
await client.cancel({ all: true });
```

- `ids` accepts both string and array, but mixing with other filters is not supported.
- `urlStartingWith` cancels _all_ descendant paths—use carefully.

---

### Retrieving Logs (`client.logs`)

Fetch workflow execution logs with filtering and cursor-based pagination.

```ts
const { runs, cursor } = await client.logs({
  workflowRunId: "wfr_123", // filter a specific run
  workflowUrl: "https://endpoint", // fetch logs for an endpoint
  state: "RUN_FAILED", // filter by execution state
  count: 50, // limit return size
  workflowCreatedAt: 1700000000, // Unix timestamp
  cursor: undefined, // pagination
});
```

---

### Notifying Events (`client.notify`)

Notify workflows paused at `context.waitForEvent`.

```ts
await client.notify({
  eventId: "order-paid",
  eventData: { orderId: 1 }, // delivered to waiting workflow
});
```

**Pitfall**: If no workflow is waiting, no error is thrown.

---

### Fetching Waiting Workflows (`client.getWaiters`)

Retrieve active waiters waiting for a specific event.

```ts
const waiters = await client.getWaiters({ eventId: "order-paid" });
```

This is useful for debugging or coordinating external signals.

---

## Dead Letter Queue (DLQ) Operations

### Listing DLQ Messages (`client.dlq.list`)

```ts
const { messages, cursor } = await client.dlq.list({
  cursor,
  count: 20,
  filter: {
    fromDate: Date.now() - 86400000,
    toDate: Date.now(),
    url: "https://your-endpoint.com",
    responseStatus: 500,
  },
});
```

- Date fields use Unix **ms**, not seconds.

---

### Retry Failure Callback (`client.dlq.retryFailureFunction`)

If a workflow's `failureFunction`/`failureUrl` call failed:

```ts
await client.dlq.retryFailureFunction({ dlqId: "dlq-123" });
```

---

### Restarting DLQ Runs (`client.dlq.restart`)

Restart from the **beginning** of the workflow.

```ts
await client.dlq.restart({
  dlqId: ["dlq-1", "dlq-2"],
  retries: 5,
  flowControl: {
    key: "restart-group",
    parallelism: 10,
  },
});
```

---

### Resuming DLQ Runs (`client.dlq.resume`)

Continue from the **failed step**.

```ts
await client.dlq.resume({
  dlqId: "dlq-123",
  retries: 3,
  flowControl: {
    key: "resume-group",
    rate: 5,
  },
});
```

**Common confusion**:

- `restart` = new run from step 0.
- `resume` = same run continues at the failed step.

---

## General Tips for TS Consumers

- Use flow control when bulk‑triggering or restarting large batches to avoid rate limits.
