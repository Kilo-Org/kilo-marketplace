背景前提
KIMI3模型在7.16日推出，同步推出的还有一个网站 K399 · K3 Game Arcade 
[图片]
内部是诸多官方挑选出来的一句话生成游戏的用户/官方案例（包含多种游戏类型和经典游戏复刻）。搜索了油管、X、谷歌、KIMI 官方等渠道，目前主要在X和Linux DO上收集到比较多消息。
[图片]
[图片]
astrocade 这边直接跑了一个具体案例，具体见下。
[图片]
KIMI3具体对话案例
以在Linux DO网站（linux.do）收集到的快速生成游戏的对话记录为案例分析
Kimi | 血月幸存者游戏反馈
用户输入的prompt只有两句,生成游戏和修复bug。便生成出一个有着完整游戏体验（逻辑、美术、音频）的类吸血鬼游戏 https://iwgf77mjicz7o.ok.kimi.link/
技术栈
层次
选型
依据(命令/文档原文)
语言
TypeScript (strict)
始终使用 npx tsc -b --noEmit 做类型检查
框架
React 19
设计文档明写 + init-webapp.sh 脚手架产出
样式
Tailwind CSS
init-webapp.sh 产出含 tailwind.config + 全局主题变量
构建
Vite
npm run build → vite build,产物 468 modules
渲染
Canvas 2D (主) + WebGL2 (特效层)
enemies.ts 程序化剪影绘制、fxgl.ts bloom+冲击波
音频
Web Audio API (零音频文件)
sfx.ts + bgm.ts,OscillatorNode/GainNode/BiquadFilter/Convolver/WaveShaper
部署
静态 HTML/JS/CSS → website_version_manager
build_version action 返回 version_id: d27d8e0

[图片]
[图片]

分析流程，如何生成出来游戏
流程总览
 主要围绕 DDD(Document-Driven Development) 的流程 ，先出全套设计文档,再按文档派发 Agent 开发。
看着工作区是在远程虚拟机沙盒上进行，内置skill和具体文件修改之类。再通过git分支隔离，各agent自验证通过，交由主agent合并。 美术和音频尽可能走程序化生成，部分使用图生成模型实现。
[图片]
（DDD+工作区这个方案很有效，但是问题在于，文档如何保持更新，这是之前尝试DDD驱动过程的最大问题。这里找到的案例，看着这文档就是一次性用的，没有更新，但是由于就两轮对话，修bug理论上确实不用文档更新，无法太确定它的工作流程。注册了一个账号尝试一下，但一直显示工作繁忙....）
Stage 1: 设计阶段
  ├── 读取 plan.md 模板
  ├── 派发 designer Agent → 产出 N 份设计文档
  └── 设计文档存入 /mnt/agents/output/design/

Stage 2: 脚手架阶段
  ├── 调用 webapp-building-swarm/init-webapp.sh 初始化项目
  ├── 派发 scaffold Agent → 建立:
  │   ├── types.ts(全类型定义)
  │   ├── store.ts(zustand 全局状态)
  │   ├── engine.ts(游戏引擎骨架,固定时间步进)
  │   ├── systems/ *.ts(占位,签名即契约)
  │   ├── 数据表(weapons.ts/passives.ts/enemies.ts)
  │   └── 页面/组件(占位或完整实现)
  └── 合并到 master,创建并行分支

Stage 3: 并行开发阶段
  ├── 同时派发 N 个 coder Agent,各自 Git 分支隔离
  ├── 每个 Agent:
  │   ├── setup-local.sh 搭建独立环境
  │   ├── 阅读自己归属的设计文档章节
  │   ├── 只能修改归属文件
  │   └── tsc + git commit 自验证
  └── 主 Agent 合并 & 构建验证

Stage 4: 交付阶段
  ├── npx tsc -b --noEmit(全量类型检查)
  ├── npm run build(Vite 生产构建)
  └── website_version_manager build_version(部署)
设计文档(设计师 Agent 产出,共 6 份,65 KB)
[图片]
具体调用SKILL
图片生成

Skill: image_generation
来源: /app/.agents/plugins/image_generation/skills/image_generation/SKILL.md 这是三个加载技能中唯一被完整读入主对话全文的技能

name: image_generation description: |- Create an image based on a text description using AI image generation.

Features:
Generate high-quality images from text prompts

