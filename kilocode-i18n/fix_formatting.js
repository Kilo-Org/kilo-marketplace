const fs = require('fs');
const path = require('path');

const workdir = process.argv[2] || '.';

function fixLongLines(content) {
  const lines = content.split('\n');
  const fixed = lines.map(line => {
    if (line.length <= 120) return line;

    // Match: <indent>"key": "value", (optional trailing comma)
    const m = line.match(/^(\s*)("(?:[^"\\]|\\.)+"):\s*("(?:[^"\\]|\\.)*")(,?)$/);
    if (!m) return line; // can't safely reformat (multiline, backtick, etc.)

    const [, indent, key, value, comma] = m;
    // Only reformat if result would exceed 120 chars
    const candidate = `${indent}${key}: ${value}${comma}`;
    if (candidate.length <= 120) return line; // shouldn't happen but be safe

    // Use prettier-style: key on its own line, value indented by 4 extra spaces
    return `${indent}${key}:\n${indent}  ${value}${comma}`;
  });
  return fixed.join('\n');
}

for (const lang of ['nl', 'tr', 'uk']) {
  const file = path.join(workdir, `fix_${lang}.ts`);
  const original = fs.readFileSync(file, 'utf8');
  const fixed = fixLongLines(original);
  if (fixed !== original) {
    fs.writeFileSync(file, fixed, 'utf8');
    const origLines = original.split('\n').filter((l,i) => l !== fixed.split('\n')[i]).length;
    console.log(`${lang}: reformatted long lines`);
    // Show which lines changed
    const origArr = original.split('\n');
    const fixedArr = fixed.split('\n');
    for (let i = 0; i < Math.max(origArr.length, fixedArr.length); i++) {
      if (origArr[i] !== fixedArr[i]) {
        console.log(`  line ${i+1}: ${origArr[i]?.substring(0,80)}...`);
      }
    }
  } else {
    console.log(`${lang}: no changes needed`);
  }
}
