<p align="center">
  <a href="https://once-email.com"><img src="assets/unpack-flow-banner.png" alt="UnpackFlow by Once Email — Extract nested archives safely" width="100%"></a>
</p>

# UnpackFlow

<p align="center"><strong>Cross-platform extraction for nested, multipart and self-extracting archives.</strong></p>

<p align="center">
  <a href="https://github.com/pangxin12345/unpack-flow/releases"><img alt="Version 2.1.4" src="https://img.shields.io/badge/version-2.1.4-635bff"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-22a06b"></a>
  <img alt="Linux, Windows and macOS" src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-1684ff">
  <a href="https://once-email.com"><img alt="Published by Once Email" src="https://img.shields.io/badge/by-Once%20Email-0aa7a7"></a>
  <a href="mailto:tiantuowl@gmail.com"><img alt="Email support at tiantuowl@gmail.com" src="https://img.shields.io/badge/support-tiantuowl%40gmail.com-ea4335"></a>
</p>

UnpackFlow is an intelligent archive extraction orchestrator for Linux, Windows and macOS. It finds the correct first volume, extracts nested layers in sequence, handles batches, reports progress, and never executes unknown self-extracting files.

[English](README.md) · [简体中文](docs/README.zh-CN.md) · [Español](docs/README.es.md) · [हिन्दी](docs/README.hi.md) · [العربية](docs/README.ar.md) · [Português](docs/README.pt-BR.md) · [Français](docs/README.fr.md) · [Deutsch](docs/README.de.md) · [日本語](docs/README.ja.md) · [Русский](docs/README.ru.md)

## Quick start

Preview what will be selected, inspect the first volume, then extract:

```bash
unpack-flow list '/path/to/archives/*'
unpack-flow plan '/path/to/archives/backup.part1.rar'
unpack-flow run '/path/to/archives/*' -Output '/path/to/extracted'
```

For a persistent background job:

