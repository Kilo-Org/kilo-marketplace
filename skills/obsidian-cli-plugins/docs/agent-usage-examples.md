# Obsidian CLI Plugins Agent 使用示例

本文面向 Agent 维护者。每个 `Uxx` 对应 `user-usage.md` 中的用户示例，并说明 Agent 应如何调用脚本。

所有示例默认：

```bash
SKILL=<skill-dir>
VAULT=~/git/obsidian-2026
PYTHON=python3
```

优先使用：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" <command>
```

跨 Agent 文件模式记录可使用：

```bash
$PYTHON "$SKILL/scripts/obs_record_sync.py" --vault-path "$VAULT" ...
```

通用停止条件：`ok=false`、`reason`、非零退出码、`unmerged`、`merge_head`、附件路径不可读、目标模板结构缺失、项目记录 `target_id` 不在模板结构中。

## 1. 环境、Vault 和同步

### U01 检查运行环境

用户说：

```text
检查 Obsidian vault 状态
```

脚本：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" doctor
```

Agent 处理：

- 新主机、新 Agent、新 shell、SSH、容器、OpenClaw runtime 必须先执行。
- 检查 `ok`、`resolved_vault`、`is_obsidian_vault`、`is_git_repo`、`configured_vaults`。
- 多 vault 不明确时停止，让用户指定 vault。

### U02 指定 vault 后检查

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault obsidian-2026 doctor
```

如果用户给出绝对路径，改用：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "/absolute/vault/path" doctor
```

### U03 查看 Git 状态

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" git-status
```

Agent 处理：报告 clean/ahead/behind；遇到 `unmerged` 或 `merge_head` 停止，不继续写入。
Git 状态优先来自主机 `git` 命令；只有主机 `git` 不存在时，相关同步流程才兜底到 Obsidian Git 插件命令。

### U04 同步 vault

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" sync --mode pull-push
```

用于读前同步或用户明确要求同步。写入类需求优先用 `add-task-sync`、`record-sync`、`project-*-sync`，不要手工组合 Git 命令。
该命令内部优先调用主机 `git pull --no-rebase`、`git push` 等命令；只有主机 `git` 不存在时才调用 `obsidian-git:*` 兜底。

### U05 使用当前打开的 vault

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault current doctor
```

只有 `doctor` 能明确解析单个当前打开 vault 时才继续。

## 2. 查看待办

### U06 今日新增待办

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  tasks show --period day --date today
```

Agent 处理：只汇总今天日记中直接写入的任务行，返回 `count`、任务文本和 note path。不要为了“今日新增待办”改跑全 vault 搜索。

### U07 今日完整待办

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  today-tasks --source
```

Agent 处理：输出结果汇总、今日相关、逾期未完成、循环任务；`--source` 保留来源定位。

### U08 本周待办

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  week-tasks --source
```

Agent 处理：区分 Tasks 查询结果和本周焦点中的非 `#task` checkbox。

### U09 周期原始任务行或任务查询结果

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  tasks show --period month --date today
```

如果用户明确说“任务查询结果”而不是“新增任务/原始任务行”，使用：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  tasks query --period month --date today
```

根据用户话术把 `--period` 改成 `day|week|month|quarter|year`。

## 3. 添加待办

### U10 添加今日待办

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  add-task-sync --period day --date today --kind auto \
  --text "整理 Obsidian 技能用户文档"
```

Agent 处理：

- 默认使用 `add-task-sync`，它会完成 Git preflight、journal 创建、章节定位、写入、提交、推送和验证。
- 不要用普通 `record-sync` 写任务。

### U11 添加指定日期待办

用户说 `7月5日前完成项目记录功能回归测试`，按当前年份推断为 `2026-07-05` 时：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  add-task-sync --period month --date 2026-07-01 --task-date 2026-07-05 \
  --kind auto --text "7月5日前完成项目记录功能回归测试"
```

Agent 处理：`--date` 是目标周期笔记选择日期，`--task-date` 是任务日期。具体日期优先于周期默认日期。

### U12 添加周期任务

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  add-task-sync --period week --date today --kind auto \
  --text "完善项目记录功能示例"
```

如果用户说本月/本季度/今年，分别使用 `month|quarter|year`。

### U13 本地测试添加待办

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  tasks add --period day --date today --kind auto \
  --text "验证新增任务章节定位"
```

只在用户明确要求“不提交不推送、本地测试”时使用。仍需验证目标章节和返回 JSON。

