# Workflow Context Basics

This skill documents all workflow context functions available inside a TypeScript workflow. It focuses on how these APIs behave, how their parameters interact, and common pitfalls when composing them into reliable long‑running workflows.

---

## context.api

`context.api` provides typed integrations for OpenAI, Anthropic, and Resend. These calls behave like `context.call` but enforce the correct operation names and body types.

### Key points

- Each provider exposes a `.call(stepName, config)` function.
- `token` is always required.
- The `operation` field selects the API method.
- `body` must match the provider's type definitions.
- Returns `{ status, body }`.

### Example (combined)

```ts
// OpenAI + Anthropic + Resend usage
const openai = await context.api.openai.call("openai chat", {
  token: process.env.OPENAI_API_KEY!,
  operation: "chat.completions.create",
  body: {
    model: "gpt-4o",
    messages: [
      { role: "system", content: "Hello" },
      { role: "user", content: "Hi" },
    ],
  },
});

const anthropic = await context.api.anthropic.call("anthropic message", {
  token: process.env.ANTHROPIC_API_KEY!,
  operation: "messages.create",
  body: {
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 1024,
    messages: [{ role: "user", content: "Hello" }],
  },
});

// Resend email
const email = await context.api.resend.call("send email", {
  token: process.env.RESEND_API_KEY!,
  headers: { "content-type": "application/json" },
  body: {
    from: "Acme <onboarding@resend.dev>",
    to: ["someone@example.com"],
    subject: "Welcome",
    html: "<p>Hi!</p>",
  },
});
```

---

## context.call

Performs an HTTP request with long execution windows (up to 12 hours). Always returns a response, even for non‑2xx status codes.

### Important parameters

- `url`: required.
- `method`: defaults to `GET`.
- `headers`: object.
- `body`: body as string.
- `retries`: number of retry attempts.
- `retryDelay`: retry delay expression as string or number (in milliseconds).
- `flowControl`: throttling config.
- `timeout`: seconds for each attempt.
- `workflow`: used only when invoking a workflow inside `serveMany`.

### Example (showing most fields)

```ts
const response = await context.call("sync user", {
  url: "https://api.example.com/user",
  method: "POST",
  headers: { authorization: `Bearer ${process.env.TOKEN}` },
  body: JSON.stringify({ id: userId, name }),
  retries: 3,
  retryDelay: "pow(2, retried)", // exponential
  timeout: 20,
  flowControl: {
    key: "user-sync",
    rate: 5,
    parallelism: 2,
  },
});
```

### Pitfalls

- Localhost requests fail unless tunneled.

---

## context.cancel

Cancels the current workflow run.

- Workflow is marked **canceled**, not failed.
- `failureFunction` does not run.
- No DLQ entry.

### Example

```ts
const result = await context.run("check something", () => ...);
if (result.cancel) await context.cancel();
```

---

## context.createWebhook

Creates a reusable webhook URL for external systems.

### Example

```ts
const { webhookUrl, eventId } = await context.createWebhook("create webhook");
// Use webhookUrl with an external service
```

---

## context.invoke

Invokes another workflow (must be served under the same `serveMany`) and waits for its completion.

### Key parameters

- `workflow`: the workflow definition.
- `body`: becomes `requestPayload` of invoked workflow.
- `headers`: forwarded headers.
- `workflowRunId`: optional override.
- `retries`, `retryDelay`, `flowControl`: control invocation retry strategy.

### Example

```ts
const { body, isFailed, isCanceled } = await context.invoke("invoke child", {
  workflow: childWorkflow,
  body: { id: 123 },
  headers: { foo: "bar" },
  retries: 2,
});
```

---

## context.notify

Notifies waiting workflows created via `context.waitForEvent`.

### Example

```ts
const { notifyResponse } = await context.notify("notify step", "order-updated", {
  status: "shipped",
});
```

`notifyResponse` lists all workflows resumed by this event.

---

## context.run

Runs custom synchronous or async logic as a step. Values must be JSON‑serializable.

### Example

```ts
const user = await context.run("load user", () => getUser());

await context.run("process user", () => process(user));

// Running in parallel
const a = context.run("step A", () => foo());
const b = context.run("step B", () => bar());
await Promise.all([a, b]);
```

### Pitfalls

- Returned class instances lose methods due to serialization. Rehydrate via `Object.assign(new Class(), data)`.

---

## context.sleep

Pauses workflow execution for a duration. String or numeric seconds.

### Example

```ts
await context.sleep("wait 1 day", "1d");
```

---

## context.sleepUntil

Pauses execution until a specific `Date`, timestamp, or parseable string.

### Example

```ts
const ts = new Date(Date.now() + 1000 * 60 * 60);
await context.sleepUntil("wait until", ts);
```

---

## context.waitForEvent

Waits for an event (triggered by `context.notify`) or until timeout.

### Example

```ts
const { eventData, timeout } = await context.waitForEvent("wait for update", "order-updated", {
  timeout: "2h",
});
```
