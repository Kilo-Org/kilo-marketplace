#!/usr/bin/env bash
set -Eeuo pipefail

host=''; source_root='/data/archives'; output_root='/data/extracted'
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
remote_probe="$script_dir/preflight-remote.sh"
usage() { echo "用法：$0 [--host user@server] [--source /data/archives] [--output /data/extracted]"; }
while (($#)); do
  case "$1" in
    --host) host=${2:?}; shift 2;; --source) source_root=${2:?}; shift 2;;
    --output) output_root=${2:?}; shift 2;; -h|--help) usage; exit 0;;
    *) echo "未知参数：$1" >&2; usage >&2; exit 2;;
  esac
done
[[ "$source_root" == /* && "$output_root" == /* ]] || { echo '源和输出必须是绝对路径' >&2; exit 2; }
[[ -f "$remote_probe" ]] || { echo "缺少预检程序：$remote_probe" >&2; exit 2; }
if [[ -n "$host" ]]; then
  ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" sh -s -- "$source_root" "$output_root" < "$remote_probe" || { echo ssh=failed >&2; exit 3; }
else
  sh "$remote_probe" "$source_root" "$output_root"
fi
