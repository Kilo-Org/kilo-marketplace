#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -d "$script_dir/tools/macos-arm64" ]; then
  source_root=$script_dir
else
  source_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
fi
target_dir=${UNPACK_FLOW_INSTALL_DIR:-/usr/local/lib/unpack-flow}
if [ -n "${UNPACK_FLOW_BIN_DIR:-}" ]; then
  bin_dir=$UNPACK_FLOW_BIN_DIR
else
  active_command=$(command -v unpack-flow 2>/dev/null || true)
  case "$active_command" in
    "$HOME/.local/bin/unpack-flow"|/usr/local/bin/unpack-flow)
      bin_dir=$(dirname -- "$active_command")
      ;;
    *)
      bin_dir=/usr/local/bin
      ;;
  esac
fi

command -v pwsh >/dev/null 2>&1 || { echo 'Missing pwsh. Run: brew install powershell sevenzip' >&2; exit 4; }
command -v 7zz >/dev/null 2>&1 || { echo 'Missing 7zz. Run: brew install sevenzip' >&2; exit 4; }
mkdir -p "$target_dir" "$bin_dir"
mkdir -p "$target_dir/tools"
cp "$script_dir/unpack-flow.ps1" "$target_dir/unpack-flow.ps1"
cp "$script_dir/unpack-flow-macos" "$target_dir/unpack-flow"
cp -R "$source_root/tools/macos-arm64" "$target_dir/tools/"
chmod 755 "$target_dir/unpack-flow"
ln -sf "$target_dir/unpack-flow" "$bin_dir/unpack-flow"
echo "Installed: $bin_dir/unpack-flow"
resolved_command=$(command -v unpack-flow 2>/dev/null || true)
if [ "$resolved_command" != "$bin_dir/unpack-flow" ]; then
  echo "Warning: PATH resolves unpack-flow to ${resolved_command:-not-found}, not $bin_dir/unpack-flow" >&2
  echo "Verify: $bin_dir/unpack-flow version"
else
  echo 'Verify: unpack-flow version'
fi
