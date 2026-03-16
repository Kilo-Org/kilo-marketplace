#!/usr/bin/env npx tsx
/**
 * Generate patch files for skills that have local modifications.
 *
 * For each skill with metadata.source, this script:
 * 1. Fetches the clean upstream version
 * 2. Applies the same frontmatter normalization that update-skills.ts does
 * 3. Diffs that against the local version
 * 4. Saves the diff as skills/<skill-name>/local.patch (if non-empty)
 *
 * Usage: npx tsx bin/generate-patches.ts [skill-name ...]
 *
 * With no arguments, generates patches for ALL skills that have metadata.source.
 * With arguments, generates patches only for the named skills.
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
  license_path?: string;
}

interface SkillInfo {
  name: string;
  dir: string;
  source: SourceInfo;
  frontmatter: Record<string, any>;
}

/**
 * Collect all skills that have a metadata.source field.
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
    if (!fs.existsSync(skillMdPath)) continue;

    const content = fs.readFileSync(skillMdPath, "utf-8");
    const { data: frontmatter } = matter(content);

    const source = frontmatter?.metadata?.source;
    if (!source?.repository || !source?.path) continue;

    skills.push({
      name: dir.name,
      dir: path.join(skillsDir, dir.name),
      source: {
        repository: source.repository,
        path: source.path,
        license_path: source.license_path,
      },
      frontmatter,
    });
  }

  return skills;
}

/**
 * Group skills by repository.
 */
function groupByRepo(skills: SkillInfo[]): Map<string, SkillInfo[]> {
  const map = new Map<string, SkillInfo[]>();
  for (const skill of skills) {
    const repo = skill.source.repository;
    if (!map.has(repo)) map.set(repo, []);
    map.get(repo)!.push(skill);
  }
  return map;
}

/**
 * Normalize upstream SKILL.md the same way update-skills.ts does:
 * - Ensure metadata object exists
 * - Preserve category from local frontmatter if upstream doesn't set one
 * - Inject source info
 */
function normalizeUpstreamSkillMd(
  upstreamContent: string,
  skill: SkillInfo,
): string {
  const { data: fm, content: body } = matter(upstreamContent);

  if (!fm.metadata) fm.metadata = {};

  if (!fm.metadata.category && skill.frontmatter?.metadata?.category) {
    fm.metadata.category = skill.frontmatter.metadata.category;
  }

  fm.metadata.source = {
    repository: skill.source.repository,
    path: skill.source.path,
    ...(skill.source.license_path && {
      license_path: skill.source.license_path,
    }),
  };

  return matter.stringify(body, fm);
}

/**
 * Recursively list all files in a directory, returning paths relative to the dir.
 */
function listFilesRecursive(dir: string, prefix = ""): string[] {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const relPath = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) {
      files.push(...listFilesRecursive(path.join(dir, entry.name), relPath));
    } else {
      files.push(relPath);
    }
  }
  return files.sort();
}

/**
 * Fetch upstream skills and generate patches by comparing with local versions.
 */
