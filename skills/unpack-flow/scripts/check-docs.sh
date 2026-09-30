#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
bash "$root/scripts/check-anonymization.sh"
version=$(sed -n "s/^VERSION='\([^']*\)'.*/\1/p" "$root/scripts/unpack-flow")
files="README.md docs/README.zh-CN.md docs/README.es.md docs/README.hi.md docs/README.ar.md docs/README.pt-BR.md docs/README.fr.md docs/README.de.md docs/README.ja.md docs/README.ru.md"
translation_state="$root/docs/.translation-state"
test -s "$translation_state" || { echo 'Missing translation state' >&2; exit 1; }
grep -qx "metadata_version=$version" "$translation_state" || {
  echo "Translation metadata is not updated to $version" >&2
  exit 1
}
for file in $files; do
  test -s "$root/$file" || { echo "Missing translation: $file" >&2; exit 1; }
  grep -q "$version" "$root/$file" || { echo "Translation is not updated to $version: $file" >&2; exit 1; }
  grep -q 'once-email.com' "$root/$file" || { echo "Missing support link: $file" >&2; exit 1; }
  grep -q 'github.com/pangxin12345/unpack-flow' "$root/$file" || { echo "Missing GitHub project path: $file" >&2; exit 1; }
  grep -q 'tiantuowl@gmail.com' "$root/$file" || { echo "Missing public support email: $file" >&2; exit 1; }
  grep -q 'assets/unpack-flow-banner.png' "$root/$file" || { echo "Missing project banner: $file" >&2; exit 1; }
  lines=$(wc -l < "$root/$file" | tr -d ' ')
  test "$lines" -ge 100 || { echo "Localization is too short to cover the user guide: $file ($lines lines)" >&2; exit 1; }
  for required_text in install.bat install-linux.sh install-macos.sh 'unpack-flow run' 'unpack-flow start' 'unpack-flow status' 'unpack-flow log' 'unpack-flow wait' '-Recursive' '%LOCALAPPDATA%\unpack-flow\state' scripts/install_local tests/test-minimal-public-suite; do
    grep -Fq -- "$required_text" "$root/$file" || { echo "Localization is missing required content in $file: $required_text" >&2; exit 1; }
  done
done
test -s "$root/assets/unpack-flow-banner.png" || { echo 'Missing project banner asset' >&2; exit 1; }
root_navigation='README.md docs/README.zh-CN.md docs/README.es.md docs/README.hi.md docs/README.ar.md docs/README.pt-BR.md docs/README.fr.md docs/README.de.md docs/README.ja.md docs/README.ru.md'
localized_navigation='../README.md README.zh-CN.md README.es.md README.hi.md README.ar.md README.pt-BR.md README.fr.md README.de.md README.ja.md README.ru.md'
for target in $root_navigation; do
  grep -q "($target)" "$root/README.md" || { echo "Missing language link in README.md: $target" >&2; exit 1; }
done
for file in docs/README.*.md; do
  for target in $localized_navigation; do
    grep -q "($target)" "$root/$file" || { echo "Missing language link in $file: $target" >&2; exit 1; }
  done
done
grep -q '^## Learning demos$' "$root/README.md" || { echo 'Missing general learning demos in README.md' >&2; exit 1; }
grep -q '`run` is foreground and `start` is background' "$root/README.md" || { echo 'Missing unified run/start semantics' >&2; exit 1; }
grep -q 'combined English and Simplified Chinese' "$root/README.md" || { echo 'Missing bilingual help documentation' >&2; exit 1; }
grep -q 'Games are one example, not the product boundary' "$root/README.md" || { echo 'Game example must remain explicitly non-exclusive' >&2; exit 1; }
zh_readme="$root/docs/README.zh-CN.md"
zh_sections=$(grep -c '^## ' "$zh_readme")
test "$zh_sections" -ge 10 || { echo "Chinese README needs clearer hierarchy: only $zh_sections main sections" >&2; exit 1; }
grep -q '^## 30 秒快速开始$' "$zh_readme" || { echo 'Chinese README is missing the quick-start section' >&2; exit 1; }
grep -q '^## 常用命令$' "$zh_readme" || { echo 'Chinese README is missing the command reference' >&2; exit 1; }
grep -q '^## 解压失败时会发生什么$' "$zh_readme" || { echo 'Chinese README is missing failure behavior' >&2; exit 1; }
grep -q '| 命令 | 用途 |' "$zh_readme" || { echo 'Chinese README command reference must be scannable' >&2; exit 1; }
grep -q '| 平台 | 默认目录 |' "$zh_readme" || { echo 'Chinese README log locations must be tabular' >&2; exit 1; }
for installer in install.bat install-linux.sh install-macos.sh; do
  test -s "$root/$installer" || { echo "Missing platform installer: $installer" >&2; exit 1; }
  grep -q "$installer" "$root/README.md" || { echo "README does not document $installer" >&2; exit 1; }
done
count=$(printf '%s\n' $files | wc -l | tr -d ' ')
test "$count" = 10 || { echo "Expected 10 documents, found $count" >&2; exit 1; }
identity_files="README.md SKILL.md PUBLISHER.md SECURITY.md SUPPORT.md CHANGELOG.md"
for file in $identity_files; do
  test -s "$root/$file" || { echo "Missing identity document: $file" >&2; exit 1; }
  grep -q 'once-email.com' "$root/$file" || { echo "Missing official website: $file" >&2; exit 1; }
  grep -q 'github.com/pangxin12345' "$root/$file" || { echo "Missing GitHub identity: $file" >&2; exit 1; }
  grep -q 'tiantuowl@gmail.com' "$root/$file" || { echo "Missing public support email: $file" >&2; exit 1; }
done
old_email='tjpu.helen.us''@gmail.com'
removed_location='geographic'' location|geographical'' location|地理''位置|所在''地|ubicación'' geográfica|localização'' geográfica|localisation'' géographique|geografische[rn]?'' Standort|भौगोलिक'' स्थान|الموقع'' الجغرافي|Географическое'' местоположение'
removed_services='deployment, integration, customization,'' training|部署、集成、定制、''培训|priority'' support|优先''支持|commercial'' support|community'' support'
if rg -n -i "$old_email|$removed_location|$removed_services" README.md SKILL.md PUBLISHER.md SECURITY.md SUPPORT.md CHANGELOG.md docs; then
  echo 'Removed identity or commercial-support wording is still present' >&2
  exit 1
fi
test -s "$root/CONTRIBUTING.md" || { echo 'Missing public contribution guide' >&2; exit 1; }
echo "Documentation synchronized: $count languages, version $version"
