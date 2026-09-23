import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { test, type TestContext } from "node:test";
import * as yaml from "yaml";
import { generatePlugins } from "./generate-plugins-marketplace.ts";

function fixture(t: TestContext) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "marketplace-plugins-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

function plugin(root: string, id: string, content: string, dir = id) {
  const item = {
    id,
    name: "Test Plugin",
    description: "A test plugin.",
    category: "development",
    author: "test",
    url: "https://example.com/plugin",
    content,
  };
  fs.mkdirSync(path.join(root, dir), { recursive: true });
  fs.writeFileSync(path.join(root, dir, "PLUGIN.yaml"), yaml.stringify(item));
  return { ...item, tags: [item.category] };
}

test("discovers scoped and unscoped plugins and preserves the catalog format", (t) => {
  const root = fixture(t);
  const unscoped = plugin(root, "my-plugin", "my-plugin@1.2.3");
  const scoped = plugin(root, "@scope/package", "@scope/package@^2.0.0");
  fs.mkdirSync(path.join(root, ".ignored"));
  fs.mkdirSync(path.join(root, "@scope", ".ignored"));
  fs.writeFileSync(path.join(root, "README.md"), "Not a plugin");

  assert.deepEqual(generatePlugins(root), [scoped, unscoped]);
  assert.deepEqual(yaml.parse(fs.readFileSync(path.join(root, "marketplace.yaml"), "utf8")), {
    items: [scoped, unscoped],
  });
});

for (const id of ["my-plugin", "@scope/package"]) {
  for (const suffix of ["", "@1.2.3", "@^1.2.0", "@~1.2.0", "@>=1 <3", "@*", "@latest", "@next"]) {
    test(`accepts registry spec ${id}${suffix}`, (t) => {
      const root = fixture(t);
      const item = plugin(root, id, `${id}${suffix}`);
      assert.deepEqual(generatePlugins(root), [item]);
    });
  }

  for (const content of [
    "other-plugin@1.2.3",
    "@other/package@latest",
    `${id}@npm:other-plugin@1.0.0`,
    `${id}@npm:${id}@1.0.0`,
    `${id}@file:../plugin`,
    `${id}@../plugin`,
    `${id}@https://example.com/plugin.tgz`,
    `${id}@git+https://github.com/example/plugin.git`,
    `${id}@github:example/plugin`,
    `${id}@invalid tag`,
    `${id}@@1.2.3`,
    "file:../plugin",
    "https://example.com/plugin.tgz",
  ]) {
    test(`rejects non-registry or mismatched spec ${content} for ${id}`, (t) => {
      const root = fixture(t);
      plugin(root, id, content);
      assert.throws(() => generatePlugins(root));
      assert.equal(fs.existsSync(path.join(root, "marketplace.yaml")), false);
    });
  }
}

for (const id of ["Uppercase", "bad name", "bad!name", "node_modules", "@Scope/package", "@scope/bad!name"]) {
  test(`rejects invalid npm package name ${id}`, (t) => {
    const root = fixture(t);
    plugin(root, id, id);
    assert.throws(() => generatePlugins(root), /valid npm package name/);
  });
}

const GIT_SPECS: Array<[string, string]> = [
  ["github.com/owner/repo", "git:github.com/owner/repo"],
  ["github.com/owner/repo", "git:github.com/owner/repo@v1"],
  ["github.com/owner/repo", "git:github.com/owner/repo@main"],
  ["github.com/owner/repo", "git:https://github.com/owner/repo"],
  ["github.com/owner/repo", "git:https://github.com/owner/repo.git@v1.2.3"],
  ["github.com/owner/repo", "git:git://github.com/owner/repo@main"],
  ["github.com/owner/repo/plugins/x", "git:github.com/owner/repo#plugins/x"],
  ["github.com/owner/repo/plugins/x", "git:github.com/owner/repo@v1#plugins/x"],
  ["github.com/owner/repo/sub", "git:https://github.com/owner/repo.git#sub"],
  ["vendor/plugin", "git:vendor/plugin"],
];

for (const [id, content] of GIT_SPECS) {
  test(`accepts git spec ${content} for ${id}`, (t) => {
    const root = fixture(t);
    const item = plugin(root, id, content);
    assert.deepEqual(generatePlugins(root), [item]);
  });
}

const MALFORMED_GIT_SPECS = [
  "git:",
  "git:github.com/owner",
  "git:github.com/owner/repo/extra",
  "git:github.com/owner/repo@",
  "git:github.com/owner/repo#",
  "git:github.com/owner/repo#/plugins/x",
  "git:github.com/owner/repo#plugins//x",
  "git:github.com/owner/repo#plugins/x/",
  "git:github.com/owner/repo#..",
  "git:github.com/owner/repo@..",
  "git:github.com/owner/repo@v1@v2",
  "git:https://",
  "git:https://github.com",
  "git:ftp://github.com/owner/repo",
  "git:ssh://git@github.com/owner/repo",
  "git:git@github.com/owner/repo",
  "git:github.com/owner/repo name",
  "git:../plugin",
  "git:./../plugin",
  "git:file://",
];

for (const content of MALFORMED_GIT_SPECS) {
  test(`rejects malformed git spec ${content}`, (t) => {
    const root = fixture(t);
    plugin(root, "github.com/owner/repo", content);
    assert.throws(() => generatePlugins(root), /invalid git content spec/);
    assert.equal(fs.existsSync(path.join(root, "marketplace.yaml")), false);
  });
}

test("requires the id to match the git repo identity", (t) => {
  const root = fixture(t);
  plugin(root, "github.com/other/repo", "git:github.com/owner/repo@v1");
  assert.throws(
    () => generatePlugins(root),
    /id must equal the git source identity \(github\.com\/owner\/repo\)/,
  );
});

test("requires the id to include the git subpath", (t) => {
  const root = fixture(t);
  plugin(root, "github.com/owner/repo", "git:github.com/owner/repo#plugins/x");
  assert.throws(
    () => generatePlugins(root),
    /id must equal the git source identity \(github\.com\/owner\/repo\/plugins\/x\)/,
  );
});

test("generates a catalog with registry and git plugins together", (t) => {
  const root = fixture(t);
  const git = plugin(root, "github.com/owner/repo", "git:github.com/owner/repo@v1");
  const registry = plugin(root, "my-plugin", "my-plugin@1.2.3");
  assert.deepEqual(generatePlugins(root), [git, registry]);
});

test("requires the id to match the full relative directory name", (t) => {
  const root = fixture(t);
  plugin(root, "@scope/package", "@scope/package", "package");
  assert.throws(() => generatePlugins(root), /id must match directory name/);
});