## 4. 普通记录

### U14 写入今天记录

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  record-sync --mode inline --period day --date today \
  --text "今天想到项目需求应该先收集，再逐步细化，不急着马上实现。"
```

Agent 处理：`--text` 保留用户原文，只去掉命令包装词；不总结、不润色、不翻译。

### U15 写入周/月/季/年记录

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  record-sync --mode inline --period week --date today \
  --text "项目记录功能需要区分普通记录和项目记录。"
```

按话术映射 `week|month|quarter|year`。

### U16 本地测试普通记录

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  record --mode inline --period day --date today \
  --text "验证记录章节追加，不提交不推送。"
```

本地测试才用 `record`；正式用户记录使用 `record-sync`。

## 5. 文件模式记录和卡片

### U17 创建独立记录卡片

第一步，获取语义分析契约：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-record \
  --text "项目灵感应该有项目文件承接，而不是只放在日记里。" \
  --date today --prompt-only
```

第二步，Agent 使用自身模型按 prompt 输出 JSON。示例只展示形状，真实值必须由模型基于 prompt 生成：

```json
{
  "kind": "灵感",
  "headline": "项目灵感应由项目文件承接",
  "insight": "长期项目灵感应沉淀到项目文件，而不是只放在日记记录中。",
  "next_actions": ["梳理项目记录文件模板"]
}
```

第三步，规范化：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-record \
  --text "项目灵感应该有项目文件承接，而不是只放在日记里。" \
  --date today \
  --analysis-json '{"kind":"灵感","headline":"项目灵感应由项目文件承接","insight":"长期项目灵感应沉淀到项目文件，而不是只放在日记记录中。","next_actions":["梳理项目记录文件模板"]}' \
  --normalized-only
```

第四步，写入：

```bash
$PYTHON "$SKILL/scripts/obs_record_sync.py" --vault-path "$VAULT" \
  --mode file --period day --date today \
  --text "项目灵感应该有项目文件承接，而不是只放在日记里。" \
  --analysis-json '{"kind":"灵感","headline":"项目灵感应由项目文件承接","insight":"长期项目灵感应沉淀到项目文件，而不是只放在日记记录中。","next_actions":["梳理项目记录文件模板"]}'
```

关键规则：语义分析必须来自 Agent 模型，脚本负责 prompt、规范化、模板渲染和写入。

### U18 记录带来源链接的内容

同 U17，但原文包含链接，并可补充 `--source`：

```bash
$PYTHON "$SKILL/scripts/obs_record_sync.py" --vault-path "$VAULT" \
  --mode file --period day --date today \
  --text "https://example.com 这个工具的交互方式值得参考。" \
  --source "https://example.com" \
  --analysis-json '<normalized-model-json>'
```

### U19 指定记录类型或主题

```bash
$PYTHON "$SKILL/scripts/obs_record_sync.py" --vault-path "$VAULT" \
  --mode file --period day --date today \
  --text "Obsidian 项目文件可以作为长期项目孵化器。" \
  --topic "灵感" \
  --analysis-json '<normalized-model-json>'
```

`--topic` 可作为提示或分类辅助，但正文仍以 `--text` 原文为准。

## 6. 附件和媒体记录

### U20 同一条消息记录附件

先确认 Agent runtime 提供的本地路径真实可读。然后：

```bash
$PYTHON "$SKILL/scripts/obs_record_sync.py" --vault-path "$VAULT" \
  --mode file --period day --date today \
  --text "这是项目记录功能的界面草图。" \
  --type mixed \
  --analysis-json '<normalized-model-json>' \
  --attach "/path/to/screenshot.png" \
  --require-attachment \
  --allow-external-attachments
```

Agent 处理：

- 用户请求包含附件时必须传 `--require-attachment`。
- 没有可读路径时返回 `attachment-path-unavailable`，不要创建文本-only 半成品。
- 成功后检查 `record_file.copied_attachments` 数量。

### U21 多个媒体文件先发、随后补一句记录

媒体消息到达时先暂存：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  attachment-stage --path "/path/to/media-1" --type <image|audio|video|file> \
  --label "media-1" --batch-key "conversation-user-bucket"

$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  attachment-stage --path "/path/to/media-2" --type <image|audio|video|file> \
  --label "media-2" --batch-key "conversation-user-bucket"
```

