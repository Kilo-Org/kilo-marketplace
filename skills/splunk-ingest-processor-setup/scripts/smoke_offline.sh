#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_OUT="$(mktemp -d "${TMPDIR:-/tmp}/splunk-ip-smoke.XXXXXX")"
trap 'rm -rf "${TMP_OUT}"' EXIT

python3 "${SCRIPT_DIR}/render_assets.py" \
  --phase all \
  --tenant-name smoke-prod \
  --stack-url https://smoke-prod.scs.splunk.com \
  --subscription-tier premier \
  --source-types "aws:cloudtrail,crowdstrike:fdr,json_app" \
  --destinations "splunk_indexer=type=splunk_cloud;default=true,metrics=type=metrics_index;index=metrics,s3_archive=type=s3;format=parquet;bucket=example-bucket" \
  --pipelines "redact_auth=template=redact;sourcetype=json_app;destination=splunk_indexer,http_metrics=template=metrics;destination=metrics,cloudtrail_ocsf=template=ocsf;sourcetype=aws:cloudtrail;destination=splunk_indexer" \
  --output-dir "${TMP_OUT}" \
  --json

required=(
  README.md
  readiness-report.md
  coverage-report.json
  apply-plan.json
  control-plane-handoffs/ingest-processor-ui.md
  control-plane-handoffs/known-issues.md
  monitoring/searches.spl
  monitoring/usage-summary-handoff.md
  spl2-pipeline-kit/lint-report.json
  pipelines/redact_auth.spl2
  pipelines/http_metrics.spl2
  handoffs/splunk-data-source-readiness-doctor.md
)
for file in "${required[@]}"; do
  [[ -f "${TMP_OUT}/${file}" ]] || { echo "missing ${file}" >&2; exit 1; }
done

if rg -n "POST /services/data-manager/input|BEGIN PRIVATE KEY|global HEC ACK" "${TMP_OUT}" >/dev/null; then
  echo "forbidden private API or secret material rendered" >&2
  exit 1
fi

echo "smoke_offline: OK"
