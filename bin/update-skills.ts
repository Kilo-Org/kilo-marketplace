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
import { execFileSync, spawnSync } from "child_process";
import * as os from "os";
import matter from "gray-matter";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsDir = path.join(__dirname, "..", "skills");

interface SourceInfo {
  repository: string;
  path: string;
  license_path?: string;
  ref?: string;
  commit?: string;
}

interface SkillInfo {
  name: string;
  dir: string;
  source: SourceInfo;
  frontmatter: Record<string, any>;
}

interface UpdateCounts {
  updated: number;
  failed: number;
}

const allowedFrontmatterFields = new Set([
  "name",
  "description",
  "license",
  "allowed-tools",
  "metadata",
  "compatibility",
]);

function ensureFinalNewline(content: string): string {
  return content.replace(/(?:\r?\n)+$/, "") + "\n";
}

function normalizeTextWhitespace(rootDir: string): void {
  for (const entry of fs.readdirSync(rootDir, { withFileTypes: true })) {
    const entryPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      normalizeTextWhitespace(entryPath);
      continue;
    }
    if (!entry.isFile()) continue;
    const data = fs.readFileSync(entryPath);
    if (data.includes(0)) continue;
    const text = data.toString("utf-8");
    const normalized = ensureFinalNewline(
      text.replace(/\r\n/g, "\n").replace(/[ \t]+$/gm, ""),
    );
    if (normalized !== text) fs.writeFileSync(entryPath, normalized);
  }
}

function sparseCheckoutPath(sourcePath: string): string {
  return sourcePath === "." ? "/*" : sourcePath;
}

function validateSourcePath(sourcePath: string, skillName: string): void {
  if (
    path.isAbsolute(sourcePath) ||
    sourcePath.split(/[\\/]/).some((part) => part === "..") ||
    /[\r\n]/.test(sourcePath)
  ) {
    throw new Error(`${skillName}: invalid source path: ${sourcePath}`);
  }
}

function normalizeFrontmatter(
  upstreamFrontmatter: Record<string, any>,
  skill: SkillInfo,
  sourceCommit?: string,
): Record<string, any> {
  const normalized = { ...upstreamFrontmatter };
  normalized.metadata = { ...(normalized.metadata ?? {}) };

  const upstreamMetadata: Record<string, unknown> = {};
  for (const key of Object.keys(normalized)) {
    if (!allowedFrontmatterFields.has(key)) {
      const value = normalized[key];
      const isEmptyCollection =
        (Array.isArray(value) && value.length === 0) ||
        (value &&
          typeof value === "object" &&
          !Array.isArray(value) &&
          Object.keys(value).length === 0);
      if (!isEmptyCollection) upstreamMetadata[key] = value;
      delete normalized[key];
    }
  }
  if (Object.keys(upstreamMetadata).length > 0) {
    normalized.metadata.upstream = {
      ...(normalized.metadata.upstream ?? {}),
      ...upstreamMetadata,
    };
  }

  normalized.name = skill.name;
  if (skill.frontmatter?.metadata?.category) {
    normalized.metadata.category = skill.frontmatter.metadata.category;
  }
  if (skill.frontmatter?.metadata?.suggest_for) {
    normalized.metadata.suggest_for = skill.frontmatter.metadata.suggest_for;
  }
  if (!skill.source.license_path && skill.frontmatter?.license && !normalized.license) {
    normalized.license = skill.frontmatter.license;
  }
  normalized.metadata.source = {
    repository: skill.source.repository,
    path: skill.source.path,
    ...(skill.source.license_path && {
      license_path: skill.source.license_path,
    }),
    ...(skill.source.ref && { ref: skill.source.ref }),
    ...(sourceCommit && { commit: sourceCommit }),
  };
  if (skill.source.license_path) {
    delete normalized.license;
  }

  return normalized;
}

function copySkillSource(
  sourceDir: string,
  destinationDir: string,
  checkoutDir: string,
): void {
  const gitDir = path.resolve(checkoutDir, ".git");
  fs.cpSync(sourceDir, destinationDir, {
    recursive: true,
    filter: (source) => {
      const resolved = path.resolve(source);
      return resolved !== gitDir && !resolved.startsWith(`${gitDir}${path.sep}`);
    },
  });
}

