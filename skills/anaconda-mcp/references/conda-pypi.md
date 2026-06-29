# conda-pypi Evaluation Guide

Last verified: 2026-06-25.

## Recommendation

`conda-pypi` is preferable to ad hoc `pip install` for the subset it supports:
conda performs the solve, owns the transaction, records installed files, includes
packages in `conda list` and `conda export`, and removes them with `conda remove`.

Do not make it an automatic fallback or treat it as an approved conda channel.
`conda-pypi` and its Rattler wheel channel are opt-in beta features that their
maintainers do not recommend for production.

Use this order:

1. Search organization-approved conda channels.
2. Prefer building, reviewing, and retaining a real package in an approved
   internal conda channel.
3. For disposable development or evaluation, offer `conda-pypi` when the user or
   organization explicitly approves public PyPI as a package source.
4. Use direct `pip` only when the package form is unsupported by `conda-pypi`,
   internal packaging is unavailable, and the user accepts an isolated
   mixed-manager environment.

## Trust Boundary

The public `conda-pypi` channel is hosted by Anaconda, but it hosts metadata
only. Wheel artifacts come directly from PyPI, are not independently vetted or
scanned, and have the same security posture as public PyPI.

Enabling it expands the supply chain beyond existing conda channels, including
typosquatting, compromised-publisher, dependency-confusion, licensing,
artifact-deletion, and malicious-package risks. Anaconda-hosted metadata does not
make the underlying package approved.

Pin an exact stable version, verify the project and publisher, inspect the solve
plan and selected source, and run project tests after installation.

## Supported Fit

Recommend the public wheel channel only when all are true:

- The environment is non-production and disposable or readily recreated.
- Host conda is version 26.5 or newer.
- The user approves the beta Rattler solver and public `conda-pypi` channel.
- The project publishes a compatible pure-Python wheel, normally ending in
  `-none-any.whl`.
- Package and dependency names have been verified.
- An exact stable version and complete solve are reviewed.

Do not recommend it for:

- Production, mission-critical, security-restricted, or regulated environments.
- Compiled wheels, native extensions, CUDA stacks, or sdist-only projects.
- Workflows requiring dependable cross-platform lockfile round trips or rollback.
- Channel policies that have not approved public PyPI.
- Valuable shared environments where a beta regression is expensive.

Continue sourcing compiled dependencies such as NumPy, SciPy, PyTorch, CUDA, and
system libraries from approved conda channels.

## Installation And Configuration

`conda-pypi` is a conda plugin installed in the conda installation's `base`
environment, not the target project environment:

```bash
conda install --name base "conda>=26.5"
conda install --name base conda-pypi
```

Upgrading `base` is consequential. Inspect the transaction and use the channel
ecosystem already responsible for that installation; do not casually mix
`defaults` and `conda-forge` in `base`.

The official beta setup changes persistent conda configuration:

```bash
conda config --set solver rattler
conda config --append channels conda-pypi
conda config --set channel_priority flexible
```

Do not run those commands automatically. Explain their effect, inspect current
configuration, and obtain explicit approval for the intended scope:

```bash
conda config --show-sources
conda config --show solver channels channel_priority
```

Record prior values. Remove the added channel when evaluation ends:

```bash
conda config --remove channels conda-pypi
```

If `solver` had no prior explicit value, remove the override with
`conda config --remove-key solver`. Otherwise restore the recorded solver with
`conda config --set solver <previous-solver>`. Restore the user's previous
channel-priority value in the same way rather than assuming one.

## Safer Evaluation Workflow

Create a new environment and preview an exact request:

```bash
conda create --name pypi-eval python=3.12
conda install --name pypi-eval --dry-run "<package>==<exact-version>"
```

During beta, `conda search` may fail for the wheel channel even when installation
works. Inspect the plan from `conda install --dry-run` or
`conda create --dry-run` instead.

Before the real transaction, verify:

- The package is the intended PyPI project and exact stable version.
- The artifact is a pure-Python wheel.
- Existing dependencies remain on approved conda channels where expected.
- No unexpected prerelease, replacement, channel switch, downgrade, or unrelated
  update appears.

Then install and validate:

```bash
conda install --name pypi-eval "<package>==<exact-version>"
conda list --name pypi-eval --show-channel-urls
conda run --name pypi-eval python -c "import <module>; print(<module>.__file__)"
```

Run the smallest relevant project tests. For long-term reproduction, retain the
exact wheel or mirror it internally because public artifacts can disappear.

## Use Alongside Anaconda MCP

Do not route `conda-pypi` operations through Anaconda MCP at the reviewed
versions. The dedicated Anaconda MCP environment can bundle an older conda than
the 26.5+ release required by `conda-pypi`, and it does not inherit a plugin
installed only in the host `base` environment. A global `solver: rattler` setting
can also break MCP operations when that runtime lacks the Rattler plugin.

Keep these workflows separate:

1. Use Anaconda MCP for supported environment inventory and ordinary conda
   operations that its bundled runtime can solve.
2. Configure and approve `conda-pypi` in the host conda installation outside the
   Anaconda MCP environment.
3. Create the fresh evaluation environment and perform both dry-run and install
   directly with that host conda executable.
4. Verify the exact environment with
   `conda list --name <env> --show-channel-urls` or
   `conda list --prefix <absolute-prefix> --show-channel-urls`.
5. Run import checks and project tests.

Before changing the global solver, verify that Anaconda MCP still lists
environments successfully. If it fails, restore the prior solver configuration
and keep `conda-pypi` evaluation in a separately configured conda installation.

## Advanced conda pypi install

The advanced conversion workflow is:

```bash
conda pypi install --prefix /absolute/path/to/pypi-eval --dry-run "<package>==<exact-version>"
conda pypi install --prefix /absolute/path/to/pypi-eval "<package>==<exact-version>"
```

It converts wheels into local `.conda` packages and prefers configured conda
channels for dependencies. Treat it as more experimental than the public channel
plus normal `conda install`.

Caveats:

- Dry-run can still download and convert artifacts into a local cache.
- Dependency marker and extras translation is incomplete.
- Source or editable conversion can execute build-backend code and install build
  requirements into the target prefix.
- Advanced conversion can mishandle compiled wheels as `noarch`; do not use it
  for native packages.
- Re-run with an exact version for upgrades; there is no
  `conda pypi update` command.

Do not use `--ignore-channels` by default because it bypasses conda-first
dependency sourcing.

## Why Not Direct pip

Direct `pip install` mutates a prefix outside conda's solver and transaction
model. Alternating conda and pip can overwrite files, hide dependency conflicts,
produce incomplete exports, and make later conda updates or removals unsafe.

`conda-pypi` reduces those risks for supported wheels but does not make public
PyPI trusted or remove beta limitations. If direct pip remains necessary, create
a fresh disposable environment, install all conda dependencies first, run pip
once with exact reviewed requirements, and do not continue mutating that
environment with conda.

## Official Sources

- Repository and beta status: https://github.com/conda/conda-pypi
- Quickstart: https://conda.github.io/conda-pypi/quickstart/
- Features and trust limits: https://conda.github.io/conda-pypi/features/
- Conda beta guide: https://docs.conda.io/projects/conda/en/stable/new-features.html#install-pypi-packages-with-conda-install
- Install command: https://conda.github.io/conda-pypi/reference/commands/install/
- Latest reviewed release: https://github.com/conda/conda-pypi/releases/tag/0.10.1