```bash
unpack-flow start '/path/to/archives/*' -Output '/path/to/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

| Need | Command | Result |
|---|---|---|
| See what will be processed | `list` | Filters unrelated files and later volumes |
| Inspect one archive | `plan` | Shows format, entry volume and contents |
| Watch extraction live | `run` | Stays in the current terminal |
| Keep extracting in the background | `start` | Returns a job ID immediately |
| Follow a background job | `status`, `log`, `wait` | Shows progress, diagnostics and the final result |

## What UnpackFlow solves

- Batch extraction of files, directories and quoted wildcard patterns.
- Safe automatic scanning for quoted or shell-expanded `*`: checksum files, unrelated files and later multipart volumes are excluded before work begins.
- Explicit recursive mode with `-r`: discover every archive below input folders, unpack nested layers, and use a safe `*-unpacked` destination when a source folder has the same name.
- Nested archives up to ten inner layers by default; failed inner archives are preserved and skipped while remaining work continues.
- Multipart RAR archives and common RAR self-extracting archives without executing the EXE.
- RAR, 7z, ZIP, ISO and WIM inputs supported by the selected extraction engine.
- Background jobs with status, elapsed time and persistent logs on Linux, Windows and macOS.
- Terminal-safe background execution on macOS and Windows: `start` detaches all interactive streams, so progress cannot inject ANSI cursor replies or terminal beeps into the prompt.
- Live monitoring for long 7-Zip and UnRAR operations: elapsed time refreshes every second and logs receive a running heartbeat every 30 seconds.
- Native PowerShell 5.1+ operation on Windows and PowerShell 7+ operation on macOS.
- Automatic fallback from 7-Zip to bundled UnRAR where supported.
- Native TAR, TAR.GZ/TGZ and standalone GZ fallback when 7-Zip cannot extract them; PowerShell also falls back to native ZIP support.

Typical uses include software distributions, datasets, backups, media assets, log bundles, disk images and large downloaded archives.

## Supported inputs at a glance

| Input | Handling |
|---|---|
| RAR and multipart RAR | Finds the first volume; can fall back from 7-Zip to bundled UnRAR |
| Common RAR SFX (`part01.exe`) | Reads archive data without executing the EXE |
| 7z and multipart 7z | Selects `.7z.001` as the entry volume |
| ZIP and multipart ZIP | Selects the first volume; PowerShell has a native ZIP fallback |
| TAR, TAR.GZ/TGZ and GZ | Uses 7-Zip when available, then native archive tools |
| ISO and WIM | Extracted through the selected 7-Zip engine |

Actual format coverage depends on the extraction engines available for the current platform.

## Install the command-line tool

The public installer name identifies the target platform:

Linux:

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

macOS:

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

Windows—double-click `install.bat`, or run:

```bat
install.bat -Check
install.bat
unpack-flow version
```

These install the CLI, not the Agent Skill. The legacy scripts under `scripts/` remain compatibility entry points, but new documentation and release packages use the platform-named installers above.

## Learning demos

Start with `list`, inspect with `plan`, submit with `start`, then follow the job with `status`, `log` or `wait`.

For fast regression testing, run `bash tests/generate-minimal-public-suite.sh`. The approximately 218 KiB `unpack-flow-minimal-testcases-v1.zip` covers ZIP, TAR.GZ, nested archives, Unicode paths, contextual output names, a real `part01.exe` plus later RAR volumes, inert EXE payloads and an expected missing-volume failure. Verify it with `tests/test-minimal-public-suite.ps1` or `.sh`; no large application files are included and the SFX is never executed.

For native Linux acceptance, place the synthetic fixture and checksum under `/data/unpack-flow-testcases`, or set a different root with `UNPACK_FLOW_TEST_ROOT`. Run `bash tests/run-native-linux-minimal.sh` for routine acceptance. Large optional suites remain outside the default fixture path and run only for explicit performance or extra format-compatibility testing.

Use `run` when you want extraction to stay in the current terminal and show progress until completion. Use `start` when you want the command to return immediately and the job to continue in the background. These meanings are identical on Linux, Windows and macOS.

Run `unpack-flow help` for combined English and Simplified Chinese command help covering commands, options, paths, formats, requirements, environment variables and safety behavior.

### Nested dataset or backup

```bash
unpack-flow list '/path/to/archives/*'
unpack-flow plan '/path/to/archives/archive.part1.rar'
unpack-flow start '/path/to/archives/*' -Output '/path/to/extracted'
unpack-flow wait
```

### Multipart game backup example

Games are one example, not the product boundary. Keep all legally obtained volumes together, select the first volume, and never launch an unknown EXE:

```powershell
unpack-flow plan 'D:\Downloads\GameBackup\GameBackup.part01.rar'
unpack-flow start 'D:\Downloads\GameBackup\GameBackup.part01.rar' -Output 'D:\Extracted'
unpack-flow log
unpack-flow wait
```

### TAR.GZ logs or source package

```bash
unpack-flow start '/data/incoming/log-bundle.tar.gz' -Output '/data/extracted'
unpack-flow status
unpack-flow log
```

`install.bat` uses execution-policy bypass only for its own PowerShell child process; it does not modify the machine or user execution policy.

Quoting wildcard patterns remains recommended, but `unpack-flow run *` is also supported. Shell-expanded inputs are scanned as one batch: files such as `.sha256` are ignored, and only entry volumes such as `part1.exe`, `part1.rar`, `.7z.001` or `.zip.001` are scheduled. Later volumes such as `part2.rar` are supplied to the extraction engine but are never started as separate jobs. Existing destinations are skipped rather than overwritten.

Use `-r` (Linux: `--recursive`; Windows/macOS: `-Recursive`) when input folders may contain archives at deeper levels. Recursive mode discovers every supported first volume and still unfolds inner archives up to `-MaxInnerLayers` (default 10). If the natural output name already exists, UnpackFlow adds the archive's source-folder context: `sample-backup.part01.exe` inside `legacy-set` becomes `sample-backup-legacy-set-unpacked`; a same-named source folder remains `name-unpacked`, and further collisions receive `-2`, `-3`, and so on.

## Background extraction, status and logs

Use `start` for a persistent background task on Windows, macOS or Linux. It immediately returns a job ID. `status`, `log` and `wait` use that ID; omit it to inspect the latest job.

```text
unpack-flow start "D:\Downloads\Archive*" -Output "E:\Extracted"
unpack-flow status [job-id]
unpack-flow log [job-id]
unpack-flow wait [job-id]
```

Logs and job metadata are stored under `%LOCALAPPDATA%\unpack-flow\state` on Windows and `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` on macOS/Linux. Logs include the archive, phase, layer, elapsed time, destination and skipped failures. `run` is foreground and `start` is background on all three platforms. Linux retains invocation without a subcommand only as a legacy background-compatible shortcut.

For each archive, UnpackFlow tries only the applicable installed engines: 7-Zip first, then UnRAR for RAR, native `tar` for TAR/TAR.GZ, native GZip for standalone `.gz`, and native ZIP support on PowerShell. A failed attempt is cleaned before the next engine. If every applicable engine fails, the original archive is preserved, the failure is logged, and processing continues with the next archive. This is a bounded retry chain, not an endless retry loop.

## Platform requirements

| Platform | Runtime | Extraction engines |
|---|---|---|
| Linux x64 | Bash 4+ and GNU utilities | System or portable 7z/7zz plus bundled official UnRAR |
| Windows x64 | PowerShell 5.1+ | Bundled portable 7-Zip and UnRAR |
| Windows ARM64 | PowerShell 5.1+ | Bundled portable 7-Zip |
| macOS ARM64 | PowerShell 7+ and `7zz` | System 7-Zip plus bundled UnRAR fallback |

Installers report missing dependencies; they do not silently install system packages.

### Is Python required?

Python is not required to run `unpack-flow`, inspect archives, or extract files. Python 3 is required only when Linux or macOS users install the Codex Skill through `scripts/install_local.py` or its `scripts/install_local.sh` wrapper, and when maintainers run the Python-based baseline audit. Windows users can install the Skill with `scripts/install_local.ps1` using PowerShell only. Manual copying into the agent's Skills directory also requires no Python.

## Install as an Agent Skill

The folder name and Skill ID are both `unpack-flow`. Install it into the Skills directory used by your agent, then open a new session and invoke `$unpack-flow`.

```bash
# Automated Skill installation on Linux/macOS (requires Python 3)
scripts/install_local.sh .