Support conditional opaque image size combinations: 1K supports 1:1, 3:2, 2:3; 2K supports 1:1, 16:9; 4K supports 16:9, 9:16.

Support multiple resolutions: 1K, 2K, 4K. Default is 1K.

If the background is transparent, only supports 1:1, 3:2, 2:3 ratios and 1K resolution.

Support background color: opaque (default) or transparent

Support JPG, JPEG, PNG format output with high resolution (only support png for transparent)

Usage Guidelines:
Provide detailed, descriptive prompts for better results

Include specific details about style, composition, colors, and mood

Use clear, descriptive language for best image quality

Specify output file path with .jpg, .jpeg, .png extension (only support png for transparent)

Best Practices:
Be specific about visual elements (lighting, perspective, style)

Include artistic style references when desired

Describe composition and framing details

Mention color schemes and atmosphere

Image Generation
Use this skill to create an image from a text description with AI image generation, then save it locally and display it to the user.

Setup
Before the first use, ensure the agent-gw Python SDK (version 0.2.6 or newer) is installed:

python3 scripts/image_generation_tool.py ensure-deps
The SDK needs an API key from api_key=..., KIMI_API_KEY, or ~/.kimi/agent-gw.json.

Parameters
description (required): detailed text description of the image to generate.
ratio: one of 1:1, 3:2, 2:3, 16:9, 9:16. Default 1:1.
resolution: one of 1K, 2K, 4K. Default 1K. Opaque background supports only these combinations: 1K: 1:1 (1024x1024), 3:2 (1536x1024), 2:3 (1024x1536); 2K: 1:1 (2048x2048), 16:9 (2048x1152); 4K: 16:9 (3840x2160), 9:16 (2160x3840). Transparent background only supports 1K with 1:1, 3:2, 2:3.
background: opaque (default) or transparent.
reference_image: public URL(s) that guide the generation. Repeat --reference-image for multiple.
output (required): local output path ending in .jpg, .jpeg, or .png. Transparent background must use .png.
Workflow
Build a detailed, descriptive description from the user's request.
Choose ratio, resolution, and background. Enforce the supported combinations.
Pick an output file path with a matching extension.
If reference images are supplied (must be public URLs), first run image-to-url to convert local images.
Run the generate command which calls generate_image on the gateway.
On success, display the image to the user by calling readFile on the output path.
Script
python3 scripts/image_generation_tool.py generate \
  --description "A serene mountain lake at sunrise..." \
  --ratio "16:9" \
  --resolution "2K" \
  --background "opaque" \
  --output "/path/to/output.png"
The script:

generate accepts only public --reference-image URLs
image-to-url uploads a local image and returns a public signed_url
sends {description, ratio, resolution, background, reference_image_urls} to the gateway
reads the generated media.url and media.mime_type from the response
downloads the image with curl
generate_image response shape:

{
    "media": {
        "url": str,        # public URL of the generated image
        "mime_type": str,  # e.g. "image/png" or "image/jpeg"
    }
}
This skill uses the agent-gw Python SDK: client.tools.generate_image(...) for generation and client.upload_storage(...) for local image to URL conversion.

多agent排布的工作流定义

Skill: vibecoding-webapp-swarm
来源: /app/.agents/skills/vibecoding-webapp-swarm/SKILL.md ⚠️ 主对话中 read_file 只返回了"Gained some skills from the file."(摘要模式) 以下内容根据各 Agent Prompt 中的引用指令和流程反推

角色
编排技能(Orchestration Skill) — 多 Agent 并行网页应用开发的顶层编排器。

已知组成部分
1. design-guide.md — 设计指南
设计师 Agent 被要求"Read /app/.agents/skills/vibecoding-webapp-swarm/design-guide.md in full. Follow it as your design reference."

可知 design-guide.md 定义了:

设计文档的格式规范(色彩/字体/动效/页面结构)
输出规范(每页一个 .md 文件)
资产策略("favor procedurally-drawn canvas sprites over generated images")
2. react-dev.md — React 开发规约
所有 coder Agent 被要求"完整阅读 /app/.agents/skills/vibecoding-webapp-swarm/react-dev.md"

可知 react-dev.md 定义了:

React + TypeScript + Tailwind 编码规范
组件文件组织结构
Props 接口契约约定
3. 多 Agent 工作流模板(从 plan.md 与执行流程反推)
Stage 1: 设计阶段
  ├── 读取 plan.md 模板
  ├── 派发 designer Agent → 产出 N 份设计文档
  └── 设计文档存入 /mnt/agents/output/design/