function applyLocalRemovals(
  skillName: string,
  stagedDir: string,
  removeContent: string,
): void {
  const entries = removeContent
    .split(/\r?\n/)
    .map((entry) => entry.trim())
    .filter((entry) => entry && !entry.startsWith("#"));

  for (const entry of entries) {
    const target = path.resolve(stagedDir, entry);
    const relativeTarget = path.relative(stagedDir, target);
    if (
      relativeTarget === "" ||
      relativeTarget.startsWith("..") ||
      path.isAbsolute(relativeTarget)
    ) {
      throw new Error(`${skillName}: invalid local.remove path: ${entry}`);
    }

    let current = stagedDir;
    for (const component of relativeTarget.split(path.sep)) {
      current = path.join(current, component);
      try {
        if (fs.lstatSync(current).isSymbolicLink()) {
          throw new Error(
            `${skillName}: local.remove path crosses a symlink: ${entry}`,
          );
        }
      } catch (error: any) {
        if (error.code !== "ENOENT") throw error;
        break;
      }
    }
    if (fs.existsSync(target)) fs.rmSync(target, { recursive: true });
  }
}

function validateStagedSkill(stagedDir: string, skillName: string): void {
  const skillMdPath = path.join(stagedDir, "SKILL.md");
  if (!fs.existsSync(skillMdPath) || !fs.statSync(skillMdPath).isFile()) {
    throw new Error(`${skillName}: staged update has no SKILL.md`);
  }
  const { data } = matter(fs.readFileSync(skillMdPath, "utf-8"));
  if (data.name !== skillName) {
    throw new Error(`${skillName}: staged name is "${data.name ?? "missing"}"`);
  }
  if (typeof data.description !== "string" || data.description.trim() === "") {
    throw new Error(`${skillName}: staged description is missing`);
  }
}

function replaceSkillAtomically(skillDir: string, stagedDir: string): void {
  const backupDir = `${skillDir}.backup-${process.pid}-${Date.now()}`;
  fs.renameSync(skillDir, backupDir);
  try {
    fs.renameSync(stagedDir, skillDir);
    fs.rmSync(backupDir, { recursive: true, force: true });
  } catch (error) {
    if (fs.existsSync(skillDir)) {
      fs.rmSync(skillDir, { recursive: true, force: true });
    }
    fs.renameSync(backupDir, skillDir);
    throw error;
  }
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

    validateSourcePath(source.path, dir.name);
    if (source.license_path) validateSourcePath(source.license_path, dir.name);
    if (source.ref && /[\r\n]/.test(source.ref)) {
      throw new Error(`${dir.name}: metadata.source.ref contains a newline`);
    }
    if (source.commit && !/^[0-9a-f]{40}$/.test(source.commit)) {
      throw new Error(`${dir.name}: metadata.source.commit must be a full Git SHA`);
    }

    skills.push({
      name: dir.name,
      dir: path.join(skillsDir, dir.name),
      source: {
        repository: source.repository,
        path: source.path,
        license_path: source.license_path,
        ref: source.ref,
        commit: source.commit,
      },
      frontmatter,
    });
  }

  return skills;
}

interface SourceGroup {
  repository: string;
  ref: string;
  skills: SkillInfo[];
}

/**
 * Group skills by repository and tracked ref so we can batch fetches.
 */
function groupBySource(skills: SkillInfo[]): SourceGroup[] {
  const groups = new Map<string, SourceGroup>();
  for (const skill of skills) {
    const ref = skill.source.ref ?? "HEAD";
    const key = `${skill.source.repository}\n${ref}`;
    if (!groups.has(key)) {
      groups.set(key, {
        repository: skill.source.repository,
        ref,
        skills: [],
      });
    }
    groups.get(key)!.skills.push(skill);
  }
  return [...groups.values()];
}

/**
 * Try to apply a patch file to a skill directory.
 * Returns true if patch applied successfully, false otherwise.
 */
