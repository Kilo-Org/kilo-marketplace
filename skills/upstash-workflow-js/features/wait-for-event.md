# Wait for Event

Use this feature to pause workflow execution until an external event arrives. It allows building asynchronous, event‑driven workflows without holding compute resources.

---

## How It Works

`context.waitForEvent()` suspends the workflow and registers a waiter under an event ID. When a matching `notify` call is sent, the workflow resumes with the provided event data.

• Each waiter has a timeout. If the event does not arrive in time, the workflow continues with `{ timeout: true }`.
• Maximum timeout depends on your pricing tier.
• Multiple workflow runs may wait on the same event ID; a notify call resumes all of them.

---

## Key Concepts & Pitfalls

### Event IDs

Use unique event IDs to avoid heavy fan‑out notifications.

Example patterns:
• `order-123-processing-complete`
• `user-42-email-verified`

### Race Conditions

A notify call sent _before_ the workflow begins waiting is lost.

To avoid this:
• Always inspect the notify response.
• Retry if no waiters were found.

---

## Combined Example

Below is a single TypeScript example showing waiting for an event, handling timeouts, and safely notifying:

```ts
import { serve } from "@upstash/workflow/nextjs";
import { Client } from "@upstash/workflow";

// Workflow that waits for an event
export const { POST } = serve(async (context) => {
  const { orderId } = context.requestPayload;
  const eventId = `order-${orderId}-processed`;

  // Wait for the event with timeout
  const { eventData, timeout } = await context.waitForEvent(
    "wait-for-order-processing", // step name
    eventId, // event id
    {
      timeout: "1d", // optional timeout
    }
  );

  if (timeout) {
    // handle timeout here
    await context.run("timeout-handler", async () => {
      console.log("Order processing timed out");
    });
    return;
  }

  // Continue workflow using eventData
  await context.run("process-completed-order", async () => {
    console.log("Order processed:", eventData);
  });
});

// External notifier (safe retry pattern)
const client = new Client({ token: "<WORKFLOW_TOKEN>" });

async function notifyProcessingComplete(orderId: string, payload: any) {
  const eventId = `order-${orderId}-processed`;

  // First attempt - returns array of NotifyResponse
  const waiters = await client.notify({ eventId, eventData: payload });

  if (waiters > 0) return waiters;

  // Retry if no workflows were waiting
  await new Promise((r) => setTimeout(r, 3000));
  return await client.notify({ eventId, eventData: payload });
}
```

---

## Best Practices

• Generate event IDs that uniquely identify a specific workflow instance.
• Always handle the timeout case explicitly.
• On notification, check the returned array length to detect if any workflows were waiting.
• Prefer one event ID per workflow run to avoid notifying large groups.
