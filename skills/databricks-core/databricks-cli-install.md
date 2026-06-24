# Databricks CLI Installation

Install or update the Databricks CLI on macOS, Windows, or Linux using verified package-manager or versioned release artifacts. Includes checksum verification, user-directory installation for non-sudo environments, and common failure recovery.

## Sandboxed / IDE environments (Cursor, containers)

CLI install commands often write to system directories outside the workspace (e.g. `/opt/homebrew/`, `/usr/local/bin/`) which are blocked in sandboxed environments.

**Agent behavior**: Do not attempt to run install commands directly. Present the appropriate command to the user and ask them to run it in their own terminal. After they confirm, verify with `databricks -v`.

For Linux/macOS containers or Cursor: prefer the **Linux manual install to user directory** method (`~/.local/bin`) — it requires no sudo and no writes outside the workspace.

## Preconditions (always do first)
1. Determine OS and shell:
   - macOS/Linux: bash/zsh
   - Windows: Command Prompt / PowerShell; optionally WSL for Linux shell
2. Detect whether `databricks` is already installed:
   - Run: `databricks -v` (or `databricks version`)
   - If already installed with a recent version, installation is already OK.
3. Avoid the legacy Python package `databricks-cli` (PyPI). This skill installs the modern Databricks CLI binary.

## Preferred installation paths (by OS)

### macOS (preferred: Homebrew)
Run:
- `brew tap databricks/tap`
- `brew install databricks`

Verify:
- `databricks -v` (or `databricks version`)

If macOS blocks the binary (Gatekeeper), follow Apple’s “open app from unidentified developer” flow.

#### macOS fallback: verified release artifact

Download the versioned macOS archive from the [official releases](https://github.com/databricks/cli/releases), verify its published checksum before extraction, inspect the archive contents, and obtain explicit user approval before placing the binary on `PATH`. Prefer a user-owned directory such as `~/.local/bin`; do not run remote installer responses directly in a shell.

Verify:
- `databricks -v`

### Linux (preferred: Homebrew if available)
Run:
- `brew tap databricks/tap`
- `brew install databricks`

Verify:
- `databricks -v`

#### Linux fallback: verified release artifact

Use the manual user-directory installation below. Select an explicit version from the [official releases](https://github.com/databricks/cli/releases), verify its published checksum, inspect the archive contents, and obtain explicit user approval before installing the binary. Never pipe a remote response directly into a shell.

Verify:
- `databricks -v`

#### Linux alternative: Manual install to user directory (when sudo unavailable)
Use this when sudo is not available or requires interactive password entry.

Steps:
1. Detect architecture with `uname -m` (`x86_64` maps to `amd64`; `aarch64` maps to `arm64`).
2. Select an explicit version from the [official releases](https://github.com/databricks/cli/releases). Do not resolve an unreviewed moving `latest` URL.
3. Download the matching archive and its published checksum/signature to a temporary directory. Verify it before extraction; if the release provides no verifiable integrity metadata, use Homebrew instead.
4. Inspect the archive, then install after explicit approval:
   ```bash
   sha256sum -c databricks.sha256
   tar -tzf "databricks_cli_<version>_linux_<arch>.tar.gz"
   mkdir -p "$HOME/.local/bin"
   tar -xzf "databricks_cli_<version>_linux_<arch>.tar.gz" -C "$HOME/.local/bin" databricks
   chmod 0755 "$HOME/.local/bin/databricks"
   ```
5. Add to PATH (add to `~/.bashrc` or `~/.zshrc` for persistence):
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
6. Verify:
   - `databricks -v`

Notes:
- The download files are `.tar.gz` archives (not `.zip`) with naming pattern: `databricks_cli_<version>_linux_<arch>.tar.gz`
- Common architectures: `amd64` (x86_64), `arm64` (aarch64)
- This method works in containerized environments and sandboxed IDEs (e.g. Cursor) without sudo access

### Windows (preferred: WinGet)
Run in Command Prompt (then restart the terminal session):
- `winget search databricks`
- `winget install Databricks.DatabricksCLI`

Verify:
- `databricks -v`

#### Windows alternative: Chocolatey (Experimental)
Run:
- `choco install databricks-cli`

Verify:
- `databricks -v`

#### Windows fallback: verified release artifact

Download an explicit Windows release archive from the [official releases](https://github.com/databricks/cli/releases), verify its published checksum in PowerShell, inspect the archive, and obtain explicit approval before extracting the binary to a user-owned directory on `PATH`. Do not execute downloaded installer scripts or run unverified artifacts as Administrator.

Verify in the same environment:
- `databricks -v`

## Manual install (all OSes): download from GitHub releases
Use this when package managers or curl install are not possible.

Steps:
1. Get the latest release download URL:
   - Visit https://github.com/databricks/cli/releases/latest
   - OR use GitHub API: `curl -s https://api.github.com/repos/databricks/cli/releases/latest | grep browser_download_url`
2. Download the appropriate file for your OS and architecture:
   - Linux: `databricks_cli_<version>_linux_<arch>.tar.gz` (use tar -xzf)
   - macOS: `databricks_cli_<version>_darwin_<arch>.zip` (use unzip)
   - Windows: `databricks_cli_<version>_windows_<arch>.zip` (use native extraction)
   - Common architectures: `amd64` (x86_64), `arm64` (aarch64/Apple Silicon)
3. Extract the archive.
4. Ensure the extracted `databricks` executable is on PATH, or run it from its folder.
5. Verify with `databricks -v`.

## Update / repair procedures

### Homebrew update (macOS/Linux)
- `brew upgrade databricks`
- `databricks -v`

### WinGet update (Windows)
- `winget upgrade Databricks.DatabricksCLI`
- `databricks -v`

### Manual release update (all OSes)
1. Resolve the currently installed binary with `which databricks` or `where databricks`; do not delete anything until the replacement is verified.
2. Select an explicit newer version from the official release page, download the matching artifact, and verify its published checksum/signature.
3. Inspect and extract the replacement to a temporary location, run `<temporary-path>/databricks -v`, then obtain explicit approval before atomically replacing the existing binary.
4. Verify the binary resolved from `PATH` with `databricks -v`; retain the prior binary until verification succeeds.

## Common failures & fixes (agent playbook)
- `Target path <path> already exists`:
  - Verify the new binary in a temporary location, obtain explicit replacement approval, then rename the existing binary to a backup before installing the new one.
- Permission error writing `/usr/local/bin`:
  - Use the manual install to `~/.local/bin` instead of elevating an installer.
- `sudo: a terminal is required to read the password`:
  - Cannot use sudo in non-interactive environments (containers, CI/CD).
  - Use manual install to `~/.local/bin` method instead (see "Linux alternative" section).
- Windows PATH not updated after WinGet:
  - Restart Command Prompt/PowerShell.
- Multiple `databricks` binaries on PATH:
  - Use `which databricks` (macOS/Linux/WSL) or `where databricks` (Windows) and remove the wrong one.
- Wrong file type (trying to unzip a tar.gz):
  - Linux releases are `.tar.gz` files, use `tar -xzf` not `unzip`.
  - macOS and Windows releases are `.zip` files, use appropriate extraction tool.
- `databricks: command not found` after installation to `~/.local/bin`:
  - Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`
  - For persistence, add the export command to `~/.bashrc` or `~/.zshrc`.
