---
name: upstash-workflow-js
description: >-
  Skills for the Upstash Workflow TypeScript/JavaScript SDK to define, trigger,
  and manage workflows. Use this Skill whenever a user wants to create workflow
  endpoints, run steps, or interact with the Upstash Workflow client.
metadata:
  category: development
  author: upstash
  source:
    repository: 'https://github.com/upstash/skills'
    path: skills/upstash-workflow-js
    license_path: LICENSE
    ref: main
    commit: fb4e6019638d5746b86a54f1bb7144dbb324480a
---

# Upstash Workflow SDK

## Quick Start

The Upstash Workflow SDK lets you expose serverless workflow endpoints and run them reliably using QStash under the hood.

Install:

```bash
npm install @upstash/workflow
```

Define a simple workflow endpoint:

```ts
import { serve } from "@upstash/workflow";

export const { POST } = serve(async (context) => {
  await context.run("step-1", () => console.log("step 1"));
  await context.run("step-2", () => console.log("step 2"));
});
```

Trigger it from your backend:

```ts
import { Client } from "@upstash/workflow";

const client = new Client({ token: process.env.QSTASH_TOKEN! });
await client.trigger({ url: "https://your-app.com/api/workflow" });
```

## Other Skill Files

These files contain the full documentation. Use them for details, patterns, and advanced behavior.

- basics:
  - **basics/serve** – How to expose workflow endpoints.
  - **basics/context** – Full API for workflow `context` (steps, waits, webhooks, events, invoke, etc.).
  - **basics/client** – Using the Workflow client to trigger, cancel, inspect, and notify runs.
- features:
  - **features/invoke** – Cross‑workflow invocation.
  - **features/reliability** – Retries, failure callbacks, and DLQ.
  - **features/flow-control** – Rate limits, concurrency, and parallelism.
  - **features/wait-for-event** – Notify and wait-for-event patterns.
  - **features/webhooks** – Webhook creation and consumption.
- how to:
  - **how-to/local-dev** – Local QStash dev server (auto via `QSTASH_DEV=true`) and tunneling.
  - **how-to/realtime** – Realtime and human‑in‑the‑loop workflows.
  - **how-to/migrations** – Migrating workflows safely.
  - **how-to/middleware** – Adding middleware to workflows.
- other files:
  - **rest-api** – Low-level REST endpoints for interacting with QStash/Workflow.
  - **troubleshooting** – Common debugging and environment issues.
  - **agents** – Using Workflow with agents, orchestrators, and automation patterns.