文本消息到达后先用 TTL-aware pending 命令核对，不要使用 `attachment-list --batch-key default`、旧 staged id 或直接读取 cache 目录：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  attachment-pending --batch-key "conversation-user-bucket" --ttl-hours 48
```

再创建记录：

```bash
$PYTHON "$SKILL/scripts/obs_record_sync.py" --vault-path "$VAULT" \
  --mode file --period day --date today \
  --text "项目文件模板设计参考。" \
  --type mixed \
  --analysis-json '<normalized-model-json>' \
  --staged-attachment "batch:conversation-user-bucket" \
  --require-attachment
```

如果用户说“三个媒体文件”但暂存数量不是 3，停止并要求确认。图片、视频、音频、文件都按同一套 staged media 流程处理；只有 `attachment-stage --type` 元数据和最终 Markdown 渲染会因文件类型不同。

### U22 清理过期附件暂存

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  attachment-prune --ttl-hours 48
```

只清理私有缓存，不删除 vault 文件。

## 7. 项目文件创建

### U23 创建项目文件

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  project-create-sync \
  --title "项目记录功能测试" \
  --folder 01_project \
  --landing-threshold "验证项目文件创建和小步更新流程"
```

`project-create-sync` 会按项目模板生成文件，运行 Linter，并提交推送。

### U24 指定项目目录和落地判断

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  project-create-sync \
  --title "项目记录功能测试" \
  --folder 01_project/obsidian \
  --landing-threshold "能稳定创建项目文件，并支持通过 target_id 小步追加内容"
```

### U25 本地测试创建项目

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  project-create \
  --title "项目记录功能测试" \
  --folder 01_project/obsidian \
  --landing-threshold "本地验证模板生成" \
  --no-lint
```

本地测试可用 `--no-lint`，正式流程不要默认跳过 Linter。

## 8. 项目小步更新

项目记录必须以项目模板和小模板为准。Agent 不得硬编码章节、字段或 `target_id`。

### U26 查看项目结构对象

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  project-template-structure --project "项目记录功能测试"
```

Agent 处理：读取返回的 `template_structure`，包括标题树、去图标标题、可写入 `target_id`、小模板字段。

### U27 追加原始灵感

第一步，获取项目语义分析 prompt：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-project-record \
  --project "项目记录功能测试" \
  --text "想到一个长期项目记录功能，平时一点点补充需求，等清晰后再落地。" \
  --prompt-only
```

第二步，Agent 基于 prompt 和 `template_structure` 用自身模型生成 JSON。示例：

```json
{
  "target_id": "<来自 template_structure 的原始灵感 target_id>",
  "text": "想到一个长期项目记录功能，平时一点点补充需求，等清晰后再落地。",
  "fields": {}
}
```

第三步，规范化和校验：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-project-record \
  --project "项目记录功能测试" \
  --text "想到一个长期项目记录功能，平时一点点补充需求，等清晰后再落地。" \
  --analysis-json '<model-json-with-valid-target-id>' \
  --normalized-only
```

第四步，正式写入：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  project-record-sync \
  --project "项目记录功能测试" \
  --text "想到一个长期项目记录功能，平时一点点补充需求，等清晰后再落地。" \
  --analysis-json '<normalized-model-json>'
```

### U28 追加功能需求

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-project-record \
  --project "项目记录功能测试" \
  --section 功能需求 \
  --text "支持把一句话灵感追加到项目文件对应章节。" \
  --prompt-only
```

模型 JSON 示例：

```json
{
  "target_id": "<来自 template_structure 的功能需求 target_id>",
  "text": "支持把一句话灵感追加到项目文件对应章节。",
  "fields": {
    "需求": "支持把一句话灵感追加到项目文件对应章节",
    "使用场景": "用户临时想到项目细节时，通过 Agent 追加到项目文件",
    "价值": "降低项目需求沉淀成本",
    "状态": "待验证"
  }
}
```

写入同 U27 的 `project-record-sync`。`fields` 字段必须来自当前 `card-project-fr` 小模板解析结果，没有内容的字段不要输出。

### U29 追加非功能需求

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-project-record \
  --project "项目记录功能测试" \
  --section 非功能需求 \
  --text "项目记录不能依赖硬编码章节，必须以模板结构解析结果为准。" \
  --prompt-only
```

模型必须使用当前 `card-project-nfr` 字段，并选择模板结构中的非功能需求 `target_id`。

### U30 追加决策记录

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-project-record \
  --project "项目记录功能测试" \
  --section 决策 \
  --text "采用 template_structure + target_id 作为写入定位机制。" \
  --prompt-only
```

