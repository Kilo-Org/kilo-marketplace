#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$script_dir/.." && pwd)
install_root=${UNPACK_FLOW_INSTALL_ROOT:-"$HOME/.local/lib/unpack-flow"}
bin_dir=${UNPACK_FLOW_BIN_DIR:-"$HOME/.local/bin"}
mode=${1:-install}

[ "$(uname -s 2>/dev/null || echo unknown)" = Linux ] || { echo 'install-cli-linux.sh requires Linux' >&2; exit 4; }
missing=''
command -v bash >/dev/null 2>&1 || missing="$missing bash"
command -v 7z >/dev/null 2>&1 || command -v 7zz >/dev/null 2>&1 || missing="$missing 7z"
if [ -n "$missing" ]; then
  echo "missing=$missing"
  if command -v apt-get >/dev/null 2>&1; then echo 'install_command=sudo apt-get update && sudo apt-get install -y bash p7zip-full'
  elif command -v dnf >/dev/null 2>&1; then echo 'install_command=sudo dnf install -y bash p7zip p7zip-plugins'
  else echo 'install_command=install Bash 4+ and 7-Zip with your system package manager'
  fi
  [ "$mode" = '--check' ] && exit 2
  exit 4
fi
[ "$mode" = '--check' ] && { echo status=ready; exit 0; }

mkdir -p "$install_root/scripts" "$bin_dir"
cp "$script_dir/unpack-flow" "$install_root/scripts/"
if [ -d "$root/tools/linux-x64" ]; then
  mkdir -p "$install_root/tools"
  cp -R "$root/tools/linux-x64" "$install_root/tools/"
  chmod 755 "$install_root/tools/linux-x64/unrar"
fi
chmod 755 "$install_root/scripts/unpack-flow"
ln -sf "$install_root/scripts/unpack-flow" "$bin_dir/unpack-flow"
echo "installed=$bin_dir/unpack-flow"
case ":$PATH:" in *":$bin_dir:"*) ;; *) echo "path_command=export PATH=\"$bin_dir:\$PATH\"" ;; esac
echo 'verify_command=unpack-flow version'
