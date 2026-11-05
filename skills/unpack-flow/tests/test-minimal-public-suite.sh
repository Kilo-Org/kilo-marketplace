#!/usr/bin/env bash
set -Eeuo pipefail

project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
engine=${UNPACK_FLOW_ENGINE:-$project/scripts/unpack-flow}
suite=${1:-$project/dist/unpack-flow-minimal-testcases-v1.zip}
[[ -f "$suite" ]] || { echo "Fixture not found: $suite" >&2; exit 2; }
root=$(mktemp -d "${TMPDIR:-/tmp}/unpack-flow-minimal-test.XXXXXX")
trap 'rm -rf -- "$root"' EXIT
set +e
UNPACK_FLOW_STATE_ROOT="$root/state" "$engine" run -r -o "$root/output" "$suite"
rc=$?
set -e
[[ $rc -eq 1 ]]
markers=$(find "$root/output" -type f -name EXPECTED.txt | wc -l | tr -d ' ')
inert_exe=$(find "$root/output" -type f -iname demo.EXE | wc -l | tr -d ' ')
first_volumes=$(find "$root/output" -type f -iname '*.part01.exe' -o -iname '*.part1.exe' | wc -l | tr -d ' ')
(( markers >= 6 ))
(( inert_exe >= 5 ))
(( first_volumes >= 1 ))
printf '%s\n' 'Minimal public suite Bash: PASS'
