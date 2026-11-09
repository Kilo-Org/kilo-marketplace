---
name: ukiyo-compute
description: >-
  Use when asked to rent GPUs, execute workloads, inspect rentals, or terminate
  Ukiyo compute using an authorized autonomous agent account.
metadata:
  category: development
  source:
    repository: 'https://github.com/ukiyocompute/ukiyo-skill'
    path: ukiyo-compute
    license_path: LICENSE
    ref: main
    commit: a32050f03c0b1eab3bbeb6ec82c7a1aaf2a7ecbb
---

# Ukiyo compute — Skill 1.0.2

## 1. What Ukiyo is

GPU rentals through one backend, paid from the account's credit balance. CLI
**0.2.5** is the canonical execution path; action MCP **0.2.0** is equivalent. Stay within the user's task and budget.
After funding, authorized rentals need no per-rental human approval, Telegram
navigation, or browser login. Pricing and business logic stay server-side.

## 2. Install

Require Node.js 22+, curl, shasum, and native OpenSSH. No repository is needed.
Check any existing `ukiyo` installation before replacing its launcher.

```sh
set -eu
mkdir -p "$HOME/.local/bin"
curl -fsSL https://u-kiyo.ai/releases/cli/0.2.5/ukiyo-cli-0.2.5.mjs -o "$HOME/.local/bin/ukiyo-cli-0.2.5.mjs"
(cd "$HOME/.local/bin" && printf '%s\n' '3328a07d01808f6a48343eb2af1cf86cc040f3b05b0077dc02857ec7538bee85  ukiyo-cli-0.2.5.mjs' | shasum -a 256 -c -)
chmod 700 "$HOME/.local/bin/ukiyo-cli-0.2.5.mjs"
ln -sf ukiyo-cli-0.2.5.mjs "$HOME/.local/bin/ukiyo"
export PATH="$HOME/.local/bin:$PATH"
ukiyo --version
```

