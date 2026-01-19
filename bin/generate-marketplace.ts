#!/usr/bin/env npx tsx
/**
 * Generate marketplace.json from meta.json and skill SKILL.md frontmatter.
 *
 * Usage: npx tsx bin/generate-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import matter from "gray-matter";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsDir = path.join(__dirname, "..", "skills");
const claudePluginDir = path.join(skillsDir, ".claude-plugin");

const marketplace = JSON.parse(
  fs.readFileSync(path.join(claudePluginDir, "meta.json"), "utf-8")
);

marketplace.plugins = fs
  .readdirSync(skillsDir, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !d.name.startsWith("."))
  .map((dir) => {
    const { data } = matter(
      fs.readFileSync(path.join(skillsDir, dir.name, "SKILL.md"), "utf-8")
    );
    console.log(`Added: ${data.name}`);
    return {
      name: data.name,
      description: data.description,
      source: `./${dir.name}`,
      ...(data.metadata?.category && { category: data.metadata.category }),
    };
  })
  .sort((a, b) => {
    const catCmp = (a.category || "zzz").localeCompare(b.category || "zzz");
    return catCmp !== 0 ? catCmp : a.name.localeCompare(b.name);
  });

fs.writeFileSync(
  path.join(claudePluginDir, "marketplace.json"),
  JSON.stringify(marketplace, null, 2) + "\n"
);

console.log(`\nGenerated marketplace.json with ${marketplace.plugins.length} plugins`);
