#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    cat <<'USAGE'
Usage: validate.sh [--help]

Validate the SPL2 pipeline kit offline:
  - syntax-check setup.sh and smoke_offline.sh
  - compile spl2_pipeline_kit.py
  - run the built-in smoke profile

This validation does not contact a Splunk tenant.
USAGE
    exit 0
fi

bash -n "${SCRIPT_DIR}/setup.sh"
bash -n "${SCRIPT_DIR}/smoke_offline.sh"
python3 -m py_compile "${SCRIPT_DIR}/spl2_pipeline_kit.py"
python3 "${SCRIPT_DIR}/spl2_pipeline_kit.py" --phase smoke
