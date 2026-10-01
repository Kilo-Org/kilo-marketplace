#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from individual MCP directories.
 *
 * Usage: npx tsx bin/generate-mcps-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import { pathToFileURL } from "url";
import matter from "gray-matter";
import * as yaml from "yaml";
import {
  archive,
  buildCategorySummary,
  generateMarketplace,
  listVisibleDirectories,
  loadMcpIds,
  MARKETPLACE_CATEGORIES,
  repoPathFromBin,
  requireString,
  validateRequirements,
  validateSuggestFor,
} from "./marketplace-generator-utils.ts";

export function generateMcps(root: string, skills: string) {
  const skillIds = new Set(listVisibleDirectories(skills));
  const mcpIds = loadMcpIds(root);

  return generateMarketplace({
    rootDir: root,
    parseItem: (dirName) => {
      const content = fs.readFileSync(path.join(root, dirName, "MCP.yaml"), "utf-8");
      const mcp = yaml.parse(content) as { id: string; category: string; [key: string]: unknown };

      if (!MARKETPLACE_CATEGORIES.has(mcp.category)) {
        throw new Error(`${dirName}/MCP.yaml: invalid category "${mcp.category}"`);
      }
      if (mcp.tags !== undefined) {
        throw new Error(`${dirName}/MCP.yaml: use category instead of tags`);
      }
      validateSuggestFor(mcp.suggest_for, mcp.id, {
        fieldName: "suggest_for",
        filenameExample: "*.ipynb",
      });
      validateRequirements(
        mcp.requirements,
        mcp.id,
        skillIds,
        mcpIds,
        { subgroup: "mcps", id: mcp.id },
      );

      if (mcp.skills !== undefined) {
        if (
          !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(mcp.id) ||
          /^(con|prn|aux|nul|com[1-9]|lpt[1-9]|constructor|prototype)$/.test(mcp.id)
        ) {
          throw new Error(`${dirName}/MCP.yaml: MCP id must be safe lowercase kebab-case when skills is present`);
        }
        if (!Array.isArray(mcp.skills) || mcp.skills.length === 0) {
          throw new Error(`${dirName}/MCP.yaml: skills must be a non-empty list of skill IDs`);
        }
        const seen = new Set<string>();
        mcp.skills = mcp.skills.map((id: unknown) => {
          if (
            typeof id !== "string" ||
            !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id) ||
            /^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/.test(id)
          ) {
            throw new Error(`${dirName}/MCP.yaml: skills must contain safe lowercase kebab-case IDs`);
          }
          if (seen.has(id)) {
            throw new Error(`${dirName}/MCP.yaml: skills contains duplicate ID "${id}"`);
          }
          seen.add(id);
          if (!skillIds.has(id)) {
            throw new Error(`${dirName}/MCP.yaml: skills references unknown skill ID "${id}"`);
          }
          const file = path.join(skills, id, "SKILL.md");
          if (!fs.lstatSync(file, { throwIfNoEntry: false })?.isFile()) {
            throw new Error(`${dirName}/MCP.yaml: skill "${id}" has no regular SKILL.md`);
          }
          const skill = matter(fs.readFileSync(file, "utf-8")).data;
          if (skill.name !== id) {
            throw new Error(`${file}: name must match skill ID "${id}"`);
          }
          requireString(skill.description, "description", file);
          return { id, content: archive(id) };
        });
      }

      const marketplaceMcp = {} as typeof mcp;
      for (const [key, value] of Object.entries(mcp)) {
        marketplaceMcp[key] = value;
        if (key === "category") {
          marketplaceMcp.tags = [value];
        }
      }

      console.log(`Added: ${mcp.name}`);
      return marketplaceMcp;
    },
    sortItems: (a, b) => a.id.localeCompare(b.id),
    header: (items) =>
      buildCategorySummary(items, {
        title: "MCP category usage",
        resourceNameSingular: "MCP",
        resourceNamePlural: "MCPs",
        scriptName: "bin/generate-mcps-marketplace.ts",
      }),
    finalMessage: (count) => `\nGenerated marketplace.yaml with ${count} MCPs`,
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  generateMcps(repoPathFromBin("mcps"), repoPathFromBin("skills"));
}
