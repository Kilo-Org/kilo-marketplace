---
name: heygrc-compliance-review
description: >
  Set up and run heyGRC compliance review on a repository's pull requests.
  Use when the user wants GRC or security compliance review of their code
  changes against ISO 27001, SOC 2, GDPR, DORA, NIS 2, or the EU AI Act,
  including installing the heyGRC GitHub App, configuring the company
  profile and frameworks as code, and choosing how often reviews run.
---

# heyGRC compliance review

heyGRC reviews every pull request for governance, risk, and compliance, grounded in your company
profile and the frameworks you must comply with (ISO 27001, SOC 2, GDPR, the EU AI Act, DORA, NIS 2,
and more). Think of it as a code reviewer, but for compliance obligations instead of bugs.

On each review it posts three things:

- **Inline findings** on the exact lines that touch an obligation, each with a control reference and
  a short reason, as resolvable review threads.
- **A neutral check run.** heyGRC never fails a check or blocks a merge; it informs, it does not gate.
- **One sticky summary comment per PR**, updated in place instead of piling up new comments.

Public repositories are always free. Private repos are free up to 25 reviews per month; claiming your
install starts a 14-day unlimited-private trial, after which on-demand private reviews are billed
$0.49 each.

## Important: heyGRC runs as a GitHub App, not from this machine

This plugin does not review code locally. The review runs server-side once the heyGRC GitHub App is
installed on the repository. Your job (and this skill's job) is to get it installed and configured.
The one-click install is an account-owner action that no agent or API can do for the user, so hand
them the install link and let them click it.

Full step-by-step instructions live in [SETUP.md](SETUP.md).

## Setup flow

**1. Install the GitHub App (the user clicks this once).**
Send them the install link matching the tool you are running in (you know which one you are):

| You are running in | Send this link |
|------|----------|
| Claude Code | `https://github.com/apps/heygrc/installations/new?via=claude-plugin` |
| Codex CLI | `https://github.com/apps/heygrc/installations/new?via=codex-cli` |
| Cursor | `https://github.com/apps/heygrc/installations/new?via=cursor` |
| GitHub Copilot CLI | `https://github.com/apps/heygrc/installations/new?via=copilot-cli` |
| Gemini CLI | `https://github.com/apps/heygrc/installations/new?via=gemini-cli` |
| Anything else | `https://github.com/apps/heygrc/installations/new?via=agent-plugin` |

Choose the org or account, select the specific repositories, and Install. heyGRC asks only for
read-only Contents and metadata, plus read + write on Checks and Pull requests. A bare install already
reviews PRs with default frameworks under the Free-plan limits, before any account exists.

**2. Get a review.**
Open a pull request, or comment `/heygrc` on an existing one (the commenter must be an Owner, Member,
or Collaborator on the repo). heyGRC posts its findings, check run, and sticky summary.

**3. Claim and configure (optional, sharpens every review).**
Have the user sign in at https://app.heygrc.com to claim the install (starts the trial) and create an
API key under Settings → API keys. The key is a `hgrc_…` token shown once; store it as
`HEYGRC_API_KEY` and send it only in the `Authorization` header.

Then configure the company context and frameworks as code with a single call. The `profile` is
free-form JSON: the more relevant it is (what they build, the data they handle, hosting, obligations),
the sharper the reviews.

```bash
curl -X PUT https://api.heygrc.com/v1/config \
  -H "Authorization: Bearer $HEYGRC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "company": "Acme Inc",
      "product": "B2B SaaS for invoice automation",
      "data_handled": "customer PII, payment metadata, uploaded documents",
      "hosting": "EU, AWS eu-central-1",
      "compliance_posture": "pursuing SOC 2 and ISO 27001; ships an AI feature"
    },
    "frameworks": ["ISO_27001", "SOC_2", "GDPR", "EU_AI_ACT"]
  }'
```

A `200 {"ok": true, …}` means it is configured. Read it back any time with
`GET https://api.heygrc.com/v1/config`.

**4. Choose the review cadence** (default is `auto`). Set it in the console, per org or per repo:

| Mode | Behavior |
|------|----------|
| `auto` | Reviews every PR when it is opened, reopened, or pushed to. |
| `auto_once` | Reviews on open / reopen only, not on every new commit. |
| `mention_only` | Stays silent until someone comments `/heygrc` on a PR. |

## Reference

- Setup guide: https://docs.heygrc.com/docs/setup-with-an-agent
- GitHub App permissions: https://docs.heygrc.com/docs/github-app-permissions
- Pricing and plans: https://docs.heygrc.com/docs/pricing-and-plans
- API reference and framework catalog: https://docs.heygrc.com/docs/api-reference
