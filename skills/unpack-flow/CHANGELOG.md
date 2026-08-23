# Changelog

## Unreleased

- Added private GitLab release gates for policy, security, one-time artifact freezing, manual GitHub publication, remote read-back and evidence aggregation without changing the tested runtime directory layout.
- Kept bundled platform executables and libraries in their existing runtime paths while excluding `.gitlab-ci.yml`, `.internal/` and the private public-export helper from public source and customer artifacts.
- Split CI dependencies by stage after the first real Runner rehearsal, keeping publication-only clients out of ordinary validation jobs.
- Added an explicit Alpine package mirror for the home Runner after live network checks showed the official CDN path was impractically slow; official images and package signature verification remain in place.
- Split Bash and PowerShell-on-Linux regression jobs, pinning the official Microsoft PowerShell image by digest so the existing background-isolation test runs in its required runtime instead of failing on a missing `pwsh` command.

## 2.1.2 — 2026-08-22

- Established [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow) as the canonical public GitHub project and synchronized the repository path across public identity and localized documentation.
- Separated private acceptance, distribution, execution-topology and VM records from the public UnpackFlow source; public source now includes tracked files by default while excluding fixed internal/build paths, and platform packages retain explicit runtime-file lists.
- Added a public test-data anonymization baseline, synthetic fixture vocabulary and blocking repository/release scans for private-looking identifiers, machine labels and paths.
- Published `tiantuowl@gmail.com` as the explicitly confirmed public support email for [once-email.com](https://once-email.com) and [pangxin12345](https://github.com/pangxin12345), then synchronized it across identity, support, security, distribution and Top 10 localized documentation.
- Added a permanent twelve-gate regression ledger covering wildcard input, multipart entry selection, recursive discovery, collision-safe output, long-running monitoring, background terminal isolation, failure continuation, clean installation, native macOS/Linux/Windows execution, and documentation/i18n/SEO.
- Made both Python and PowerShell project audits reject missing, unfinished or unevidenced regression gates.
- Fixed recursive output collisions for identical archive names in different source folders: source context now produces names such as `sample-backup-legacy-set-unpacked`, with deterministic numeric suffixes for further collisions.
- Added a roughly 218 KiB reproducible public regression suite with ZIP, TAR.GZ, nesting, Unicode, inert EXE payloads, real multipart RAR SFX volumes and an expected missing-volume failure.
- Standardized native Linux/Windows tests on the anonymous synthetic fixture root `/data/unpack-flow-testcases`; the compact suite is the default regression path and large suites are optional.

## 2.1.1 — 2026-08-22

- Fixed macOS terminal beeps and leaked cursor-position responses such as `5;35R` after `unpack-flow start`.
- Background PowerShell workers now run non-interactively, disable progress UI before startup, close standard input, redirect and drain standard output/error, and write ongoing activity only to the persistent job log.
- Added a deterministic terminal-isolation regression that waits for a real background extraction and rejects ANSI/control-sequence leakage.

## 2.1.0 — 2026-08-22

- Added `-r`/`--recursive` on Linux and `-r`/`-Recursive` on Windows/macOS to recursively discover every archive entry volume below input folders and continue extracting nested archives.
- Added collision-safe `*-unpacked` output when recursive input is inside a same-named source directory; source folders and archives remain untouched.
- Added missing Linux nested detection for multipart `part01.exe` and `.7z.001` entry volumes.
- Added PowerShell and Bash regression fixtures for recursive discovery and same-name output safety.

## 2.0.2 — 2026-08-22

- Fixed apparent hangs during large Windows/macOS extractions: external 7-Zip and UnRAR processes are monitored while running, elapsed time refreshes every second, and a persistent heartbeat is emitted every 30 seconds.
- Preserved extractor exit codes, password retries, cleanup and fallback behavior while adding live monitoring.
- Fixed the Linux `unpack-flow version` command so it matches the installer verification instruction and the Windows/macOS command contract; `--version` remains supported.

## 2.0.1 — 2026-08-22

- Fixed `unpack-flow run *` after shell expansion: non-archives such as checksum files and later multipart volumes are filtered before scheduling.
- Added first-volume normalization for `part1.exe`/`part1.rar`, `.7z.001`, `.zip.001`, classic `.rar`/`.r00` and `.zip`/`.z01` layouts on Linux, Windows and macOS.
- Fixed macOS upgrades when an older `~/.local/bin/unpack-flow` shadows `/usr/local/bin/unpack-flow`; the installer now updates the active known command directory and reports remaining PATH conflicts.
- Added cross-engine regression tests for shell-expanded wildcard input and multipart entry selection.
- Bundled official RARLAB UnRAR 7.23 with the Linux x64 release so nested modern multipart RAR behavior matches macOS and Windows; retained the original package and license.
- Added a Windows extended-length path cleanup fallback for nested Unicode archives under PowerShell 5.1.
- Restored the official `7za.dll` companion so the retained 7-Zip Extra artifacts are complete.
- Added portable full `7z.exe` and `7z.dll` from the official 7-Zip 26.02 x64 and ARM64 packages and made them the preferred Windows engine for ISO and extended formats.

## 2.0.0 — 2026-08-22

- Expanded `unpack-flow help` into consistent English/Chinese guidance for commands, options, paths, formats, requirements, environment variables and safety on all platforms.
- Unified command semantics across Linux, Windows and macOS: `run` is foreground with live progress, while `start` is background and returns a job ID immediately.
- Standardized public CLI installers as `install.bat`, `install-linux.sh` and `install-macos.sh`; retained separate Agent Skill installers with safe replace-and-backup behavior and restored Python/PowerShell baseline audits.
- Added general learning demos for nested backups, datasets, TAR.GZ logs and multipart game backups without narrowing the product to games.
- Added TAR/TAR.GZ and standalone GZ native fallbacks plus bounded multi-engine retries that continue with later archives after all applicable tools fail.
- Added persistent background jobs for Windows and macOS with `start`, `status`, `wait` and `log`, and unified the `start` command on Linux.
- Added one-step Windows installation through `install.bat` without changing the system or user execution policy.
- Fixed macOS CLI installation so the bundled UnRAR fallback is installed with the recursive extraction engine.
- Changed recursive extraction to continue past failed inner archives, report a final skipped-failure summary, support optional `-StopOnError`, and use a default limit of 10 inner layers.
- Added archive-signature detection for extensionless ZIP, RAR and 7z files found during recursive scans.
- Fixed recursive extraction of multiple sibling archives, nested multipart sets, and numbered split ZIP entry files such as `.zip.001`.
- Verified all 30 cases in `game-unpack-public-testcases-v1-v2.zip`: 28 successful extraction cases and 2 expected corrupt/missing-volume failures.
- Renamed the product, Skill ID, CLI, installation paths, state directories, environment variables and release artifacts to UnpackFlow.
- Removed application-specific executable detection and launch-file generation.
- Expanded discovery for TAR, compressed TAR, GZ, BZ2, XZ, CAB, ARJ, LZH, CHM, DEB, RPM, APK, CPIO, DMG, SWM and ESD archives.
- Added Windows x64 UnRAR fallback and fixed native Windows PowerShell 5.1 and installation-path failures.
- Reworked documentation for general archive extraction, Top 10 localization, search discoverability and clean public distribution.
- Clarified that Python is not an extraction dependency and is used only by the Linux/macOS automated Skill installer and Python audit.
- Added a canonical publisher identity baseline covering once-email.com, creator helen.jar and GitHub profile pangxin12345.

This is a breaking release: previous command names, environment variables and installation directories are intentionally unsupported.