function applyPatch(skillDir: string, patchContent: string): boolean {
  const args = [
    "apply",
    "--binary",
    "--ignore-whitespace",
    "--unidiff-zero",
    "--recount",
    "-p2",
  ];
  const check = spawnSync("git", [...args, "--check", "-"], {
    cwd: skillDir,
    input: patchContent,
    encoding: "utf-8",
  });
  if (check.status !== 0) {
    const output = `${check.stdout ?? ""}${check.stderr ?? ""}`.trim();
    if (output) console.error(output);
    return false;
  }

  const applied = spawnSync("git", [...args, "-"], {
    cwd: skillDir,
    input: patchContent,
    encoding: "utf-8",
  });
  if (applied.status !== 0) {
    const output = `${applied.stdout ?? ""}${applied.stderr ?? ""}`.trim();
    if (output) console.error(output);
    return false;
  }
  return true;
}

/**
 * Fetch all skills from a single repository via sparse checkout,
 * then copy each skill directory over the local one and re-apply
 * the source metadata.
 */
function updateFromRepo(
  repoUrl: string,
  ref: string,
  skills: SkillInfo[],
): UpdateCounts {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "skill-update-"));
  const counts: UpdateCounts = { updated: 0, failed: 0 };

  try {
    // Init sparse checkout
    execFileSync("git", ["init"], { cwd: tempDir, stdio: "pipe" });
    execFileSync("git", ["remote", "add", "origin", `${repoUrl}.git`], {
      cwd: tempDir,
      stdio: "pipe",
    });
    execFileSync("git", ["config", "core.sparseCheckout", "true"], {
      cwd: tempDir,
      stdio: "pipe",
    });

    // Write all skill paths (and any license paths) into the sparse-checkout file
    const sparseCheckoutFile = path.join(
      tempDir,
      ".git",
      "info",
      "sparse-checkout",
    );
    const pathSet = new Set(
      skills.map((s) => sparseCheckoutPath(s.source.path)),
    );
    for (const s of skills) {
      if (s.source.license_path) {
        pathSet.add(sparseCheckoutPath(s.source.license_path));
      }
    }
    const paths = [...pathSet].join("\n") + "\n";
    fs.writeFileSync(sparseCheckoutFile, paths);

    // Fetch and checkout
    execFileSync("git", ["fetch", "--depth", "1", "origin", ref], {
      cwd: tempDir,
      stdio: "pipe",
    });
    execFileSync("git", ["checkout", "FETCH_HEAD"], {
      cwd: tempDir,
      stdio: "pipe",
    });
    const fetchedCommit = execFileSync(
      "git",
      ["rev-parse", "FETCH_HEAD"],
      { cwd: tempDir, encoding: "utf-8" },
    ).trim();

    // Update each skill
    for (const skill of skills) {
      const sourceDir = path.join(tempDir, skill.source.path);

      if (!fs.existsSync(sourceDir) || !fs.statSync(sourceDir).isDirectory()) {
        console.error(
          `  ✗ ${skill.name}: directory "${skill.source.path}" not found in ${repoUrl}`,
        );
        counts.failed += 1;
        continue;
      }

      const stagedDir = fs.mkdtempSync(
        path.join(skillsDir, ".skill-stage-"),
      );
      try {
        const patchPath = path.join(skill.dir, "local.patch");
        const savedPatch = fs.existsSync(patchPath)
          ? fs.readFileSync(patchPath, "utf-8")
          : null;
        const removePath = path.join(skill.dir, "local.remove");
        const savedRemove = fs.existsSync(removePath)
          ? fs.readFileSync(removePath, "utf-8")
          : null;

        let savedLicense: { name: string; content: Buffer } | null = null;
        for (const licenseName of ["LICENSE", "LICENSE.txt"]) {
          const licensePath = path.join(skill.dir, licenseName);
          if (fs.existsSync(licensePath)) {
            savedLicense = {
              name: licenseName,
              content: fs.readFileSync(licensePath),
            };
            break;
          }
        }

        copySkillSource(sourceDir, stagedDir, tempDir);

        const newSkillMdPath = path.join(stagedDir, "SKILL.md");
        if (fs.existsSync(newSkillMdPath) && fs.statSync(newSkillMdPath).isFile()) {
          const newContent = fs.readFileSync(newSkillMdPath, "utf-8");
          const { data: newFrontmatter, content: body } = matter(newContent);
          const normalizedFrontmatter = normalizeFrontmatter(
            newFrontmatter,
            skill,
            skill.source.commit,
          );
          fs.writeFileSync(
            newSkillMdPath,
            ensureFinalNewline(matter.stringify(body, normalizedFrontmatter)),
          );
        } else if (!savedPatch) {
          throw new Error(`${skill.name}: no SKILL.md at upstream path`);
        }

        if (skill.source.license_path) {
          const licenseSrc = path.join(tempDir, skill.source.license_path);
          if (!fs.existsSync(licenseSrc) || !fs.statSync(licenseSrc).isFile()) {
            throw new Error(
              `${skill.name}: license_path "${skill.source.license_path}" not found in ${repoUrl}`,
            );
          }
          fs.copyFileSync(licenseSrc, path.join(stagedDir, "LICENSE"));
        }

        const hasLicense =
          fs.existsSync(path.join(stagedDir, "LICENSE")) ||
          fs.existsSync(path.join(stagedDir, "LICENSE.txt"));
        if (!hasLicense && savedLicense) {
          fs.writeFileSync(
            path.join(stagedDir, savedLicense.name),
            savedLicense.content,
          );
        }

        if (savedRemove) {
          applyLocalRemovals(skill.name, stagedDir, savedRemove);
          fs.writeFileSync(path.join(stagedDir, "local.remove"), savedRemove);
        }

        normalizeTextWhitespace(stagedDir);

        if (savedPatch) {
          if (!applyPatch(stagedDir, savedPatch)) {
            throw new Error(`${skill.name}: local.patch failed to apply cleanly`);
          }
          fs.writeFileSync(path.join(stagedDir, "local.patch"), savedPatch);
        }

        normalizeTextWhitespace(stagedDir);

        // A patch may touch frontmatter; marketplace identity and provenance win.
        const finalContent = fs.readFileSync(newSkillMdPath, "utf-8");
        const { data: finalFrontmatter, content: finalBody } = matter(finalContent);
        const finalNormalizedFrontmatter = normalizeFrontmatter(
          finalFrontmatter,
          skill,
          fetchedCommit,
        );
        fs.writeFileSync(
          newSkillMdPath,
          ensureFinalNewline(
            matter.stringify(finalBody, finalNormalizedFrontmatter),
          ),
        );

        validateStagedSkill(stagedDir, skill.name);
        replaceSkillAtomically(skill.dir, stagedDir);
        counts.updated += 1;
        console.log(
          savedPatch
            ? `  ✓ ${skill.name} (patch applied)`
            : `  ✓ ${skill.name}`,
        );
      } catch (error: any) {
        counts.failed += 1;
        console.error(`  ✗ ${skill.name}: ${error.message}`);
      } finally {
        if (fs.existsSync(stagedDir)) {
          fs.rmSync(stagedDir, { recursive: true, force: true });
        }
      }
    }
    return counts;
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

  if (filter) {
    const collected = new Set(skills.map((skill) => skill.name));
    const missing = filter.filter((name) => !collected.has(name));
    if (missing.length > 0) {
      throw new Error(
        `Unknown skills or missing metadata.source: ${missing.join(", ")}`,
      );
    }
  }

  if (skills.length === 0) {
    console.log("No skills with metadata.source found to update.");
    return;
  }

  const grouped = groupBySource(skills);
  const totals: UpdateCounts = { updated: 0, failed: 0 };

  for (const group of grouped) {
    console.log(
      `${group.repository}@${group.ref} (${group.skills.length} skill${group.skills.length > 1 ? "s" : ""})`,
    );
    const counts = updateFromRepo(
      group.repository,
      group.ref,
      group.skills,
    );
    totals.updated += counts.updated;
    totals.failed += counts.failed;
    console.log();
  }

  console.log(
    `Done. Updated ${totals.updated} skill(s); ${totals.failed} failed.`,
  );
  if (totals.failed > 0) process.exitCode = 1;
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
