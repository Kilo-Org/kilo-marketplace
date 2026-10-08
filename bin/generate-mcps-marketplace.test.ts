import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { test, type TestContext } from "node:test";
import * as yaml from "yaml";
import { generateMcps } from "./generate-mcps-marketplace.ts";

function fixture(t: TestContext) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "marketplace-mcps-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const mcps = path.join(root, "mcps");
  const skills = path.join(root, "skills");
  fs.mkdirSync(mcps);
  fs.mkdirSync(skills);
  return { mcps, skills };
}

function mcp(root: string, fields: Record<string, unknown> = {}, dir?: string) {
  const item = {
    id: "sample",
    name: "Sample MCP",
    description: "A remote MCP server.",
    author: "test",
    url: "https://example.com/server",
    category: "development",
    content: '{"type":"streamable-http","url":"https://example.com/mcp"}',
    ...fields,
  };
  fs.mkdirSync(path.join(root, dir ?? item.id));
  fs.writeFileSync(path.join(root, dir ?? item.id, "MCP.yaml"), yaml.stringify(item));
  return { ...item, tags: [item.category] };
}

function skill(root: string, id: string, fields: Record<string, unknown> = {}) {
  fs.mkdirSync(path.join(root, id));
  const front = yaml.stringify({ name: id, description: "A companion workflow.", ...fields });
  fs.writeFileSync(path.join(root, id, "SKILL.md"), `---\n${front}---\n\nUse the MCP tools.\n`);
}

test("preserves entries without companions and historical dependency references", (t) => {
  const dirs = fixture(t);
  skill(dirs.skills, "workflow");
  const plain = mcp(dirs.mcps, {
    id: "plain",
    content: [{ name: "Remote", content: '{"url":"https://example.com/mcp"}' }],
    prerequisites: ["An account"],
    parameters: [{ key: "TOKEN", name: "Token" }],
  });
  const required = mcp(dirs.mcps, {
    requirements: { skills: ["workflow", "workflow"], mcps: ["plain"] },
  });

  const items = generateMcps(dirs.mcps, dirs.skills);
  assert.deepEqual(items, [plain, required]);
  assert.ok(items.every((item) => !Object.hasOwn(item, "skills")));
  assert.deepEqual(yaml.parse(fs.readFileSync(path.join(dirs.mcps, "marketplace.yaml"), "utf8")), {
    items: [plain, required],
  });
});

test("expands companion IDs in order without expanding requirements", (t) => {
  const dirs = fixture(t);
  for (const id of ["first", "second", "required"]) skill(dirs.skills, id);
  const item = mcp(dirs.mcps, {
    skills: ["second", "first"],
    requirements: { skills: ["required"] },
  });
  const expected = {
    ...item,
    skills: [
      {
        id: "second",
        content: "https://github.com/Kilo-Org/kilo-marketplace/releases/download/skills-latest/second.tar.gz",
      },
      {
        id: "first",
        content: "https://github.com/Kilo-Org/kilo-marketplace/releases/download/skills-latest/first.tar.gz",
      },
    ],
  };

  assert.deepEqual(generateMcps(dirs.mcps, dirs.skills), [expected]);
  assert.deepEqual(yaml.parse(fs.readFileSync(path.join(dirs.mcps, "marketplace.yaml"), "utf8")), {
    items: [expected],
  });
});

test("rejects unsafe MCP IDs when companions are present", (t) => {
  for (const id of ["../server", "nested/server", ".", "server.name", "Server"]) {
    const dirs = fixture(t);
    skill(dirs.skills, "workflow");
    mcp(dirs.mcps, { id, skills: ["workflow"] }, "sample");
    assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /MCP id must be safe/);
    assert.equal(fs.existsSync(path.join(dirs.mcps, "marketplace.yaml")), false);
  }
});

test("rejects reserved MCP IDs when companions are present", (t) => {
  for (const id of ["con", "com1", "__proto__", "constructor", "prototype"]) {
    const dirs = fixture(t);
    skill(dirs.skills, "workflow");
    mcp(dirs.mcps, { id, skills: ["workflow"] }, "sample");
    assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /MCP id must be safe/);
  }
});

test("rejects a missing MCP ID when companions are present", (t) => {
  const dirs = fixture(t);
  skill(dirs.skills, "workflow");
  mcp(dirs.mcps, { id: undefined, skills: ["workflow"] }, "sample");
  assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /missing required string field id/);
});

test("preserves valid bundle IDs and legacy IDs without companions", (t) => {
  const dirs = fixture(t);
  skill(dirs.skills, "workflow");
  const legacy = mcp(dirs.mcps, { id: "legacy/server" }, "legacy");
  const item = mcp(dirs.mcps, { id: "new-server", skills: ["workflow"] });
  assert.deepEqual(generateMcps(dirs.mcps, dirs.skills), [
    legacy,
    {
      ...item,
      skills: [
        {
          id: "workflow",
          content: "https://github.com/Kilo-Org/kilo-marketplace/releases/download/skills-latest/workflow.tar.gz",
        },
      ],
    },
  ]);
});

for (const skills of [
  null,
  "workflow",
  {},
  [],
  [""],
  [" "],
  [1],
  [null],
  [[]],
  ["../workflow"],
  ["a/b"],
  ["a\\b"],
  [".hidden"],
  ["workflow."],
  ["Workflow"],
  ["con"],
  ["com1"],
  ["workflow--name"],
  ["https://example.com/skill.tar.gz"],
  [{ id: "workflow", content: "https://example.com/skill.tar.gz" }],
]) {
  test(`rejects malformed or unsafe companion references ${JSON.stringify(skills)}`, (t) => {
    const dirs = fixture(t);
    mcp(dirs.mcps, { skills });
    assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /skills must/);
    assert.equal(fs.existsSync(path.join(dirs.mcps, "marketplace.yaml")), false);
  });
}

test("rejects duplicate companion IDs", (t) => {
  const dirs = fixture(t);
  skill(dirs.skills, "workflow");
  mcp(dirs.mcps, { skills: ["workflow", "workflow"] });
  assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /duplicate ID "workflow"/);
});

test("rejects unknown skill IDs without overwriting an existing catalog", (t) => {
  const dirs = fixture(t);
  mcp(dirs.mcps, { skills: ["missing"] });
  const file = path.join(dirs.mcps, "marketplace.yaml");
  fs.writeFileSync(file, "items: []\n");
  assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /unknown skill ID "missing"/);
  assert.equal(fs.readFileSync(file, "utf8"), "items: []\n");
});

test("requires a regular SKILL.md, not an empty directory or symlink", (t) => {
  const dirs = fixture(t);
  skill(dirs.skills, "source");
  fs.mkdirSync(path.join(dirs.skills, "workflow"));
  mcp(dirs.mcps, { skills: ["workflow"] });
  assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /no regular SKILL.md/);
  fs.symlinkSync(
    path.join(dirs.skills, "source", "SKILL.md"),
    path.join(dirs.skills, "workflow", "SKILL.md"),
  );
  assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /no regular SKILL.md/);
});

for (const fields of [{ name: "other" }, { description: "" }, { description: 1 }]) {
  test(`rejects invalid companion frontmatter ${JSON.stringify(fields)}`, (t) => {
    const dirs = fixture(t);
    skill(dirs.skills, "workflow", fields);
    mcp(dirs.mcps, { skills: ["workflow"] });
    assert.throws(() => generateMcps(dirs.mcps, dirs.skills), /name must match|description/);
  });
}
