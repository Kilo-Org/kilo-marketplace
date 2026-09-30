#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_root=$(mktemp -d "${TMPDIR:-/tmp}/unpack-flow-monitor.XXXXXX")
trap 'rm -rf -- "$test_root"' EXIT
touch "$test_root/input.zip"
output=$(UNPACK_FLOW_HEARTBEAT_SECONDS=2 UNPACK_FLOW_TEST_DELAY=3 pwsh -NoLogo -NoProfile -File "$project_root/scripts/unpack-flow.ps1" run "$test_root/input.zip" -Output "$test_root/output" -SevenZip "$project_root/tests/fake-slow-extractor.sh" 2>&1)
printf '%s\n' "$output" | grep -q 'running/运行中'
test -f "$test_root/output/input/extracted.txt"
printf '%s\n' 'Monitored extractor heartbeat: PASS'
