#!/bin/sh
set -eu

echo "os=$(uname -s 2>/dev/null || echo unknown)"
echo "arch=$(uname -m 2>/dev/null || echo unknown)"
missing=''
for command_name in pwsh 7zz; do
  if command -v "$command_name" >/dev/null 2>&1; then
    echo "$command_name=$(command -v "$command_name")"
  else
    echo "$command_name=missing"
    missing="$missing $command_name"
  fi
done
if [ -z "$missing" ]; then
  echo status=ready
else
  echo "missing=$missing"
  echo 'install_command=brew install powershell sevenzip'
  echo status=missing_dependencies
fi
