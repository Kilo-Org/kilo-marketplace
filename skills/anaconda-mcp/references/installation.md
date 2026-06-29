# Anaconda MCP Installation Reference

Last verified: 2026-06-25.

Anaconda MCP changes quickly during public beta. Re-check official documentation,
package metadata, stable releases, and current legal terms before relying on a
version-specific detail.

## Product Identity

Install `anaconda-mcp`. Do not confuse it with:

- `anaconda-assistant-mcp`, an older conda plugin.
- `mcp`, the generic Model Context Protocol Python SDK.
- Anaconda Documentation MCP, a hosted read-only documentation service.
- `conda-meta-mcp`, a separate read-only conda metadata project.

## Prerequisites

- Miniconda, Anaconda Distribution, or another working conda installation with
  approved access to Anaconda's package channel.
- An MCP-capable client.
- An Anaconda account or API key.
- Acceptance of the current Anaconda MCP Beta Agreement.
- Network access for installation, authentication, and Anaconda-backed search.

The package metadata supported Python 3.10 through 3.13 at the review date. Check
live metadata instead of assuming those bounds remain unchanged.

## Preferred CLI Installation

Use a dedicated environment rather than `base`:

```bash
conda create --name anaconda-mcp -c anaconda anaconda-mcp
conda activate anaconda-mcp
```

The package currently comes from Anaconda's channel. The command applies the
channel to this transaction without persisting it in `.condarc`. On Miniforge or
another conda-forge-based installation, proceed only when organization policy
and applicable Anaconda terms permit access to that channel.

Confirm what was installed and capture the interpreter path:

```bash
conda list --name anaconda-mcp anaconda-mcp
conda run --name anaconda-mcp python -c "import anaconda_mcp, sys; print(sys.executable)"
```

A dedicated environment reduces dependency conflicts and gives the client a
stable executable. Installing into an existing environment with
`conda install -c anaconda anaconda-mcp` is supported but not preferred. Do not install a
release candidate by default.

## Authentication

Interactive OAuth is preferred:

```bash
anaconda login
```

It opens a browser and stores the resulting credential in the system keyring.
For an authorized headless setup, Anaconda also supports a process environment
variable. On macOS or Linux:

```bash
export ANACONDA_AUTH_API_KEY="<api-key>"
```

In PowerShell:

```powershell
$env:ANACONDA_AUTH_API_KEY = "<api-key>"
```

Keep the key in a secret manager or process environment. Do not commit it in
`kilo.json`, `opencode.json`, `.mcp.json`, editor settings, shell scripts, or
environment specifications.

## Beta Terms

Show the user the current agreement and status before acceptance:

```bash
anaconda mcp terms
anaconda mcp terms status
```

`anaconda mcp terms accept` accepts and persists the agreement immediately; it
does not present a confirmation prompt. An agent must not run it for the user.
After reading the current agreement, the user must personally run:

```bash
anaconda mcp terms accept
```

The stable v1.1.2 README documented these headless variables for an already
authorized non-interactive process. On macOS or Linux:

```bash
export ANACONDA_MCP_ACCEPTED_TERMS=true
export ANACONDA_MCP_ACCEPTED_TERMS_VERSION=2026-05-27
```

In PowerShell:

```powershell
$env:ANACONDA_MCP_ACCEPTED_TERMS = "true"
$env:ANACONDA_MCP_ACCEPTED_TERMS_VERSION = "2026-05-27"
```

The terms version is time-sensitive. Verify it against current official sources
or the installed package rather than copying this historical value blindly.

## Client Setup

The interactive wizard is safest for supported non-Kilo clients because schemas
differ:

```bash
anaconda mcp setup
anaconda mcp setup --client <client>
```

Project scope is supported for `claude-code`, `cursor`, `vscode`, and
`opencode`:

```bash
anaconda mcp setup --client opencode --scope project
```

Inspect and remove wizard-managed entries with the same scope used at setup:

```bash
anaconda mcp clients
anaconda mcp remove --client <client>
anaconda mcp remove --client <client> --scope project
```

