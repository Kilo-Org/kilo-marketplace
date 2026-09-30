#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
installer="$root/scripts/install-cli-macos.sh"
[ -f "$installer" ] || { echo "Installer not found: $installer" >&2; exit 2; }
exec sh "$installer" "$@"
