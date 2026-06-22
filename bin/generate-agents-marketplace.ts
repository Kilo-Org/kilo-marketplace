#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from individual agent directories.
 *
 * Usage: npx tsx bin/generate-agents-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import matter from "gray-matter";
import { Document } from "yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const agentsDir = path.join(__dirname, "..", "agents");

const AGENT_MODES = new Set(["primary", "subagent", "all"]);
const AGENT_CONFIG_KEYS = ["model", "variant", "temperature", "top_p", "permission", "color", "steps", "hidden"];
const MARKETPLACE_KEYS = ["author", "authorUrl", "tags", "prerequisites"];

type AgentContent = {
  mode: "primary" | "subagent" | "all";
  description: string;
  prompt: string;
  options: Record<string, unknown>;
  model?: string;
  variant?: string;
  temperature?: number;
  top_p?: number;
  permission?: Record<string, unknown>;
  color?: string;
  steps?: number;
  hidden?: boolean;
};

type MarketplaceAgent = {
  id: string;
  name: string;
  description: string;
  author?: string;
  authorUrl?: string;
  tags?: string[];
  prerequisites?: string[];
  content: AgentContent;
};

function requireString(value: unknown, field: string, file: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${file}: missing required string field ${field}`);
  }
  return value;
}

function agentFromMarkdown(dirName: string): MarketplaceAgent {
  const file = path.join(agentsDir, dirName, "AGENT_DEFINITION.md");
  const { data, content } = matter(fs.readFileSync(file, "utf-8"));
  const frontmatter = data as Record<string, unknown>;

  const id = frontmatter.id === undefined ? dirName : requireString(frontmatter.id, "id", file);
  const name = requireString(frontmatter.name, "name", file);
  const description = requireString(frontmatter.description, "description", file);
  const prompt = content.trim();

  if (id !== dirName) {
    throw new Error(`${file}: id must match directory name (${dirName})`);
  }
  if (!prompt) {
    throw new Error(`${file}: agent prompt body is required`);
  }

  const mode = frontmatter.mode ?? "primary";
  if (typeof mode !== "string" || !AGENT_MODES.has(mode)) {
    throw new Error(`${file}: mode must be one of primary, subagent, all`);
  }

  const options = frontmatter.options ?? {};
  if (!options || typeof options !== "object" || Array.isArray(options)) {
    throw new Error(`${file}: options must be an object`);
  }

  const agentContent: Record<string, unknown> = {
    mode,
    description,
    prompt,
    options: {
      displayName: name,
      ...(options as Record<string, unknown>),
      id,
    },
  };

  for (const key of AGENT_CONFIG_KEYS) {
    if (frontmatter[key] !== undefined) agentContent[key] = frontmatter[key];
  }

  const agent: Record<string, unknown> = { id, name, description, content: agentContent };
  for (const key of MARKETPLACE_KEYS) {
    if (frontmatter[key] !== undefined) agent[key] = frontmatter[key];
  }

  return agent as MarketplaceAgent;
}

const items = fs
  .readdirSync(agentsDir, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !d.name.startsWith("."))
  .map((dir) => {
    const agent = agentFromMarkdown(dir.name);
    console.log(`Added: ${agent.name}`);
    return agent;
  })
  .sort((a, b) => a.id.localeCompare(b.id));

const doc = new Document({ items });
const output = doc.toString({ lineWidth: 120 });

fs.writeFileSync(path.join(agentsDir, "marketplace.yaml"), output);

console.log(`\nGenerated marketplace.yaml with ${items.length} agents`);