The setup command uses local stdio, resolves the active environment's Python,
and normally backs up existing config. Avoid `--no-backup`; use `--force` only
after preserving and inspecting user-owned configuration.

## Kilo-Specific Setup

Kilo uses this local MCP shape:

```jsonc
{
  "mcp": {
    "anaconda-mcp": {
      "type": "local",
      "command": [
        "/absolute/path/to/python",
        "-m",
        "anaconda_mcp",
        "serve"
      ],
      "environment": {},
      "enabled": true,
      "timeout": 600000
    }
  }
}
```

Use the interpreter printed by:

```bash
conda run --name anaconda-mcp python -c "import sys; print(sys.executable)"
```

The ten-minute timeout accommodates dependency solves and environment creation.
If a request times out, inspect the exact environment before retrying because the
conda process may have continued. On Windows, use forward slashes in JSON or
escape every backslash. Configuration choices are:

- Project Kilo config: merge into `kilo.json` or `kilo.jsonc`.
- Global Kilo config: merge into `~/.config/kilo/kilo.json` or `.jsonc`.
- Project compatibility config: run the OpenCode wizard from the project root,
  then separately add the `600000` server timeout to the generated
  `opencode.json`. Configure Kilo permissions separately if the user wants a
  custom policy.

Do not use the vendor's global OpenCode path as Kilo global configuration. It
writes `~/.config/opencode/opencode.json`, while Kilo's global root is
`~/.config/kilo/`.

## Anaconda Desktop

In Anaconda Desktop's beta MCP view, enabling a supported client creates an
`anaconda-mcp` environment, installs the package, and updates the selected client
configuration. Restart the client afterward.

Use Desktop when the user wants GUI-managed setup. Prefer the dedicated CLI
environment and explicit Kilo stanza for team configuration or Kilo global use.

## Experimental ana CLI

The `ana` CLI offers a managed runtime, but its installer defaults to a mutable
`latest` release, modifies shell profiles, and runs `ana bootstrap`. Do not pipe
the remote installer directly into a shell.

If the user explicitly requests this experimental path:

1. Open https://github.com/anaconda/anaconda-cli/releases and choose an exact
   stable version.
2. Use the current official installer for the platform: `install.sh` on macOS or
   Linux, or `install.ps1` on Windows.
3. Download the installer to a temporary file rather than piping it to a shell.
4. Inspect the complete script and verify the selected release checksums.
5. Run the local installer with the pinned version. On macOS or Linux, use
   `--no-path-update` and `--no-bootstrap` unless the user explicitly wants those
   side effects; use equivalent documented options on Windows when available.
6. Run `ana mcp serve` only after authentication and terms acceptance are ready.

Conda remains necessary for users who need to inspect or activate environments
outside MCP. Prefer a client's verified MCPB registry UI over an arbitrary bundle.

## Docker

The repository's Docker route is for development and disposable testing, not the
preferred desktop integration:

- Container-local conda environments disappear unless storage is designed.
- Host conda environments are not automatically container environments.
- Published beta documentation has had port inconsistencies.

## Platform Caveat

On 2026-06-25, current Anaconda channel builds existed for Linux x86-64/aarch64,
Apple Silicon macOS, and Windows x86-64, but not Intel macOS. If installation
fails with `PackagesNotFoundError`, inspect the live package API and conda subdir
before changing channels or substituting another product:

```bash
conda info
conda config --show subdir
```

## Official Sources

- Product guide: https://www.anaconda.com/docs/tools/anaconda-mcp-server
- CLI guide: https://www.anaconda.com/docs/cli-reference/anaconda-mcp/getting-started
- Announcement and examples: https://www.anaconda.com/blog/anaconda-mcp
- Stable v1.1.2 README: https://github.com/anaconda/anaconda-mcp/blob/v1.1.2/README.md
- Releases: https://github.com/anaconda/anaconda-mcp/releases
- Package metadata: https://api.anaconda.org/package/anaconda/anaconda-mcp
- Beta agreement: https://www.anaconda.com/legal/terms/mcpbeta
- Official demo: https://github.com/Anaconda-Labs/anaconda-mcp-claude-desktop-demo
