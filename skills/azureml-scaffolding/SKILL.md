---
name: "azureml-scaffolding"
description: "Scaffold, structure, and manage AI/ML projects that run on AzureML. Covers project initialization (uv workspaces, devcontainers, Makefile), Python packaging with explicit dependencies, local and cloud execution, experiment reproducibility, and extensibility patterns (pipelines, datasets, linting). Use this skill whenever the user asks to create, modify, run, test, or deploy an AzureML-based ML project — or when they need guidance on project layout, dependency management, or cloud job submission with Azure Machine Learning."
metadata:
  category: data
  source:
    repository: "https://github.com/bepuca/azureml-scaffolding"
    path: "azureml-scaffolding"
    license_path: "LICENSE"
---

# AzureML Project Scaffolding

A battle-tested structure for AI projects that require reproducible experimentation, leveraging
AzureML for cloud execution. It ensures reproducibility from day one without sacrificing the path to
production — and without breaking the ability to keep experimenting once you're there. Code,
environments, specs, and dependencies are wired so that what runs locally runs on [AzureML][aml],
with no surprises.

## Principles

These principles are foundational. Every decision about project structure, tooling, or workflow must
be evaluated against them.

- **Three layers** — Each layer depends only on inner layers:

  1. *Code — the what.* Pure Python, no platform deps.
  1. *Specification — the how.* job YAML. Declares how code executes on a target platform. Lives
     next to the code it describes.
  1. *Orchestration — the when.* Makefile, CI. Triggers execution. Knows about specs, knows nothing
     about code internals.

  **Litmus test** — If Python code imports or shells out to anything platform-specific (`az`,
  `mlflow.register_model`, endpoint APIs), it has escaped the Code layer. If a job YAML knows about
  scheduling, version registration, or what happens after the job finishes, it has escaped the
  Specification layer. Push the concern up to the next layer. Every generated or modified file must
  respect this layering — never merge concerns across layers even when it seems expedient.

- **One mental model** — Everything is a *package*: a [uv workspace][uv-workspace] member with its
  own [`pyproject.toml`][pyproject-toml], [`[build-system]`][build-system],
  [src layout][src-layout], source, tests, and dependencies. Same structure, same commands,
  everywhere.

  ```
  src/my_package/
  ├── pyproject.toml       # deps, metadata, [build-system]
  ├── aml-job.yaml         # aml spec (if executable, optional)
  ├── src/my_package/       # package source (src layout)
  │   ├── __init__.py
  │   └── __main__.py       # entry point (if executable, optional)
  └── tests/
  ```

  Same structure for every package — no special cases, nothing to restructure later. A package is
  for *computation* — read from paths, do work, write to paths. If a task doesn't compute
  (registering assets, deploying models, downloading data via platform tools), it isn't a package —
  it's orchestration.

- **Explicit deps** — Each package declares its own dependencies — including other workspace
  packages via [`[tool.uv.sources]`][uv-sources] — in its `pyproject.toml`. Runs are isolated per
  package, so undeclared imports fail by design. This keeps cloud jobs lean and makes deploying a
  subset of packages straightforward.

- **Colocation** — Everything needed to understand and run a piece of work lives together in one
  folder. Easy to find, easy to reason about.

- **Run anywhere the same** — Same command, same lockfile, same result — whether on your laptop, a
  colleague's machine, a VM, or AzureML. One [Dockerfile] serves as both [devcontainer] and cloud
  runner. Python deps installed at runtime by uv, not baked in.

- **Complexity must be earned** — Start with the simplest correct thing. Add structure only when a
  specific need demands it. But respect what exists: if the project has grown beyond the basics,
  that complexity was earned and should not be regressed without understanding why it was
  introduced.

A lean **Makefile** orchestrates everything: self-documenting (`make help`), the single entry point
for running, testing, and managing the project. All packages are uv workspace members resolved by
one lockfile at the root. Keep one target per concept (run/test/aml); avoid package-specific aliases
unless explicitly requested.

## Initializing a Project

A complete minimal project lives in `assets/` — use it as the reference for every file's exact
content and structure. Contents match project tree outlined below and package trees outlined above.

### Steps

1. **Scaffold the root.** Copy the core assets to get the root `pyproject.toml` (workspace
   declaration, dev deps only), `Makefile`, `AGENTS.md`, `.devcontainer/` (Dockerfile +
   devcontainer.json), and `.env`.
1. **Create your first package.** Add a folder under `src/` with its own `pyproject.toml`,
   `src/<name>/` (with `__init__.py` and `__main__.py`), and `tests/`. Adapt from the `mypkg`
   package in `assets/` and rename — grep for `mypkg` and replace with your package name everywhere
   (pyproject.toml, imports, etc.). Treat `__main__.py` as starter sample logic.
1. **Create user `.env.local`.** Copy from `.env` and substitute placeholders.
1. **Reopen in devcontainer.** Must be done by human.
1. **Lock deps.** Run `make sync` — this creates `uv.lock`. Commit it.
1. **Verify local.** Run the verification loop below. Do not continue until every command passes.

```
<project>/
├── .devcontainer/          # Dockerfile + devcontainer.json
├── .env                    # Azure config (safe defaults, committed)
├── AGENTS.md               # project context for AI agents
├── Makefile                # single entry point
├── pyproject.toml          # workspace root, dev deps only
├── uv.lock                 # committed — reproducibility anchor
└── src/
    └── <package>/           # one package to start
```

### Verify

All three must exit 0 before proceeding. Fix and re-run from `make sync` until they do.

```bash
make sync                    # uv.lock exists at root
make run pkg=<package_name>  # produces expected stdout/files
make test                    # all tests pass
```

