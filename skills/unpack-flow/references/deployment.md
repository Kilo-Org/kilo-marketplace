# 部署与故障处理

## Python 是否必需

运行 `unpack-flow`、列出归档、生成计划和执行解压都不需要 Python。Python 3 只用于 Linux/macOS 的 Codex Skill 自动安装器 `scripts/install_local.py`（`scripts/install_local.sh` 是它的 Shell 入口）以及 Python 版基线审计。Windows 可使用纯 PowerShell 的 `scripts/install_local.ps1` 安装 Skill，不依赖 Python；三端手工复制 Skill 目录也不依赖 Python。

CLI 安装器与 Skill 安装器不是同一类工具。CLI 的公开入口按平台命名：Windows `install.bat`、Linux `install-linux.sh`、macOS `install-macos.sh`；它们分别调用 `scripts/install-cli-windows.ps1`、`scripts/install-cli-linux.sh`、`scripts/install-cli-macos.sh`。带下划线的 `scripts/install_local.py/.sh/.ps1` 只安装 Agent Skill，并保留拒绝覆盖与 `--replace` 备份语义。

## 本地安装和命令行使用

Linux 解压发布包后先检查，再安装到当前用户目录：

```bash
chmod +x install-linux.sh
./install-linux.sh --check
./install-linux.sh
export PATH="$HOME/.local/bin:$PATH"  # 仅当脚本输出 path_command 时
unpack-flow version
```

macOS 使用对应名称：

