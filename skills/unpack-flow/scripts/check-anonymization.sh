#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
customer_id='XJ''[0-9]{4,}'
dated_folder='待删除''-旧版'
private_data='/data/''game'
private_download='Downloads/''1111'
numbered_host='[Hh]ost[- ]?''1''8|1''8 号|ホスト''1''8|होस्ट 1''8|المضيف 1''8|hôte 1''8'
private_lab='/home/''虚拟机'
legacy_variable='UNPACK_FLOW_HOST''18'
forbidden="$customer_id|$dated_folder|$private_data|$private_download|$numbered_host|$private_lab|$legacy_variable"

if rg -n --hidden \
  -g '!**/.git/**' \
  -g '!**/.internal/**' \
  -g '!**/dist/**' \
  -g '!**/tools/**' \
  -g '!**/scripts/check-anonymization.sh' \
  "$forbidden" "$root"; then
  echo 'Public anonymization audit failed: private-looking test identifiers remain.' >&2
  exit 1
fi

echo 'Public test-data anonymization: PASS'
