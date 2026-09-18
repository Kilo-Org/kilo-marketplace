#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from individual plugin directories.
 *
 * Usage: npx tsx bin/generate-plugins-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "yaml";
import {
  buildCategorySummary,
  generateMarketplace,
  PLUGIN_CATEGORIES,
  repoPathFromBin,
  requireString,
} from "./marketplace-generator-utils.ts";

const pluginsDir = repoPathFromBin("plugins");

type MarketplacePlugin = {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  author: string;
  url: string;
  content: string;
};

function pluginFromYaml(dirName: string): MarketplacePlugin {
  const file = path.join(pluginsDir, dirName, "PLUGIN.yaml");
  const raw = yaml.parse(fs.readFileSync(file, "utf-8")) as Record<string, unknown>;

  const id = requireString(raw.id, "id", file);
  const name = requireString(raw.name, "name", file);
  const description = requireString(raw.description, "description", file);
  const category = requireString(raw.category, "category", file);
  const author = requireString(raw.author, "author", file);
  const url = requireString(raw.url, "url", file);
  const content = requireString(raw.content, "content", file);

  if (id !== dirName) {
    throw new Error(`${file}: id must match directory name (${dirName})`);
  }
  if (!PLUGIN_CATEGORIES.has(category)) {
    throw new Error(`${file}: invalid category "${category}"`);
  }
  if (raw.tags !== undefined) {
    throw new Error(`${file}: use category instead of tags`);
  }

  return { id, name, description, category, tags: [category], author, url, content };
}

generateMarketplace({
  rootDir: pluginsDir,
  parseItem: (dirName) => {
    const plugin = pluginFromYaml(dirName);
    console.log(`Added: ${plugin.name}`);
    return plugin;
  },
  sortItems: (a, b) => a.id.localeCompare(b.id),
  header: (items) =>
    buildCategorySummary(items, {
      title: "Plugin category usage",
      resourceNameSingular: "plugin",
      resourceNamePlural: "plugins",
      scriptName: "bin/generate-plugins-marketplace.ts",
      singleCategoryAware: true,
    }),
  finalMessage: (count) => `\nGenerated marketplace.yaml with ${count} plugins`,
});
