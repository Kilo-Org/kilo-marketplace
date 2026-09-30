#!/bin/sh
set -eu

destination=
for argument in "$@"; do
  case "$argument" in
    -o*) destination=${argument#-o} ;;
  esac
done
[ -n "$destination" ] || exit 2
sleep "${UNPACK_FLOW_TEST_DELAY:-3}"
mkdir -p "$destination"
printf 'monitored extraction completed\n' > "$destination/extracted.txt"
