---
name: upstash-box-js
description: >-
  Work with the @upstash/box TypeScript/JavaScript SDK for sandboxed cloud
  containers with AI agents, shell, filesystem, git, cron schedules, and a
  headless browser. Use when building with Upstash Box, creating sandboxed
  environments, running AI agents in containers, browser automation from a box,
  or orchestrating parallel boxes.
metadata:
  category: development
  author: upstash
  source:
    repository: 'https://github.com/upstash/skills'
    path: skills/upstash-box-js
    license_path: LICENSE
    ref: main
    commit: fb4e6019638d5746b86a54f1bb7144dbb324480a
---

# @upstash/box SDK

Sandboxed cloud containers with built-in AI agents, shell, filesystem, git, cron schedules, and an optional headless browser.

## Install & Setup

```bash
npm install @upstash/box
npm install zod   # peer dependency, only needed for responseSchema / browser schemas
```

Set `UPSTASH_BOX_API_KEY` env var or pass `apiKey` to constructors.

Anonymous telemetry headers are sent by default. Opt out with the
`UPSTASH_DISABLE_TELEMETRY` env var, or `enableTelemetry: false` in the config
(the only option on runtimes without `process.env`, e.g. Cloudflare Workers).

## Box Lifecycle

```ts
import { Box, Agent, ClaudeCode, BoxApiKey } from "@upstash/box"

// Create with agent + git + env vars
const box = await Box.create({
  name: "my-box",
  runtime: "node", // "node" | "python" | "golang" | "ruby" | "rust" (+ "-alpine" variants)
  size: "small",   // "small" (2 CPU/4GB) | "medium" (4/8) | "large" (8/16)
  labels: ["beta", "x-team"], // max 5, ≤20 chars each
  keepAlive: true,            // don't idle-pause the box
  initCommand: "npm install && npm run dev", // keep-alive boxes only
  browser: true,              // provision headless Chromium for box.browser
  agent: {
    harness: Agent.ClaudeCode, // Agent.Codex | Agent.OpenCode | Agent.Cursor | Agent.Custom
    model: ClaudeCode.Sonnet_4_5,
    // apiKey options:
    //   omit          → server decides which key to use
    //   BoxApiKey.UpstashKey  → use Upstash-provided LLM key
    //   BoxApiKey.StoredKey   → use key previously stored via Upstash Console
    //   "sk-..."      → direct API key string
    apiKey: BoxApiKey.UpstashKey,
  },
  git: { // all fields optional
    token: process.env.GITHUB_TOKEN, // alternatively link your GitHub account via Upstash Console
    userName: "Bot",
    userEmail: "bot@example.com",
  },
  env: { DATABASE_URL: "..." },
  skills: ["upstash/qstash-js/qstash-js"], // owner/repo/skill-name
  timeout: 600_000, // request timeout in ms
  debug: false,
})

// Reconnect, list, delete, pause/resume
const same = await Box.get(box.id)
const byName = await Box.getByName("my-box")
const all = await Box.list()
const beta = await Box.list({ label: "beta" }) // filter by label
await box.pause()
await box.resume()
await box.delete()  // irreversible
const { status } = await box.getStatus()

box.id; box.size; box.keepAlive; box.cwd; box.networkPolicy

// Init command (keep-alive boxes only — throws otherwise)
await box.setInitCommand("npm run dev")
const script = await box.getInitCommand()
await box.deleteInitCommand()

// Bulk delete (static, by ID)
await Box.delete({ boxIds: ["box_1", "box_2"] })
const { deleted } = await Box.deleteSnapshots({ snapshotIds: ["snap_1"] }) // omit ids → delete all
```

### Account-level env vars

Injected into every box you create.

```ts
await Box.setEnv("API_TOKEN", "secret")
const env = await Box.listEnv()          // values are masked
await Box.setAllEnv({ A: "1", B: "2" })  // full replace — unlisted keys are removed
await Box.deleteEnv("API_TOKEN")
```

## Agent Runs

