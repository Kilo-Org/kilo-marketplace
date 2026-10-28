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

const licenseFileNames = new Set([
  "LICENSE",
  "LICENSE.txt",
  "LICENSE.md",
  "COPYING",
  "COPYING.txt",
  "COPYING.md",
]);

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

    validateSourcePath(source.path, dir.name);
    if (source.license_path) validateSourcePath(source.license_path, dir.name);
    if (source.ref && /[\r\n]/.test(source.ref)) {
      throw new Error(`${dir.name}: metadata.source.ref contains a newline`);
    }
    if (!source.commit || !/^[0-9a-f]{40}$/.test(source.commit)) {
      throw new Error(
        `${dir.name}: run update-skills.ts first to record metadata.source.commit`,
      );
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
 * Group skills by repository and recorded source commit.
 */
function groupBySource(skills: SkillInfo[]): SourceGroup[] {
  const map = new Map<string, SourceGroup>();
  for (const skill of skills) {
    const ref = skill.source.commit!;
    const key = `${skill.source.repository}\n${ref}`;
    if (!map.has(key)) {
      map.set(key, {
        repository: skill.source.repository,
        ref,
        skills: [],
      });
    }
    map.get(key)!.skills.push(skill);
  }
  return [...map.values()];
}

/**
 * Normalize upstream SKILL.md the same way update-skills.ts does:
 * - Ensure metadata object exists
 * - Preserve marketplace-owned metadata from local frontmatter
 * - Inject source info
 */
function normalizeUpstreamSkillMd(
  upstreamContent: string,
  skill: SkillInfo,
): string {
  const { data: upstreamFrontmatter, content: body } = matter(upstreamContent);
  const fm = { ...upstreamFrontmatter };
  fm.metadata = { ...(fm.metadata ?? {}) };

  const upstreamMetadata: Record<string, unknown> = {};
  for (const key of Object.keys(fm)) {
    if (!allowedFrontmatterFields.has(key)) {
      const value = fm[key];
      const isEmptyCollection =
        (Array.isArray(value) && value.length === 0) ||
        (value &&
          typeof value === "object" &&
          !Array.isArray(value) &&
          Object.keys(value).length === 0);
      if (!isEmptyCollection) upstreamMetadata[key] = value;
      delete fm[key];
    }
  }
  if (Object.keys(upstreamMetadata).length > 0) {
    fm.metadata.upstream = {
      ...(fm.metadata.upstream ?? {}),
      ...upstreamMetadata,
    };
  }

  fm.name = skill.name;
  if (skill.frontmatter?.metadata?.category) {
    fm.metadata.category = skill.frontmatter.metadata.category;
  }
  if (skill.frontmatter?.metadata?.suggest_for) {
    fm.metadata.suggest_for = skill.frontmatter.metadata.suggest_for;
  }
  if (!skill.source.license_path && skill.frontmatter?.license && !fm.license) {
    fm.license = skill.frontmatter.license;
  }

  fm.metadata.source = {
    repository: skill.source.repository,
    path: skill.source.path,
    ...(skill.source.license_path && {
      license_path: skill.source.license_path,
    }),
    ...(skill.source.ref && { ref: skill.source.ref }),
    commit: skill.source.commit,
  };
  if (skill.source.license_path) {
    delete fm.license;
  }

  return ensureFinalNewline(matter.stringify(body, fm));
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

function applyLocalRemovals(
  skillName: string,
  skillDir: string,
  normalizedDir: string,
): void {
  const removePath = path.join(skillDir, "local.remove");
  if (!fs.existsSync(removePath)) return;

  const entries = fs
    .readFileSync(removePath, "utf-8")
    .split(/\r?\n/)
    .map((entry) => entry.trim())
    .filter((entry) => entry && !entry.startsWith("#"));

  for (const entry of entries) {
    const target = path.resolve(normalizedDir, entry);
    const relativeTarget = path.relative(normalizedDir, target);
    if (
      relativeTarget === "" ||
      relativeTarget.startsWith("..") ||
      path.isAbsolute(relativeTarget)
    ) {
      throw new Error(`${skillName}: invalid local.remove path: ${entry}`);
    }

    let current = normalizedDir;
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
    if (fs.existsSync(target)) {
      fs.rmSync(target, { recursive: true, force: true });
    }
  }
}

function seedLicenseFiles(sourceDir: string, destinationDir: string): void {
  for (const licenseName of licenseFileNames) {
    const sourcePath = path.join(sourceDir, licenseName);
    const destinationPath = path.join(destinationDir, licenseName);
    if (
      fs.existsSync(sourcePath) &&
      fs.statSync(sourcePath).isFile() &&
      !fs.existsSync(destinationPath)
    ) {
      fs.copyFileSync(sourcePath, destinationPath);
    }
  }
}

/**
 * Fetch upstream skills and generate patches by comparing with local versions.
 */
function generatePatchesFromRepo(
  repoUrl: string,
  ref: string,
  skills: SkillInfo[],
): void {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "skill-patch-"));

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

    // Write sparse-checkout paths
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
    fs.writeFileSync(sparseCheckoutFile, [...pathSet].join("\n") + "\n");

    // Fetch and checkout
    execFileSync("git", ["fetch", "--depth", "1", "origin", ref], {
      cwd: tempDir,
      stdio: "pipe",
    });
    execFileSync("git", ["checkout", "FETCH_HEAD"], {
      cwd: tempDir,
      stdio: "pipe",
    });

    for (const skill of skills) {
      const upstreamSourceDir = path.join(tempDir, skill.source.path);

      if (
        !fs.existsSync(upstreamSourceDir) ||
        !fs.statSync(upstreamSourceDir).isDirectory()
      ) {
        throw new Error(
          `${skill.name}: directory "${skill.source.path}" not found upstream`,
        );
      }

      // Create a "normalized upstream" temp directory that mirrors what
      // update-skills.ts would produce (before patches). Keep it outside the
      // checkout so repository-root skills cannot recursively copy into it.
      const normalizedRoot = fs.mkdtempSync(
        path.join(os.tmpdir(), "skill-normalized-"),
      );
      const normalizedParent = path.join(normalizedRoot, "a");
      const localParent = path.join(normalizedRoot, "b");
      const normalizedDir = path.join(normalizedParent, skill.name);
      const localComparisonDir = path.join(localParent, skill.name);
      fs.mkdirSync(normalizedDir, { recursive: true });
      fs.mkdirSync(localComparisonDir, { recursive: true });
      copySkillSource(upstreamSourceDir, normalizedDir, tempDir);
      fs.cpSync(skill.dir, localComparisonDir, { recursive: true });

      // Handle license_path copying (same as update-skills.ts)
      if (skill.source.license_path) {
        const licenseSrc = path.join(tempDir, skill.source.license_path);
        if (!fs.existsSync(licenseSrc) || !fs.statSync(licenseSrc).isFile()) {
          throw new Error(
            `${skill.name}: license_path "${skill.source.license_path}" not found upstream`,
          );
        }
        fs.copyFileSync(licenseSrc, path.join(normalizedDir, "LICENSE"));
        fs.copyFileSync(licenseSrc, path.join(localComparisonDir, "LICENSE"));
      }

      seedLicenseFiles(normalizedDir, localComparisonDir);
      seedLicenseFiles(localComparisonDir, normalizedDir);

      applyLocalRemovals(skill.name, skill.dir, normalizedDir);
      applyLocalRemovals(skill.name, skill.dir, localComparisonDir);
      normalizeTextWhitespace(normalizedDir);
      normalizeTextWhitespace(localComparisonDir);

      // Normalize both SKILL.md files with marketplace-owned metadata.
      for (const skillMdPath of [
        path.join(normalizedDir, "SKILL.md"),
        path.join(localComparisonDir, "SKILL.md"),
      ]) {
        if (fs.existsSync(skillMdPath)) {
          const content = fs.readFileSync(skillMdPath, "utf-8");
          fs.writeFileSync(
            skillMdPath,
            normalizeUpstreamSkillMd(content, skill),
          );
        }
      }

      // Generate unified diff between normalized upstream and local
      try {
        const diff = spawnSync(
          "diff",
          [
            "-rN",
            "-U0",
            "--ignore-trailing-space",
            path.join("a", skill.name),
            path.join("b", skill.name),
          ],
          { cwd: normalizedRoot, encoding: "utf-8" },
        );
        if (diff.status !== 0) {
          const output = `${diff.stdout ?? ""}${diff.stderr ?? ""}`.trim();
          throw Object.assign(new Error(output || "diff failed"), {
            status: diff.status,
            stdout: diff.stdout ?? "",
          });
        }
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

          // Normalize only diff header timestamps; diff paths are already relative
          // because diff runs from normalizedRoot.
          diffOutput = diffOutput
            .replace(
              /^(---|\+\+\+) ([^\t\n]+)\t(.*)$/gm,
              (_line, marker, file, timestamp) => {
                const missing = /^(?:1969-12-31|1970-01-01)/.test(timestamp);
                const fixedTimestamp = missing
                  ? "1970-01-01 00:00:00.000000000 +0000"
                  : "2000-01-01 00:00:00.000000000 +0000";
                return `${marker} ${file}\t${fixedTimestamp}`;
              },
            );

          // Filter out local control files from the diff
          diffOutput = filterOutControlFiles(diffOutput);
          diffOutput = stripTrailingWhitespace(diffOutput);

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
          throw new Error(`${skill.name}: diff failed: ${err.message}`);
        }
      } finally {
        fs.rmSync(normalizedRoot, { recursive: true, force: true });
      }
    }
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

