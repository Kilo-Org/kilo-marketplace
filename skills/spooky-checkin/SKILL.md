---
name: spooky-checkin
description: >-
  Make every scheduled job watched, so a missed or failed run raises an alert.
  Adds one check-in line to jobs that run off Vercel. Use when adding a cron
  job, a GitHub Actions schedule, or any recurring task.
metadata:
  category: observability
  author: banana-intelligence-dot-ai
  source:
    repository: 'https://github.com/banana-intelligence-dot-ai/spookyparticles'
    path: skills/spooky-checkin
    license_path: LICENSE
    ref: main
    commit: 9bd4819a7c62032b501487b1a63267c332002abe
---

# Watch every scheduled job

Covers Standard item 4: every scheduled job is watched, and a missed or failed run raises an alert. See [the Standard, Keep it running](https://github.com/banana-intelligence-dot-ai/spookyparticles/blob/main/docs/standard/STANDARD.md#keep-it-running).

Spooky reads Vercel cron jobs and their run history on its own, with no code change, when the team is connected with a pasted token. With Sign in with Vercel alone, Vercel does not share run history, so a Vercel cron route needs a check-in too (see "A Vercel cron route" below). Jobs that run anywhere else (GitHub Actions, another host, a machine under a desk) need a check-in: a link the job calls when it finishes. If the call does not arrive on time, Spooky alerts.

## Requirements and network calls

- `SPOOKY_API_KEY`: a Spooky Particles key, set in the environment by the person. Never ask for it in chat, print it or write it to a file. Listing jobs needs a read key. Creating a job needs a write key. If it is not set, stop and tell the person to make one on the Agents page at https://spookyparticles.com/app/agents.
- Every call goes to `spookyparticles.com` over HTTPS. There are no other hosts and nothing is installed except the optional `spooky-checkin` npm package.
  - `GET https://spookyparticles.com/api/v1/checkins` (or the MCP tool `list_jobs`) reads the job list. It writes nothing.
  - `POST https://spookyparticles.com/api/v1/checkins` creates one check-in job. This writes to the person's Spooky account.
  - The job's ping link (`https://spookyparticles.com/api/ping/<token>`) is called by the person's job itself, on each run. A call to it records a run, and a failure ending can alert the owner. Never call it while testing.
- Ask the person to confirm before each `POST`: the job name, the period and the project it will watch.

## Check

1. List every schedule in the project:
   - `crons` in `vercel.json`.
   - `schedule:` triggers in `.github/workflows/*.yml`.
   - Any other cron config the repo has (a host's config file, a `crontab` line in the docs).
2. If the person uses Spooky, call the MCP tool `list_jobs` (or `GET https://spookyparticles.com/api/v1/checkins` with `Authorization: Bearer $SPOOKY_API_KEY`, piped in with `curl -H @-` so the key never sits on a command line). Each job shows `status`, `lastCheckIn` and `nextDue`. Vercel cron jobs appear on their own once the team is connected.
3. A schedule off Vercel with no matching job in the list is not watched.

## Fix

For each schedule off Vercel that is not watched:

1. After the person confirms, create a check-in job. This needs a Spooky key with the write scope:

   ```bash
   printf 'Authorization: Bearer %s\n' "$SPOOKY_API_KEY" | curl -fsS -X POST https://spookyparticles.com/api/v1/checkins \
     -H @- -H "Content-Type: application/json" \
     -d '{"name":"<job name>","periodMinutes":<minutes between runs>,"project":"<vercel project>"}'
   ```

   The answer has `job.pingUrl` and a ready `curl` line.
2. Treat the ping link like a password: anyone with it can say the job ran. Do not put it in code. Give it to the person and ask them to store it as a secret named `SPOOKY_PING_URL` where the job runs (for GitHub Actions: repo Settings, Secrets and variables, Actions). Do not print it in logs or in the pull request.
3. On a new branch, add one line as the last step of the job, so it runs only when the job succeeds:

   ```bash
   curl -fsS -m 10 --retry 3 "$SPOOKY_PING_URL"
   ```

   In a GitHub Actions step, pass it in with `env: SPOOKY_PING_URL: ${{ secrets.SPOOKY_PING_URL }}`.
4. Open one pull request per job. Say in the description that the person must add the secret before merging.

## A Vercel cron route

Use the `spooky-checkin` package on npm, one file with no dependencies. Guide: https://spookyparticles.com/docs/npm-package.

1. Create the job and have the person store the link as `SPOOKY_PING_URL` in the Vercel project's environment variables (Production), as in steps 1 and 2 above.
2. Add the package: `npm i spooky-checkin`. If the project avoids new dependencies, copy the single file `packages/checkin/src/index.ts` from https://github.com/banana-intelligence-dot-ai/spookyparticles into it instead, for example as `lib/spooky-checkin.ts`.
3. Wrap the route's handler, keeping any existing `CRON_SECRET` check inside it:

   ```ts
   import { withCheckin } from "spooky-checkin";
   export const GET = withCheckin(async (req) => { /* the existing handler body */ });
   ```

   Each run checks in ok on a 2xx or 3xx answer and fail on a throw or a 4xx or 5xx answer. Only calls from Vercel's scheduler count.
4. Open one pull request. Say in the description that the person must add `SPOOKY_PING_URL` before merging.

## Prove it is done

- `list_jobs` shows a job for every schedule found in step 1.
- After the next run, the job's `status` is `up` and `lastCheckIn` is recent.
- Report the pull request links. Spooky decides when the job counts as watched.

## Rules

- Never print, copy or commit the ping link or any secret.
- Pull requests only. Never merge.
- Never delete a job, a schedule or a workflow.
