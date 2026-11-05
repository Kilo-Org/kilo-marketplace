#!/usr/bin/env bash
set -Eeuo pipefail

test_root=${UNPACK_FLOW_TEST_ROOT:-/data/unpack-flow-testcases}
engine=${UNPACK_FLOW_ENGINE:-$HOME/.local/bin/unpack-flow}
suite="$test_root/unpack-flow-minimal-testcases-v1.zip"
checksum="$suite.sha256"
[[ -d "$test_root" ]] || { echo "Synthetic fixture root missing: $test_root" >&2; exit 2; }
[[ -x "$engine" ]] || { echo "UnpackFlow executable missing: $engine" >&2; exit 3; }
[[ -f "$suite" && -f "$checksum" ]] || { echo "Compact fixture or checksum missing under $test_root" >&2; exit 4; }

(cd "$test_root" && sha256sum -c "$(basename "$checksum")")
run_root=$(mktemp -d "$test_root/.unpack-flow-run.XXXXXX")
if [[ ${UNPACK_FLOW_KEEP_TEST_OUTPUT:-0} != 1 ]]; then
  trap 'rm -rf -- "$run_root"' EXIT
fi

set +e
UNPACK_FLOW_STATE_ROOT="$run_root/state" "$engine" run -r -o "$run_root/output" "$suite"
rc=$?
set -e
[[ $rc -eq 1 ]] || { echo "Expected partial-failure exit 1, got $rc" >&2; exit 5; }
markers=$(find "$run_root/output" -type f -name EXPECTED.txt | wc -l | tr -d ' ')
inert_exe=$(find "$run_root/output" -type f -iname demo.EXE | wc -l | tr -d ' ')
failed_first=$(find "$run_root/output" -type f \( -iname '*.part01.exe' -o -iname '*.part1.exe' \) | wc -l | tr -d ' ')
(( markers >= 6 )) || { echo "Expected at least 6 markers, got $markers" >&2; exit 6; }
(( inert_exe >= 5 )) || { echo "Expected at least 5 inert EXE files, got $inert_exe" >&2; exit 7; }
(( failed_first >= 1 )) || { echo 'Expected the missing-volume first part to be preserved' >&2; exit 8; }
printf 'Native Linux synthetic suite: PASS (markers=%s inert_exe=%s failed_first=%s)\n' "$markers" "$inert_exe" "$failed_first"
