const fs = require('fs');
const path = require('path');

const workdir = process.argv[2] || '.';

// Map of language -> key -> new translation
// Only includes strings that genuinely need translation
// Skips technical terms, proper nouns, and words used identically in target language
const translations = {
  ar: {
    "revert.banner.count_one": "تم التراجع عن {{count}} رسالة",
    "revert.banner.count_other": "تم التراجع عن {{count}} رسائل",
    "revert.banner.redo": "إعادة",
    "revert.banner.redo.all": "إعادة الكل",
    "revert.banner.hint": "أرسل رسالة جديدة لجعل هذا دائمًا",
    "settings.permissions.tool.task.title": "مهمة",
    "settings.permissions.tool.skill.title": "مهارة",
    "session.tab.local": "محلي",
    "session.tab.cloud": "السحابة",
    "settings.agentBehaviour.subtab.agents": "الوكلاء",
    "migration.whatsNew.features.agentManager.title": "مدير الوكلاء",
  },
  br: {
    "revert.banner.count_one": "{{count}} mensagem revertida",
    "revert.banner.count_other": "{{count}} mensagens revertidas",
    "revert.banner.redo": "Refazer",
    "revert.banner.redo.all": "Refazer Tudo",
    "revert.banner.hint": "Envie uma nova mensagem para tornar isso permanente",
    "prompt.slash.badge.skill": "habilidade",
    "provider.custom.headers.key.label": "Cabeçalho",
    "session.tab.cloud": "Nuvem",
    "settings.agentBehaviour.subtab.agents": "Agentes",
    "migration.whatsNew.features.agentManager.title": "Gerenciador de Agentes",
  },
  bs: {
    "revert.banner.count_one": "{{count}} poruka poništena",
    "revert.banner.count_other": "{{count}} poruka poništeno",
    "revert.banner.redo": "Ponovi",
    "revert.banner.redo.all": "Ponovi Sve",
    "revert.banner.hint": "Pošalji novu poruku da bi ovo postalo trajno",
    "prompt.slash.badge.skill": "vještina",
    "session.tab.local": "Lokalno",
    "session.tab.cloud": "Oblak",
    "settings.agentBehaviour.subtab.agents": "Agenti",
    "migration.whatsNew.features.agentManager.title": "Upravljač agentima",
  },
  da: {
    "revert.banner.count_one": "{{count}} besked fortrudt",
    "revert.banner.count_other": "{{count}} beskeder fortrudt",
    "revert.banner.redo": "Gentag",
    "revert.banner.redo.all": "Gentag alt",
    "revert.banner.hint": "Send en ny besked for at gøre dette permanent",
    "prompt.slash.badge.skill": "færdighed",
    "context.stats.totalTokens": "Tokens i alt",
    "context.stats.inputTokens": "Input-tokens",
    "context.stats.outputTokens": "Output-tokens",
    "ui.permission.toolLabel.list": "Liste",
    "session.tab.local": "Lokal",
    "session.tab.cloud": "Sky",
    "settings.agentBehaviour.subtab.agents": "Agenter",
    "migration.whatsNew.features.agentManager.title": "Agentstyring",
  },
  de: {
    "revert.banner.count_one": "{{count}} Nachricht zurückgesetzt",
    "revert.banner.count_other": "{{count}} Nachrichten zurückgesetzt",
    "revert.banner.redo": "Wiederholen",
    "revert.banner.redo.all": "Alle wiederholen",
    "revert.banner.hint": "Sende eine neue Nachricht, um dies dauerhaft zu machen",
    "prompt.slash.badge.skill": "Fertigkeit",
    "dialog.project.edit.name": "Name",
    "dialog.project.edit.icon": "Symbol",
    "settings.general.section.updates": "Aktualisierungen",
    "settings.permissions.section.tools": "Werkzeuge",
    "provider.custom.models.name.label": "Name",
    "provider.custom.headers.key.label": "Kopfzeile",
    "session.tab.local": "Lokal",
    "session.tab.cloud": "Cloud",
    "feedback.button": "Feedback & Support",
    "settings.checkpoints.title": "Prüfpunkte",
    "settings.aboutKiloCode.community": "Community & Support",
    "settings.agentBehaviour.subtab.agents": "Agenten",
    "settings.agentBehaviour.subtab.workflows": "Arbeitsabläufe",
    "settings.agentBehaviour.selectAgent.title": "Agent",
    "settings.agentBehaviour.createMode.name": "Name",
    "migration.whatsNew.features.agentManager.title": "Agentenverwaltung",
    "error.details.show": "Details",
  },
  es: {
    "revert.banner.count_one": "{{count}} mensaje revertido",
    "revert.banner.count_other": "{{count}} mensajes revertidos",
    "revert.banner.redo": "Rehacer",
    "revert.banner.redo.all": "Rehacer todo",
    "revert.banner.hint": "Envía un nuevo mensaje para hacerlo permanente",
    "model.input.audio": "audio",
    "model.input.video": "video",
    "prompt.slash.badge.skill": "habilidad",
    "dialog.project.edit.color": "Color",
    "session.tab.local": "Local",
    "session.tab.cloud": "Nube",
    "settings.experimental.title": "Experimental",
    "settings.aboutKiloCode.status.error": "Error",
    "settings.agentBehaviour.subtab.agents": "Agentes",
    "migration.whatsNew.features.agentManager.title": "Administrador de agentes",
  },
  fr: {
    "revert.banner.count_one": "{{count}} message annulé",
    "revert.banner.count_other": "{{count}} messages annulés",
    "revert.banner.redo": "Rétablir",
    "revert.banner.redo.all": "Tout rétablir",
    "revert.banner.hint": "Envoyez un nouveau message pour rendre ceci permanent",
    "command.category.session": "Session",
    "command.category.agent": "Agent",
    "command.category.permissions": "Autorisations",
    "model.input.image": "image",
    "model.input.audio": "audio",
    "prompt.slash.badge.skill": "compétence",
    "context.breakdown.assistant": "Assistant",
    "context.stats.session": "Session",
    "context.stats.messages": "Messages",
    "notification.question.title": "Question",
    "session.tab.session": "Session",
    "settings.general.notifications.agent.title": "Agent",
    "settings.general.notifications.permissions.title": "Autorisations",
    "settings.general.sounds.agent.title": "Agent",
    "settings.general.sounds.permissions.title": "Autorisations",
    "settings.shortcuts.group.session": "Session",
    "settings.shortcuts.group.navigation": "Navigation",
    "settings.shortcuts.group.terminal": "Terminal",
    "settings.shortcuts.group.prompt": "Invite",
    "settings.agents.title": "Agents",
    "settings.permissions.title": "Autorisations",
    "session.tab.local": "Local",
    "session.tab.cloud": "Cloud",
    "settings.section.configuration": "Configuration",
    "settings.notifications.title": "Notifications",
    "settings.agentBehaviour.subtab.modes": "Modes",
    "settings.agentBehaviour.subtab.agents": "Agents",
    "settings.agentBehaviour.selectAgent.title": "Agent",
    "settings.agentBehaviour.mcpDetail.args": "Arguments",
    "settings.agentBehaviour.addMcp.args": "Arguments",
    "settings.agentBehaviour.workflows.detail.description": "Description",
    "settings.agentBehaviour.createMode.description": "Description",
    "settings.agentBehaviour.editMode.description": "Description",
    "settings.autoApprove.exceptions": "Exceptions",
    "migration.whatsNew.features.agentManager.title": "Gestionnaire d'agents",
  },
  ja: {
    "revert.banner.count_one": "{{count}} 件のメッセージが元に戻されました",
    "revert.banner.count_other": "{{count}} 件のメッセージが元に戻されました",
    "revert.banner.redo": "やり直し",
    "revert.banner.redo.all": "すべてやり直し",
    "revert.banner.hint": "新しいメッセージを送信してこれを永続させてください",
    "settings.permissions.tool.webfetch.title": "ウェブ取得",
    "settings.permissions.tool.websearch.title": "ウェブ検索",
    "settings.permissions.tool.codesearch.title": "コード検索",
    "session.tab.local": "ローカル",
    "session.tab.cloud": "クラウド",
    "settings.agentBehaviour.subtab.agents": "エージェント",
    "migration.whatsNew.features.agentManager.title": "エージェントマネージャー",
  },
  ko: {
    "revert.banner.count_one": "{{count}}개 메시지 되돌림",
    "revert.banner.count_other": "{{count}}개 메시지 되돌림",
    "revert.banner.redo": "다시 실행",
    "revert.banner.redo.all": "모두 다시 실행",
    "revert.banner.hint": "새 메시지를 보내 이를 영구적으로 만드세요",
    "session.tab.local": "로컬",
    "session.tab.cloud": "클라우드",
    "settings.agentBehaviour.subtab.agents": "에이전트",
    "migration.whatsNew.features.agentManager.title": "에이전트 관리자",
  },
  nl: {
    "prompt.slash.badge.skill": "vaardigheid",
    "session.tab.context": "Context",
    "provider.custom.field.providerID.label": "Provider-ID",
    "settings.providers.title": "Providers",
    "settings.agents.title": "Agenten",
    "settings.permissions.section.tools": "Hulpmiddelen",
    "settings.permissions.tool.skill.title": "Vaardigheid",
    "session.recent": "Recent",
    "session.tab.local": "Lokaal",
    "session.tab.cloud": "Cloud",
    "workspace.reset.title": "Werkruimte herstellen",
    "workspace.reset.button": "Werkruimte herstellen",
    "settings.checkpoints.title": "Controlepunten",
    "settings.context.title": "Context",
    "settings.agentBehaviour.subtab.agents": "Agenten",
    "settings.agentBehaviour.subtab.workflows": "Werkstromen",
    "settings.agentBehaviour.subtab.skills": "Vaardigheden",
    "settings.agentBehaviour.topP.description": "Nucleus-samplingparameter (0-1)",
    "settings.agentBehaviour.createMode": "Nieuwe modus aanmaken",
    "settings.agentBehaviour.createMode.name": "Naam",
    "settings.agentBehaviour.createMode.name.description": "Unieke identifier voor de modus. Gebruik alleen kleine letters, cijfers en koppeltekens.",
    "settings.agentBehaviour.createMode.description": "Beschrijving",
    "settings.agentBehaviour.createMode.description.help": "Korte beschrijving van wat deze modus doet.",
    "settings.agentBehaviour.createMode.prompt": "Systeemprompt",
    "settings.agentBehaviour.createMode.prompt.help": "Instructies voor de AI-agent bij gebruik van deze modus.",
    "settings.agentBehaviour.createMode.button": "Aanmaken",
    "settings.agentBehaviour.createMode.cancel": "Annuleren",
    "settings.agentBehaviour.createMode.nameRequired": "Naam is verplicht",
    "settings.agentBehaviour.createMode.nameInvalid": "Naam moet beginnen met een kleine letter en mag alleen kleine letters, cijfers en koppeltekens bevatten",
    "settings.agentBehaviour.createMode.nameTaken": "Er bestaat al een modus met deze naam",
    "settings.agentBehaviour.editMode": "Modus bewerken",
    "settings.agentBehaviour.editMode.description": "Beschrijving",
    "settings.agentBehaviour.editMode.prompt": "Systeemprompt",
    "settings.agentBehaviour.editMode.save": "Klaar",
    "settings.agentBehaviour.editMode.back": "Terug naar lijst",
    "settings.agentBehaviour.editMode.native": "Ingebouwde modus (alleen-lezen definitie)",
    "settings.agentBehaviour.editMode.promptOverride": "Aangepaste systeemprompt voor deze ingebouwde modus",
    "migration.whatsNew.features.agentManager.title": "Agentenbeheer",
    "error.details.show": "Details",
  },
  no: {
    "revert.banner.count_one": "{{count}} melding angret",
    "revert.banner.count_other": "{{count}} meldinger angret",
    "revert.banner.redo": "Gjenta",
    "revert.banner.redo.all": "Gjenta alt",
    "revert.banner.hint": "Send en ny melding for å gjøre dette permanent",
    "prompt.slash.badge.skill": "ferdighet",
    "ui.permission.toolLabel.list": "Liste",
    "session.tab.local": "Lokal",
    "session.tab.cloud": "Sky",
    "settings.agentBehaviour.subtab.agents": "Agenter",
    "migration.whatsNew.features.agentManager.title": "Agentbehandling",
  },
  pl: {
    "revert.banner.count_one": "Cofnięto {{count}} wiadomość",
    "revert.banner.count_other": "Cofnięto {{count}} wiadomości",
    "revert.banner.redo": "Ponów",
    "revert.banner.redo.all": "Ponów wszystko",
    "revert.banner.hint": "Wyślij nową wiadomość, aby to utrwalić",
    "prompt.slash.badge.skill": "umiejętność",
    "session.tab.local": "Lokalny",
    "session.tab.cloud": "Chmura",
    "settings.agentBehaviour.subtab.agents": "Agenci",
    "settings.agentBehaviour.selectAgent.title": "Agent",
    "migration.whatsNew.features.agentManager.title": "Menedżer agentów",
  },
  ru: {
    "revert.banner.count_one": "Отменено {{count}} сообщение",
    "revert.banner.count_other": "Отменено {{count}} сообщений",
    "revert.banner.redo": "Повторить",
    "revert.banner.redo.all": "Повторить всё",
    "revert.banner.hint": "Отправьте новое сообщение, чтобы сделать это постоянным",
    "settings.permissions.tool.task.title": "Задача",
    "settings.permissions.tool.skill.title": "Навык",
    "settings.permissions.tool.webfetch.title": "Веб-загрузка",
    "settings.permissions.tool.websearch.title": "Веб-поиск",
    "session.tab.local": "Локальный",
    "session.tab.cloud": "Облако",
    "settings.agentBehaviour.subtab.agents": "Агенты",
    "migration.whatsNew.features.agentManager.title": "Менеджер агентов",
  },
  th: {
    "revert.banner.count_one": "ย้อนกลับ {{count}} ข้อความแล้ว",
    "revert.banner.count_other": "ย้อนกลับ {{count}} ข้อความแล้ว",
    "revert.banner.redo": "ทำซ้ำ",
    "revert.banner.redo.all": "ทำซ้ำทั้งหมด",
    "revert.banner.hint": "ส่งข้อความใหม่เพื่อทำให้การเปลี่ยนแปลงนี้ถาวร",
    "prompt.slash.badge.skill": "ทักษะ",
    "session.tab.local": "ในเครื่อง",
    "session.tab.cloud": "คลาวด์",
    "settings.agentBehaviour.subtab.agents": "ตัวแทน",
    "settings.agentBehaviour.createMode.prompt": "พรอมต์ระบบ",
    "settings.agentBehaviour.editMode.prompt": "พรอมต์ระบบ",
    "migration.whatsNew.features.agentManager.title": "ตัวจัดการตัวแทน",
  },
  tr: {
    "settings.agentBehaviour.createMode": "Yeni Mod Oluştur",
    "settings.agentBehaviour.createMode.name": "Ad",
    "settings.agentBehaviour.createMode.name.description": "Mod için benzersiz tanımlayıcı. Yalnızca küçük harf, rakam ve tire kullanın.",
    "settings.agentBehaviour.createMode.description": "Açıklama",
    "settings.agentBehaviour.createMode.description.help": "Bu modun ne yaptığının kısa açıklaması.",
    "settings.agentBehaviour.createMode.prompt": "Sistem İstemi",
    "settings.agentBehaviour.createMode.prompt.help": "Bu modu kullanırken yapay zeka ajanı için talimatlar.",
    "settings.agentBehaviour.createMode.button": "Oluştur",
    "settings.agentBehaviour.createMode.cancel": "İptal",
    "settings.agentBehaviour.createMode.nameRequired": "Ad gereklidir",
    "settings.agentBehaviour.createMode.nameInvalid": "Ad küçük harfle başlamalı ve yalnızca küçük harf, rakam ve tire içermelidir",
    "settings.agentBehaviour.createMode.nameTaken": "Bu adda bir mod zaten mevcut",
    "settings.agentBehaviour.editMode": "Modu Düzenle",
    "settings.agentBehaviour.editMode.description": "Açıklama",
    "settings.agentBehaviour.editMode.prompt": "Sistem İstemi",
    "settings.agentBehaviour.editMode.save": "Tamam",
    "settings.agentBehaviour.editMode.back": "Listeye dön",
    "settings.agentBehaviour.editMode.native": "Yerleşik mod (salt okunur tanım)",
    "settings.agentBehaviour.editMode.promptOverride": "Bu yerleşik mod için özel sistem istemi geçersiz kılma",
    "profile.switchingAccount": "Hesap değiştiriliyor…",
    "migration.whatsNew.features.agentManager.title": "Ajan Yöneticisi",
  },
  uk: {
    "settings.agentBehaviour.createMode": "Створити новий режим",
    "settings.agentBehaviour.createMode.name": "Назва",
    "settings.agentBehaviour.createMode.name.description": "Унікальний ідентифікатор режиму. Використовуйте лише малі літери, цифри та дефіси.",
    "settings.agentBehaviour.createMode.description": "Опис",
    "settings.agentBehaviour.createMode.description.help": "Короткий опис того, що робить цей режим.",
    "settings.agentBehaviour.createMode.prompt": "Системний запит",
    "settings.agentBehaviour.createMode.prompt.help": "Інструкції для агента ШІ при використанні цього режиму.",
    "settings.agentBehaviour.createMode.button": "Створити",
    "settings.agentBehaviour.createMode.cancel": "Скасувати",
    "settings.agentBehaviour.createMode.nameRequired": "Назва обов'язкова",
    "settings.agentBehaviour.createMode.nameInvalid": "Назва повинна починатися з малої літери і містити лише малі літери, цифри та дефіси",
    "settings.agentBehaviour.createMode.nameTaken": "Режим з такою назвою вже існує",
    "settings.agentBehaviour.editMode": "Редагувати режим",
    "settings.agentBehaviour.editMode.description": "Опис",
    "settings.agentBehaviour.editMode.prompt": "Системний запит",
    "settings.agentBehaviour.editMode.save": "Готово",
    "settings.agentBehaviour.editMode.back": "Назад до списку",
    "settings.agentBehaviour.editMode.native": "Вбудований режим (визначення лише для читання)",
    "settings.agentBehaviour.editMode.promptOverride": "Власне перевизначення системного запиту для цього вбудованого режиму",
    "profile.switchingAccount": "Перемикання акаунту…",
    "migration.whatsNew.features.agentManager.title": "Менеджер агентів",
  },
  zh: {
    "revert.banner.count_one": "已还原 {{count}} 条消息",
    "revert.banner.count_other": "已还原 {{count}} 条消息",
    "revert.banner.redo": "重做",
    "revert.banner.redo.all": "全部重做",
    "revert.banner.hint": "发送新消息以使此更改永久生效",
    "settings.permissions.tool.task.title": "任务",
    "settings.permissions.tool.skill.title": "技能",
    "settings.permissions.tool.webfetch.title": "网页获取",
    "settings.permissions.tool.websearch.title": "网页搜索",
    "settings.permissions.tool.codesearch.title": "代码搜索",
    "session.tab.local": "本地",
    "session.tab.cloud": "云端",
    "settings.agentBehaviour.subtab.agents": "代理",
    "migration.whatsNew.features.agentManager.title": "代理管理器",
  },
  zht: {
    "command.category.agent": "代理程式",
    "revert.banner.count_one": "已還原 {{count}} 則訊息",
    "revert.banner.count_other": "已還原 {{count}} 則訊息",
    "revert.banner.redo": "重做",
    "revert.banner.redo.all": "全部重做",
    "revert.banner.hint": "傳送新訊息以使此變更永久生效",
    "settings.general.notifications.agent.title": "代理程式",
    "settings.general.sounds.agent.title": "代理程式",
    "settings.agents.title": "代理程式",
    "settings.permissions.tool.task.title": "任務",
    "settings.permissions.tool.skill.title": "技能",
    "settings.permissions.tool.webfetch.title": "網頁擷取",
    "settings.permissions.tool.websearch.title": "網頁搜尋",
    "settings.permissions.tool.codesearch.title": "程式碼搜尋",
    "session.tab.local": "本機",
    "session.tab.cloud": "雲端",
    "settings.agentBehaviour.subtab.agents": "代理程式",
    "settings.agentBehaviour.subtab.skills": "技能",
    "settings.agentBehaviour.selectAgent.title": "代理程式",
    "migration.whatsNew.features.agentManager.title": "代理程式管理員",
  },
};

function escapeForRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function applyTranslations(content, lang, langTranslations) {
  let modified = content;
  let changedKeys = [];
  
  for (const [key, newValue] of Object.entries(langTranslations)) {
    // Match the key with its current value (any value in quotes)
    // Pattern: "key": "currentValue",
    const keyEscaped = escapeForRegex(key);
    
    // Match both single-line strings
    const singleLinePattern = new RegExp(
      `("${keyEscaped}":\\s*)"((?:[^"\\\\]|\\\\.)*)"`,
      'g'
    );
    
    const newValueEscaped = newValue.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    
    const before = modified;
    modified = modified.replace(singleLinePattern, `$1"${newValueEscaped}"`);
    
    if (modified !== before) {
      changedKeys.push(key);
    }
  }
  
  return { content: modified, changedKeys };
}

let totalChanges = 0;

for (const [lang, langTranslations] of Object.entries(translations)) {
  const filePath = path.join(workdir, `${lang}.ts`);
  if (!fs.existsSync(filePath)) {
    console.log(`Skipping ${lang} - file not found`);
    continue;
  }
  
  const content = fs.readFileSync(filePath, 'utf8');
  const { content: modified, changedKeys } = applyTranslations(content, lang, langTranslations);
  
  if (changedKeys.length > 0) {
    fs.writeFileSync(filePath, modified, 'utf8');
    console.log(`${lang}: Updated ${changedKeys.length} keys: ${changedKeys.join(', ')}`);
    totalChanges += changedKeys.length;
  } else {
    console.log(`${lang}: No changes needed (keys may already be translated or patterns didn't match)`);
  }
}

console.log(`\nTotal changes: ${totalChanges}`);
