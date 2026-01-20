#!/usr/bin/env npx tsx
/**
 * Add a remote skill from a GitHub repository.
 *
 * Usage: npx tsx bin/add-remote-skill.ts <github-url-with-path>
 *
 * Example:
 *   npx tsx bin/add-remote-skill.ts https://github.com/vercel-labs/agent-skills/tree/main/skills/claude.ai/web-design-guidelines
 *   npx tsx bin/add-remote-skill.ts https://github.com/google-gemini/gemini-cli/tree/main/.gemini/skills/pr-creator
 *
 * This script will:
 * 1. Clone/download the specified directory from the GitHub repo
 * 2. Copy it to the local skills directory
 * 3. Update the SKILL.md frontmatter to add source metadata and category if missing
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";
import matter from "gray-matter";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsDir = path.join(__dirname, "..", "skills");

function parseGitHubUrl(url: string): {
  owner: string;
  repo: string;
  skillPath: string;
} {
  // Handle GitHub URL with path: https://github.com/owner/repo/tree/branch/path/to/skill
  const treePattern =
    /github\.com\/([^\/]+)\/([^\/]+)\/tree\/[^\/]+\/(.+?)(?:\/)?$/;
  const treeMatch = url.match(treePattern);
  if (treeMatch) {
    return { owner: treeMatch[1], repo: treeMatch[2], skillPath: treeMatch[3] };
  }

  // Handle GitHub URL with blob (file): https://github.com/owner/repo/blob/branch/path/to/file
  const blobPattern =
    /github\.com\/([^\/]+)\/([^\/]+)\/blob\/[^\/]+\/(.+?)(?:\/)?$/;
  const blobMatch = url.match(blobPattern);
  if (blobMatch) {
    // Get the directory containing the file
    const filePath = blobMatch[3];
    const dirPath = path.dirname(filePath);
    return { owner: blobMatch[1], repo: blobMatch[2], skillPath: dirPath };
  }

  throw new Error(
    `Invalid GitHub URL: ${url}\n\nExpected format: https://github.com/owner/repo/tree/branch/path/to/skill`,
  );
}

function getSkillName(skillPath: string): string {
  // Get the last component of the path as the skill name
  return path.basename(skillPath);
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error(
      "Usage: npx tsx bin/add-remote-skill.ts <github-url-with-path>",
    );
    console.error(
      "\nExample: npx tsx bin/add-remote-skill.ts https://github.com/vercel-labs/agent-skills/tree/main/skills/claude.ai/web-design-guidelines",
    );
    console.error(
      "         npx tsx bin/add-remote-skill.ts https://github.com/google-gemini/gemini-cli/tree/main/.gemini/skills/pr-creator",
    );
    process.exit(1);
  }

  const [fullUrl] = args;

  const { owner, repo, skillPath } = parseGitHubUrl(fullUrl);
  const skillName = getSkillName(skillPath);
  const targetDir = path.join(skillsDir, skillName);

  console.log(`Adding skill from ${owner}/${repo}:${skillPath}`);
  console.log(`Target directory: ${targetDir}`);

  // Check if target already exists
  if (fs.existsSync(targetDir)) {
    console.error(`Error: Skill directory already exists: ${targetDir}`);
    console.error("Remove it first if you want to re-add the skill.");
    process.exit(1);
  }

  // Create a temporary directory for sparse checkout
  const tempDir = fs.mkdtempSync(path.join("/tmp", "skill-"));

  try {
    console.log("\nCloning repository (sparse checkout)...");

    // Initialize a sparse checkout
    execSync(`git init`, { cwd: tempDir, stdio: "pipe" });
    execSync(`git remote add origin https://github.com/${owner}/${repo}.git`, {
      cwd: tempDir,
      stdio: "pipe",
    });
    execSync(`git config core.sparseCheckout true`, {
      cwd: tempDir,
      stdio: "pipe",
    });

    // Set up sparse checkout for just the skill directory
    fs.writeFileSync(
      path.join(tempDir, ".git", "info", "sparse-checkout"),
      skillPath + "\n",
    );

    // Fetch and checkout
    execSync(`git fetch --depth 1 origin HEAD`, { cwd: tempDir, stdio: "pipe" });
    execSync(`git checkout FETCH_HEAD`, { cwd: tempDir, stdio: "pipe" });

    const sourceDir = path.join(tempDir, skillPath);

    if (!fs.existsSync(sourceDir)) {
      throw new Error(`Skill directory not found in repository: ${skillPath}`);
    }

    // Copy the skill directory
    console.log(`Copying skill to ${targetDir}...`);
    fs.cpSync(sourceDir, targetDir, { recursive: true });

    // Update the SKILL.md frontmatter
    const skillMdPath = path.join(targetDir, "SKILL.md");
    if (!fs.existsSync(skillMdPath)) {
      throw new Error(`SKILL.md not found in ${targetDir}`);
    }

    console.log("Updating SKILL.md frontmatter...");
    const content = fs.readFileSync(skillMdPath, "utf-8");
    const { data: frontmatter, content: body } = matter(content);

    // Ensure metadata object exists
    if (!frontmatter.metadata) {
      frontmatter.metadata = {};
    }

    // Add category if not present
    if (!frontmatter.metadata.category) {
      frontmatter.metadata.category = "unknown";
      console.log("  Added category: unknown");
    }

    // Add source information
    frontmatter.metadata.source = {
      repository: `https://github.com/${owner}/${repo}`,
      path: skillPath,
    };
    console.log(`  Added source: https://github.com/${owner}/${repo}`);
    console.log(`  Added path: ${skillPath}`);

    // Write back the updated SKILL.md
    const updatedContent = matter.stringify(body, frontmatter);
    fs.writeFileSync(skillMdPath, updatedContent);

    console.log(`\n✓ Successfully added skill: ${skillName}`);
    console.log(`  Location: ${targetDir}`);
  } finally {
    // Clean up temp directory
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