```ts
import { z } from "zod"

// Structured output with Zod schema
const run = await box.agent.run({
  prompt: "Review the code for security issues",
  responseSchema: z.object({
    verdict: z.enum(["approved", "changes_requested"]),
    findings: z.array(z.object({
      severity: z.enum(["high", "medium", "low"]),
      file: z.string(),
      issue: z.string(),
    })),
  }),
  timeout: 120_000,
  maxRetries: 2,
  options: { maxTurns: 20, maxBudgetUsd: 1.0, effort: "high" }, // harness-specific
  onToolUse: (tool) => console.log(tool.name, tool.input),
  onToolResult: (result) => console.log(result.toolCallId, result.output),
})

run.status  // "running" | "completed" | "failed" | "cancelled" | "detached"
run.result  // typed from schema
run.cost    // { inputTokens, outputTokens, cachedInputTokens, computeMs, totalUsd }

// Attach files to a prompt (max 10 files, 10 MB each)
await box.agent.run({ prompt: "Describe this", files: ["./screenshot.png"] })
await box.agent.run({
  prompt: "Describe this",
  files: [{ data: base64, mediaType: "image/png", filename: "shot.png" }],
})

// Streaming — chunk is a discriminated union
const stream = await box.agent.stream({ prompt: "Build a REST API" })
for await (const chunk of stream) {
  if (chunk.type === "text-delta") process.stdout.write(chunk.text)
  if (chunk.type === "reasoning") process.stdout.write(chunk.text)
  if (chunk.type === "tool-call") console.log(chunk.toolName, chunk.input)
  if (chunk.type === "tool-result") console.log(chunk.output)
  if (chunk.type === "finish") console.log(chunk.usage, chunk.sessionId)
  // also: { type: "start", runId } | { type: "stats", cpuNs, memoryPeakBytes } | { type: "unknown" }
}
stream.status // "completed" after iteration finishes
stream.result // final output

// Fire-and-forget with webhook
await box.agent.run({
  prompt: "Run tests",
  webhook: { url: "https://example.com/hook", headers: { Authorization: "Bearer ..." } },
})
```

### Harness & model

`harness` is required (`provider` / `runner` are deprecated aliases). Model
enums: `ClaudeCode`, `OpenAICodex`, `OpenCodeModel`, `CursorModel`,
`OpenRouterModel`, `VercelModel` — or any plain provider-prefixed string.

```ts
import { ClaudeCode, OpenAICodex, CursorModel, OpenRouterModel, VercelModel } from "@upstash/box"

ClaudeCode.Opus_5        // "anthropic/claude-opus-5"
ClaudeCode.Sonnet_5      // "anthropic/claude-sonnet-5"
OpenAICodex.GPT_5_6      // "openai/gpt-5.6"
CursorModel.Composer_2_5 // "cursor/composer-2.5"
OpenRouterModel.Claude_Opus_5 // "openrouter/anthropic/claude-opus-5"
VercelModel.GPT_5_5      // "vercel/openai/gpt-5.5"

// Read / change the box's harness + model at runtime
const { harness, model } = box.modelConfig
await box.configureModel("anthropic/claude-opus-4-8")
```

### Custom harness

Run your own agent binary inside the box instead of a managed harness.

```ts
import { Box, Agent, runCustomHarness } from "@upstash/box"

const box = await Box.create({
  agent: {
    harness: Agent.Custom,
    model: "my-agent",                                  // label forwarded to the process
    customHarness: { command: "node", args: ["/workspace/home/agent.js"] },
  },
})
await box.configureCustomHarness({ command: "node", args: ["/workspace/home/agent2.js"] })

// Inside the box, agent.js emits box-sse-v1 events:
await runCustomHarness(async ({ prompt, model, sessionId, stream }, emit) => {
  emit.text("working...")
  emit.tool({ name: "Bash", input: { command: "ls" } })
  return { output: "done", inputTokens: 10, outputTokens: 5 }
})
```

## Run Fields

Every `run` (agent, command, or code) returns a `Run<T>`:

```ts
const run = await box.exec.command("npm test")
run.id        // run ID
run.status    // "completed" | "failed" | ...
run.result    // stdout on success, stderr on failure (or typed T with responseSchema)
run.stdout    // raw stdout (command/code runs)
run.stderr    // raw stderr (command/code runs)
run.exitCode  // number | null (null for agent runs)
run.cost      // { inputTokens, outputTokens, cachedInputTokens, computeMs, totalUsd }

await run.cancel()          // cancel a running run
const logs = await run.logs() // [{ timestamp, level, message }]

// Box-level history
const entries = await box.logs({ limit: 100 }) // [{ timestamp, level, source, message }]
const runs = await box.listRuns()              // backend run records, newest first
```