### Key rules

- **Always a uv workspace**, even with one package. The root `pyproject.toml` declares
  `members = ["src/*"]` and has no runtime deps — only dev tools in `[dependency-groups]`.
- **[`uv.lock`][uv-lock] is committed.** Created/updated automatically by `uv run` and `make sync`
  (which runs `uv sync --all-packages` under the hood). Always use `make sync` instead of bare
  `uv sync` — the flag ensures every workspace member is installed, so `make test` and imports work.
- **One Dockerfile, two roles** — devcontainer and cloud runner. The devcontainer is optional — you
  can develop without it. But uv only isolates Python deps; OS-level dependencies (system libraries,
  CLI tools, native builds) can still conflict across projects. The devcontainer solves that, and
  because the same Dockerfile backs both local development and cloud execution, skipping it means
  losing the guarantee that your local environment matches AzureML exactly. Python deps are **not**
  baked in and follow this split:
  1. Python deps (`uv`-managed) → `pyproject.toml` / `uv.lock`.
  1. System deps (OS libs/tools) → `Dockerfile`.
  1. Dev-only tooling deps (for example Azure CLI + `ml`) → `.devcontainer/devcontainer.json`
     `features`.
- **`.env`** is committed with empty/safe defaults. Per-developer overrides go in `.env.local`
  (gitignored).
- **Tool/runtime version alignment** — Keep tool targets (for example [Ruff] `target-version` and
  type-checker Python version) aligned with `requires-python` in root and package `pyproject.toml`
  files.

### Existing projects

Map each independently runnable piece to a package under `src/`, extract its deps into a
`pyproject.toml`, and follow the same steps above. Get one package working end-to-end first, then
migrate the rest. If clashes exist (e.g., existing AGENTS.md), make sure to merge gracefully.

## Cloud execution (after local works)

Keep cloud as a separate step: first `make run`, then `make aml` to submit to AzureML.

### Steps

1. **Add `aml-job.yaml`** to the package folder if it doesn't exist yet. Copy from
   `./assets/src/mypkg/aml-job.yaml` and rename `mypkg` references. For the full schema, see the
   `$schema` link inside the file.
1. **Align the YAML with `__main__.py`.** The `command`, `inputs` in `aml-job.yaml` must match the
   current entry point and any arguments it expects. If `__main__.py` changed since the YAML was
   created, update the YAML to reflect the current state.
1. **Ensure `.env` / `.env.local` are populated.** Cloud submission requires valid Azure
   configuration (subscription, resource group, workspace). Ask the human to verify `.env.local` has
   all values filled in before proceeding.
1. **Fill YAML placeholders.** Ask the human to provide values for any remaining placeholders in the
   YAML — compute target (`<azure-ml-cluster-name>`), dataset references, etc.
1. **Submit.** Run `make aml pkg=<package_name>` from the project root.

### Verify

Ask the human to confirm in Azure ML Studio: job completed, tags/metrics visible, `outputs/`
contains expected artifacts.

### Beyond the job

This skill covers what runs inside a job and how to submit it. What happens after — registering
outputs as versioned data or model assets, deploying models to endpoints, scheduling recurring runs
— is orchestration that lives outside the job, typically in CI pipelines or operational scripts. The
same layer rule applies: those concerns never leak into Python code or job YAML. How they're
implemented varies by project; where they live does not — always the outermost layer.

### Why [CLI v2][cli-v2] over Python SDK

- YAML is a clear, declarative run contract.
- Python code stays platform-agnostic.
- Matches the layers: code (what), YAML spec (how), Makefile (when).

### Example files to inspect

- `./assets/src/mypkg/aml-job.yaml`: command, inputs, code path, environment build context, compute.
- `./assets/src/mypkg/src/mypkg/__main__.py` how to persist in AzureML:
  - tags = run metadata labels,
  - metrics = tracked numeric values,
  - stdout/stderr = captured AzureML logs,
  - `./outputs` = persisted job artifacts.

## Extensibility patterns (optional)

Keep the core scaffold minimal. Add these only when the project needs them. Each reference file
includes an **AGENTS.md section** — merge it to the project's `AGENTS.md` when applying the
extension so new agent sessions discover the added capabilities.

- **Linting & hooks** — team-level quality automation with [Ruff], [Ty], and [mdformat], optionally
  wired through [pre-commit]. [details](references/linting.md).
- **Experimentation & traceability** — outputs-by-run in `runs/` for local runs, cloud-job output
  download, and git-linked experiment commits for diff-from-main traceability:
  [details](references/experimentation.md).
- **Pipelines** — multi-step execution with composable packages/components:
  [details](references/pipelines.md).
- **Datasets** — download registered [Data Assets][data-assets] by name or raw blob data to the
  developer's machine for local usage: [details](references/datasets.md).

[aml]: https://learn.microsoft.com/en-us/azure/machine-learning/
[build-system]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#declaring-the-build-backend
[cli-v2]: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-configure-cli
[data-assets]: https://learn.microsoft.com/en-us/azure/machine-learning/concept-data
[devcontainer]: https://containers.dev/
[dockerfile]: https://docs.docker.com/reference/dockerfile/
[mdformat]: https://mdformat.readthedocs.io/
[pre-commit]: https://pre-commit.com/
[pyproject-toml]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
[ruff]: https://docs.astral.sh/ruff/
[src-layout]: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
[ty]: https://docs.astral.sh/ty/
[uv-lock]: https://docs.astral.sh/uv/concepts/lockfile/
[uv-sources]: https://docs.astral.sh/uv/concepts/dependencies/#dependency-sources
[uv-workspace]: https://docs.astral.sh/uv/concepts/workspaces/
