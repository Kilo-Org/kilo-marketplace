#!/usr/bin/env bash
set -Eeuo pipefail

host=''; source_root='/data/archives'; output_root='/data/extracted'; install_deps=0
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
payload="$script_dir/unpack-flow"
usage() { echo "用法：$0 [--host user@server] [--source /data/archives] [--output /data/extracted] [--install-deps]"; }
while (($#)); do
  case "$1" in
    --host) host=${2:?}; shift 2;; --source) source_root=${2:?}; shift 2;;
    --output) output_root=${2:?}; shift 2;; --install-deps) install_deps=1; shift;;
    -h|--help) usage; exit 0;; *) echo "未知参数：$1" >&2; usage >&2; exit 2;;
  esac
done
[[ -f "$payload" ]] || { echo "缺少部署文件：$payload" >&2; exit 2; }
[[ "$source_root" == /* && "$output_root" == /* ]] || { echo '源和输出必须是绝对路径' >&2; exit 2; }

installer=$(cat <<'EOF'
set -Eeuo pipefail
payload=$1; src=$2; out=$3; install_deps=$4
[[ "$(uname -s)" == Linux ]] || { echo '仅支持 Linux' >&2; exit 3; }
(( BASH_VERSINFO[0] >= 4 )) || { echo '需要 Bash 4+' >&2; exit 3; }
if (( install_deps )); then
  if command -v apt-get >/dev/null; then
    apt-get update
    apt-get install -y bash openssh-client p7zip-full coreutils findutils procps util-linux
    command -v unrar >/dev/null || apt-get install -y unrar || apt-get install -y unrar-free
  elif command -v dnf >/dev/null; then dnf install -y bash openssh-clients p7zip p7zip-plugins unrar coreutils findutils procps-ng util-linux
  elif command -v yum >/dev/null; then yum install -y bash openssh-clients p7zip p7zip-plugins unrar coreutils findutils procps-ng util-linux
  elif command -v zypper >/dev/null; then zypper --non-interactive install bash openssh p7zip unrar coreutils findutils procps util-linux
  elif command -v pacman >/dev/null; then pacman -Sy --noconfirm bash openssh p7zip unrar coreutils findutils procps-ng util-linux
  elif command -v apk >/dev/null; then apk add bash openssh-client 7zip unrar coreutils findutils procps util-linux
  else echo '无法识别包管理器，请根据预检提示手工安装依赖' >&2; exit 4
  fi
fi
command -v 7zz >/dev/null || command -v 7z >/dev/null || [[ -x /opt/unpack-flow/tools/7zz || -x /opt/unpack-flow/tools/7z ]] || { echo '缺少 7z/7zz；授权后使用 --install-deps，或放入 /opt/unpack-flow/tools' >&2; exit 4; }
command -v unrar >/dev/null || [[ -x /opt/unpack-flow/tools/unrar ]] || { echo '缺少 unrar；授权后使用 --install-deps，或放入 /opt/unpack-flow/tools' >&2; exit 4; }
install -m 755 "$payload" /usr/local/bin/unpack-flow
mkdir -p "$src" "$out"
rm -f /etc/profile.d/unpack-flow.sh
unpack-flow --version
unpack-flow help >/dev/null
echo '部署完成：/usr/local/bin/unpack-flow'
EOF
)

if [[ -n "$host" ]]; then
  remote_payload="/tmp/unpack-flow.deploy.$$"
  scp "$payload" "$host:$remote_payload"
  ssh "$host" bash -s -- "$remote_payload" "$source_root" "$output_root" "$install_deps" <<< "$installer"
  ssh "$host" rm -f -- "$remote_payload"
else
  tmp_payload="/tmp/unpack-flow.deploy.$$"
  cp "$payload" "$tmp_payload"
  bash -s -- "$tmp_payload" "$source_root" "$output_root" "$install_deps" <<< "$installer"
  rm -f -- "$tmp_payload"
fi
