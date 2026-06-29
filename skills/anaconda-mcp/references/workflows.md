# Anaconda MCP Workflows And Troubleshooting

## Prompt Pattern

Give the assistant enough constraints to solve against the real conda ecosystem:

```text
Using the conda server, <operation> for environment <exact-name>.
Use Python <version> on <platform> and respect my configured channels.
First inspect the current environment and show the proposed top-level changes.
Do not modify unrelated packages or use pip without explaining why.
```

For read-only requests:

```text
Using the conda server, list my environments and summarize their Python version
and important top-level packages. Do not change anything.
```

Explicitly naming the conda server helps when a client exposes several package or
shell tools.

## Build An Environment From Source Files

Anaconda MCP cannot read local source files by itself. Use client file tools
first:

1. Read `environment.yml`, `pyproject.toml`, `requirements.txt`, notebooks, and
   Python imports when present.
2. Separate standard-library, local, optional, and third-party imports.
3. Ask Anaconda MCP to resolve third-party imports to conda package names and
   compatible versions.
4. Include platform, Python version, CUDA/runtime needs, and approved channels.
5. Show the proposed top-level specification before creation.
6. Create a fresh named environment through Anaconda MCP.
7. Run import checks or the smallest relevant project test.
8. Record a concise environment specification when the project expects one.

Common mappings include `cv2` to `opencv`, `sklearn` to `scikit-learn`, `PIL`
to `pillow`, and `skimage` to `scikit-image`. Verify them against the user's
configured channels rather than treating examples as authoritative.

## Dependency Conflict Workflow

1. Reproduce the solve in a fresh environment when practical.
2. Inspect exact Python, platform, channel order, pins, and virtual packages.
3. Search available builds before relaxing constraints.
4. Explain the smallest conflicting constraint set.
5. Offer explicit alternatives, such as another Python minor version, package
   version, or already-approved channel.
6. Apply only the alternative selected by the user.
7. Validate imports and behavior after solving.

Do not silently add `conda-forge` or `conda-pypi`, change solver or channel
priority, remove organization channels, or mix direct `pip` installs into the
environment. If approved channels cannot provide a package, follow
`conda-pypi.md` before considering direct pip.

## Environment Comparison

For two environments:

1. Inspect both through MCP.
2. Compare Python, platform-relevant builds, channels when available, and
   top-level requested packages.
3. Separate direct differences from transitive dependency noise.
4. Highlight behavior-changing differences such as major versions, BLAS/CUDA
   variants, compiler runtimes, and channel origin.
5. Do not mutate either environment unless requested.

## Safe Cleanup

Environment deletion requires a deliberate flow:

1. List environments and identify `base`, the active environment, and the
   environment running Anaconda MCP.
2. Present candidates with exact names or prefixes and available context; age or
   naming alone does not make an environment disposable.
3. Ask the user to select exact environments.
4. Write a full export to a verified file outside the target environment. Use the
   selector that matches the environment:

```bash
conda env export --name <env> > /safe/path/<env>-full.yml
conda env export --prefix /absolute/env/prefix > /safe/path/<env>-full.yml
```

5. Optionally write a separate `--from-history` export for a concise,
   human-maintained specification.
6. Verify the backup file is non-empty and does not contain credentials or an
   unwanted machine-specific `prefix:` before relying on it.
7. Delete only the exact selected environment through MCP.
8. Re-list environments and report the result and backup path.

Never delete `base`, the active environment, the MCP runtime environment, or an
environment inferred from a broad request such as "clean everything up."

## Reproducibility

Choose the artifact based on intent:

- `conda env export --from-history`: concise top-level intent.
- Full `conda env export`: detailed snapshot, but potentially platform-specific.
- Explicit lock tooling: appropriate when the project already uses it and exact
  reproduction is required.

Read an existing environment file before changing it, preserve project
conventions, and never include authentication credentials.

## Optional MCP Permissions In Kilo

Do not impose a permission policy when installing the server. Kilo users can
customize MCP permissions independently when they want approval prompts or
blocked operations.

MCP permission keys combine the sanitized server name and exposed tool name.
Anaconda MCP composes servers and can prefix or alias tools, so inspect the
actual names before writing rules. Kilo permission rules are order-sensitive;
place broad rules before later specific overrides.

## Troubleshooting

### Package unavailable during installation

- Confirm the package is `anaconda-mcp`, not `anaconda-assistant-mcp` or `mcp`.
- Inspect `conda info`, active channels, platform subdir, and Python support.
- Check the live Anaconda package API for a matching build.
- Current Intel macOS builds may be unavailable; do not substitute a different
  product under the same assumption.

### Tools do not appear

- Fully quit and restart the MCP client.
- In Kilo, start a new session and inspect `/mcps`.
- Verify the config file is one Kilo loads.
- Verify the command contains the dedicated environment's absolute Python path.
- Confirm the module invocation is `python -m anaconda_mcp serve`.
- Check client MCP logs before reinstalling.
- If a long create or install request timed out, inspect the exact environment
  before retrying; the underlying conda process may have continued.

### Authentication fails

Run from the dedicated environment:

```bash
anaconda login
```

For headless use, verify `ANACONDA_AUTH_API_KEY` reaches the MCP server process,
not only the interactive shell. Never print the key while debugging.

### Terms are rejected or stale

```bash
anaconda mcp terms status
```

Let the user accept the current agreement interactively. Verify the current
terms version before using headless acceptance variables.

### Client config points to a missing interpreter

Resolve the path again:

```bash
conda run --name anaconda-mcp python -c "import sys; print(sys.executable)"
```

Update only the command path. On Windows, JSON-escape backslashes or use forward
slashes, then restart the client.

### MCP and conda disagree about environments

```bash
conda env list
conda config --show envs_dirs
```

Check whether the MCP process uses another user, home, conda installation, or
container. GUI clients can inherit a different environment from terminals.

### Wrong tool handles the request

Say `Using the conda server` and name the exact environment. Inspect exposed tool
names rather than guessing when several servers offer similar capabilities.

### Source files cannot be read

This is expected. Use Kilo file tools or a separate filesystem MCP restricted to
the project. Exclude credentials and unrelated directories.

### Existing entry blocks setup

Inspect current config and generated backups:

```bash
anaconda mcp clients
```

Remove a vendor-managed stale entry with the same scope used to create it:

```bash
anaconda mcp remove --client <client>
anaconda mcp remove --client <client> --scope project
```

Run the project-scoped command from the project root. Do not use `--force` until
user-owned config is preserved.

## Security Checklist

- Keep the server local over stdio.
- Configure MCP tool permissions according to the user's own risk policy.
- Keep credentials out of project files and logs.
- Restrict companion filesystem access to the project.
- Do not send any personal data without Anaconda's written agreement.
- Do not use the beta in production or mission-critical environments.
- Independently validate package, security, policy, and forum-derived claims.
- Review changes and run project tests after every mutation.
