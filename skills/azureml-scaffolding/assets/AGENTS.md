# AGENTS.md

ML project following a layered approach to MLOps — reproducible from experimentation through
production. What runs locally runs in the cloud with no surprises. Three concentric layers, inner
layers know nothing about outer ones:

1. **Code** — *the what.* Pure Python packages under `src/`. Business logic only, no platform
   imports, no CLI tools, no infra awareness.
1. **Specification** — *the how.* `aml-job.yaml` per package. Declares how code executes on a
   compute platform. Lives next to the code it describes but never leaks into it.
1. **Orchestration** — *the when.* `Makefile`, CI. Triggers execution. Knows about specs, knows
   nothing about code internals.

```
├── Makefile                # single entry point — `make help` for commands
├── pyproject.toml          # uv workspace root, dev deps only
├── uv.lock                 # committed lockfile
├── .env                    # env var template (committed, safe defaults)
├── .env.local              # real values per developer (gitignored)
└── src/
    └── <package>/
        ├── pyproject.toml
        ├── aml-job.yaml
        ├── src/<package>/
        └── tests/
```

The **Makefile** is the single entry point for all local execution. Run `make help` for the current
list of available commands. `.env` documents which variables the project needs; `.env.local`
(gitignored) carries real values.

For a deeper understanding of why this project is structured this way, see the `azureml-scaffolding`
skill.
