const fs = require('fs');
const path = require('path');

const workdir = process.argv[2] || '.';

// Only revert keys I actually changed in this PR
// Keyed by language → key → value to restore
const revertMap = {
  ar: {
    "settings.permissions.tool.skill.title": "Skill",
  },
  br: {
    "prompt.slash.badge.skill": "skill",
  },
  bs: {
    "prompt.slash.badge.skill": "skill",
  },
  da: {
    "prompt.slash.badge.skill": "skill",
  },
  de: {
    "prompt.slash.badge.skill": "skill",
    "settings.agentBehaviour.subtab.workflows": "Workflows",
    "settings.permissions.section.tools": "Tools",
  },
  es: {
    "prompt.slash.badge.skill": "skill",
  },
  fr: {
    "prompt.slash.badge.skill": "skill",
  },
  nl: {
    "prompt.slash.badge.skill": "skill",
    "settings.permissions.tool.skill.title": "Skill",
    "settings.agentBehaviour.subtab.skills": "Skills",
    "settings.agentBehaviour.subtab.workflows": "Workflows",
    "settings.permissions.section.tools": "Tools",
  },
  no: {
    "prompt.slash.badge.skill": "skill",
  },
  pl: {
    "prompt.slash.badge.skill": "skill",
  },
  ru: {
    "settings.permissions.tool.skill.title": "Skill",
  },
  th: {
    "prompt.slash.badge.skill": "skill",
  },
  zh: {
    "settings.permissions.tool.skill.title": "Skill",
  },
  zht: {
    "settings.permissions.tool.skill.title": "Skill",
    "settings.agentBehaviour.subtab.skills": "Skills",
  },
};

function escapeForRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

let totalReverted = 0;

for (const [lang, reverts] of Object.entries(revertMap)) {
  const filePath = path.join(workdir, `${lang}.ts`);
  let content = fs.readFileSync(filePath, 'utf8');
  const changed = [];

  for (const [key, englishValue] of Object.entries(reverts)) {
    const keyEscaped = escapeForRegex(key);
    const englishEscaped = englishValue.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    const pattern = new RegExp(`("${keyEscaped}":\\s*)"((?:[^"\\\\]|\\\\.)*)"`, 'g');
    const before = content;
    content = content.replace(pattern, `$1"${englishEscaped}"`);
    if (content !== before) changed.push(key);
  }

  if (changed.length > 0) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`${lang}: reverted ${changed.length} key(s): ${changed.join(', ')}`);
    totalReverted += changed.length;
  }
}

console.log(`\nTotal reverted: ${totalReverted}`);
