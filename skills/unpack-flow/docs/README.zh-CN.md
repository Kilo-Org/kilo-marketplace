# UnpackFlow：跨平台多层、分卷和批量归档解压

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

UnpackFlow 用来安全处理批量归档、嵌套压缩包和分卷文件。它会识别正确的首卷，逐层解压，持续显示进度，并保留原始压缩包。

适合处理软件包、数据集、备份、素材、日志、ISO/WIM 镜像和大型下载归档。它不会执行压缩包中的未知 EXE，也不会覆盖已有结果。

## 30 秒快速开始

先查看将要处理的文件：

```bash
unpack-flow list '/data/archives/*'
```

检查压缩包结构和分卷首卷：

```bash
unpack-flow plan '/data/archives/backup.part1.rar'
```

在当前终端解压并查看实时进度：

```bash
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

如果希望任务在后台继续运行：

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

## 安装命令行工具

先运行检查命令。检查只报告环境和缺失依赖，不会自动安装系统软件。

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

先完整解压 Windows 发布包，然后双击 `install.bat`，或者在命令提示符中运行：

```bat
install.bat -Check
install.bat
unpack-flow version
```

`install.bat` 只为本次安装启动 PowerShell，不会修改系统或当前用户的执行策略。

## 前台运行还是后台运行

| 需求 | 命令 | 行为 |
|---|---|---|
| 想一直看着解压进度 | `run` | 留在当前终端，完成后返回结果 |
| 想关闭当前窗口或继续做其他事 | `start` | 立即返回任务号，解压在后台继续 |

三个系统的含义完全一致：`run` 始终是前台，`start` 始终是后台。

## 常用命令

| 命令 | 用途 |
|---|---|
| `list` | 列出真正会处理的压缩包和分卷首卷 |
| `plan` | 检查单个归档的格式、首卷和内容结构 |
| `run` | 前台解压并持续显示进度 |
| `start` | 创建后台任务并返回任务号 |
| `status` | 查看任务状态和已运行时间 |
| `log` | 查看任务日志和失败原因 |
| `wait` | 等待后台任务结束并返回最终结果 |
| `help` | 查看中英文命令、参数、格式和安全说明 |

省略任务号时，`status`、`log` 和 `wait` 默认操作最近一次任务。

## 常见使用方式

### 批量解压目录中的所有归档

```bash
unpack-flow run '/data/incoming/*' -Output '/data/extracted'
```

带引号的通配符最稳妥。即使直接执行 `unpack-flow run *`，UnpackFlow 也会统一扫描参数并自动过滤：

- `.sha256` 等校验文件；
- 普通文件和不支持的文件；
- `part2.rar`、`.7z.002`、`.zip.002` 等后续分卷。

只有普通单包以及 `part1.exe`、`part1.rar`、`.7z.001`、`.zip.001` 等首卷会成为独立任务。

### 解压子目录和内层压缩包

目录中还有子目录或嵌套归档时，使用 `-r`：

```bash
unpack-flow run -r '/data/incoming/*' -Output '/data/extracted'
```

Windows 和 macOS PowerShell 也支持 `-Recursive`。默认最多继续展开 10 个内层。

如果目标名称已经存在，UnpackFlow 不会覆盖。它会加入来源目录作为上下文，并在继续重名时追加编号：

```text
sample-backup-unpacked
sample-backup-legacy-set-unpacked
sample-backup-legacy-set-unpacked-2
```

### 处理 RAR 分卷或自解压包

所有分卷必须放在同一目录中。只需要选择第一个分卷，不要运行未知 EXE：

```powershell
unpack-flow plan 'D:\Downloads\Backup\Backup.part01.exe'
unpack-flow start 'D:\Downloads\Backup\Backup.part01.exe' -Output 'E:\Extracted'
unpack-flow log
unpack-flow wait
```

UnpackFlow 把 `part01.exe` 当作归档数据读取，不会执行其中的程序。

## 后台任务和日志

创建后台任务后，终端会立即显示任务号：

```bash
unpack-flow start '/data/archives/backup.7z' -Output '/data/extracted'
```

随后可以使用：

```bash
unpack-flow status JOB_ID
unpack-flow log JOB_ID
unpack-flow wait JOB_ID
```

### 日志保存位置

| 平台 | 默认目录 |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |
| macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

日志包含当前归档、处理阶段、嵌套层数、已运行时间、输出目录和失败原因。

大型归档长时间没有新输出时，界面仍会刷新耗时；任务日志每 30 秒写入一次运行心跳。macOS 和 Windows 的后台任务不会向当前终端泄漏进度、ANSI 控制码或提示音。

## 解压失败时会发生什么

UnpackFlow 只尝试与文件格式匹配的工具，不会无限重试：

1. 优先使用 7-Zip；
2. RAR 可以回退到 UnRAR；
3. TAR、TAR.GZ、GZ 和 ZIP 可以按平台回退到系统工具；
4. 每次失败后先清理本次产生的不完整结果；
5. 所有可用工具都失败时，保留原包并记录错误，然后继续处理下一个归档。

只有明确需要“遇到第一个错误就停止”时，才使用 `-StopOnError`。

## 支持格式和运行环境

常见支持格式包括 RAR、分卷 RAR、7z、ZIP、TAR、TAR.GZ/TGZ、GZ、ISO 和 WIM。实际可解压格式取决于当前平台可用的引擎。

| 平台 | 运行环境 | 解压引擎 |
|---|---|---|
| Linux x64 | Bash 4+、GNU 工具 | 系统 7z/7zz，发布包内置 UnRAR 7.23 |
| Windows x64 | PowerShell 5.1+ | 内置完整版 7-Zip 26.02 和 UnRAR |
| Windows ARM64 | PowerShell 5.1+ | 内置完整版 7-Zip 26.02 |
| macOS ARM64 | PowerShell 7+ | 系统 `7zz`，发布包内置 UnRAR |

内置工具来自官方发布包，原始包和许可证保留在仓库中。

## 是否需要 Python

日常安装和解压不需要 Python：

- 运行 `unpack-flow` 不需要 Python；
- Windows、Linux、macOS 的 CLI 安装器不需要 Python；
- Windows 的 Agent Skill 安装器不需要 Python；
- 手工复制 Skill 目录不需要 Python。

只有以下维护操作需要 Python 3：

- Linux/macOS 使用 `scripts/install_local.py` 或 `scripts/install_local.sh` 自动安装 Agent Skill；
- 运行 Python 版本的项目审计。

## 安全规则

- 保留所有源压缩包；
- 不覆盖已有目标目录；
- 不执行归档中的未知 EXE；
- 不绕过密码、DRM 或访问控制；
- 拒绝把系统根目录作为输入或输出；
- 大型任务开始前应确认磁盘空间充足。

## 测试和发布验证

生成并运行小型公开回归套件：

```bash
bash tests/generate-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
```

约 218 KiB 的 `unpack-flow-minimal-testcases-v1.zip` 覆盖 ZIP、TAR.GZ、嵌套归档、Unicode 路径、同名输出、真实分卷首卷和预期的缺卷失败。套件不包含大型应用文件，也不会执行 SFX。

维护者可以运行：

```bash
scripts/check-docs.sh
scripts/build-release.sh
```

## 安装为 Agent Skill

Linux/macOS 自动安装：

```bash
scripts/install_local.sh .
```

Windows 自动安装：

```powershell
.\scripts\install_local.ps1 -Source .
```

也可以把整个 `unpack-flow` 目录手工复制到 Agent 使用的 Skills 目录。安装后新建会话，再调用 `$unpack-flow`。

## 支持与发布者

- 发布者、维护者和官网：[once-email.com](https://once-email.com)
- 创建者与开发者：helen.jar
- GitHub 项目：[pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)
- 公开支持邮箱：[tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

有问题请直接发送邮件至 [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)。

MIT License，版本 2.1.2。
