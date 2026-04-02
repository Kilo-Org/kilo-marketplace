const fs = require('fs');
const path = require('path');

const workdir = process.argv[2] || '.';

// Keys to revert back to English
const revertToEnglish = {
  "prompt.slash.badge.skill": "skill",
  "settings.permissions.tool.skill.title": "Skill",
  "settings.agentBehaviour.subtab.skills": "Skills",
  "settings.agentBehaviour.subtab.workflows": "Workflows",
  "settings.permissions.section.tools": "Tools",
};

const langs = ['ar', 'br', 'bs', 'da', 'de', 'es', 'fr', 'ja', 'ko', 'nl', 'no', 'pl', 'ru', 'th', 'tr', 'uk', 'zh', 'zht'];

for (const lang of langs) {
  const filePath = path.join(workdir, `${lang}.ts`);
  const content = fs.readFileSync(filePath, 'utf8');
  
  const pattern = /"([^"]+)":\s*"((?:[^"\\]|\\.)*)"/g;
  let match;
  const found = [];
  while ((match = pattern.exec(content)) !== null) {
    const key = match[1];
    const val = match[2];
    if (key in revertToEnglish && val !== revertToEnglish[key]) {
      found.push(`  [${key}]: "${val}" → "${revertToEnglish[key]}"`);
    }
  }
  if (found.length > 0) {
    console.log(`${lang}:`);
    found.forEach(f => console.log(f));
  }
}