## Shell Execution

```ts
// Run commands
const run = await box.exec.command("echo hello && ls -la")

// Run code snippets — lang: "js" | "ts" | "python"
const run2 = await box.exec.code({ code: "console.log(1+1)", lang: "js", timeout: 10_000 })

// Streaming shell / code
const stream = await box.exec.stream("npm run build")
const stream2 = await box.exec.streamCode({ code: "print('hi')", lang: "python" })
for await (const chunk of stream) {
  // chunk: { type: "output", data } | { type: "exit", exitCode, cpuNs }
}
```

## Filesystem

```ts
await box.files.write({ path: "/workspace/home/app.js", content: "console.log('hi')" })
const content = await box.files.read("/workspace/home/app.js")
const entries = await box.files.list("/workspace/home") // [{ name, path, size, is_dir, mod_time }]

// Binary files — use encoding: "base64" for read and write
await box.files.write({ path: "/workspace/home/image.png", content: base64String, encoding: "base64" })
const b64 = await box.files.read("/workspace/home/image.png", { encoding: "base64" })

// Upload local files
await box.files.upload([{ path: "./local/file.txt", destination: "/workspace/home/file.txt" }])

// Download — `folder` is a path INSIDE the box; files land in ./<basename>
await box.files.download({ folder: "src" }) // → ./src
await box.files.download()                  // whole cwd → ./workspace
```

## cd / Working Directory

The SDK tracks `cwd` client-side. All operations (exec, files, git, agent) run relative to it.

```ts
box.cwd // current working directory (starts at /workspace/home)
await box.cd("my-repo")     // relative to current cwd
await box.cd("/workspace/home/other") // absolute path
```

## Git

Clones land inside the box's isolated container, never on the caller's machine. Cloned
code is data until something runs it — treat an untrusted repo as untrusted input, and
pair it with a restrictive `networkPolicy` (see below) before running its build or tests.

```ts
await box.git.clone({ repo: "github.com/org/repo", branch: "main" })
await box.git.clone({ repo: "github.com/org/repo", depth: 1 }) // shallow clone
await box.cd("repo") // cd into cloned repo

const status = await box.git.status()
const diff = await box.git.diff()
const { sha } = await box.git.commit({
  message: "fix: resolve bug",
  authorName: "Jane Doe",      // optional per-commit override
  authorEmail: "jane@example.com",
})
await box.git.push({ branch: "feature/fix" })

await box.git.checkout({ branch: "release/v2" })
const pr = await box.git.createPR({ title: "Fix bug", body: "...", base: "main" })
// pr: { url, number, title, base }

// Update the box-wide git identity
const cfg = await box.git.updateConfig({ userName: "Bot", userEmail: "bot@example.com" })
// cfg: { git_user_name, git_user_email }

// Arbitrary git commands
const { output } = await box.git.exec({ args: ["log", "--oneline", "-5"] })
```

## Schedules

Cron tasks on a box — shell commands or agent prompts. Available on `Box` and `EphemeralBox`. Cron is UTC.

```ts
const execSchedule = await box.schedule.exec({
  cron: "* * * * *",
  command: ["bash", "-c", "date >> /workspace/home/cron.log"],
  folder: "/workspace/home",            // optional cwd override
  webhookUrl: "https://example.com/hook",
  webhookHeaders: { Authorization: "Bearer ..." },
})

const agentSchedule = await box.schedule.agent({
  cron: "0 9 * * *",
  prompt: "Run the test suite and fix any failures",
  model: "anthropic/claude-sonnet-5",   // optional override
  options: { maxBudgetUsd: 1.0, effort: "high" },
  timeout: 300_000,
})

const schedules = await box.schedule.list()
const one = await box.schedule.get(agentSchedule.id)

// Partial update — omitted fields keep their value, "" / [] / {} clear a field,
// `options: null` clears agent options. The schedule's type cannot change.
await box.schedule.update(agentSchedule.id, { cron: "0 18 * * *", webhookUrl: "" })

await box.schedule.pause(agentSchedule.id)
await box.schedule.resume(agentSchedule.id)
await box.schedule.delete(agentSchedule.id)
```