模型必须使用当前 `card-project-decision` 字段，并选择模板结构中的决策 `target_id`。

### U31 追加项目任务或问题

任务示例：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-project-record \
  --project "项目记录功能测试" \
  --section 任务 \
  --text "补充项目记录功能的用户文档。" \
  --prompt-only
```

问题示例：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  analyze-project-record \
  --project "项目记录功能测试" \
  --section 问题 \
  --text "是否需要支持自动识别多个候选项目？" \
  --prompt-only
```

Agent 处理：任务和问题写入模板 tail 附录对应 `target_id`。不要写入已删除或重复的正文“待验证问题/任务候选”章节。

本地测试写入可用：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  project-record \
  --project "项目记录功能测试" \
  --text "<project detail>" \
  --analysis-json '<normalized-model-json>' \
  --no-lint
```

正式流程使用 `project-record-sync`，默认运行 Obsidian Linter。

## 9. 安全读取和搜索

### U32 安全读取 vault 文件

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  safe-read "01_project/obsidian/项目记录功能测试.md" --max-lines 160
```

Agent 处理：遵守敏感路径跳过、脱敏和最小必要片段原则。

### U33 搜索 vault 内容

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  safe-search "项目记录功能" --max-results 50
```

Agent 处理：返回标题、路径、短片段；不要绕过 `safe-search` 做全量内容 dump。

## 10. 插件、命令和官方 CLI

### U34 查看已启用插件

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" plugins
```

### U35 查找社区插件命令

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  commands --plugin obsidian-linter --json
```

Agent 处理：社区插件命令用 `commands --plugin <plugin-id>`，不要从旧文档硬猜 command id。

### U36 执行普通插件命令

先查 command id，再执行：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  run obsidian-linter:lint-file
```

Agent 处理：`Executed: <command-id>` 只代表命令派发成功；还要检查文件、Git 或插件实际效果。

### U37 查询官方 Obsidian CLI 命令

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  official-commands --search property --json
```

也可按分类：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  official-commands --category properties
```

官方 CLI 查找用于原生 Obsidian 能力；journal 任务和记录仍优先走本技能封装命令。

### U38 执行敏感或破坏性命令

只有用户明确确认具体命令后：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  run "plugin:disable" --risk destructive --yes
```

Agent 处理：安装、卸载、启用、禁用、删除、恢复、发布、developer/eval/debug 等命令都需要确认。

## 11. OpenClaw 和跨 Agent 使用

### U39 同步技能到 OpenClaw

先 dry-run：

```bash
$PYTHON "$SKILL/scripts/sync_openclaw.py" --dry-run
```

确认后同步：

```bash
$PYTHON "$SKILL/scripts/sync_openclaw.py"
```

如果用户明确要求替换已有副本：

```bash
$PYTHON "$SKILL/scripts/sync_openclaw.py" --force
```

### U40 检查 OpenClaw 技能可用

同步后至少检查：

```bash
test -f "$HOME/.openclaw/skills/obsidian-cli-plugins/SKILL.md"
$PYTHON "$HOME/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py" doctor
```

如果 OpenClaw 有自己的 skill discovery 命令，再运行其发现命令。OpenClaw 可能缓存技能，需要刷新或重启。

## 12. 扩展和维护

### U41 为新插件补充工作流支持

发现插件：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" plugins
```

发现命令：

```bash
$PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" \
  commands --plugin "<plugin-id>" --json
```

只读取必要配置键：

```bash
jq 'keys' "$VAULT/.obsidian/plugins/<plugin-id>/data.json"
jq '.safeKeyNeededForThisWorkflow' "$VAULT/.obsidian/plugins/<plugin-id>/data.json"
```

Agent 处理：重复解析、写入或同步逻辑必须沉淀到 `scripts/obsidian_cli_plugins/`，不要把临时 shell 片段写进说明文档。

### U42 验证技能脚本

```bash
PYTHONDONTWRITEBYTECODE=1 $PYTHON -m pytest "$SKILL/scripts/tests"
PYTHONDONTWRITEBYTECODE=1 $PYTHON "$SKILL/scripts/obsidian_workflows.py" --vault-path "$VAULT" doctor
$PYTHON "$SKILL/scripts/sync_openclaw.py" --dry-run
```

验证后清理生成的 `__pycache__` 或 `.pyc`，再同步技能副本。
