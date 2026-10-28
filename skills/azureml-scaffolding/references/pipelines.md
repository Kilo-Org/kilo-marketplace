# Pipelines (Optional)

Use this pattern when one package is no longer enough and work must be composed as multiple steps.

## What this adds

- Step packages/components with clear input/output contracts.
- A pipeline spec that wires steps and data flow explicitly.
- Ability to run steps independently while keeping orchestration declarative.

## Practical structure

- Keep each step as an independent package/component with colocated code, environment, and spec.
- Keep `aml-job.yaml` in packages that are runnable standalone.
- You may add `aml-component.yaml` ([docs][component-docs], [schema][component-schema]) to packages
  that participate in more than one pipeline to reuse step definition.
- Create a pipeline folder per flow under `pipelines/`:

```text
pipelines/
└── <pipeline_name>/
    ├── aml-pipeline.yaml      # AzureML pipeline spec
    └── main.py                # local sequential runner
```

The `aml-pipeline.yaml` file follows the AzureML pipeline job spec ([docs][pipeline-docs],
[schema][pipeline-schema]).

**No `__init__.py` in `pipelines/`.** Runners are plain scripts, not modules.

## Local runner

`pipelines/<name>/main.py` imports and calls the main functions of each step package directly — pure
Python, no subprocess, no `make`. Keep runner logic thin: orchestration only, no step business
logic.

## Makefile extension

Extend `run` and `aml` so they also accept `pipe=`. The YAML / command path is resolved by
convention — `pkg=` looks in `src/`, `pipe=` looks in `pipelines/`:

```makefile
run: ## Run pkg or pipeline locally
	@test -n "$(pkg)$(pipe)" || { echo "usage: make run pkg=<name> | pipe=<name> [ARGS='...']"; exit 1; }
	@if [ -n "$(pkg)" ]; then uv run --isolated --package $(pkg) -m $(pkg) $(ARGS); \
	else uv run pipelines/$(pipe)/main.py $(ARGS); fi

aml: ## Submit job to AzureML (CLI v2)
	@test -n "$(pkg)$(pipe)" || { echo "usage: make aml pkg=<name> | pipe=<name> [AML_ARGS='...']"; exit 1; }
	...
	@if [ -n "$(pkg)" ]; then spec=src/$(pkg)/aml-job.yaml; \
	else spec=pipelines/$(pipe)/aml-pipeline.yaml; fi; \
	az ml job create -f "$$spec" ...
```

## Verify

```bash
make run pipe=<pipeline_name>    # all steps execute locally
make run pkg=<package_name>      # individual packages still work
make test
make aml pipe=<pipeline_name>   # submits pipeline job to AzureML
```

Cloud: ask the human to confirm the pipeline job completed in Azure ML Studio and step outputs are
visible.

## AGENTS.md section

Append to project `AGENTS.md`:

```markdown
## Pipelines

Multi-step workflows live under `pipelines/<name>/`. Run locally with
`make run pipe=<name>` or submit with `make aml pipe=<name>`.
```

## Agent guidance

- Do not add pipeline machinery by default.
- Offer pipelines only when users request multi-step orchestration, reusable components, or explicit
  step-level lineage.
- Keep pipeline docs and templates separate from the minimal core path.
- When multiple extensions are active, merge their Makefile changes into a single coherent target
  rather than duplicating or replacing.
- **No double-runs.** If a package is a pipeline step, don't also run it standalone in the same
  flow. `make run/aml pkg=X` is for isolated dev/test, not for duplicating work the pipeline already
  covers.

[component-docs]: https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-component-command?view=azureml-api-2
[component-schema]: https://azuremlschemas.azureedge.net/latest/commandComponent.schema.json
[pipeline-docs]: https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-job-pipeline?view=azureml-api-2
[pipeline-schema]: https://azuremlschemas.azureedge.net/latest/pipelineJob.schema.json
