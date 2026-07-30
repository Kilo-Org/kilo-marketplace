import assert from "node:assert/strict";
import test from "node:test";

import { validateRequirements } from "./marketplace-generator-utils.ts";

const skillIds = new Set(["skill-one"]);
const mcpIds = new Set(["mcp-one"]);

test("rejects duplicate skill requirements", () => {
  assert.throws(
    () =>
      validateRequirements(
        { skills: ["skill-one", "skill-one"] },
        "example",
        skillIds,
        mcpIds,
      ),
    /requirements\.skills contains duplicate ID "skill-one"/,
  );
});

test("rejects duplicate MCP requirements", () => {
  assert.throws(
    () =>
      validateRequirements(
        { mcps: ["mcp-one", "mcp-one"] },
        "example",
        skillIds,
        mcpIds,
      ),
    /requirements\.mcps contains duplicate ID "mcp-one"/,
  );
});

test("rejects duplicate VS Code extension IDs case-insensitively", () => {
  assert.throws(
    () =>
      validateRequirements(
        {
          vscode_extensions: [
            { name: "Jupyter", id: "ms-toolsai.jupyter" },
            { name: "Jupyter duplicate", id: "MS-TOOLSai.Jupyter" },
          ],
        },
        "example",
        skillIds,
        mcpIds,
      ),
    /requirements\.vscode_extensions contains duplicate extension ID "ms-toolsai\.jupyter"/,
  );
});
