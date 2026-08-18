# Workflow Troubleshooting (TypeScript)

This guide provides clear, TypeScript‑focused patterns for diagnosing and fixing common issues in Upstash Workflow. It highlights correct usage of core workflow features and shows how to avoid pitfalls that commonly occur in real applications.

---

## Steps Inside try/catch

Workflow steps (`context.run`, `context.sleep`, `context.sleepUntil`, `context.call`) intentionally throw `WorkflowAbort` after completing. Catching this error prevents the workflow engine from progressing.

**Correct pattern:** rethrow `WorkflowAbort` or avoid `try/catch` around steps.

```ts
import { WorkflowAbort } from "@upstash/workflow";

try {
  // Any step will throw WorkflowAbort
  const result = await context.run("step", () => "ok");
} catch (err) {
  if (err instanceof WorkflowAbort) throw err; // required
  // handle real errors
}
```

If you _must_ handle errors, move the `try/catch` into the function passed to `context.run`.

---

## requestPayload Becoming Undefined

During `context.call`, the workflow endpoint is invoked multiple times internally. Before the first step executes, `context.requestPayload` may appear `undefined`.

**Fix:** capture the payload via a step:

```ts
export const { POST } = serve(async (context) => {
  const payload = await context.run("get-payload", () => context.requestPayload);

  // payload remains stable even during context.call
  await context.call("my-call", {
    url: "https://example.com",
    body: payload,
  });
});
```

**Header considerations:** When triggering workflows, ensure payload‑friendly headers like:

- `Content-Type: text/plain`
- `Content-Type: application/json`

---

## Signature Verification Failures

If QStash request verification fails:

- Ensure the workflow is triggered through QStash (`client.trigger` or publish)
- Verify `QSTASH_CURRENT_SIGNING_KEY` and `QSTASH_NEXT_SIGNING_KEY`
- Pass appropriate `Content-Type` headers when triggering

Error looks like:

```
Failed to verify that the Workflow request comes from QStash: ...
```

---

## Authorization Errors from Early Returns

If your workflow returns **before running any step**, the SDK interprets this as failed authorization:

```
HTTP 400 – Failed to authenticate Workflow request.
```

To safely perform non‑deterministic checks, wrap them in a step:

```ts
export const { POST } = serve(async (context) => {
  const shouldExit = await context.run("check-condition", () => Math.random() > 0.5);
  if (shouldExit) return;

  // remaining workflow
});
```

---

## Retry Configuration

Retries come from two locations:

- Workflow start (`client.trigger`): default **3**, applies to workflow steps
- `context.call`: default **0**
- `context.invoke`: default **0**

Use these in combination to tune behavior correctly.

---

## Verbose Mode Diagnostics

Enable verbose logging to debug rare edge cases:

```ts
serve(handler, { verbose: true });
```

Useful warnings include:

- Localhost in workflow URL
- Duplicate step execution
- Network response anomalies
- Parallel `context.call` race warnings

Each of these indicates environmental or routing issues rather than workflow logic problems.

---

## HTTPS Protocol Issues (Proxy Environments)

If deployed behind a proxy that downgrades HTTPS → HTTP (e.g., Railway), the SDK may infer the wrong protocol.

**Fix:** explicitly set:

```
UPSTASH_WORKFLOW_URL=https://your-deployment-url
```

---

## Workflow Stuck on First Step

If the first step appears stuck:

- Check step logs in the dashboard
- Ensure the endpoint URL is correct and reachable
- Verify SDK versions
- If inference is failing, explicitly set `baseUrl`:

```ts
serve(handler, { baseUrl: "https://your-url" });
```

---

## Non‑workflow Destination Error

Occurs when triggering a non‑workflow endpoint or using mismatched SDK versions.

```
detected a non-workflow destination for trigger/invoke
```

**Ensure:**

- The URL points to a `serve()` workflow endpoint
- Both caller and workflow endpoint use the latest SDK

---

## Vercel Preview Deployment Protection

Preview deployments block external requests unless bypassed.

**Steps:**

1. Create a bypass secret in Vercel → Deployment Protection
2. Add it to the QStash client + pass it when triggering

```ts
import { Client as QStash } from "@upstash/qstash";
import { serve } from "@upstash/workflow/nextjs";

export const { POST } = serve(
  async (context) => {
    // workflow logic
  },
  {
    qstashClient: new QStash({
      token: process.env.QSTASH_TOKEN!,
      headers: {
        "x-vercel-protection-bypass": process.env.VERCEL_AUTOMATION_BYPASS_SECRET!,
      },
    }),
  }
);

// Triggering
await client.trigger({
  url: "https://preview.vercel.app/workflow",
  headers: {
    "x-vercel-protection-bypass": process.env.VERCEL_AUTOMATION_BYPASS_SECRET!,
  },
  body: "hello",
});
```

Both trigger header and client header are required.