function generatePatchesFromRepo(
  repoUrl: string,
  skills: SkillInfo[],
): void {
  const tempDir = fs.mkdtempSync(path.join("/tmp", "skill-patch-"));

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

    // Write sparse-checkout paths
    const sparseCheckoutFile = path.join(
      tempDir,
      ".git",
      "info",
      "sparse-checkout",
    );
    const pathSet = new Set(skills.map((s) => s.source.path));
    for (const s of skills) {
      if (s.source.license_path) pathSet.add(s.source.license_path);
    }
    fs.writeFileSync(sparseCheckoutFile, [...pathSet].join("\n") + "\n");

    // Fetch and checkout
    execSync(`git fetch --depth 1 origin HEAD`, {
      cwd: tempDir,
      stdio: "pipe",
    });
    execSync(`git checkout FETCH_HEAD`, { cwd: tempDir, stdio: "pipe" });

    for (const skill of skills) {
      const upstreamSourceDir = path.join(tempDir, skill.source.path);

      if (!fs.existsSync(upstreamSourceDir)) {
        console.error(
          `  ✗ ${skill.name}: path "${skill.source.path}" not found upstream`,
        );
        continue;
      }

      // Create a "normalized upstream" temp directory that mirrors what
      // update-skills.ts would produce (before patches)
      const normalizedDir = path.join(tempDir, `_normalized_${skill.name}`);
      fs.mkdirSync(normalizedDir, { recursive: true });
      fs.cpSync(upstreamSourceDir, normalizedDir, { recursive: true });

      // Handle license_path copying (same as update-skills.ts)
      if (skill.source.license_path) {
        const licenseSrc = path.join(tempDir, skill.source.license_path);
        if (fs.existsSync(licenseSrc)) {
          fs.copyFileSync(licenseSrc, path.join(normalizedDir, "LICENSE"));
        }
      }

      // Normalize SKILL.md frontmatter
      const normalizedSkillMd = path.join(normalizedDir, "SKILL.md");
      if (fs.existsSync(normalizedSkillMd)) {
        const upstreamContent = fs.readFileSync(normalizedSkillMd, "utf-8");
        const normalized = normalizeUpstreamSkillMd(upstreamContent, skill);
        fs.writeFileSync(normalizedSkillMd, normalized);
      }

      // Generate unified diff between normalized upstream and local
      try {
        const diff = execSync(
          `diff -ruN "${normalizedDir}" "${skill.dir}"`,
          { encoding: "utf-8" },
        );
        // diff exits 0 = no differences
        const patchPath = path.join(skill.dir, "local.patch");
        if (fs.existsSync(patchPath)) {
          fs.unlinkSync(patchPath);
          console.log(`  - ${skill.name}: no local modifications (removed stale patch)`);
        } else {
          console.log(`  - ${skill.name}: no local modifications`);
        }
      } catch (err: any) {
        if (err.status === 1) {
          // diff exits 1 = differences found
          let diffOutput: string = err.stdout;

          // Post-process the diff to use relative paths instead of absolute temp paths
          // Replace the normalized temp dir path with a/ prefix
          // Replace the local skill dir path with b/ prefix
          diffOutput = diffOutput
            .replace(new RegExp(escapeRegExp(normalizedDir), "g"), `a/${skill.name}`)
            .replace(new RegExp(escapeRegExp(skill.dir), "g"), `b/${skill.name}`);

          // Filter out the local.patch file itself from the diff
          diffOutput = filterOutPatchFile(diffOutput, skill.name);

          if (diffOutput.trim() === "") {
            const patchPath = path.join(skill.dir, "local.patch");
            if (fs.existsSync(patchPath)) {
              fs.unlinkSync(patchPath);
              console.log(`  - ${skill.name}: no local modifications (removed stale patch)`);
            } else {
              console.log(`  - ${skill.name}: no local modifications`);
            }
            continue;
          }

          const patchPath = path.join(skill.dir, "local.patch");
          fs.writeFileSync(patchPath, diffOutput);
          console.log(`  ✓ ${skill.name}: patch saved`);
        } else {
          console.error(`  ✗ ${skill.name}: diff failed: ${err.message}`);
        }
      }
    }
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

/**
 * Escape a string for use in a RegExp.
 */
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Filter out diff hunks that only relate to the local.patch file itself.
 */
function filterOutPatchFile(diffOutput: string, skillName: string): string {
  // Split diff into per-file sections (each starts with "diff -ruN")
  const sections = diffOutput.split(/(?=^diff -ruN )/m);
  const filtered = sections.filter((section) => {
    return !section.includes(`local.patch`);
  });
  return filtered.join("");
}

async function main() {
  const args = process.argv.slice(2);
  const filter = args.length > 0 ? args : undefined;

  console.log(
    filter
      ? `Generating patches for: ${filter.join(", ")}`
      : "Generating patches for all skills with upstream sources...",
  );
  console.log();

  const skills = collectSkills(filter);

  if (skills.length === 0) {
    console.log("No skills with metadata.source found.");
    return;
  }

  const grouped = groupByRepo(skills);

  for (const [repoUrl, repoSkills] of grouped) {
    console.log(
      `${repoUrl} (${repoSkills.length} skill${repoSkills.length > 1 ? "s" : ""})`,
    );
    generatePatchesFromRepo(repoUrl, repoSkills);
    console.log();
  }

  console.log("Done.");
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
