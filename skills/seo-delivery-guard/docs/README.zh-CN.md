# SEO Delivery Guard

**面向 AI 编程 Agent、遵循 Google Search 官方边界的 SEO 开发与发布治理 Skill。**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?logo=openai&logoColor=white)](../SKILL.md)
[![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-2563eb)](../CHANGELOG.md)
[![MIT License](https://img.shields.io/badge/license-MIT-16a34a)](../LICENSE)
[![Documentation languages: 10](https://img.shields.io/badge/docs-10%20languages-7c3aed)](../README.md#documentation)
[![GitHub source](https://img.shields.io/badge/GitHub-pangxin12345%2Fseo--delivery--guard-181717?logo=github&logoColor=white)](https://github.com/pangxin12345/seo-delivery-guard)
[![Official website](https://img.shields.io/badge/website-once--email.com-0f766e?logo=googlechrome&logoColor=white)](https://once-email.com)
[![skills.sh](https://skills.sh/b/pangxin12345/seo-delivery-guard)](https://skills.sh/pangxin12345/seo-delivery-guard)

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português do Brasil](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Tiếng Việt](README.vi.md)

SEO 审计负责发现问题，**SEO Delivery Guard 帮助 AI 编程 Agent 将已经接受的问题推进到实现、审核、发布和生产验证**。

它不替代爬虫、性能工具、内容分析、Schema 校验、SERP 调研或 Search Console 数据。它编排当前环境已有能力，执行项目自己的规则，区分发布阻断与可选建议，并把延迟发生的搜索引擎结果与工程验证分开。

## 为什么需要它

- 源码中的 canonical 正确，但生成产物可能仍然错误；
- 未完成专业审校的翻译可能提前进入 Sitemap；
- 结构化数据可能描述页面上不可见的事实；
- robots 指令可能被错误地当成隐私或访问控制；
- SEO 综合分数可能掩盖索引或隐私硬阻断；
- 候选环境通过，但生产环境返回不同元数据；
- Google 尚未重抓取时，项目可能错误宣布 SEO 已生效。

SEO Delivery Guard 衔接网页分析与工程交付，覆盖 SEO 开发、CI/CD、回归审核、发布门禁和生产复验。

## 核心能力

- 根据真实改动选择最小必要的 SEO 分析组合；
- 读取项目已有的开发、隐私、国际化、分析、广告、测试和发布规则；
- 按明确优先级裁决互相冲突的建议；
- 为每个发现记录证据来源、时间、置信度、严重性、动作和验证层级；
- 硬阻断保持二元判定，不被健康分数平均掉；
- 比较改动前后、候选和生产的搜索可见合同；
- 区分源码、生成产物、浏览器、公网 HTTP、实验室、第一方数据和第三方估算；
- 不扩大用户授权，把接受的问题映射为开发与验收工作；
- 收录、排名、流量、富媒体结果、广告审核和 AI 展示在真实验证前保持“外部等待”。
- 内容或 URL 变化时，明确选择保留、增强、合并、`noindex` 或删除；只有真实等价页面才能使用 301，否则保持真实 `404/410`。

## 不做什么

- 不是另一个全站爬虫或一体化 SEO 审计器；
- 不依赖特定 SEO 厂商、API、MCP 或配套 Skill；
- 未经当前任务授权，不提交 URL、不修改搜索后台、不发布代码、不部署；
- 不承诺排名、收录、流量、富媒体结果、广告通过或 AI 引用；
- 不把关键词密度、固定字数、机械 E-E-A-T 分数或 Schema 数量当成排名保证。

## 输入、输出与拒绝边界

只提供完成任务必需的公开 URL、仓库路径、改动意图、目标用户、索引意图、语言和脱敏证据，不要提交密码、Cookie、私钥、完整分析导出或敏感用户数据。输出会区分规则、阻断、建议、未知项、证据限制、实施动作、验证层级、生产状态和外部等待。

Skill 拒绝排名操纵、虚构经验或证据、门页、无用户价值的批量页面、访问控制绕过、敏感信息暴露和虚假搜索引擎认证。页面或分析器不可用时保持“未知”，不能写成通过。

新增可索引页面必须解决现有最强页面无法替代的真实任务。机器翻译和结构检查不能证明语言质量；每个公开语言版本都需要事实与表达审校。

## 使用方式

通过支持的 Skill 市场安装，或把完整的 `seo-delivery-guard` 文件夹复制到 AI Agent 识别的 Skill 目录。重新加载 Skill 或开启新会话后调用：

```text
$seo-delivery-guard
```

公开安装包只有文本指令和元数据，不包含运行时、API Key、爬虫、可执行文件或操作系统专属组件。

## Google Search 边界

涉及 Google Search 的结论必须来自当前官方文档或经过验证的第一方站点数据。第三方 SEO 工具可以提供线索，但不能定义 Google 的 API 范围、索引决策、排名因素、标题链接、富媒体结果或 AI 搜索结果。

SEO Delivery Guard 是独立开源项目，与 Google 不存在隶属、认证、赞助或背书关系。

## 发布者

- 发布者与官网：[once-email.com](https://once-email.com)
- 创建者：helen.jar
- GitHub：[pangxin12345](https://github.com/pangxin12345)
- 公开支持：[tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

MIT License · 版本 0.1.0

变更记录见 [CHANGELOG.md](../CHANGELOG.md)。