# Or install manually without Python
cp -R unpack-flow ~/.codex/skills/unpack-flow
```

Windows Skill installation does not require Python:

```powershell
.\scripts\install_local.ps1 -Source .
```

The repository follows the Agent Skills directory format. Compatibility with a format or client does not imply marketplace publication.

## Safety and data handling

UnpackFlow keeps source archives, refuses system roots as extraction inputs or outputs, skips existing destinations, and never executes unknown EXE files. It does not bypass DRM, passwords or access controls. Verify available disk space before large jobs.

The Windows x64/ARM64 packages contain the portable full 7-Zip 26.02 engine plus the complete 7-Zip Extra artifacts; Windows x64 also includes official UnRAR command-line freeware. Linux x64 and macOS ARM64 releases include the official UnRAR binary, original package and license. Original 7-Zip installers, the Extra package and licenses are retained in source. UnRAR is used only as the bounded RAR fallback documented above.

## Build and verify releases

```bash
scripts/check-docs.sh
scripts/build-release.sh
scripts/export-public-source.sh /tmp/unpack-flow-public/unpack-flow
```

The build creates Linux `.tar.gz`, macOS `.tar.gz`, Windows `.zip`, and `SHA256SUMS` under `dist/`. The export command includes tracked project files by default, excludes the fixed private/build paths, and rejects internal acceptance or distribution records. Platform packages still copy only the runtime files required by that platform. See [deployment details](references/deployment.md), [contributing and synthetic-fixture rules](CONTRIBUTING.md), [security policy](SECURITY.md), [support](SUPPORT.md), and the [canonical project identity](PUBLISHER.md).

## Project and support

- Official website: [once-email.com](https://once-email.com)
- Creator and developer: helen.jar
- GitHub project: [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)
- Support email: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

For questions, email [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com) or [open a GitHub issue](https://github.com/pangxin12345/unpack-flow/issues).

MIT License. Version 2.1.4.
