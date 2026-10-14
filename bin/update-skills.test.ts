import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { test } from "node:test";
import { applyPatch } from "./update-skills.ts";

const patch = `diff --git a/example/SKILL.md b/example/SKILL.md
--- a/example/SKILL.md
+++ b/example/SKILL.md
@@ -1 +1 @@
-before
+after
`;
const addedFile = `diff --git a/example/NOTICE b/example/NOTICE
new file mode 100644
--- /dev/null
+++ b/example/NOTICE
@@ -0,0 +1 @@
+retained notice
`;

for (const inRepository of [true, false]) {
  test(`patch changes actual staged files (repository=${inRepository})`, (t) => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "kilo-updater-test-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    if (inRepository) execFileSync("git", ["init", "--quiet", root]);
    const stage = path.join(root, "skills", ".skill-stage-space ü");
    fs.mkdirSync(stage, { recursive: true });
    fs.writeFileSync(path.join(stage, "SKILL.md"), "before\n");
    fs.writeFileSync(path.join(root, "SKILL.md"), "outside must stay\n");
    assert.equal(applyPatch(stage, patch + addedFile), true);
    assert.equal(fs.readFileSync(path.join(stage, "SKILL.md"), "utf8"), "after\n");
    assert.equal(fs.readFileSync(path.join(stage, "NOTICE"), "utf8"), "retained notice\n");
    assert.equal(fs.readFileSync(path.join(root, "SKILL.md"), "utf8"), "outside must stay\n");
    fs.writeFileSync(path.join(stage, "SKILL.md"), "before\n");
    fs.unlinkSync(path.join(stage, "NOTICE"));
    assert.equal(applyPatch(stage, patch + addedFile), true);
    assert.equal(fs.readFileSync(path.join(stage, "SKILL.md"), "utf8"), "after\n");
  });
  test(`patch cannot escape staging (repository=${inRepository})`, (t) => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "kilo-updater-path-"));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    if (inRepository) execFileSync("git", ["init", "--quiet", root]);
    const stage = path.join(root, "skills", ".stage");
    fs.mkdirSync(stage, { recursive: true });
    const outside = path.join(root, "skills", "outside.txt");
    fs.writeFileSync(outside, "before\n");
    const unsafe = patch.replaceAll("example/SKILL.md", "example/../outside.txt");
    assert.equal(applyPatch(stage, unsafe), false);
    assert.equal(fs.readFileSync(outside, "utf8"), "before\n");
  });
}
