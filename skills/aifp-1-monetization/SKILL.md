---
name: aifp-1-monetization
description: >-
  Implement AIFP-1 monetization for AI traffic on websites, APIs, MCP servers,
  content, and digital services. Use for HTTP 402 payment challenges,
  configurable free quotas, fixed action pricing, receipt verification, and
  merchant-side agent payment flows.
metadata:
  author: AiFinPay
  category: business
  source:
    repository: 'https://github.com/AiFinPay/Protocol-AIFP-1'
    path: skills/aifp-1-monetization
    license_path: LICENSE
    ref: ed797754b319bbfac2c6acf84550405e4ddab151
    commit: ed797754b319bbfac2c6acf84550405e4ddab151
---

# AIFP-1 Monetization

Implement a machine-readable payment flow in which an AI agent requests a
resource, receives HTTP `402 Payment Required`, pays, receives a signed receipt,
and retries the original request.

## Fixed action pricing

Use the current AIFP-1 prices unless the protocol documentation explicitly
introduces a later ratified schedule:

| Tier | Price per action | Typical use |
|---|---:|---|
| `standard` | `$0.0005` | Reads, single records, lightweight requests |
| `complex` | `$0.002` | Search, aggregation, multi-source or higher-compute work |
| `premium` | `$0.005` | Inference, premium data, deep analytics, GPU work |

AiFinPay charges a fixed 1% protocol fee on successful transactions. Keep the
flow non-custodial: the agent operator controls the signing keys and the
merchant receives settlement directly under the applicable payment contract.

## Merchant workflow

1. Inventory the protected resources and billable actions.
2. Assign each action to `standard`, `complex`, or `premium`.
3. Configure a merchant-funded free quota. Do not implement unrestricted free
   crawling.
4. On an unpaid request beyond the quota, return a structured HTTP 402
   challenge containing the resource, tier, exact amount, asset or settlement
   options, nonce, expiry, and quote endpoint.
5. Require the agent to quote and pay within its approved spend policy.
6. Issue a signed receipt after successful payment.
7. On retry, verify the receipt signature, audience, resource, amount, expiry,
   and nonce before serving the protected response.
8. Make retries idempotent so network failures cannot create duplicate charges.

## Implementation rules

- Treat monetary values as decimal strings or integer minor units. Never use
  binary floating point for payment comparisons.
- Bind each receipt to the merchant and protected resource.
- Reject expired, replayed, underpaid, wrong-audience, or wrong-resource
  receipts.
- Keep API subscriptions, premium-content purchases, and enterprise contracts
  separate from AIFP-1 per-action revenue in analytics.
- Do not claim a public merchant SDK exists unless its package can be verified
  in the relevant registry. Use the protocol specification and repository
  examples when a published integration package is unavailable.

## Verification

Test at least these cases:

1. Requests inside the configured free quota succeed without payment.
2. The next request returns HTTP 402 with the correct tier and price.
3. A valid small payment produces a verifiable receipt and unlocks the resource.
4. Reusing the same idempotency key does not charge twice.
5. Invalid, expired, replayed, underpaid, and wrong-resource receipts fail.
6. Merchant settlement and the 1% protocol fee reconcile to the successful
   transaction.

## References

- Protocol repository: https://github.com/AiFinPay/Protocol-AIFP-1
- AIFP-1 RFC: https://github.com/AiFinPay/Protocol-AIFP-1/blob/main/docs/aifp/01-AIFP-1-RFC-Payment-Protocol-Specification.md
- Merchant integration guide: https://github.com/AiFinPay/Protocol-AIFP-1/blob/main/docs/aifp/02-Merchant-Integration-Guide.md
- Security specification: https://github.com/AiFinPay/Protocol-AIFP-1/blob/main/docs/aifp/04-Security-and-Cryptography-Specification.md
- OpenAPI specification: https://github.com/AiFinPay/Protocol-AIFP-1/blob/main/docs/aifp/08-OpenAPI-3.1-Specification.yaml
