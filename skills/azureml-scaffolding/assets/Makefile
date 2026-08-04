## Load project env vars for all targets
-include .env.local
export

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-15s %s\n", $$1, $$2}'

sync: ## Sync master env
	uv sync --all-packages

run: ## Isolated local run for pkg
	@test -n "$(pkg)" || { echo "usage: make run pkg=<name> [ARGS='...']"; exit 1; }
	uv run --isolated --package $(pkg) -m $(pkg) $(ARGS)

test: ## Run tests across all pkgs
	uv run pytest

aml: ## Submit job to AzureML (CLI v2)
	@test -n "$(pkg)" || { echo "usage: make aml pkg=<name> [AML_ARGS='...']"; exit 1; }
	@test -n "$(AZUREML_WORKSPACE)" || { echo "AZUREML_WORKSPACE is not set (define it in .env/.env.local)"; exit 1; }
	@test -n "$(AZUREML_RESOURCE_GROUP)" || { echo "AZUREML_RESOURCE_GROUP is not set (define it in .env/.env.local)"; exit 1; }
	az ml job create \
		-f src/$(pkg)/aml-job.yaml \
		--resource-group "$(AZUREML_RESOURCE_GROUP)" \
		--workspace-name "$(AZUREML_WORKSPACE)" \
		$(AML_ARGS)
