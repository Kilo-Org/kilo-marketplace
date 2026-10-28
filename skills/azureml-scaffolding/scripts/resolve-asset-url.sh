#!/usr/bin/env bash

set -euo pipefail

# Resolve a registered AzureML Data Asset to its blob URL.
#
# Usage: resolve-asset-url.sh <name> <version>
# Output: one https:// blob URL to stdout
#
# Requires: az cli (logged in) with ml extension,
#           AZUREML_RESOURCE_GROUP, AZUREML_WORKSPACE env vars.

die() { echo "error: $*" >&2; exit 1; }

[[ $# -eq 2 ]] || die "usage: $(basename "$0") <name> <version>"

name="$1"
version="$2"

[[ -n "${AZUREML_RESOURCE_GROUP:-}" ]] || die "AZUREML_RESOURCE_GROUP is not set"
[[ -n "${AZUREML_WORKSPACE:-}" ]]      || die "AZUREML_WORKSPACE is not set"

aml_flags=(--resource-group "$AZUREML_RESOURCE_GROUP" --workspace-name "$AZUREML_WORKSPACE")

path=$(az ml data show --name "$name" --version "$version" "${aml_flags[@]}" --query path -o tsv)

case "$path" in
    azureml://datastores/*/paths/*)
        ds="${path#azureml://datastores/}"; ds="${ds%%/paths/*}"
        blob_path="${path#*paths/}"
        account=$(az ml datastore show --name "$ds" "${aml_flags[@]}" --query account_name -o tsv)
        container=$(az ml datastore show --name "$ds" "${aml_flags[@]}" --query container_name -o tsv)
        echo "https://${account}.blob.core.windows.net/${container}/${blob_path}"
        ;;
    https://*)
        echo "$path"
        ;;
    *)
        die "unsupported path format: $path"
        ;;
esac
