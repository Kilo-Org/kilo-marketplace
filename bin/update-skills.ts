#!/usr/bin/env npx tsx
/**
 * Update all skills from their upstream source repositories.
 *
 * Usage: npx tsx bin/update-skills.ts [skill-name ...]
 *
 * With no arguments, updates ALL skills that have metadata.source.
 * With arguments, updates only the named skills.
 *
 * Example:
 *   npx tsx bin/update-skills.ts                     # update all
 *   npx tsx bin/update-skills.ts changelog-generator  # update one
 *   npx tsx bin/update-skills.ts vercel-deploy web-design-guidelines  # update several
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";
import matter from "gray-matter";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsDir = path.join(__dirname, "..", "skills");

interface SourceInfo {
  repository: string;
  path: string;
}

interface SkillInfo {
  name: string;
  dir: string;
  source: SourceInfo;
  frontmatter: Record<string, any>;
}

/**
 * Collect all skills that have a metadata.source field.
 * Optionally filter to only the given skill names.
 */
function collectSkills(filter?: string[]): SkillInfo[] {
  const dirs = fs
    .readdirSync(skillsDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith("."));

  const skills: SkillInfo[] = [];

  for (const dir of dirs) {
    if (filter && filter.length > 0 && !filter.includes(dir.name)) {
      continue;
    }

    const skillMdPath = path.join(skillsDir, dir.name, "SKILL.md");
    if (!fs.existsSync(skillMdPath)) {
      console.warn(`  ⚠ ${dir.name}: no SKILL.md found, skipping`);
      continue;
    }

    const content = fs.readFileSync(skillMdPath, "utf-8");
    const { data: frontmatter } = matter(content);

    const source = frontmatter?.metadata?.source;
    if (!source?.repository || !source?.path) {
      if (filter?.includes(dir.name)) {
        console.warn(`  ⚠ ${dir.name}: no metadata.source, skipping`);
      }
      continue;
    }

    skills.push({
      name: dir.name,
      dir: path.join(skillsDir, dir.name),
      source: { repository: source.repository, path: source.path },
      frontmatter,
    });
  }

  return skills;
}

/**
 * Group skills by repository so we can batch fetches.
 */
function groupByRepo(
  skills: SkillInfo[],
): Map<string, SkillInfo[]> {
  const map = new Map<string, SkillInfo[]>();
  for (const skill of skills) {
    const repo = skill.source.repository;
    if (!map.has(repo)) map.set(repo, []);
    map.get(repo)!.push(skill);
  }
  return map;
}

/**
 * Fetch all skills from a single repository via sparse checkout,
 * then copy each skill directory over the local one and re-apply
 * the source metadata.
 */
function updateFromRepo(repoUrl: string, skills: SkillInfo[]): void {
  const tempDir = fs.mkdtempSync(path.join("/tmp", "skill-update-"));

  try {
    // Init sparse checkout
    execSync(`git init`, { cwd: tempDir, stdio: "pipe" });
    execSync(`git remote add origin ${repoUrl}.git`, {
      cwd: tempDir,
      stdio: "pipe",
    });
    execSync(`git config core.sparseCheckout true`, {
      cwd: tempDir,
      stdio: "pipe",
    });

    // Write all skill paths into the sparse-checkout file
    const sparseCheckoutFile = path.join(
      tempDir,
      ".git",
      "info",
      "sparse-checkout",
    );
    const paths = skills.map((s) => s.source.path).join("\n") + "\n";
    fs.writeFileSync(sparseCheckoutFile, paths);

    // Fetch and checkout
    execSync(`git fetch --depth 1 origin HEAD`, {
      cwd: tempDir,
      stdio: "pipe",
    });
    execSync(`git checkout FETCH_HEAD`, { cwd: tempDir, stdio: "pipe" });

    // Update each skill
    for (const skill of skills) {
      const sourceDir = path.join(tempDir, skill.source.path);

      if (!fs.existsSync(sourceDir)) {
        console.error(
          `  ✗ ${skill.name}: path "${skill.source.path}" not found in ${repoUrl}`,
        );
        continue;
      }

      // Check for SKILL.md in the upstream source
      const upstreamSkillMd = path.join(sourceDir, "SKILL.md");
      if (!fs.existsSync(upstreamSkillMd)) {
        console.error(
          `  ✗ ${skill.name}: no SKILL.md at upstream path, skipping`,
        );
        continue;
      }

      // Remove current skill contents (except .git artifacts, if any)
      const existingEntries = fs.readdirSync(skill.dir);
      for (const entry of existingEntries) {
        const entryPath = path.join(skill.dir, entry);
        const stat = fs.statSync(entryPath);
        if (stat.isDirectory()) {
          fs.rmSync(entryPath, { recursive: true });
        } else {
          fs.unlinkSync(entryPath);
        }
      }

      // Copy upstream files into the skill directory
      fs.cpSync(sourceDir, skill.dir, { recursive: true });

      // Re-apply source metadata to SKILL.md
      const newSkillMdPath = path.join(skill.dir, "SKILL.md");
      const newContent = fs.readFileSync(newSkillMdPath, "utf-8");
      const { data: newFrontmatter, content: body } = matter(newContent);

      // Ensure metadata object exists
      if (!newFrontmatter.metadata) {
        newFrontmatter.metadata = {};
      }

      // Preserve category from our local frontmatter if upstream doesn't set one
      if (
        !newFrontmatter.metadata.category &&
        skill.frontmatter?.metadata?.category
      ) {
        newFrontmatter.metadata.category =
          skill.frontmatter.metadata.category;
      }

      // Re-inject source info (upstream won't have this)
      newFrontmatter.metadata.source = {
        repository: skill.source.repository,
        path: skill.source.path,
      };

      const updatedContent = matter.stringify(body, newFrontmatter);
      fs.writeFileSync(newSkillMdPath, updatedContent);

      console.log(`  ✓ ${skill.name}`);
    }
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

async function main() {
  const args = process.argv.slice(2);
  const filter = args.length > 0 ? args : undefined;

  console.log(
    filter
      ? `Updating skills: ${filter.join(", ")}`
      : "Updating all skills from upstream sources...",
  );
  console.log();

  const skills = collectSkills(filter);

  if (skills.length === 0) {
    console.log("No skills with metadata.source found to update.");
    return;
  }

  const grouped = groupByRepo(skills);

  for (const [repoUrl, repoSkills] of grouped) {
    console.log(
      `${repoUrl} (${repoSkills.length} skill${repoSkills.length > 1 ? "s" : ""})`,
    );
    updateFromRepo(repoUrl, repoSkills);
    console.log();
  }

  console.log(`Done. Updated ${skills.length} skill(s).`);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
