#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from individual agent directories.
 *
 * Usage: npx tsx bin/generate-agents-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import matter from "gray-matter";
import {
  AGENT_CATEGORIES,
  buildCategorySummary,
  generateMarketplace,
  repoPathFromBin,
  requireString,
} from "./marketplace-generator-utils.ts";

const agentsDir = repoPathFromBin("agents");

const AGENT_MODES = new Set(["primary", "subagent", "all"]);
const AGENT_CONFIG_KEYS = ["model", "variant", "temperature", "top_p", "permission", "color", "steps", "hidden"];
const MARKETPLACE_KEYS = ["author", "authorUrl", "prerequisites"];

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
  category: string;
  author?: string;
  authorUrl?: string;
  tags: string[];
  prerequisites?: string[];
  content: AgentContent;
};

function agentFromMarkdown(dirName: string): MarketplaceAgent {
  const file = path.join(agentsDir, dirName, "AGENT_DEFINITION.md");
  const { data, content } = matter(fs.readFileSync(file, "utf-8"));
  const frontmatter = data as Record<string, unknown>;

  const id = frontmatter.id === undefined ? dirName : requireString(frontmatter.id, "id", file);
  const name = requireString(frontmatter.name, "name", file);
  const description = requireString(frontmatter.description, "description", file);
  const category = requireString(frontmatter.category, "category", file);
  const prompt = content.trim();

  if (!AGENT_CATEGORIES.has(category)) {
    throw new Error(`${file}: invalid category "${category}"`);
  }
  if (frontmatter.tags !== undefined) {
    throw new Error(`${file}: use category instead of tags`);
  }
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

  const agent: Record<string, unknown> = {
    id,
    name,
    description,
    category,
    tags: [category],
    content: agentContent,
  };
  for (const key of MARKETPLACE_KEYS) {
    if (frontmatter[key] !== undefined) agent[key] = frontmatter[key];
  }

  return agent as MarketplaceAgent;
}

generateMarketplace({
  rootDir: agentsDir,
  parseItem: (dirName) => {
    const agent = agentFromMarkdown(dirName);
    console.log(`Added: ${agent.name}`);
    return agent;
  },
  sortItems: (a, b) => a.id.localeCompare(b.id),
  header: (items) =>
    buildCategorySummary(items, {
      title: "Agent category usage",
      resourceNameSingular: "agent",
      resourceNamePlural: "agents",
      scriptName: "bin/generate-agents-marketplace.ts",
      singleCategoryAware: true,
    }),
  finalMessage: (count) => `\nGenerated marketplace.yaml with ${count} agents`,
});
