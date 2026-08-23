#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$script_dir/.." && pwd)
install_root=${UNPACK_FLOW_INSTALL_ROOT:-"$HOME/.local/lib/unpack-flow"}
bin_dir=${UNPACK_FLOW_BIN_DIR:-"$HOME/.local/bin"}
mode=${1:-install}
os=$(uname -s 2>/dev/null || echo unknown)
arch=$(uname -m 2>/dev/null || echo unknown)

echo "os=$os"
echo "arch=$arch"
echo "install_root=$install_root"
echo "bin_dir=$bin_dir"

case "$os" in
  Darwin)
    missing=''
    command -v pwsh >/dev/null 2>&1 || missing="$missing pwsh"
    command -v 7zz >/dev/null 2>&1 || missing="$missing 7zz"
    if [ -n "$missing" ]; then
      echo "missing=$missing"
      echo 'install_command=brew install powershell sevenzip'
      [ "$mode" = '--check' ] && exit 2
      echo 'Run the install_command after approving system changes, then retry.' >&2
      exit 4
    fi
    entry=unpack-flow-macos
    ;;
  Linux)
    missing=''
    command -v bash >/dev/null 2>&1 || missing="$missing bash"
    command -v 7z >/dev/null 2>&1 || command -v 7zz >/dev/null 2>&1 || missing="$missing 7z"
    command -v unrar >/dev/null 2>&1 || missing="$missing unrar"
    if [ -n "$missing" ]; then
      echo "missing=$missing"
      if command -v apt-get >/dev/null 2>&1; then
        echo 'install_command=sudo apt-get update && sudo apt-get install -y bash p7zip-full unrar'
      elif command -v dnf >/dev/null 2>&1; then
        echo 'install_command=sudo dnf install -y bash p7zip p7zip-plugins unrar'
      else
        echo 'install_command=install Bash 4+, 7-Zip and UnRAR with your system package manager'
      fi
      [ "$mode" = '--check' ] && exit 2
      echo 'Run the install_command after approving system changes, then retry.' >&2
      exit 4
    fi
    entry=unpack-flow
    ;;
  *) echo "Unsupported platform: $os" >&2; exit 4 ;;
esac

[ "$mode" = '--check' ] && { echo status=ready; exit 0; }
mkdir -p "$install_root/scripts" "$bin_dir"
cp "$script_dir/unpack-flow" "$script_dir/unpack-flow.ps1" "$script_dir/unpack-flow-macos" "$install_root/scripts/"
if [ -d "$root/tools" ]; then cp -R "$root/tools" "$install_root/"; fi
chmod 755 "$install_root/scripts/unpack-flow" "$install_root/scripts/unpack-flow-macos"
ln -sf "$install_root/scripts/$entry" "$bin_dir/unpack-flow"
echo "installed=$bin_dir/unpack-flow"
case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *) echo "path_command=export PATH=\"$bin_dir:\$PATH\"" ;;
esac
echo 'verify_command=unpack-flow version'
