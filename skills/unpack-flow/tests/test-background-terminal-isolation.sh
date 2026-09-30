#!/bin/sh
set -eu

project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
root=$(mktemp -d "${TMPDIR:-/tmp}/unpack-flow-background.XXXXXX")
trap 'rm -rf -- "$root"' EXIT
touch "$root/input.zip"

start_output=$(UNPACK_FLOW_STATE_ROOT="$root/state" UNPACK_FLOW_HEARTBEAT_SECONDS=1 UNPACK_FLOW_TEST_DELAY=3 pwsh -NoLogo -NoProfile -File "$project/scripts/unpack-flow.ps1" start "$root/input.zip" -Output "$root/output" -SevenZip "$project/tests/fake-slow-extractor.sh" 2>&1)
job_id=$(printf '%s\n' "$start_output" | sed -n 's/^Background job \/ 后台任务: //p')
worker_pid=$(printf '%s\n' "$start_output" | sed -n 's/^PID: //p')
[ -n "$job_id" ]
[ -n "$worker_pid" ]
test -f "$root/state/$job_id/job.log"
kill -0 "$worker_pid"
status_output=$(UNPACK_FLOW_STATE_ROOT="$root/state" pwsh -NoLogo -NoProfile -File "$project/scripts/unpack-flow.ps1" status "$job_id" 2>&1)
printf '%s\n' "$status_output" | grep -E 'Status[[:space:]]*: (queued|running)'
initial_log=$(UNPACK_FLOW_STATE_ROOT="$root/state" pwsh -NoLogo -NoProfile -File "$project/scripts/unpack-flow.ps1" log "$job_id" 2>&1)
sleep 4
wait_output=$(UNPACK_FLOW_STATE_ROOT="$root/state" pwsh -NoLogo -NoProfile -File "$project/scripts/unpack-flow.ps1" wait "$job_id" 2>&1)
test -f "$root/output/input/extracted.txt"
grep -q 'scan/扫描' "$root/state/$job_id/job.log"
grep -q 'extract/解压' "$root/state/$job_id/job.log"
grep -q 'finalize/整理' "$root/state/$job_id/job.log"
grep -q 'Completed / 完成' "$root/state/$job_id/job.log"
escape=$(printf '\033')
if printf '%s%s%s%s' "$start_output" "$status_output" "$initial_log" "$wait_output" | LC_ALL=C grep -E "${escape}\[[0-9;?]*[A-Za-z]|[0-9]+;[0-9]+R|$(printf '\a')" >/dev/null; then
  echo 'terminal escape sequence leaked from background worker' >&2
  exit 1
fi
printf '%s\n' 'Background terminal isolation: PASS'