Stop on checksum failure. Expected version: `0.2.5`. On Windows, follow the
[CLI installation guide](https://u-kiyo.ai/releases/cli/0.2.5/INSTALL.md). Use the CLI directly, not a
legacy Skill API wrapper.

## 3. Signup

Only if no account/credential exists. Signup requires explicit agreement to the
current [Terms](https://u-kiyo.ai/terms/) ([Privacy](https://u-kiyo.ai/privacy/)).
Agree only when the user has authorized it; never infer or auto-accept a future
version. `GET https://pay.u-kiyo.ai/api/v1/terms` returns the current version.

```sh
ukiyo signup --accept-terms 2026-10-10 --json
```

A changed Terms version makes signup fail without creating an account; report it
and ask the user. Agreement is once per account, not per rental.

No email, browser or Telegram is required. Signup stores the scoped credential
in `~/.ukiyo/credentials.json` (0600 inside a 0700 directory); output is account/key
metadata, not the secret. Preserve it. With existing credentials use
`ukiyo me --json`; do not sign up again after an authentication/network error.
`ukiyo connect` is the optional existing-human-account approval path, not a
requirement for new agents. Never give an agent an owner token.

## 4. Funding

```sh
ukiyo balance --json
```

Read `availableMinor`, `currency`, and `key.remainingBudgetMinor` before renting.
If insufficient, create one link, hand it to the payer, and recheck balance after
payment. Do not rent until credited or generate repeated funding requests.

```sh
ukiyo topup link --amount 5 --json
```

Save `checkoutUrl` and `idempotencyKey`; retry an ambiguous top-up response using
the same amount and `--idempotency-key`. Funding is a payment handoff, not browser
account login. Backend top-up limits are $5–$500; credits are non-transferable and
non-withdrawable. No signup credits are promised. Funding does not override key limits.

## 5. Find GPU

```sh
ukiyo offers --gpu RTX4090 --count 1 --json
```

Inventory is public, including before signup. Use live `id`, `gpuCount`,
`pricePerHourMinor`, and `currency`; never hardcode prices. USD minor units are
cents. CLI `--budget 5` is dollars; API/MCP `budgetMinor: 500` is cents. The backend
supplies price/runtime. The $5 examples are budgets, not hourly-price claims.

## 6. Rent

Check the billing model first:

```sh
ukiyo me --json
```

If `billing.model` is `ACCOUNT_BALANCE` and `budgetRequired` is `false`, `--budget`
is optional: the rental draws from the shared balance until terminated, and Ukiyo
stops it automatically when the balance can no longer cover it or a spending limit
is reached. Pass `--budget` anyway to cap this rental. Otherwise (`LEGACY_PREPAID`)
`--budget` is required and buys a fixed runtime.

Respect the task budget and key's per-rental, remaining-budget and concurrency
limits. Generate and save one key per intended rental before submitting:

```sh
RENT_KEY="$(node -e 'console.log(require("node:crypto").randomUUID())')"
ukiyo rent --gpu RTX4090 --count 1 --budget 5 --idempotency-key "$RENT_KEY" --wait --timeout 600 --json
```

Alternatively use `--offer OFFER_ID` instead of `--gpu/--count`. Save `offerId`,
`budgetMinor`, `idempotencyKey`, `rentalId` and `deploymentId` from the result/error.
For retries use the original `--offer`, budget and key, not a fresh selection or
new key. Wait for `status: ACTIVE`; acceptance alone does not mean usable compute.

## 7. Execute

Replace `DEPLOYMENT_ID` with the returned deployment ID:

```sh
ukiyo exec DEPLOYMENT_ID --json -- nvidia-smi
```

Use `exec` for the workload too. It reveals credentials internally, writes a
temporary 0600 key, deletes it afterward, and returns `deploymentId`, `exitCode`,
`stdout`, `stderr`. Check `exitCode`. Prefer this or MCP `run_command` over manual
credential handling. Never print API tokens/private keys or commit them; do not
put secrets in commands or transcripts.

## 8. Inspect/manage

```sh
ukiyo rental RENTAL_ID --json
ukiyo rental RENTAL_ID --wait --timeout 600 --json
ukiyo list --json
ukiyo status DEPLOYMENT_ID --json
```

Use `rentalId` for quote/failure/credit-reversal status, `deploymentId` for
exec/status/terminate. Save important outputs before `endsAt` or termination.
Prepaid runtime expires automatically; nothing renews. Account-balance rentals run
until terminated or stopped automatically for low balance or a spending limit.

## 9. Terminate

Terminate immediately when the authorized workload finishes, including after
command failure. Termination is irreversible and destroys the instance and its
data. Account balance: unused credit stays in the balance and final charges settle
a few minutes later. Prepaid: early termination gives no unused-credit return. `--yes` makes task-authorized cleanup noninteractive.

```sh
ukiyo terminate DEPLOYMENT_ID --yes --wait --json
ukiyo status DEPLOYMENT_ID --json
ukiyo balance --json
```

Require `TERMINATED`, not merely `accepted: true`. Verify balance/ledger a few
minutes later: charges for this rental only, no duplicate charge, no
voluntary-termination reversal. A rental that failed before becoming usable is not
charged. A timeout
means unresolved cleanup: preserve the ID and report it; never claim success.

## 10. Failure/retry rules

JSON stdout is machine-readable. Exit codes: 0 success, 1 runtime/API/command
failure, 2 invalid usage, 3 wait timeout. API errors preserve `error.code`,
`status`, `message`, `requestId`. Rental failure can instead return `status: FAILED`,
`failureReason`, and `credits` (exit 1 when waiting).

| Condition | Action |
| --- | --- |
| `INSUFFICIENT_BALANCE` | Check balance; create a funding link only if needed and authorized. |
| `RENTAL_LIMIT_EXCEEDED`, `KEY_BUDGET_EXCEEDED`, `CONCURRENCY_LIMIT`, `SCOPE_REQUIRED` | Respect the restriction; never bypass it using new accounts/keys or split purchases. |
| `OFFER_NOT_FOUND` / `NO_MATCHING_OFFER` | Rediscover. A changed offer is a new intent needing its own key and remaining task authorization; never silently substitute. |
| Readiness/provider/Ukiyo failure | Inspect the same rental. Backend performs full credit reversal exactly once; verify `credits.reversalStatus: SUCCEEDED` and balance before a separately authorized attempt. Never issue another reversal. |
| Command failure | Inspect exitCode/stderr; do not replace the rental. Clean up the existing deployment when finished. |
| Wait/termination timeout | Preserve IDs; resume `rental --wait` or inspect `status`. Retry termination on the same deployment if needed. Timeout never means “create another rental.” |

For ambiguous transport errors retain the original key/parameters and known IDs.
For `IDEMPOTENCY_CONFLICT`, reconcile the original intent; do not evade it with a
new key. Stop on `ACCOUNT_FROZEN` or disabled purchases/API and report the code.

## 11. CLI/MCP/API references

- CLI: `ukiyo COMMAND --help`; [release manifest](https://u-kiyo.ai/releases/latest.json).
- API: `https://pay.u-kiyo.ai/api/v1`; [live OpenAPI](https://pay.u-kiyo.ai/api/openapi.json).
- Docs: [docs.u-kiyo.ai](https://docs.u-kiyo.ai/).

MCP 0.2.0 is a local stdio server, not a hosted HTTP endpoint. Download
[the bundle](https://u-kiyo.ai/releases/mcp/0.2.0/ukiyo-mcp-0.2.0.mjs), verify against
[SHA256SUMS](https://u-kiyo.ai/releases/SHA256SUMS), and configure `node` with its
absolute path. Supply the existing scoped token through the host's private
`UKIYO_API_TOKEN` environment, never a conversation. MCP does not automatically
read CLI credentials. For a new account, use CLI signup/funding first.

| Same lifecycle | MCP tool/arguments |
| --- | --- |
| Account/balance, discovery | `get_account`, `list_gpus`, `list_offers` |
| Rent selected offer | `rent_gpu({offerId, budgetMinor: 500, idempotencyKey})` |
| Wait/inspect | `get_rental({rentalId, waitForActive: true, timeoutSeconds: 600})`, `list_deployments` |
| Execute/terminate | `run_command({deploymentId, command: "nvidia-smi"})`, `terminate_gpu({deploymentId, timeoutSeconds: 600})` |

MCP uses the same scoped permissions, balance and retry rules. Keys stay
local; termination waits for API-confirmed `TERMINATED`. No separate workflow.
