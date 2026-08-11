# Verify the real integration

Do not claim completion after compilation, mocked responses, OAuth callback success, or Space publication alone.

## Required proof

1. Run the application or open the Space draft/public URL.
2. Start from the product's actual AI action.
3. Confirm the real AI Pass connection experience appears when authorization is needed.
4. Complete authorization with a real user wallet.
5. Observe that exactly one model request is sent for one user action. Use the browser network panel, server request log, or an existing request counter when available; do not claim stronger delivery guarantees than the evidence provides.
6. Render the real model response in the product's normal UI.
7. Confirm the authenticated connection is reusable through SDK state or the absence of another connection prompt. A second paid call requires separate approval.
8. Exercise cancellation or one understandable error path.
9. Confirm existing login and billing paths still behave as before.
10. Confirm `.aipass/config.json` contains public metadata only.
11. Confirm the same approved project grant was reused for every setup operation in the current agent conversation, without unnecessary reauthorization.
12. When persistence is implemented, confirm private app data is isolated. When shared vaults are
    implemented, confirm the SDK asks before granting access, the least-powerful permission works,
    forbidden writes fail, revocation takes effect, and a different signed-in user cannot see it.

Never initiate a paid model request, manual or automated, without separate and contemporaneous user approval for that specific action. State the selected model or variable usage basis when it is knowable; do not promise an exact final amount for usage-priced output. Device authorization is setup approval, not spend approval. One approved paid call is sufficient for completion. Run every safe local check first; if approval is absent, report "implemented and built; live wallet-funded verification pending" rather than claiming completion. Provisioning, compilation, linting, publication, and seeing the connection modal are not substitutes for the real call.

## Public configuration example

```json
{
  "schemaVersion": 1,
  "projectFingerprint": "4f23c8c2-75ee-4c7f-8762-cdb8225d7a31",
  "path": "sdk",
  "appName": "Example app",
  "clientId": "public-client-id",
  "oauthClientIdempotencyKey": "oauth-client:v1"
}
```

Never include device codes, `asg_` grants, OAuth tokens, cookies, client secrets, or provider API keys.

## Completion report

Report:

- selected path and why it was the smallest working option;
- public resource created or reused;
- files changed;
- real model call used for verification, or "not run; live wallet-funded verification pending";
- tests and local checks run;
- existing authentication, subscriptions, credits, and providers preserved;
- setup-grant status in this explicit form: "retained in agent memory; expires at [time] or the user can revoke it," unless it was actually revoked for a documented reason;
- user interaction still required, if any;
- optional hardening left for later.

Redact all credentials and token-bearing responses.

After reporting the core integration, offer at most one to three relevant options from [feature-opportunities.md](feature-opportunities.md). Offer Spaces only under the conditions in [spaces-path.md](spaces-path.md), never as a requirement for using AI Pass.