Stage 2: 脚手架阶段
  ├── 调用 webapp-building-swarm/init-webapp.sh 初始化项目
  ├── 派发 scaffold Agent → 建立:
  │   ├── types.ts(全类型定义)
  │   ├── store.ts(zustand 全局状态)
  │   ├── engine.ts(游戏引擎骨架,固定时间步进)
  │   ├── systems/*.ts(占位,签名即契约)
  │   ├── 数据表(weapons.ts/passives.ts/enemies.ts)
  │   └── 页面/组件(占位或完整实现)
  └── 合并到 master,创建并行分支

Stage 3: 并行开发阶段
  ├── 同时派发 N 个 coder Agent,各自 Git 分支隔离
  ├── 每个 Agent:
  │   ├── setup-local.sh 搭建独立环境
  │   ├── 阅读自己归属的设计文档章节
  │   ├── 只能修改归属文件
  │   └── tsc + git commit 自验证
  └── 主 Agent 合并 & 构建验证

Stage 4: 交付阶段
  ├── npx tsc -b --noEmit(全量类型检查)
  ├── npm run build(Vite 生产构建)
  └── website_version_manager build_version(部署)
4. 关键契约机制
从 Agent Prompt 中可见的核心约束:

文件归属隔离:每个 Agent 只能修改指定文件列表,禁止越界(约 20+ 文件明文列入黑名单)
接口签名冻结:脚手架阶段定义的 types/store/engine/systems 签名一旦提交不得修改
Git 分支隔离:每个 Agent 独立分支,主 Agent 负责合并
自验证闭环:每个 Agent 提交前必须 npx tsc -b --noEmit 通过
不启动 dev server 原则:Agent 只负责提交代码,主 Agent 负责构建验证

项目初始化

Skill: vibecoding-webapp-swarm
来源: /app/.agents/skills/vibecoding-webapp-swarm/SKILL.md ⚠️ 主对话中 read_file 只返回了"Gained some skills from the file."(摘要模式) 以下内容根据各 Agent Prompt 中的引用指令和流程反推

角色
编排技能(Orchestration Skill) — 多 Agent 并行网页应用开发的顶层编排器。

已知组成部分
1. design-guide.md — 设计指南
设计师 Agent 被要求"Read /app/.agents/skills/vibecoding-webapp-swarm/design-guide.md in full. Follow it as your design reference."

可知 design-guide.md 定义了:

设计文档的格式规范(色彩/字体/动效/页面结构)
输出规范(每页一个 .md 文件)
资产策略("favor procedurally-drawn canvas sprites over generated images")
2. react-dev.md — React 开发规约
所有 coder Agent 被要求"完整阅读 /app/.agents/skills/vibecoding-webapp-swarm/react-dev.md"

可知 react-dev.md 定义了:

React + TypeScript + Tailwind 编码规范
组件文件组织结构
Props 接口契约约定
3. 多 Agent 工作流模板(从 plan.md 与执行流程反推)
Stage 1: 设计阶段
  ├── 读取 plan.md 模板
  ├── 派发 designer Agent → 产出 N 份设计文档
  └── 设计文档存入 /mnt/agents/output/design/

Stage 2: 脚手架阶段
  ├── 调用 webapp-building-swarm/init-webapp.sh 初始化项目
  ├── 派发 scaffold Agent → 建立:
  │   ├── types.ts(全类型定义)
  │   ├── store.ts(zustand 全局状态)
  │   ├── engine.ts(游戏引擎骨架,固定时间步进)
  │   ├── systems/*.ts(占位,签名即契约)
  │   ├── 数据表(weapons.ts/passives.ts/enemies.ts)
  │   └── 页面/组件(占位或完整实现)
  └── 合并到 master,创建并行分支

Stage 3: 并行开发阶段
  ├── 同时派发 N 个 coder Agent,各自 Git 分支隔离
  ├── 每个 Agent:
  │   ├── setup-local.sh 搭建独立环境
  │   ├── 阅读自己归属的设计文档章节
  │   ├── 只能修改归属文件
  │   └── tsc + git commit 自验证
  └── 主 Agent 合并 & 构建验证

Stage 4: 交付阶段
  ├── npx tsc -b --noEmit(全量类型检查)
  ├── npm run build(Vite 生产构建)
  └── website_version_manager build_version(部署)
4. 关键契约机制
从 Agent Prompt 中可见的核心约束:

文件归属隔离:每个 Agent 只能修改指定文件列表,禁止越界(约 20+ 文件明文列入黑名单)
接口签名冻结:脚手架阶段定义的 types/store/engine/systems 签名一旦提交不得修改
Git 分支隔离:每个 Agent 独立分支,主 Agent 负责合并
自验证闭环:每个 Agent 提交前必须 npx tsc -b --noEmit 通过
不启动 dev server 原则:Agent 只负责提交代码,主 Agent 负责构建验证

Astrocade 具体对话案例
美术和音频资产是走内部资产库/可能AI生成，通过公用SDK库来加载获取，AI主要写玩法逻辑。优点生成的游戏实时反馈,逐步增量构建，用户交互感觉很足，缺点在于游戏类型可能还是过于受限。
[图片]
[图片]
[图片]

技术栈对比
Astrocade 模式:
  平台(资产/存档/排行榜/设置面板/部署) 
    └── 你的单文件 game.js
         └── 游戏逻辑(约 300-500 行)

Kimi 模式:
  你的项目(42+ 文件, ~5000 行) 
    ├── React + Vite + Tailwind
    ├── Canvas 2D 引擎(自建)
    ├── Web Audio 引擎(自建)
    ├── 程序化精灵系统(自建)
    ├── image_generation skill(2张图)
    ├── website_version_manager(部署)
    └── 无平台(纯静态)

维度
Astrocade
Kimi 
游戏入口
单文件 run(mode)
完整 React + Vite 项目
渲染
平台给 Canvas 2D Context(隐式)
自建双层 Canvas + WebGL2
资产
平台资产库(lib.getAsset)
自管理(2 张 AI 生图 + 全程序化)
音频
平台托管(type: "audio")
自建 Web Audio 程序化合成
存档/排行榜
lib.saveUserGameState / lib.addPlayerScoreToLeaderboard
无(纯单机)
LLM
lib.llm() 内建
无(不涉及)
部署
上传到 Astrocade 平台
Vite build → 静态文件 → website_version_manager
编辑模式
平台自带 mode='edit' + undo/redo
无
分析流程
具体代码没有给出，对话也隐藏了具体的思考链，只能尽可能分析了。

[图片]
[图片]
[图片]
大致是走框架集成，在已经构建好的基础游戏模板上填充逻辑，一个run函数解决全部
run(mode)
  ├── window.gameConfig      ← 平台注入配置
  │     ├── ghost.speed/maxGhosts/spawnRate/health
  │     ├── wizard.maxHealth
  │     ├── gem.value
  │     └── ... (lib.showGameParameters 自动渲染设置面板)
  ├── 运行时状态(局部变量)
  │     ├── ghosts[] / lastSpawnTime
  │     ├── wizardPos / health / score / invulnTimer
  │     └── gameOver flag
  └── gameLoop(timestamp)
        ├── spawnGhosts()       — 随机屏幕边缘生成
        ├── updateGhosts()      — 向量追踪 + 角度计算
        ├── updateSpells()      — 弹幕移动
        ├── checkCollisions()   — 圆形碰撞检测(spell↔ghost, ghost↔wizard)
        ├── updateGems()        — 掉落 + 拾取(distance-based)
        └── draw()             — drawImage 精灵渲染
// 对比KIMI生成出来的游戏
React App
  └── GameScreen.tsx
        └── GameEngine (class, rAF loop)
              ├── engine.ts — 固定时间步进 1/60
              ├── player.ts
              ├── enemies.ts — 12 敌 AI + 3 Boss(子状态 WeakMap)
              ├── spawner.ts — 波次时间线 + 难度倍率
              ├── combat.ts — 空间哈希 O(n) 碰撞
              ├── pickups.ts — 经验宝石/宝箱/磁吸
              ├── weapons.ts — 12 武器 + 8 超武 + 弹道池
              ├── upgrades.ts — 卡池权重/进化判定
              ├── fx.ts — 粒子/震屏/顿帧/伤害数字
              ├── audio.ts — Web Audio 程序化
              ├── input.ts — 虚拟摇杆 + 键盘降级
              └── store.ts — zustand 全局状态(settings 持久化 localStorage)

[图片]
