#!/usr/bin/env npx tsx
/**
 * Generate the backwards-compatible modes marketplace from agent definitions.
 *
 * Usage: npx tsx bin/generate-modes-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import matter from "gray-matter";
import { Document, Scalar } from "yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const agentsDir = path.join(__dirname, "..", "agents");
const modesDir = path.join(__dirname, "..", "modes");
const MARKETPLACE_KEYS = ["author", "authorUrl", "tags", "prerequisites"];

function requireString(value: unknown, field: string, file: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${file}: missing required string field ${field}`);
  }
  return value;
}

function globToRegex(glob: string): string {
  let regex = glob.includes("/") ? "^" : "(?:^|/)";

  for (let index = 0; index < glob.length; index += 1) {
    const character = glob[index];
    if (character === "*" && glob[index + 1] === "*") {
      regex += ".*";
      index += 1;
    } else if (character === "*") {
      regex += "[^/]*";
    } else if (character === "?") {
      regex += "[^/]";
    } else {
      regex += character.replace(/[.+^${}()|[\]\\]/g, "\\$&");
    }
  }

  return regex;
}

function groupsFromPermissions(value: unknown): unknown[] {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];

  const permission = value as Record<string, unknown>;
  const groups: unknown[] = [];

  if (permission.read === "allow") groups.push("read");

  if (permission.edit === "allow") {
    groups.push("edit");
  } else if (permission.edit && typeof permission.edit === "object" && !Array.isArray(permission.edit)) {
    const allowedGlobs = Object.entries(permission.edit as Record<string, unknown>)
      .filter(([glob, access]) => glob !== "*" && access === "allow")
      .map(([glob]) => globToRegex(glob));

    if (allowedGlobs.length > 0) {
      groups.push([
        "edit",
        {
          fileRegex: `(?:${allowedGlobs.join("|")})$`,
          description: "Files allowed by agent edit permissions",
        },
      ]);
    }
  }

  if (permission.bash === "allow") groups.push("command");
  if (permission.mcp === "allow") groups.push("mcp");

  // Browser is intentionally omitted because native agent permissions have no equivalent capability.
  return groups;
}

function modeFromAgent(dirName: string): Record<string, unknown> {
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

  const modeDoc = new Document({
    slug: id,
    name,
    description,
    roleDefinition: prompt,
    groups: groupsFromPermissions(frontmatter.permission),
  });
  const roleDefinition = modeDoc.get("roleDefinition", true);
  if (roleDefinition instanceof Scalar) roleDefinition.type = Scalar.BLOCK_LITERAL;
  const modeContent = modeDoc.toString({ lineWidth: 120 });

  const mode: Record<string, unknown> = { id, name, description };
  for (const key of MARKETPLACE_KEYS) {
    if (frontmatter[key] !== undefined) mode[key] = frontmatter[key];
  }
  mode.content = modeContent;

  return mode;
}

const items = fs
  .readdirSync(agentsDir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
  .map((dir) => {
    const mode = modeFromAgent(dir.name);
    console.log(`Added: ${mode.name}`);
    return mode;
  })
  .sort((a, b) => (a.id as string).localeCompare(b.id as string));

const doc = new Document({ items });
const output = doc.toString({ lineWidth: 120 });

fs.writeFileSync(path.join(modesDir, "marketplace.yaml"), output);

console.log(`\nGenerated marketplace.yaml with ${items.length} modes`);