## Snapshots

```ts
// Snapshot — checkpoint workspace state
const snap = await box.snapshot({ name: "after-setup" })
// snap: { id, name, box_id, size_bytes, status, created_at }

const restored = await Box.fromSnapshot(snap.id, { size: "medium", keepAlive: true })
const snaps = await box.listSnapshots()
await box.deleteSnapshot(snap.id)
```

## Browser

Create the box with `browser: true` to drive a headless Chromium. Tab management
lives on `box.browser`; every page operation lives on the `Tab` handle.
`extract` / `observe` / `act` / `run` are AI-powered and metered.

```ts
import { z } from "zod"

const box = await Box.create({
  browser: true,
  agent: { harness: Agent.ClaudeCode, model: ClaudeCode.Sonnet_4_5 },
})

// Tabs
const tab = await box.browser.tab.create("https://example.com", { waitUntil: "load", timeout: 30_000 })
const tabs = await box.browser.listTabs()
const again = box.browser.getTab(tab.id) // no network call

// Page operations
const content = await tab.goto("https://news.ycombinator.com") // { title, url, text, links }
const current = await tab.content()
const png = await tab.screenshot()                                  // Uint8Array
const b64 = await tab.screenshot({ type: "base64", fullPage: true })

// AI operations (metered)
const data = await tab.extract(
  "Top story title and points",
  z.object({ title: z.string(), points: z.number() }),
)
const { elements } = await tab.observe("What can I click?")
const acted = await tab.act("Click the first headline") // { success, message, actions, inputTokens, ... }
const result = await tab.run("Find the top comment and summarize it", {
  maxSteps: 10,                       // default 15, max 30
  schema: z.object({ summary: z.string() }),
  model: "anthropic/claude-sonnet-4-5",
})
result.data; result.result; result.completed; result.steps

// Live view + raw CDP
const liveUrl = await tab.liveViewUrl()      // view-only screencast page/iframe
const cdpUrl = await box.browser.cdpUrl()    // Playwright / Puppeteer / Stagehand
await tab.close()

// Session recordings (HLS playback URL + MP4 download, chapter markers)
const handle = await box.browser.recordings.start({ maxDurationSeconds: 600 }) // default & max 600
const recording = await handle.stop()
// recording: { id, boxId, status, startedAt, endedAt, durationMs, sizeBytes, mp4SizeBytes,
//              segmentCount, markers, stoppedReason, expiresAt, playlistUrl }
const all = await box.browser.recordings.list()
const one = await box.browser.recordings.get(recording.id)

// Download the video to a local file — returns the path written.
// Defaults to ./box-recording-<id>.mp4 (.ts for recordings captured before MP4 support).
const file = await box.browser.recordings.download(recording.id)
await box.browser.recordings.download(recording.id, { path: "./out/demo.mp4" })
```

## EphemeralBox

Lightweight, short-lived boxes (max 3 days). Supports `exec`, `files`, `schedule`, `cd`, network policy, and snapshots. No agent, git, skills, labels namespace, browser, or public URLs.

```ts
import { EphemeralBox } from "@upstash/box"

const ebox = await EphemeralBox.create({
  runtime: "python",
  size: "small",
  ttl: 3600,  // seconds, max 259200 (3 days), default 259200
  env: { API_KEY: "..." },
  labels: ["scratch"], // settable at create time; filter via Box.list({ label })
})

ebox.expiresAt // unix timestamp when auto-deleted
await ebox.exec.command("python -c 'print(1+1)'")
await ebox.exec.code({ code: "print('hi')", lang: "python" })
await ebox.files.write({ path: "/workspace/home/data.json", content: "{}" })
await ebox.schedule.exec({ cron: "* * * * *", command: ["bash", "-c", "date"] })
await ebox.cd("subdir")
const snap = await ebox.snapshot({ name: "checkpoint" })
await ebox.delete()

// Restore from snapshot
const ebox2 = await EphemeralBox.fromSnapshot(snap.id, { ttl: 7200 })
```

