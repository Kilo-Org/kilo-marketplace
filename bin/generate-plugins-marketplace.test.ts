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

test("requires the id to match the full relative directory name", (t) => {
  const root = fixture(t);
  plugin(root, "@scope/package", "@scope/package", "package");
  assert.throws(() => generatePlugins(root), /id must match directory name/);
});
