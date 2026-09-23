#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from individual plugin directories.
 *
 * Usage: npx tsx bin/generate-plugins-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import { pathToFileURL } from "url";
import npa from "npm-package-arg";
import validate from "validate-npm-package-name";
import * as yaml from "yaml";
import {
  buildCategorySummary,
  generateMarketplace,
  listVisibleDirectories,
  PLUGIN_CATEGORIES,
  repoPathFromBin,
  requireString,
} from "./marketplace-generator-utils.ts";

type MarketplacePlugin = {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  author: string;
  url: string;
  content: string;
};

type GitSource = {
  repo: string;
  ref?: string;
  subpath?: string;
};

const GIT_PREFIX = "git:";
const GIT_SCHEMES = new Set(["https", "http", "git", "ssh", "file"]);
const GIT_SHORTHAND = /^github\.com\/[^/\s@#]+\/[^/\s@#]+$/;
const GIT_SCHEME = /^([a-z][a-z0-9+.-]*):\/\//i;
const GIT_RELATIVE = /^(?:[^/\s@#\\]+\/)+[^/\s@#\\]+$/;
const GIT_PREFIXED = /^(?:\.\.?\/|~\/)[^\s@#\\]+$/;

function hasParentSegment(value: string): boolean {
  return value.split("/").some((segment) => segment === "..");
}

function isValidGitRepo(repo: string): boolean {
  if (repo.length === 0 || repo.includes("@") || repo.endsWith("/") || hasParentSegment(repo)) {
    return false;
  }
  // The github.com shorthand must be exactly owner/repo; anything else is malformed.
  if (repo.startsWith("github.com/")) return GIT_SHORTHAND.test(repo);

  const scheme = GIT_SCHEME.exec(repo);
  if (scheme) {
    if (!GIT_SCHEMES.has(scheme[1].toLowerCase())) return false;
    try {
      const url = new URL(repo);
      return url.protocol === "file:"
        ? url.pathname !== "" && url.pathname !== "/"
        : url.hostname.length > 0 && url.pathname !== "" && url.pathname !== "/";
    } catch {
      return false;
    }
  }

  return GIT_RELATIVE.test(repo) || GIT_PREFIXED.test(repo);
}

function isValidGitRef(ref: string): boolean {
  return ref.length > 0 && !/[\s@#\\]/.test(ref) && !hasParentSegment(ref);
}

function isValidGitSubpath(subpath: string): boolean {
  if (subpath.length === 0 || /[\s@#\\]/.test(subpath) || hasParentSegment(subpath)) return false;
  return subpath.split("/").every((segment) => segment.length > 0 && segment !== ".");
}

function parseGitSource(content: string): GitSource | undefined {
  if (!content.startsWith(GIT_PREFIX)) return undefined;
  let body = content.slice(GIT_PREFIX.length);
  if (body.length === 0) return undefined;

  let subpath: string | undefined;
  const hash = body.indexOf("#");
  if (hash !== -1) {
    subpath = body.slice(hash + 1);
    body = body.slice(0, hash);
    if (!isValidGitSubpath(subpath)) return undefined;
  }

  let ref: string | undefined;
  const at = body.lastIndexOf("@");
  if (at !== -1) {
    ref = body.slice(at + 1);
    body = body.slice(0, at);
    if (!isValidGitRef(ref)) return undefined;
  }

  const repo = body;
  if (!isValidGitRepo(repo)) return undefined;
  return { repo, ref, subpath };
}

function gitSourceId(source: GitSource): string {
  const base = source.repo.replace(GIT_SCHEME, "").replace(/\.git$/, "");
  return source.subpath ? `${base}/${source.subpath}` : base;
}

function pluginFromYaml(root: string, dirName: string): MarketplacePlugin {
  const file = path.join(root, dirName, "PLUGIN.yaml");
  const raw = yaml.parse(fs.readFileSync(file, "utf-8")) as Record<string, unknown>;

  const id = requireString(raw.id, "id", file);
  const name = requireString(raw.name, "name", file);
  const description = requireString(raw.description, "description", file);
  const category = requireString(raw.category, "category", file);
  const author = requireString(raw.author, "author", file);
  const url = requireString(raw.url, "url", file);
  const content = requireString(raw.content, "content", file);

  if (id !== dirName) {
    throw new Error(`${file}: id must match directory name (${dirName})`);
  }

  const source = parseGitSource(content);
  if (source) {
    // Git plugins are keyed by their normalized repository identity, not a package name.
    const expected = gitSourceId(source);
    if (expected !== id) {
      throw new Error(`${file}: id must equal the git source identity (${expected})`);
    }
  } else if (content.startsWith(GIT_PREFIX)) {
    throw new Error(`${file}: invalid git content spec "${content}"`);
  } else {
    if (!validate(id).validForNewPackages) {
      throw new Error(`${file}: id must be a valid npm package name`);
    }
    // Installed state is keyed by package name. Only registry specs are supported.
    const spec = npa(content);
    if (
      spec.name !== id ||
      !spec.registry ||
      !["version", "range", "tag"].includes(spec.type)
    ) {
      throw new Error(`${file}: content must be the ${id} registry package with an optional version, range, or tag`);
    }
  }

  if (!PLUGIN_CATEGORIES.has(category)) {
    throw new Error(`${file}: invalid category "${category}"`);
  }
  if (raw.tags !== undefined) {
    throw new Error(`${file}: use category instead of tags`);
  }

  return { id, name, description, category, tags: [category], author, url, content };
}

function listPluginDirectories(root: string): string[] {
  const found: string[] = [];
  // Returns true when the directory contains a plugin, directly or in a nested directory.
  const visit = (rel: string): boolean => {
    const abs = rel === "" ? root : path.join(root, rel);
    if (fs.existsSync(path.join(abs, "PLUGIN.yaml"))) {
      if (rel !== "") found.push(rel);
      return true;
    }
    let nested = false;
    for (const name of listVisibleDirectories(abs)) {
      if (visit(rel === "" ? name : `${rel}/${name}`)) nested = true;
    }
    // Keep non-plugin leaf directories so the parser reports the missing manifest.
    if (!nested && rel !== "") found.push(rel);
    return nested;
  };
  visit("");
  return found;
}

export function generatePlugins(root: string) {
  const directories = listPluginDirectories(root);
  return generateMarketplace({
    rootDir: root,
    directories,
    parseItem: (dirName) => {
      const plugin = pluginFromYaml(root, dirName);
      console.log(`Added: ${plugin.name}`);
      return plugin;
    },
    sortItems: (a, b) => a.id.localeCompare(b.id),
    header: (items) =>
      buildCategorySummary(items, {
        title: "Plugin category usage",
        resourceNameSingular: "plugin",
        resourceNamePlural: "plugins",
        scriptName: "bin/generate-plugins-marketplace.ts",
        singleCategoryAware: true,
      }),
    finalMessage: (count) => `\nGenerated marketplace.yaml with ${count} plugins`,
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  generatePlugins(repoPathFromBin("plugins"));
}
