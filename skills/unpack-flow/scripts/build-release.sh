#!/usr/bin/env bash
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
bash "$root/scripts/check-anonymization.sh"
version=$(sed -n "s/^VERSION='\([^']*\)'.*/\1/p" "$root/scripts/unpack-flow")
dist="$root/dist"
stage="$dist/.stage"
rm -rf -- "$dist"
mkdir -p "$stage/linux/scripts" "$stage/macos/scripts" "$stage/macos/tools" "$stage/windows/scripts" "$stage/windows/tools"

cp "$root/install-linux.sh" "$stage/linux/"
cp "$root/scripts/unpack-flow" "$root/scripts/preflight.sh" "$root/scripts/preflight-remote.sh" "$root/scripts/deploy.sh" "$root/scripts/install-cli-linux.sh" "$stage/linux/scripts/"
mkdir -p "$stage/linux/tools"
cp -R "$root/tools/linux-x64" "$stage/linux/tools/"
cp "$root/install-macos.sh" "$stage/macos/"
cp "$root/scripts/unpack-flow.ps1" "$root/scripts/unpack-flow-macos" "$root/scripts/preflight-macos.sh" "$root/scripts/install-cli-macos.sh" "$stage/macos/scripts/"
cp -R "$root/tools/macos-arm64" "$stage/macos/tools/"
cp "$root/scripts/unpack-flow.ps1" "$root/scripts/preflight-windows.ps1" "$root/scripts/install-cli-windows.ps1" "$stage/windows/scripts/"
cp "$root/install.bat" "$stage/windows/"
cp -R "$root/tools/windows-x64" "$root/tools/windows-arm64" "$stage/windows/tools/"
cp "$root/tools/7zip-License.txt" "$stage/windows/tools/"
public_docs=(LICENSE README.md PUBLISHER.md SECURITY.md SUPPORT.md)
for platform in linux macos windows; do
  for file in "${public_docs[@]}"; do
    cp "$root/$file" "$stage/$platform/"
  done
done

COPYFILE_DISABLE=1 tar --no-xattrs -C "$stage/linux" -czf "$dist/unpack-flow-$version-linux.tar.gz" .
COPYFILE_DISABLE=1 tar --no-xattrs -C "$stage/macos" -czf "$dist/unpack-flow-$version-macos.tar.gz" .
if command -v zip >/dev/null 2>&1; then
  (cd "$stage/windows" && COPYFILE_DISABLE=1 zip -Xqr "$dist/unpack-flow-$version-windows.zip" .)
else
  echo 'zip is required to build the Windows package' >&2; exit 4
fi
if command -v sha256sum >/dev/null 2>&1; then
  (cd "$dist" && sha256sum unpack-flow-* > SHA256SUMS)
elif command -v shasum >/dev/null 2>&1; then
  (cd "$dist" && shasum -a 256 unpack-flow-* > SHA256SUMS)
else
  echo 'sha256sum or shasum is required' >&2; exit 4
fi

verify_root="$dist/.verify"
mkdir -p "$verify_root"
for artifact in "$dist/unpack-flow-$version-linux.tar.gz" "$dist/unpack-flow-$version-macos.tar.gz" "$dist/unpack-flow-$version-windows.zip"; do
  artifact_name=$(basename -- "$artifact")
  extracted="$verify_root/$artifact_name"
  mkdir -p "$extracted"
  case "$artifact" in
    *.tar.gz) tar -xzf "$artifact" -C "$extracted" ;;
    *.zip) unzip -q "$artifact" -d "$extracted" ;;
    *) echo "Unsupported release artifact: $artifact" >&2; exit 5 ;;
  esac
  while IFS= read -r forbidden_path; do
    echo "Private control-plane content leaked into $artifact_name: ${forbidden_path#$extracted/}" >&2
    exit 5
  done < <(find "$extracted" \( -name '.gitlab-ci.yml' -o -name '.internal' -o -path '*/.internal/*' -o -path '*/scripts/export-public-source.sh' \) -print)
done
rm -rf -- "$verify_root"
rm -rf -- "$stage"
printf 'Built release %s in %s\n' "$version" "$dist"
