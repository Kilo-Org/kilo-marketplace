# Flow Control

Flow Control defines how many workflow steps may run or start within a given time, ensuring predictable load and preventing overload of internal or third‑party systems. It applies per **flow control key**, allowing steps across different workflow runs to share the same limits.

This skill documents:

- parallelism
- rate and period
- monitoring
- common behaviors and pitfalls

## Core Concepts

### Flow Control Key

A string identifier grouping related workflow steps under shared limits.
All steps triggered with the same key share the same concurrency and rate budget.

```ts
const client = new Client({ token: "<QSTASH_TOKEN>" });

await client.trigger({
  url: "https://<YOUR_ENDPOINT>",
  flowControl: {
    key: "user-onboarding", // Groups steps under this key
    parallelism: 5, // max concurrent steps
    rate: 20, // max starts per period
    period: "1m", // time window
  },
});
```

## Parallelism

Controls **how many steps may run concurrently**.
Works like a token bucket: each running step consumes one token; when it finishes, the token is released.

- If tokens are available → step starts immediately.
- If no tokens → step enters the waitlist.
- Token handoff is **not FIFO**; later steps may start earlier.

### Example Behavior

- `parallelism = 3` → at most 3 steps run at the same time.
- Step 4 waits until one of the first 3 completes.

Parallelism affects **execution concurrency**, not rate‑of‑start per time window.

## Rate & Period

Controls **how many steps may START within a defined time window**.

```ts
flowControl: {
  key: "billing-jobs",
  rate: 2,           // allow 2 starts
  period: "10s",    // every 10 seconds
  parallelism: 1,    // can be combined
}
```

Behavior:

- First `rate` steps in each period start immediately.
- Additional steps wait until the next window.
- Execution duration **does not** count toward the period; only start time matters.

This is rate limiting, not concurrency control.

## Combining Rate + Parallelism

Both limits apply **independently**.
A step must satisfy _both_ to run.

Example:

- `rate = 3 per minute`
- `parallelism = 7`

Even if concurrency slots are free, steps may be delayed by the rate window.
Even if rate window is open, steps may be delayed by concurrency.

This enables predictable load patterns.

## Monitoring

Flow control queues and waitlists are visible from:

- Console → **FlowControl** tab (waitlist size per key)
- REST API:
  - List all keys
  - Get details for one key

Useful for diagnosing bottlenecks, long queues, or misconfigured limits.

## Important Behaviors & Pitfalls

### Limits are stored on each step

If you deploy new limits, previously published steps keep their original configuration.

### No per‑step config (mostly)

All steps inherit the workflow‑run’s flowControl block.
Exceptions:

- `context.call` – may define a separate key to isolate API throttling.
- `context.invoke` – spawns a new workflow run with its own flowControl.

To isolate heavy or sensitive steps, move them into a separate workflow and invoke them.

### Waitlist order is not guaranteed

A later step may receive a token before an earlier one.
Do not rely on ordering.

### Queueing is automatic

Exceeding limits never rejects steps. Everything is eventually executed.

## Full Example

Demonstrates defining all parameters together and how they interact.

```ts
import { Client } from "@upstash/workflow";

const client = new Client({ token: "<QSTASH_TOKEN>" });

await client.trigger({
  url: "https://<YOUR_WORKFLOW_ENDPOINT>/process",
  flowControl: {
    key: "media-processing", // Shared grouping key
    parallelism: 4, // Max 4 at the same time
    rate: 10, // Max 10 starts
    period: "60s", // in 60 seconds
  },
});
```

This configuration:

- ensures no more than 4 processing tasks run concurrently
- ensures no more than 10 tasks start per minute
- queues everything automatically beyond those limits
