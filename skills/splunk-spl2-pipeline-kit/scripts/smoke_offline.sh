#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_OUT="$(mktemp -d "${TMPDIR:-/tmp}/spl2-kit-smoke.XXXXXX")"
trap 'rm -rf "${TMP_OUT}"' EXIT

python3 "${SCRIPT_DIR}/spl2_pipeline_kit.py" --phase all --profile both --output-dir "${TMP_OUT}"

required=(
  README.md
  coverage-report.json
  lint-report.json
  lint-report.md
  templates/ingestProcessor/metrics.spl2
  templates/ingestProcessor/decrypt.spl2
  templates/edgeProcessor/route.spl2
  custom-template-app/default/data/spl2/ip_route_redact_template.spl2
)
for file in "${required[@]}"; do
  [[ -f "${TMP_OUT}/${file}" ]] || { echo "missing ${file}" >&2; exit 1; }
done

python3 - "${TMP_OUT}/lint-report.json" <<'PY'
import json
import sys
reports = json.load(open(sys.argv[1], encoding="utf-8"))
if any(report["status"] == "FAIL" for report in reports):
    raise SystemExit("lint report has failures")
PY

echo "smoke_offline: OK"
