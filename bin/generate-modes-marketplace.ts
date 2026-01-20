#!/usr/bin/env npx tsx
/**
 * Generate marketplace.yaml from individual mode YAML files.
 *
 * Usage: npx tsx bin/generate-modes-marketplace.ts
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import * as yaml from "yaml";
import { Document } from "yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const modesDir = path.join(__dirname, "..", "modes");

const items = fs
  .readdirSync(modesDir)
  .filter((file) => file.endsWith(".yaml") && file !== "marketplace.yaml")
  .map((file) => {
    const content = fs.readFileSync(path.join(modesDir, file), "utf-8");
    const mode = yaml.parse(content);
    console.log(`Added: ${mode.name}`);
    return mode;
  })
  .sort((a, b) => a.id.localeCompare(b.id));

const doc = new Document({ items });
const output = doc.toString({ lineWidth: 120 });

fs.writeFileSync(path.join(modesDir, "marketplace.yaml"), output);

console.log(`\nGenerated marketplace.yaml with ${items.length} modes`);
