## Webhooks

This skill teaches agents how to use webhooks inside Upstash Workflow to pause execution, wait for external callbacks, and resume reliably. It covers creation, waiting, validation, and multi-step usage.

---

### Key Concepts

• **Webhook URLs are unique per context.createWebhook() call**.
• **Workflow execution pauses** when calling `context.waitForWebhook()` until the webhook receives a request or times out.
• **Lookback protection** ensures the workflow still receives early webhook calls.
• **Workflows remain dormant** during the waiting period, avoiding compute cost.
• **Webhooks are ideal for third‑party APIs** that support callback URLs.

---

### Core Workflow: Create → Call External API → Wait → Resume

Below is a consolidated example showing:
• Creating a webhook
• Passing it to an external API
• Handling the callback
• Waiting for multiple updates
• Error/timeout handling

```ts
import { serve } from "@upstash/workflow/nextjs";

export const { POST } = serve(async (context) => {
  // Create a unique webhook for this workflow
  const webhook = await context.createWebhook("create webhook");

  // Trigger an external service, sending it the callback URL
  await context.call("trigger-external", {
    url: "https://api.example.com/process",
    method: "POST",
    body: { webhookUrl: webhook.webhookUrl },
  });

  // Loop: wait for progress updates until service signals completion
  let updates = [];
  while (true) {
    const res = await context.waitForWebhook(`wait update`, webhook, "5m");

    if (res.timeout) break; // no progress received

    const req = res.request;
    const payload = await req.json();
    updates.push(payload);

    if (req.headers.get("x-task-finished") === "true") break;
  }

  return updates;
});
```

---

### Webhook Reliability: Lookback Protection

**Common pitfall:** external systems may call the webhook _before_ the workflow reaches `waitForWebhook()`.

Upstash automatically stores early webhook calls. The next `waitForWebhook()` will immediately resolve with the stored request.

This avoids race conditions and eliminates the need for manual buffering.

---

### When to Use Webhooks vs. Wait for Event

Use **webhooks** when:
• integrating with third‑party APIs
• the external system invokes a callback URL
• you need race‑condition‑safe behavior

Use **Wait for Event** when:
• you control the notifying system and can use the Workflow Client
• you don't need lookback semantics
