#!/usr/bin/env bash
set -Eeuo pipefail

project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
engine=${UNPACK_FLOW_ENGINE:-$project/scripts/unpack-flow}
root=$(mktemp -d "${TMPDIR:-/tmp}/unpack-flow-recursive.XXXXXX")
trap 'rm -rf -- "$root"' EXIT
mkdir -p "$root/source/nested" "$root/payload"
printf 'recursive pass\n' > "$root/payload/marker.txt"
(cd "$root/payload" && zip -q "$root/source/nested/nested.zip" marker.txt)

listed=$("$engine" list -r "$root/source/*")
[[ "$listed" == *nested.zip* ]]
UNPACK_FLOW_STATE_ROOT="$root/state" "$engine" run -r -o "$root/source" "$root/source/*"
test -f "$root/source/nested-unpacked/marker.txt"
mkdir -p "$root/source/legacy-set" "$root/source/sample-backup"
(cd "$root/payload" && zip -q "$root/source/legacy-set/sample-backup.zip" marker.txt)
UNPACK_FLOW_STATE_ROOT="$root/state-parent" "$engine" run -r -o "$root/source" "$root/source/legacy-set/sample-backup.zip"
test -f "$root/source/sample-backup-legacy-set-unpacked/marker.txt"
UNPACK_FLOW_STATE_ROOT="$root/state-parent-2" "$engine" run -r -o "$root/source" "$root/source/legacy-set/sample-backup.zip"
test -f "$root/source/sample-backup-legacy-set-unpacked-2/marker.txt"
printf '%s\n' 'Bash recursive mode: PASS'
