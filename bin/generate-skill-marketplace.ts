#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from skill SKILL.md frontmatter.
 *
 * Usage: npx tsx bin/generate-skill-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import matter from "gray-matter";
import {
  foldedScalar,
  generateMarketplace,
  listVisibleDirectories,
  loadMcpIds,
  repoPathFromBin,
  validateRequirements,
  validateSuggestFor,
} from "./marketplace-generator-utils.ts";

const skillsDir = repoPathFromBin("skills");
const mcpsDir = repoPathFromBin("mcps");

const GITHUB_BASE_URL =
  "https://github.com/Kilo-Org/kilo-marketplace/tree/main/skills";
const RAW_BASE_URL =
  "https://raw.githubusercontent.com/Kilo-Org/kilo-marketplace/main/skills";
const CONTENT_BASE_URL =
  "https://github.com/Kilo-Org/kilo-marketplace/releases/download/skills-latest";

const skillIds = new Set(listVisibleDirectories(skillsDir));
const mcpIds = loadMcpIds(mcpsDir);
const declaredNames = new Set<string>();
generateMarketplace({
  rootDir: skillsDir,
  parseItem: (dirName) => {
    const { data } = matter(
      fs.readFileSync(path.join(skillsDir, dirName, "SKILL.md"), "utf-8"),
    );
    if (data.name !== dirName) {
      throw new Error(
        `${dirName}/SKILL.md: name must match directory (found "${data.name ?? "missing"}")`,
      );
    }
    if (declaredNames.has(data.name)) {
      throw new Error(`Duplicate skill name: ${data.name}`);
    }
    declaredNames.add(data.name);
    const requirements = validateRequirements(
      data.requirements,
      dirName,
      skillIds,
      mcpIds,
      { subgroup: "skills", id: dirName },
    );
    console.log(`Added: ${data.name}`);
    return {
      id: dirName,
      description: foldedScalar(data.description),
      category: data.metadata?.category || undefined,
      suggest_for: validateSuggestFor(data.metadata?.suggest_for, dirName, {
        fieldName: "metadata.suggest_for",
        filenameExample: "*.rb",
      }),
      requirements,
      githubUrl: `${GITHUB_BASE_URL}/${dirName}`,
      rawUrl: `${RAW_BASE_URL}/${dirName}/SKILL.md`,
      content: `${CONTENT_BASE_URL}/${dirName}.tar.gz`,
    };
  },
  sortItems: (a, b) => {
    const catCmp = (a.category || "zzz").localeCompare(b.category || "zzz");
    return catCmp !== 0 ? catCmp : a.id.localeCompare(b.id);
  },
  finalMessage: (count) => `\nGenerated marketplace.yaml with ${count} skills`,
});
