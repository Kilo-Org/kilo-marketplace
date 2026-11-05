#!/usr/bin/env bash
set -Eeuo pipefail

project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output=${1:-$project/dist/unpack-flow-minimal-testcases-v1.zip}
work=$(mktemp -d "${TMPDIR:-/tmp}/unpack-flow-minimal-suite.XXXXXX")
trap 'rm -rf -- "$work"' EXIT

suite="$work/unpack-flow-minimal-testcases-v1"
seed="$work/seed"
mkdir -p "$suite" "$seed/bin" "$seed/config"
printf '%s\n' 'UnpackFlow minimal public fixture' > "$seed/README.txt"
printf '%s\n' 'EXPECTED: minimal-suite-marker' > "$seed/EXPECTED.txt"
printf '%s\n' 'This is inert test text, not an executable.' > "$seed/bin/demo.EXE"
printf '%s\n' 'language=zh-CN' > "$seed/config/settings.ini"

mkdir -p "$suite/01_zip_single"
(cd "$seed" && zip -X -q -r "$suite/01_zip_single/single.zip" .)

mkdir -p "$suite/02_tar_gz"
tar -C "$seed" -czf "$suite/02_tar_gz/log-bundle.tar.gz" .

mkdir -p "$suite/03_nested_zip"
(cd "$seed" && zip -X -q -r "$work/inner.zip" .)
mkdir -p "$work/nested"
cp "$work/inner.zip" "$work/nested/inner.zip"
(cd "$work/nested" && zip -X -q -r "$suite/03_nested_zip/outer.zip" .)

mkdir -p "$suite/04_unicode_spaces/示例资料"
(cd "$seed" && zip -X -q -r "$suite/04_unicode_spaces/示例资料/归档包.zip" .)

rar_bundle="$project/tools/macos-arm64/rarmacos-arm-723.tar.gz"
if [[ ! -f "$rar_bundle" ]]; then
  echo "Missing bundled official RAR tool: $rar_bundle" >&2
  exit 4
fi
tar -xzf "$rar_bundle" -C "$work"
rar_tool="$work/rar/rar"
sfx_module="$work/rar/default.sfx"
chmod +x "$rar_tool"

mkdir -p "$work/sfx-payload/sample-sfx/data" "$suite/05_sfx_multipart"
cp "$seed/EXPECTED.txt" "$work/sfx-payload/sample-sfx/data/EXPECTED.txt"
cp "$seed/bin/demo.EXE" "$work/sfx-payload/sample-sfx/demo.EXE"
dd if=/dev/zero of="$work/sfx-payload/sample-sfx/data/padding.bin" bs=1024 count=2600 2>/dev/null
(cd "$work/sfx-payload" && "$rar_tool" a -idq -m0 -v256k -sfx"$sfx_module" "$suite/05_sfx_multipart/sample-sfx.rar" sample-sfx)

first_sfx_native=$(find "$suite/05_sfx_multipart" -maxdepth 1 -type f -iname '*.part01.sfx' -print -quit)
if [[ -n "$first_sfx_native" ]]; then
  mv -- "$first_sfx_native" "${first_sfx_native%.sfx}.exe"
fi
first_sfx=$(find "$suite/05_sfx_multipart" -maxdepth 1 -type f -iname '*.exe' -print -quit)
if [[ -z "$first_sfx" ]]; then
  echo 'RAR did not create an SFX first volume' >&2
  exit 5
fi

mkdir -p "$suite/06_missing_part_expected_failure"
cp "$suite/05_sfx_multipart"/* "$suite/06_missing_part_expected_failure/"
missing=$(find "$suite/06_missing_part_expected_failure" -maxdepth 1 -type f -iname '*.part02.rar' -print -quit)
if [[ -z "$missing" ]]; then
  missing=$(find "$suite/06_missing_part_expected_failure" -maxdepth 1 -type f -iname '*.part2.rar' -print -quit)
fi
[[ -n "$missing" ]] || { echo 'Could not identify the second multipart volume' >&2; exit 6; }
rm -f -- "$missing"

mkdir -p "$suite/07_same_name_context/sample-backup/legacy-set"
(cd "$seed" && zip -X -q -r "$suite/07_same_name_context/sample-backup/legacy-set/sample-backup.zip" .)

cat > "$suite/MANIFEST.txt" <<'EOF'
UnpackFlow minimal public test suite v1
01 ZIP single archive
02 TAR.GZ native fallback
03 ZIP inside ZIP recursive extraction
04 Unicode and spaces in paths
05 multipart RAR SFX: part01.exe plus later partNN.rar volumes
06 expected failure caused by a missing second volume
07 same archive name in a contextual source directory
All EXE payloads are inert text except the RAR-generated SFX first volume; tests must extract it as data and never execute it.
EOF

mkdir -p "$(dirname -- "$output")"
rm -f -- "$output" "$output.sha256"
(cd "$work" && zip -X -q -r "$output" "$(basename "$suite")")
if command -v shasum >/dev/null 2>&1; then
  (cd "$(dirname -- "$output")" && shasum -a 256 "$(basename "$output")") > "$output.sha256"
else
  (cd "$(dirname -- "$output")" && sha256sum "$(basename "$output")") > "$output.sha256"
fi
printf 'suite=%s\nchecksum=%s\n' "$output" "$output.sha256"
