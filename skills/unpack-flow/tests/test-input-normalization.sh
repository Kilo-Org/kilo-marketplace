#!/usr/bin/env bash
set -Eeuo pipefail

root=$(mktemp -d "${TMPDIR:-/tmp}/unpack-flow-input.XXXXXX")
trap 'rm -rf -- "$root"' EXIT
engine=${UNPACK_FLOW_ENGINE:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/scripts/unpack-flow}

touch "$root"/{bundle.zip,bundle.zip.sha256,data.part1.exe,data.part2.rar,data.part03.rar,set.part01.rar,set.part02.rar,split.7z.001,split.7z.002,numbered.zip.001,numbered.zip.002,classic.rar,classic.r00,notes.txt}
output=$(cd "$root" && "$engine" list *)

for expected in bundle.zip data.part1.exe set.part01.rar split.7z.001 numbered.zip.001 classic.rar; do
  [[ "$output" == *"$expected"* ]] || { echo "missing entry volume: $expected" >&2; exit 1; }
done
for unexpected in bundle.zip.sha256 data.part2.rar data.part03.rar set.part02.rar split.7z.002 numbered.zip.002 classic.r00 notes.txt; do
  [[ "$output" != *"$unexpected"* ]] || { echo "unexpected continuation/non-archive: $unexpected" >&2; exit 1; }
done
echo 'Bash input normalization: PASS'
