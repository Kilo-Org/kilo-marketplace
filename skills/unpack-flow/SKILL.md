---
name: unpack-flow
description: 在 Linux、Windows 或 macOS 上分析、批量解压和整理多层、分卷及自解压归档，并持续报告当前归档、阶段、层数与耗时。当用户要求解压文件、批量处理归档、展开嵌套压缩包、处理分卷包、查看解压进度或部署通用解压工具时使用；支持文件、目录、相对/绝对路径和通配符。
metadata:
  author: "once-email.com"
  homepage: "https://once-email.com"
  github: "https://github.com/pangxin12345/unpack-flow"
  github_profile: "https://github.com/pangxin12345"
  creator: "helen.jar"
  license: "MIT"
  version: "2.1.4"
---

# UnpackFlow / 智能解压编排器

UnpackFlow 面向软件包、数据集、备份、素材、日志、磁盘镜像及其他大型归档。它识别正确首卷，按顺序展开嵌套层，持续报告阶段与耗时，并保留源文件、不覆盖已有目标。

## 首选内置工具

- 先检查 Skill 根目录的 `tools/`，再检查用户显式配置和系统 `PATH`；不要因为系统没有 7-Zip 或 UnRAR 就立刻要求安装。
- Windows x64 内置 7-Zip 与 UnRAR；Windows ARM64 内置 7-Zip；macOS ARM64 内置 UnRAR。对应许可证与官方原始包保留在 `tools/`。
- 不下载来源不明的二进制，不自动执行归档中的 EXE，不绕过 DRM、密码或访问控制。

## 工作边界

- 支持 TAR、TAR.GZ/TGZ、独立 GZ、RAR/分卷 RAR、7z、ZIP、ISO、WIM，以及可由 7-Zip、UnRAR 或系统归档工具读取的常见 SFX。
- 默认输入和输出根目录都是命令启动时的当前目录；每个匹配项建立独立目标目录。
- 裸 `*` 被 Shell 展开成多个参数后仍会统一扫描：过滤 `.sha256` 等非归档文件和 `part2`、`.7z.002`、`.zip.002`、`.r00`、`.z01` 等后续卷，只把 `part1.exe`、`part1.rar`、`.7z.001`、`.zip.001` 或普通单包作为任务入口。
- `-r`/`--recursive`（PowerShell 也支持 `-Recursive`）递归发现输入目录中的全部归档首卷，并继续展开解压结果中的内层归档；同名源目录存在时安全输出为 `*-unpacked`，不覆盖源目录。
- 不删除源包，不覆盖已有目标。修复残缺输出前必须精确确认待删除目录。
- 三平台命令语义一致：`run` 前台运行并持续显示阶段，`start` 提交后台任务并立即返回任务号；`status`、`wait`、`log` 查看状态、等待结果和读取持久日志。Linux 无子命令调用仅保留为旧版后台兼容入口，新脚本和文档必须显式使用 `run` 或 `start`。
- Windows/macOS 的 `start` 后台进程必须使用非交互模式并完全断开父终端的标准输入、输出和错误；后台进度只写任务日志，禁止向当前终端泄漏 ANSI/光标查询序列。
- Windows/macOS 调用 7-Zip、UnRAR 等外部工具时必须持续刷新耗时；长任务每30秒写入运行心跳，不能因同步等待而表现为无响应。
- Windows 使用 PowerShell 5.1+；macOS 使用 PowerShell 7+；Linux 使用 Bash 4+。
- CLI 安装和解压运行时不依赖 Python：Windows 使用根目录 `install.bat`，Linux 使用 `install-linux.sh`，macOS 使用 `install-macos.sh`。Agent Skill 安装是另一条链路：Linux/macOS 的 `scripts/install_local.py`/`install_local.sh` 与 Python 审计需要 Python 3；Windows 使用纯 PowerShell 的 `scripts/install_local.ps1`；手工复制 Skill 不需要 Python。
- 每个归档按可用能力有限重试：优先 7-Zip，RAR 可回退 UnRAR，TAR/TAR.GZ 回退系统 tar，独立 GZ 回退系统或 .NET GZip，ZIP 在 PowerShell 端回退系统 ZIP。每次失败先清理该次残留；所有适用工具都失败后保留原包、记录日志并继续下一个包，不无限循环盲试。`-StopOnError` 仅用于用户明确要求严格停止的场景。

## 工作流

1. 确认平台、输入、输出和是否允许实际写盘；远程主机不明确时询问。
2. 运行平台预检：Linux `scripts/preflight.sh`，Windows `scripts/preflight-windows.ps1`，macOS `scripts/preflight-macos.sh`。
3. 用 `unpack-flow list '<输入>'` 确认匹配项，再用 `unpack-flow plan '<输入>'` 检查首卷与内容结构。
4. 前台执行使用 `unpack-flow run '<输入>' -Output '<输出>'`；后台执行使用 `unpack-flow start '<输入>' -Output '<输出>'`，再用 `status`、`wait`、`log` 跟踪任务。Linux 也可使用 `-o <输出>`。
5. 核对退出码、目标目录、文件数量和代表性文件；修复后重跑失败场景与相邻主路径。

原生 Linux/Windows 验收默认使用匿名合成夹具目录 `/data/unpack-flow-testcases`，也可通过 `UNPACK_FLOW_TEST_ROOT` 显式指定隔离目录。日常回归使用 `unpack-flow-minimal-testcases-v1.zip` 及其 SHA-256，通过 `tests/run-native-linux-minimal.sh` 执行；大型套件只在性能或小套件未覆盖的格式兼容性验收中运行。

## 常用命令

```bash
unpack-flow list '/data/archives/*'
unpack-flow help
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run -r -o /data/extracted '/data/archives/*'
unpack-flow start -o /data/extracted '/data/archives/*'
unpack-flow status
unpack-flow wait
unpack-flow log
```

Windows/macOS PowerShell：

```powershell
unpack-flow list 'D:\Downloads\Archive*'
unpack-flow help
unpack-flow plan 'D:\Downloads\Archive.part1.rar'
unpack-flow run 'D:\Downloads\Archive*' -r -Output 'E:\Extracted'
unpack-flow start 'D:\Downloads\Archive*' -Output 'E:\Extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

安装、部署、依赖策略和故障处理见 [references/deployment.md](references/deployment.md)。通用备份、数据集、日志包、软件分发与游戏分卷等学习示例见 [README.md](README.md)；游戏示例只是能力示范，不限制产品定位。

公开文档、测试夹具和日志示例必须使用匿名合成数据；创建或更新这些内容前读取 [公开贡献与测试数据规则](CONTRIBUTING.md)，并运行 `scripts/check-anonymization.sh`。

发布者与官网：[once-email.com](https://once-email.com)。创建者：helen.jar；GitHub 项目：[pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)；支持邮箱：[tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)。统一公开身份字段见 [PUBLISHER.md](PUBLISHER.md)。