```bash
chmod +x install-macos.sh
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

Windows 发布 ZIP 内含免安装 7-Zip。完整解压后双击 `install.bat`，或在 CMD/PowerShell 中运行：

```bat
install.bat
# 如果提示 PATH 已更新，打开新 PowerShell 窗口
unpack-flow version
unpack-flow list "D:\Downloads\Archive*"
unpack-flow plan "D:\Downloads\Archive.part1.rar"
unpack-flow run "D:\Downloads\Archive*" -Output "E:\Extracted"
```

`install.bat` 在单次 PowerShell 子进程中调用 `scripts/install-cli-windows.ps1`，不会修改计算机或用户级执行策略。维护者仍可运行 `install.bat -Check` 只做安装前检查。

`--check`/`-Check` 只检测环境。缺少依赖时脚本输出 `install_command`，不自动执行。macOS 通常是 `brew install powershell sevenzip`；Debian/Ubuntu 通常是 `sudo apt-get update && sudo apt-get install -y bash p7zip-full unrar`；Fedora/RHEL 通常是 `sudo dnf install -y bash p7zip p7zip-plugins unrar`。

Codex Skill 自动安装：

```bash
# Linux/macOS，需要 Python 3
scripts/install_local.sh .
```

```powershell
# Windows，只需要 PowerShell
.\scripts\install_local.ps1 -Source .
```

## Skill 内置工具是默认首选

不要把“系统 PATH 没有 7-Zip/UnRAR”误判为“Skill 不能解压”。先从 Skill 根目录解析 `tools/`，检查 Windows x64/ARM64 的便携 7-Zip、Windows x64 的 UnRAR 和 macOS ARM64 的 UnRAR。内置工具可用时直接调用，不请求用户做系统安装。

## 平台选择

- Linux：`install-linux.sh` 安装 `scripts/unpack-flow`。`run` 前台持续显示进度，`start` 后台运行；无子命令调用仅保留旧版后台兼容。`status` 显示当前包、阶段、层数、耗时和 PID，`wait` 每两秒刷新直到结束。
- Windows：`install.bat` 调用 `scripts/install-cli-windows.ps1` 安装 `scripts/unpack-flow.ps1`。默认前台运行并显示进度，支持 PowerShell 5.1+ 和 PowerShell 7+。
- macOS：`install-macos.sh` 调用 `scripts/install-cli-macos.sh`，安装由 PowerShell 7 驱动的 `scripts/unpack-flow-macos`；先用 `--check` 或 `scripts/preflight-macos.sh` 检查依赖。
- WSL：按 Linux 使用，但 Windows 盘符通常挂载为 `/mnt/c`、`/mnt/d`；大量小文件写入 WSL 原生文件系统通常更稳定。

## 后台任务、状态与日志

三平台统一使用 `unpack-flow run <输入> -Output <输出>` 前台解压，使用 `unpack-flow start <输入> -Output <输出>` 提交后台任务。`start` 立即返回任务号；随后执行 `unpack-flow status [任务号]`、`unpack-flow log [任务号]`、`unpack-flow wait [任务号]`。省略任务号时操作最近任务。Windows 状态根目录默认为 `%LOCALAPPDATA%\unpack-flow\state`，macOS/Linux 默认为 `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow`，可用 `UNPACK_FLOW_STATE_ROOT` 覆盖。日志包含输入、输出、阶段、层数、耗时、完成路径和被跳过的失败归档。

解压引擎按格式和实际可用性有限重试：7-Zip 为通用首选；RAR 再尝试 UnRAR；TAR、TAR.GZ/TGZ 再尝试系统 `tar`；独立 `.gz` 再尝试系统 `gzip` 或 .NET GZip；PowerShell 的 ZIP 还会尝试系统 ZIP 能力。每次失败会清空本次临时输出再换引擎。全部适用引擎均失败时保留原归档、写入日志并继续后续包，不会无限重试。

## 脚本参数

```bash
scripts/preflight.sh [--host root@example-server] [--source /data/archives] [--output /data/extracted]
scripts/deploy.sh [--host root@example-server] [--source /data/archives] [--output /data/extracted]
scripts/deploy.sh --host root@example-server --install-deps
```

`deploy.sh` 安装主程序到 `/usr/local/bin/unpack-flow`。它是无扩展名的 Bash 文本文件，不是 ZIP 或 BIN。运行状态默认写入 `~/.local/state/unpack-flow`，可用 `UNPACK_FLOW_STATE_ROOT` 修改。

## 使用路径和输出目录

```bash
unpack-flow 'Archive*'                                # 当前目录下的名称/通配符
unpack-flow .                                         # 当前目录
unpack-flow './子目录/*'                              # 当前目录的相对通配符
unpack-flow '/mnt/incoming/Archive*.7z'                  # 绝对文件/通配符
unpack-flow -o /data/extracted2 '/mnt/incoming/Archive*'   # 指定输出根目录
cd /data/archives && unpack-flow -o /data/extracted 'Archive*' # 显式使用服务器整理目录
```

通配符应加引号。`-o/--output` 必须使用绝对路径；每个匹配项仍会建立独立目标目录。工具拒绝把 `/` 等系统目录作为输入，也拒绝把输出放进源项目内部。

## 依赖策略

- Bash 4+：脚本使用关联数组和 `mapfile`。
- 7-Zip：优先 `/opt/unpack-flow/tools/7zz` 或 `7z`，其次系统 PATH。
- UnRAR：优先 `UNPACK_FLOW_UNRAR`，其次 `/opt/unpack-flow/tools/unrar`，最后使用系统 PATH。
- GNU coreutils/findutils、procps、util-linux：提供路径解析、查找、进程和低优先级运行能力。
- 权限：输入可读，输出和 `UNPACK_FLOW_STATE_ROOT` 可写；输出磁盘空间足够。
- 密码包（可选）：通过 `UNPACK_FLOW_PASSWORDS_FILE` 指定 UTF-8 文本，每行一个候选密码；仓库不内置第三方密码。
- `--install-deps` 只在明确授权后使用。支持 apt、dnf、yum、zypper、pacman 的常见包名；安装失败后停止并报告，不反复重试。

## 绿色部署

主脚本本身是绿色单文件。若已有合法取得的静态 `7zz`、`unrar`，可放入目标机：

```text
/opt/unpack-flow/tools/7zz
/opt/unpack-flow/tools/unrar
```

权限设为 `755`。仓库只内置来自官方发布、具有再分发授权并保留许可证的便携二进制；新增或升级二进制时必须核对来源、架构、哈希和许可。

## Windows 环境

Windows 发布 ZIP 自带 `tools/windows-x64/7za.exe` 和 `tools/windows-arm64/7za.exe`，脚本按系统架构自动选择，无需安装 7-Zip。x64 包还自带官方命令行版 `tools/windows-x64/UnRAR.exe`，在 7-Zip 无法读取某些 RAR/SFX 方法时自动回退。7-Zip 授权文件位于 `tools/7zip-License.txt`，UnRAR 授权文件位于 `tools/windows-x64/UnRAR-License.txt`。解压发布 ZIP 后直接运行：

```powershell
.\scripts\unpack-flow.ps1 help
.\scripts\unpack-flow.ps1 run 'D:\Downloads\Archive*' -Output 'E:\Extracted'
```

若 7-Zip 不在 PATH，设置：

```powershell
$env:UNPACK_FLOW_7Z = 'C:\Program Files\7-Zip\7z.exe'
```

PowerShell 执行策略阻止本地脚本时，可仅对当前进程使用 `Set-ExecutionPolicy -Scope Process Bypass`；不要永久降低整机策略。

## macOS 环境

```bash
brew install powershell sevenzip
scripts/preflight-macos.sh
./install-macos.sh
unpack-flow run "$HOME/Downloads/Archive*" -Output "$HOME/Extracted"
```

macOS 复用 PowerShell 7 核心程序，确保 Windows 与 macOS 的首卷识别、嵌套展开和安全规则一致。安装脚本只复制本项目脚本，不会自动安装 Homebrew 或依赖。

## Wine 与虚拟 Windows

按以下顺序处理 Windows 自解压 EXE：

1. 先由 7-Zip 或 UnRAR 当作普通归档读取，绝大多数情况不需要 Windows。
2. 普通工具无法读取时，优先把包交给 Windows 版脚本或隔离 Windows 虚拟机。
3. Wine 只在用户明确批准执行该 EXE 后考虑。Wine 是兼容层，不是安全沙箱；不得自动安装、自动执行或用它绕过 DRM。

Linux 可以安装 Windows 虚拟机，但仅为解压通常成本过高，需要 Windows 授权、CPU 虚拟化、额外磁盘和图形/远程访问配置，因此不作为默认依赖。

## 安全停止条件

- 平台不是 Linux/Windows/macOS，或所选平台运行环境不足（Linux 需要 Bash 4+；Windows 需要 PowerShell 5.1+；macOS 需要 PowerShell 7+）。
- 源目录不存在、输出目录不可创建，或目标磁盘空间明显不足。
- 绝对路径允许位于默认源目录之外，但拒绝 `/` 等系统根目录和源内嵌输出。
- 目标目录已存在：跳过，不覆盖。
- 权限、SSH 或依赖安装被拒绝：停止并请用户处理。
- 包可能涉及 DRM 绕过：只做普通归档整理，不提供破解或绕过步骤。
