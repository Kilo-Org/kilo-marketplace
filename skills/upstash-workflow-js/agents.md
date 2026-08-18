---
name: workflow-agents
description: Skill for building, configuring, and orchestrating Upstash Workflow Agents. Use when the user mentions agent workflows, multi-agent collaboration, tools, tasks, Upstash Workflow, or patterns like evaluator-optimizer, prompt chaining, parallelization, or orchestrator-workers.
---

# Workflow Agents

This Skill provides guidance for defining and orchestrating agents, tools, models, and tasks inside **Upstash Workflow** using **TypeScript**. It explains core concepts, common patterns, workflow configuration, and pitfalls.

## Quick Overview

Use this Skill when:

- Building agents with tools and backgrounds
- Creating multi-step or multi-agent tasks
- Implementing patterns like evaluator-optimizer or prompt chaining
- Integrating LangChain or AI SDK tools
- Running workflows reliably inside Upstash Workflow

The Workflow Agents API centers around four elements:

- **Models** — LLM providers (OpenAI, Anthropic, or any AI SDK provider)
- **Tools** — Functions agents can call
- **Agents** — LLM instances with background, maxSteps, and tools
- **Tasks** — Executable prompts assigned to one or more agents

---

# Defining Models

A model defines which provider the agent uses and includes optional configuration for retries, timeouts, or rate‑limits.

```ts
const agents = agentWorkflow(context);

// Basic OpenAI model
const model = agents.openai("gpt-3.5-turbo");

// OpenAI-compatible provider
const deepseek = agents.openai("deepseek-chat", {
  baseURL: "https://api.deepseek.com",
  apiKey: process.env.DEEPSEEK_API_KEY,
});

// AI SDK provider (ex: Anthropic)
const anthropic = agents.AISDKModel({
  context,
  provider: createAnthropic, // imported from @ai-sdk/anthropic
  providerParams: { apiKey: process.env.ANTHROPIC_KEY },
  agentCallParams: {
    timeout: 1000,
    retries: 0,
  },
});
```

**Key parameters:**

- **callSettings / agentCallParams** — timeout, retries, flow control
- **provider / providerParams** — when using AI SDK providers

**Pitfall:** If you use an OpenAI-compatible provider, you **must** set `baseURL`.

---

# Defining Tools

Tools extend what agents can do. Workflow supports:

- WorkflowTool (native)
- AI SDK tools
- LangChain tools
- Agentic toolkits

```ts
import { z } from "zod";
import { tool } from "ai";
import { WorkflowTool } from "@upstash/workflow-agents";
import { WikipediaQueryRun } from "@langchain/community/tools/wikipedia_query_run";

const mathTool = tool({
  description: "Evaluate a math expression",
  parameters: z.object({ expression: z.string() }),
  execute: async ({ expression }) => mathjs.evaluate(expression),
});

const workflowMath = new WorkflowTool({
  description: "Evaluate math (workflow step aware)",
  schema: z.object({ expression: z.string() }),
  invoke: async ({ expression }) => mathjs.evaluate(expression),
  executeAsStep: false, // allows context.call, etc.
});

const wikiTool = new WikipediaQueryRun({
  topKResults: 1,
  maxDocContentLength: 500,
});
```

**Common mistakes:**

- Workflow wraps execute/invoke in `context.run` by default, so you **cannot use context.call** unless `executeAsStep: false` is set.
- LangChain tools must return **strings**, not objects.

---

# Defining Agents

Agents wrap a model and add behavior via:

- `maxSteps` — how many LLM calls the agent is allowed to make
- `background` — system prompt
- `tools` — available actions

```ts
const generator = agents.agent({
  model,
  name: "generator",
  maxSteps: 1,
  background: "Generate text from prompts.",
  tools: {},
});

const evaluator = agents.agent({
  model,
  name: "evaluator",
  maxSteps: 1,
  background: "Evaluate responses and give corrections.",
  tools: {},
});
```

**Tips:**

- Pick maxSteps carefully; too low prevents tool use; too high increases cost.
- Names appear in Upstash Console logs; keep them descriptive.

---

# Tasks (Single & Multi Agent)

A **task** is a single execution of an agent or a group of agents.

```ts
// Single agent task
const single = agents.task({
  agent: generator,
  prompt: "Explain quantum mechanics.",
});
const { text } = await single.run();

// Multi-agent with manager agent
const multi = agents.task({
  model, // manager LLM
  agents: [generator, evaluator],
  maxSteps: 3,
  prompt: "Generate text and refine it until quality improves.",
});
const result = await multi.run();
```

**Tip:** In multi-agent mode, the model becomes a "manager" system that decides which agent to call.

---

# Common Agent Patterns

Below are the patterns supported by the source files in this skill.

## Prompt Chaining

Sequential agent calls where each output becomes the next input.
Useful for: stepwise research, multi‑stage content generation, breaking down complex tasks.

Pitfall: watch `maxSteps` for agents that need both tool calls and summarization.

## Evaluator‑Optimizer

Loop until evaluator returns a PASS. Simple feedback‑refinement pattern.

Pitfall: Always check evaluator output with `.includes("PASS")`, not strict equality.

## Parallelization

Use multiple agents with `Promise.all` and then aggregate.

Pitfall: Avoid extremely large aggregated prompts; summarizing before combining is recommended.

## Orchestrator‑Workers

Manager delegates sub‑tasks to specialized workers.
Useful for structured Q&A, multi‑topic analysis, or complex synthesis.

Pitfall: The manager must have enough `maxSteps` to orchestrate multiple workers.

---

# Best Practices

- Give each agent a _clear_ background; ambiguous roles cause incorrect tool use.
- Define tools with strict schemas so LLMs call them reliably.
- Use multi-agent tasks when the problem requires specialization.
- Inspect console logs to debug tool calls and agent decisions.
- Use local QStash dev server during development to avoid rate limits.

---

# Example: Combined Setup (models + tools + agents + tasks)

This shows all core fields together in one concise example.

```ts
export const { POST } = serve(async (context) => {
  const agents = agentWorkflow(context);
  const model = agents.openai("gpt-4o");

  const mathTool = tool({
    description: "Compute math",
    parameters: z.object({ expression: z.string() }),
    execute: async ({ expression }) => mathjs.evaluate(expression),
  });

  const researcher = agents.agent({
    model,
    name: "researcher",
    maxSteps: 2,
    background: "Research topics using wiki.",
    tools: { wikiTool },
  });

  const mathematician = agents.agent({
    model,
    name: "math",
    maxSteps: 2,
    background: "Solve numeric problems.",
    tools: { mathTool },
  });

  const task = agents.task({
    model, // manager
    agents: [researcher, mathematician],
    maxSteps: 3,
    prompt: "Tell me about 3 stars and compute the sum of their masses.",
  });

  return (await task.run()).text;
});
```
