#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from individual plugin directories.
 *
 * Usage: npx tsx bin/generate-plugins-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import { pathToFileURL } from "url";
import npa from "npm-package-arg";
import validate from "validate-npm-package-name";
import * as yaml from "yaml";
import {
  buildCategorySummary,
  generateMarketplace,
  listVisibleDirectories,
  PLUGIN_CATEGORIES,
  repoPathFromBin,
  requireString,
} from "./marketplace-generator-utils.ts";

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

function pluginFromYaml(root: string, dirName: string): MarketplacePlugin {
  const file = path.join(root, dirName, "PLUGIN.yaml");
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
  if (!validate(id).validForNewPackages) {
    throw new Error(`${file}: id must be a valid npm package name`);
  }
  // Installed state is keyed by package name. Only registry specs are supported.
  const spec = npa(content);
  if (
    spec.name !== id ||
    !spec.registry ||
    !["version", "range", "tag"].includes(spec.type)
  ) {
    throw new Error(`${file}: content must be the ${id} registry package with an optional version, range, or tag`);
  }
  if (!PLUGIN_CATEGORIES.has(category)) {
    throw new Error(`${file}: invalid category "${category}"`);
  }
  if (raw.tags !== undefined) {
    throw new Error(`${file}: use category instead of tags`);
  }

  return { id, name, description, category, tags: [category], author, url, content };
}

export function generatePlugins(root: string) {
  const directories = listVisibleDirectories(root).flatMap((dir) =>
    dir.startsWith("@")
      ? listVisibleDirectories(path.join(root, dir)).map((name) => `${dir}/${name}`)
      : [dir],
  );
  return generateMarketplace({
    rootDir: root,
    directories,
    parseItem: (dirName) => {
      const plugin = pluginFromYaml(root, dirName);
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
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  generatePlugins(repoPathFromBin("plugins"));
}
