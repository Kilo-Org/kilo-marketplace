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
  repoPathFromBin,
  validateSuggestFor,
} from "./marketplace-generator-utils.ts";

const skillsDir = repoPathFromBin("skills");

const GITHUB_BASE_URL =
  "https://github.com/Kilo-Org/kilo-marketplace/tree/main/skills";
const RAW_BASE_URL =
  "https://raw.githubusercontent.com/Kilo-Org/kilo-marketplace/main/skills";
const CONTENT_BASE_URL =
  "https://github.com/Kilo-Org/kilo-marketplace/releases/download/skills-latest";

generateMarketplace({
  rootDir: skillsDir,
  parseItem: (dirName) => {
    const { data } = matter(
      fs.readFileSync(path.join(skillsDir, dirName, "SKILL.md"), "utf-8"),
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
