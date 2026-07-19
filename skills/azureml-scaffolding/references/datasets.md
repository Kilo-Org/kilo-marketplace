# Datasets (Optional)

Pull data to the developer's machine for exploration and testing. Cloud jobs receive data through
YAML inputs (Blob URIs or registered [Data Assets][data-assets]) — never through a download
pre-step.

Both targets use [`azcopy`][azcopy] — it parallelises transfers and resumes on failure, making it
significantly faster than `az storage blob download` or SDK equivalents for large datasets.

## What this adds

Two Makefile targets for getting data into `./data/` (gitignored):

- `get-dataset` — download a registered Data Asset by name and version.
- `get-data` — download directly from blob storage with a regex filter.

A helper script (`scripts/resolve-asset-url.sh`) resolves a registered asset to its blob URL. The
Makefile stays readable; the script handles the AzureML plumbing.

## Setup

Copy `scripts/resolve-asset-url.sh` from this skill into the project's `scripts/` folder.

## Makefile targets

```makefile
get-dataset: ## Download registered Data Asset into ./data/<name>/<version>
	@test -n "$(name)" || { echo "usage: make get-dataset name=<asset> version=<v>"; exit 1; }
	@test -n "$(version)" || { echo "usage: make get-dataset name=<asset> version=<v>"; exit 1; }
	@url=$$(scripts/resolve-asset-url.sh "$(name)" "$(version)"); \
	mkdir -p "data/$(name)/$(version)"; \
	AZCOPY_AUTO_LOGIN_TYPE=azcli AZCOPY_TENANT_ID="$(TENANT_ID)" \
		azcopy copy "$$url" "data/$(name)/$(version)" --recursive

get-data: ## Download blob data into ./data
	@test -n "$(account)" || { echo "usage: make get-data account=<acct> container=<ctr> regex=<pattern>"; exit 1; }
	@mkdir -p data
	AZCOPY_AUTO_LOGIN_TYPE=azcli AZCOPY_TENANT_ID="$(TENANT_ID)" \
		azcopy copy "https://$(account).blob.core.windows.net/$(container)" \
		"data" --recursive --include-regex "$(regex)"
```

### Usage

```bash
# Registered Data Asset → data/my-dataset/3/
make get-dataset name=my-dataset version=3

# Raw blob storage
make get-data account=myacct container=mycontainer regex='^datasets/train/.*'
```

## Prerequisites

- Logged-in [Azure CLI][az-cli] session and `TENANT_ID` in `.env.local`.
- `get-dataset` also requires `AZUREML_WORKSPACE` / `AZUREML_RESOURCE_GROUP` and the `ml` CLI
  extension.
- [`azcopy`][azcopy] installed. Add the [Microsoft package registry][ms-pkg] to the Dockerfile so
  `azcopy` can be installed through the existing `apt-get install` block:

```dockerfile
# Add Microsoft package registry (before the main apt-get install)
RUN curl -sSL -O https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update
```

Then add `azcopy` to the existing `apt-get install` line that is already in the Dockerfile
(commented out by default):

```dockerfile
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends azcopy
```

## Verify

With Azure access: download, then `ls data/` to confirm files arrived. Without: run targets with no
arguments — they should print usage and exit non-zero.

```bash
make get-dataset name=<asset> version=<v>
make get-data account=<acct> container=<ctr> regex=<pattern>
make run pkg=<package_name> && make test     # core still works
```

## AGENTS.md section

Append to project `AGENTS.md`:

```markdown
## Datasets

Data lives in `data/` (gitignored). `make get-dataset` downloads
registered Data Assets; `make get-data` downloads from blob storage.
Cloud jobs receive data through YAML inputs, not downloads.
```

## Agent guidance

- Offer this extension when users need data on their local machine for exploration or testing.
- Prefer `get-dataset` when the team uses registered Data Assets.
- Use `get-data` when data isn't registered or the user needs regex-based file selection from blob
  storage.
- Ensure `data/` is in `.gitignore`.

[az-cli]: https://learn.microsoft.com/en-us/cli/azure/
[azcopy]: https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10
[data-assets]: https://learn.microsoft.com/en-us/azure/machine-learning/concept-data
[ms-pkg]: https://learn.microsoft.com/en-us/linux/packages
