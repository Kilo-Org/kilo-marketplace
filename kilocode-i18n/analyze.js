const fs = require('fs');
const path = require('path');

const workdir = process.argv[2] || '.';

function parseTsDict(content) {
  const pairs = {};
  // Match: "key": "value" or "key": `value`
  const pattern = /"([^"]+)":\s*(?:"((?:[^"\\]|\\.)*)"|`((?:[^`\\]|\\.)*)`)/g;
  let match;
  while ((match = pattern.exec(content)) !== null) {
    const key = match[1];
    const value = match[2] !== undefined ? match[2] : match[3];
    pairs[key] = value;
  }
  return pairs;
}

const enContent = fs.readFileSync(path.join(workdir, 'en.ts'), 'utf8');
const enPairs = parseTsDict(enContent);
console.log(`English: ${Object.keys(enPairs).length} keys`);

const languages = ['ar', 'br', 'bs', 'da', 'de', 'es', 'fr', 'ja', 'ko', 'nl', 'no', 'pl', 'ru', 'th', 'tr', 'uk', 'zh', 'zht'];

for (const lang of languages) {
  const content = fs.readFileSync(path.join(workdir, `${lang}.ts`), 'utf8');
  const langPairs = parseTsDict(content);
  
  const sameAsEnglish = {};
  for (const [key, enVal] of Object.entries(enPairs)) {
    if (key in langPairs && langPairs[key] === enVal) {
      sameAsEnglish[key] = enVal;
    }
  }
  
  console.log(`\n${lang}: ${Object.keys(langPairs).length} keys, ${Object.keys(sameAsEnglish).length} same as English:`);
  for (const [key, val] of Object.entries(sameAsEnglish)) {
    console.log(`  [${key}]: ${JSON.stringify(val.substring(0, 80))}`);
  }
}
