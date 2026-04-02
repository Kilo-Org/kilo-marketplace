const fs = require('fs');
const path = require('path');

const workdir = process.argv[2] || '.';

// These keys are OK to remain in English (technical terms, proper nouns, etc.)
const keepInEnglish = new Set([
  // Technical acronyms
  'command.category.mcp',
  'command.category.terminal',
  'command.category.server', // Server is a loanword in most languages
  'dialog.mcp.title',
  'status.popover.tab.mcp',
  'status.popover.tab.lsp',
  'ui.permission.toolLabel.lsp',
  'ui.permission.toolLabel.bash',
  'settings.mcp.title',
  'settings.permissions.tool.glob.title',
  'settings.permissions.tool.grep.title',
  'settings.permissions.tool.bash.title',
  'settings.permissions.tool.lsp.title',
  'settings.experimental.lsp.title',
  'lsp.label.connected',
  
  // Proper nouns - company names
  'model.provider.anthropic',
  'model.provider.openai',
  'model.provider.google',
  'model.provider.xai',
  'model.provider.meta',
  
  // Product names
  'app.name.desktop',
  
  // URLs and code placeholders
  'provider.connect.opencodeZen.visit.link',
  'dialog.server.add.placeholder',
  'provider.custom.field.providerID.placeholder',
  'provider.custom.field.baseURL.placeholder',
  'provider.custom.models.id.placeholder',
  'provider.custom.headers.key.placeholder',
  'provider.custom.headers.value.placeholder',
  'settings.agentBehaviour.addMcp.command.placeholder',
  'settings.agentBehaviour.addMcp.args.placeholder',
  'settings.agentBehaviour.addMcp.url.placeholder',
  
  // Punctuation/technical
  'common.loading.ellipsis',
  'provider.custom.description.suffix',
  'common.key.esc',
  
  // Language names (native form)
  'language.en', 'language.zh', 'language.zht', 'language.ko', 'language.de',
  'language.es', 'language.fr', 'language.da', 'language.ja', 'language.pl',
  'language.ru', 'language.ar', 'language.no', 'language.br', 'language.bs',
  'language.th', 'language.tr',
  
  // Font names (universal)
  'font.option.ibmPlexMono', 'font.option.cascadiaCode', 'font.option.firaCode',
  'font.option.hack', 'font.option.inconsolata', 'font.option.intelOneMono',
  'font.option.iosevka', 'font.option.jetbrainsMono', 'font.option.mesloLgs',
  'font.option.robotoMono', 'font.option.sourceCodePro', 'font.option.ubuntuMono',
  
  // Sound option names (custom Kilo names, not real words)
  'sound.option.bipbop01', 'sound.option.bipbop02', 'sound.option.bipbop03',
  'sound.option.bipbop04', 'sound.option.bipbop05', 'sound.option.bipbop06',
  'sound.option.bipbop07', 'sound.option.bipbop08', 'sound.option.bipbop09',
  'sound.option.bipbop10',
  'sound.option.staplebops01', 'sound.option.staplebops02', 'sound.option.staplebops03',
  'sound.option.staplebops04', 'sound.option.staplebops05', 'sound.option.staplebops06',
  'sound.option.staplebops07',
  
  // Technical ML term
  'settings.agentBehaviour.topP.title',
  
  // Technical product feature (Doom Loop is a specific product name)
  'settings.permissions.tool.doom_loop.title',
  
  // Shell mode (Shell/Bash are used in all languages)
  'prompt.mode.shell',
  'prompt.slash.badge.mcp',
  
  // MCP technical
  'settings.providers.tag.gateway',
  
  // Model inputs (file format terms - universal)
  'model.input.pdf',
  
  // Gateway technical term
  'settings.providers.tag.gateway',
  
  // Status/Port/Version labels that are universally used
  'settings.aboutKiloCode.status.label', // "Status:" - same in most languages
  'settings.aboutKiloCode.port.label', // "Port:" - technical term
]);

function parseTsDict(content) {
  const pairs = {};
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

const languages = ['ar', 'br', 'bs', 'da', 'de', 'es', 'fr', 'ja', 'ko', 'nl', 'no', 'pl', 'ru', 'th', 'tr', 'uk', 'zh', 'zht'];

for (const lang of languages) {
  const content = fs.readFileSync(path.join(workdir, `${lang}.ts`), 'utf8');
  const langPairs = parseTsDict(content);
  
  const needsTranslation = {};
  for (const [key, enVal] of Object.entries(enPairs)) {
    if (keepInEnglish.has(key)) continue;
    if (key in langPairs && langPairs[key] === enVal) {
      needsTranslation[key] = enVal;
    }
  }
  
  if (Object.keys(needsTranslation).length > 0) {
    console.log(`\n=== ${lang} (${Object.keys(needsTranslation).length} needs translation) ===`);
    for (const [key, val] of Object.entries(needsTranslation)) {
      console.log(`  [${key}]: ${JSON.stringify(val)}`);
    }
  }
}