## Public URLs

Expose box ports as public URLs with optional auth.

```ts
const publicURL = await box.getPublicURL(3000)
// publicURL: { url: "https://{id}-3000.preview.box.upstash.com", port }

const authed = await box.getPublicURL(3000, { bearerToken: true })
// authed: { url, port, token }

const basic = await box.getPublicURL(3000, { basicAuth: true })
// basic: { url, port, username, password }

const { publicURLs } = await box.listPublicURLs()
await box.deletePublicURL(3000)
```

## Skills

Install agent skills from the Context7 registry. Format: `owner/repo/skill-name`.

An installed skill becomes instructions for the box's agent, so pin skills to owners you
trust the same way you would a dependency. Skills resolve from the registry at box
creation, not from arbitrary URLs, and they only ever run inside the box's container.

```ts
const box = await Box.create({ skills: ["upstash/qstash-js/qstash-js"] })

await box.skills.add("upstash/workflow-js/workflow-js")
const enabled = await box.skills.list()
await box.skills.remove("upstash/workflow-js/workflow-js")
```

## Labels

```ts
const labels = await box.labels.add("prod")     // returns the updated set
await box.labels.remove("beta")
const current = await box.labels.list()
const prodBoxes = await Box.list({ label: "prod" })
```

## Network Policy & Outbound Headers

```ts
const box = await Box.create({
  // mode: "allow-all" (default) | "deny-all" | "custom"
  networkPolicy: { mode: "custom", allowedDomains: ["api.example.com"], deniedCidrs: ["10.0.0.0/8"] },

  // Inject secret headers into matching outbound HTTPS requests (write-only, never read back)
  attachHeaders: {
    "api.stripe.com": { Authorization: "Bearer sk_live_..." },
    "*.example.com": { "X-Custom-Token": "secret123" },
  },
})

box.networkPolicy
await box.updateNetworkPolicy({ mode: "deny-all" })
```

## MCP Servers

Attach MCP servers to the box agent. An attached server supplies tools the agent can call,
so use servers you control or trust — and keep `networkPolicy` restrictive when the agent
also handles untrusted input.

```ts
const box = await Box.create({
  agent: { harness: Agent.ClaudeCode, model: ClaudeCode.Sonnet_4_5 },
  mcpServers: [
    { name: "fs", package: "@modelcontextprotocol/server-filesystem", args: [] },
    { name: "custom", url: "<your-mcp-server-url>", headers: { Authorization: "..." } },
  ],
})
```

## Errors & SSH

```ts
import { BoxError } from "@upstash/box"

try {
  await box.agent.run({ prompt: "..." })
} catch (e) {
  if (e instanceof BoxError) console.error(e.message, e.statusCode)
}
```

Shell into a box directly (Box API key is the SSH password):

```bash
ssh <box-id>@us-east-1.box.upstash.com
```

## Gotchas

- Default working directory is `/workspace/home`, not `/home` or `/`
- `box.cd()` is client-side tracking — it validates the path exists but doesn't change the box's shell cwd. All SDK methods use it automatically.
- `agent.harness` is required; `provider` / `runner` still work but are deprecated
- There is **no** `box.fork()` — it was removed from the SDK. Snapshot the box and use `Box.fromSnapshot()` instead.
- `EphemeralBox` does NOT support `agent`, `git`, `skills`, `browser`, or public URLs — use full `Box` for those (it does support `schedule` and snapshots)
- `run.exitCode` is `null` for agent runs, only available for exec commands
- `run.result` is stdout on success and stderr on failure — a command that exits 0 writing only to stderr yields `""`; read `run.stderr` for it
- `files.download({ folder })` takes a path *inside the box*; output lands in `./<basename>` locally
- `box.browser` requires a box created with `browser: true`
- `getInitCommand` / `setInitCommand` / `deleteInitCommand` throw unless the box was created with `keepAlive: true`
- `box.delete()` is irreversible — snapshot first if you need the state
- Git operations require `git.token` in `BoxConfig` for private repos and PRs
- `Box.fromSnapshot()` creates a new box — it does not modify the original
- `responseSchema` and browser `schema` need `zod` installed (peer dependency, v3 or v4)
- All `timeout` values are milliseconds