/**
 * Filter out diff hunks that only relate to local control files.
 */
function filterOutControlFiles(diffOutput: string): string {
  // Split diff into per-file sections (each starts with "diff ...")
  const sections = diffOutput.split(/(?=^diff )/m);
  const filtered = sections.filter((section) => {
    const firstLine = section.split(/\r?\n/, 1)[0] ?? "";
    const match = firstLine.match(/^diff .* (\S+) (\S+)$/);
    if (!match) return true;
    return (
      ![match[1], match[2]].some(isGeneratedFilePath) &&
      !isWhitespaceOnlySection(section)
    );
  });
  return filtered.join("");
}

function isGeneratedFilePath(filePath: string): boolean {
  const normalizedPath = filePath.replace(/\\/g, "/");
  const relativePath = normalizedPath.replace(/^[ab]\/[^/]+\//, "");
  return (
    relativePath === "local.patch" ||
    relativePath === "local.remove" ||
    licenseFileNames.has(relativePath)
  );
}

function stripTrailingWhitespace(content: string): string {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  return ensureFinalNewline(
    lines
      .map((line) => {
        const marker = line[0];
        const isPatchBodyLine =
          [" ", "+", "-"].includes(marker) &&
          !line.startsWith("--- ") &&
          !line.startsWith("+++ ");
        if (isPatchBodyLine) {
          return marker + line.slice(1).replace(/[ \t]+$/, "");
        }
        return line.replace(/[ \t]+$/, "");
      })
      .join("\n"),
  );
}

function isWhitespaceOnlySection(section: string): boolean {
  const removed: string[] = [];
  const added: string[] = [];
  for (const line of section.split(/\r?\n/)) {
    if (line.startsWith("--- ") || line.startsWith("+++ ")) continue;
    if (line.startsWith("-") && !line.startsWith("diff ")) {
      removed.push(line.slice(1).replace(/[ \t]+$/, ""));
    } else if (line.startsWith("+")) {
      added.push(line.slice(1).replace(/[ \t]+$/, ""));
    }
  }
  return (
    removed.length > 0 &&
    removed.length === added.length &&
    removed.every((line, index) => line === added[index])
  );
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

  const grouped = groupBySource(skills);

  for (const group of grouped) {
    console.log(
      `${group.repository}@${group.ref} (${group.skills.length} skill${group.skills.length > 1 ? "s" : ""})`,
    );
    generatePatchesFromRepo(group.repository, group.ref, group.skills);
    console.log();
  }

  console.log("Done.");
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
