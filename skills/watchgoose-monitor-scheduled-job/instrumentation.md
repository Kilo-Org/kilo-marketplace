# Draft heartbeat instrumentation

Read this before producing a shell example. This is a draft for the operator to adapt and install,
not an instruction to run it during setup.

## POSIX shell wrapper

Save the private check URL from the Watchgoose dashboard in `WATCHGOOSE_PING_URL` using the job's
environment/secret manager. Never paste it into chat, print it, commit it, or derive it from
`unique_key`. Use the dashboard's bare per-check URL, without added query parameters or path
suffixes. Configure the expected schedule and alert integrations separately.

The wrapper runs one supplied command, records its actual exit status and, when configured, sends a
success or failure heartbeat after it returns. It preserves job status even when notification fails.
It uses POST, also compatible with checks configured to accept POST only. It sends no start ping and
makes one bounded heartbeat attempt. Review any retry policy separately: retries affect
history/timing and may improve resilience; the no-blind-retry rule for check creation is a different
concern.

```sh
#!/bin/sh
# Draft only: adapt and install after review; do not execute during setup.
if [ "$#" -eq 0 ]; then
  printf '%s\n' 'Provide a job command.' >&2
  exit 64
fi

# The job itself does not need the wrapper's heartbeat credential.
if (unset WATCHGOOSE_PING_URL; exec "$@"); then
  job_status=0
else
  job_status=$?
fi

if [ -z "${WATCHGOOSE_PING_URL:-}" ]; then
  printf '%s\n' 'Watchgoose heartbeat URL is not configured; job ran without notification.' >&2
  exit "$job_status"
fi

ping_url="$WATCHGOOSE_PING_URL"
if [ "$job_status" -ne 0 ]; then
  ping_url="${WATCHGOOSE_PING_URL%/}/fail"
fi

if ! curl --fail --silent --max-time 10 --request POST --output /dev/null "$ping_url" 2>/dev/null; then
  printf '%s\n' 'Watchgoose heartbeat request failed; job exit status preserved.' >&2
fi
exit "$job_status"
```

Example invocation after the operator configures the secret:
`sh heartbeat-wrapper.sh /usr/local/bin/run-backup`. No private URL is needed in the command shown
to the agent.

## Boundaries and verification

- The job command must correctly return failure itself. This wrapper cannot detect hidden
  pipeline/subcommand failures inside a script that incorrectly returns zero. Do not promise that
  `set -e` catches every failure.
- Missing or empty heartbeat configuration never prevents the job from running. The wrapper skips
  notification, prints a fixed warning, and returns the job's status. Only a missing job command
  exits 64. Missing-heartbeat alerts still depend on an armed check and configured alert routing.
- A notification failure emits only the fixed warning, not curl stderr/private URLs. Do not enable
  shell tracing (`set -x`) around credentials. Curl's URL argument and the wrapper's environment can
  still be visible to local process inspection; use a trusted job runner, not an untrusted shared
  host. The wrapper removes its ping variable from the job's inherited environment; do not wrap a
  job that already needs that variable for its own instrumentation. The job's own output may contain
  sensitive data; handle it under its existing logging policy.
- A killed process or unavailable host may send no failure heartbeat; missed-heartbeat detection is
  still required. This example does not claim retries, run correlation, notification delivery, or
  root-cause diagnosis.
- Optional **operator-reviewed opt-in**: a bounded POST to the private URL's `/start` path before
  the actual job enables runtime measurement and overrun monitoring. It is not enabled in this
  wrapper. A start notification failure must not prevent the job; preserve its exit status and
  completion heartbeat. Concurrent runs need deliberate correlation; start-without-finish history is
  not proof a job hung. Never send a synthetic start ping during setup.
- A first real failure heartbeat can move a new check directly to down; creation alone is not
  activation. After installation, verify the first **real successful job run** in the dashboard.
  Never send an artificial heartbeat to make setup appear complete.
