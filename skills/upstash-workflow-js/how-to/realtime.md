# Realtime Workflow Integration (TypeScript)

This Skill provides guidance for building real‑time and human‑in‑the‑loop workflows using Upstash Workflow + Upstash Realtime. It covers event schemas, workflow patterns, emitting/receiving updates, and handling interactive pauses.

Key capabilities:

- Emit strongly typed workflow events.
- Subscribe to live updates in the frontend.
- Implement pause/resume workflows using `waitForEvent` and `notify`.

---

## Core Concepts

### Realtime schema design

Define all workflow event types in one schema. Keep event definitions minimal and stable.

```ts
// lib/realtime.ts
const schema = {
  workflow: {
    // Completion events
    runFinish: z.object({}),
    stepFinish: z.object({ stepName: z.string(), result: z.unknown().optional() }),

    // Human‑in‑the‑loop events
    waitingForInput: z.object({ eventId: z.string(), message: z.string() }),
    inputResolved: z.object({ eventId: z.string() }),
  },
};

export const realtime = new Realtime({ schema, redis });
export type RealtimeEvents = InferRealtimeEvents<typeof realtime>;
```

Common mistakes:

- Forgetting to wrap events under a namespace (e.g. `workflow.*`).

---

## Emitting Events Inside Workflows

Emit inside `context.run()` whenever possible to avoid duplicate emissions on retries.

```ts
// app/api/workflow/route.ts
export const { POST } = serve(async (context) => {
  const channel = realtime.channel(context.workflowRunId);

  // Emit step updates
  await context.run("validate", async () => {
    const result = { ok: true };
    await channel.emit("workflow.stepFinish", { stepName: "validate", result });
    return result;
  });

  // Final event
  await context.run("finish", () => channel.emit("workflow.runFinish", {}));
});
```

Pitfall:

- Emitting events _outside_ of `context.run()` risks duplicate delivery if retries happen.

---

## Human‑in‑the‑Loop Workflows

Use `waitForEvent()` with unique `eventId` values and emit a `waitingForInput` event immediately.

```ts
// Step that pauses for human input
const eventId = `approval-${context.workflowRunId}`;

const [{ eventData, timeout }] = await Promise.all([
  context.waitForEvent("wait-for-approval", eventId, { timeout: "5m" }),
  context.run("notify-wait", () =>
    channel.emit("workflow.waitingForInput", {
      eventId,
      message: "Waiting for approval...",
    })
  ),
]);

if (timeout) return { success: false, reason: "timeout" };

await context.run("resolved", () => channel.emit("workflow.inputResolved", { eventId }));
```

Important details:

- Always handle timeout: otherwise the workflow may appear stuck.
- Emit `inputResolved` so the UI can clear any pending state.
- Use deterministic `eventId` prefixes per action/approval.

---

## Notify Endpoint (User Response)

The frontend sends input back to the workflow using `client.notify()`.

```ts
// app/api/notify/route.ts
export async function POST(req: NextRequest) {
  const { eventId, eventData } = await req.json();

  await workflowClient.notify({ eventId, eventData }); // resumes workflow
  return NextResponse.json({ success: true });
}
```

Common mistakes:

- Sending the wrong `eventId` → workflow never resumes.
- Sending `eventData` that doesn’t match the awaited type.

---

## Realtime Subscription in the Frontend

Use a single hook to consume all workflow‑related events and manage state.

```ts
// lib/realtime-client.ts & useWorkflow hooks
useRealtime({
  enabled: !!workflowRunId,
  channels: [workflowRunId],
  events: [
    "workflow.stepFinish",
    "workflow.runFinish",
    "workflow.waitingForInput",
    "workflow.inputResolved",
  ],
  onData({ event, data }) {
    switch (event) {
      case "workflow.stepFinish":
        setSteps((prev) => [...prev, data]);
        break;
      case "workflow.waitingForInput":
        setWaitingState(data);
        break;
      case "workflow.inputResolved":
        setWaitingState((prev) => (prev?.eventId === data.eventId ? null : prev));
        break;
      case "workflow.runFinish":
        setIsRunFinished(true);
    }
  },
});
```

Pitfalls:

- Forgetting to clear waiting state on `inputResolved`.
- Forgetting to reset state on re‑trigger.

---

## Triggering the Workflow

One simple endpoint triggers both basic and human‑in‑the‑loop flows.

```ts
// app/api/trigger/route.ts
export async function POST(req: NextRequest) {
  const workflowUrl = `${req.nextUrl.origin}/api/workflow`; // or /human-in-loop
  const { workflowRunId } = await workflowClient.trigger({
    url: workflowUrl,
    body: { userId: "123", action: "process" },
  });
  return NextResponse.json({ workflowRunId });
}
```

---

## Recommended Patterns

- Use one channel per workflow run (`workflowRunId`).
- Always place event emissions inside `context.run()`.
- Use stable `eventId` formats for all interactive steps.
- Subscribe to only the events your UI needs.
- Reset UI state before every new trigger.
