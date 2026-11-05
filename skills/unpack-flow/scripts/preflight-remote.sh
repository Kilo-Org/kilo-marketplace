#!/bin/sh
set -eu

src=${1:-/data/archives}; out=${2:-/data/extracted}
os=$(uname -s 2>/dev/null || echo unknown); arch=$(uname -m 2>/dev/null || echo unknown)
echo "os=$os"; echo "arch=$arch"
if [ -r /etc/os-release ]; then . /etc/os-release; else ID=unknown; VERSION_ID=unknown; fi
echo "distro=${ID:-unknown}"; echo "distro_version=${VERSION_ID:-unknown}"
if command -v bash >/dev/null 2>&1; then echo "bash=$(bash -c 'echo "$BASH_VERSION"')"; else echo bash=missing; fi
missing=''
for c in ionice nice nohup realpath find sort sed awk grep df du stat pgrep; do
  if command -v "$c" >/dev/null 2>&1; then echo "tool_$c=$(command -v "$c")"; else echo "tool_$c=missing"; missing="$missing $c"; fi
done
seven=missing
for c in /opt/unpack-flow/tools/7zz /opt/unpack-flow/tools/7z "$(command -v 7zz 2>/dev/null || true)" "$(command -v 7z 2>/dev/null || true)"; do
  [ -n "$c" ] && [ -x "$c" ] && { seven=$c; break; }
done
unrar_bin=missing
for c in /opt/unpack-flow/tools/unrar "$(command -v unrar 2>/dev/null || true)"; do
  [ -n "$c" ] && [ -x "$c" ] && { unrar_bin=$c; break; }
done
echo "seven=$seven"; echo "unrar=$unrar_bin"
[ "$seven" = missing ] && missing="$missing 7z"
[ "$unrar_bin" = missing ] && missing="$missing unrar"
if command -v unpack-flow >/dev/null 2>&1; then echo "unpack_flow=$(unpack-flow --version 2>/dev/null || echo installed)"; else echo unpack_flow=missing; fi
[ -d "$src" ] && echo source=present || echo source=missing
[ -d "$out" ] && echo output=present || echo output=missing
df -h "$src" 2>/dev/null | tail -n1 | sed 's/^/disk=/' || true
pgrep -af 'unrar|7zz|unpack-flow' 2>/dev/null | sed 's/^/process=/' | head -n20 || true
grep -E 'check =|resync =' /proc/mdstat 2>/dev/null | sed 's/^/raid=/' || true
if [ -z "$missing" ]; then
  echo status=ready
else
  echo "missing=$missing"
  case "${ID:-unknown}" in
    ubuntu|debian|linuxmint) echo 'install_command=sudo apt-get update && sudo apt-get install -y bash openssh-client p7zip-full unrar coreutils findutils procps util-linux' ;;
    fedora|rhel|centos|rocky|almalinux) echo 'install_command=sudo dnf install -y bash openssh-clients p7zip p7zip-plugins unrar coreutils findutils procps-ng util-linux' ;;
    opensuse*|sles) echo 'install_command=sudo zypper --non-interactive install bash openssh p7zip unrar coreutils findutils procps util-linux' ;;
    arch|manjaro) echo 'install_command=sudo pacman -Sy --noconfirm bash openssh p7zip unrar coreutils findutils procps-ng util-linux' ;;
    alpine) echo 'install_command=sudo apk add bash openssh-client 7zip unrar coreutils findutils procps util-linux' ;;
    *) echo 'install_command=unknown; install Bash 4+, OpenSSH client, 7z/7zz, UnRAR, coreutils, findutils, procps and util-linux' ;;
  esac
  echo status=missing_dependencies
fi
