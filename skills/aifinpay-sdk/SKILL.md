---
name: aifinpay-sdk
description: >-
  Integrate non-custodial payments into AI agents with the AiFinPay Node SDK.
  Use for x402 or AIFP-1 paid API calls, provider payments, agent wallets, spend
  limits, receipts, and pay-per-call workflows.
metadata:
  author: AiFinPay
  category: business
  source:
    repository: 'https://github.com/AiFinPay/sdk'
    path: skills/aifinpay-sdk
    license_path: LICENSE
    ref: 68a1865123065eb13ea43c83b3bb056613f15088
    commit: 68a1865123065eb13ea43c83b3bb056613f15088
---

# AiFinPay SDK

Use the stable `@aifinpay/agent` package to give an AI agent a locally
controlled wallet and the ability to pay for APIs, data, content, inference,
and other machine services.

## Workflow

1. Inspect the project runtime and package manager.
2. Install the stable package:

   ```bash
   npm install @aifinpay/agent
   ```

3. Use the current chain-opaque API for new integrations:

   ```ts
   import { AiFinPayAgent } from "@aifinpay/agent";

   const agent = await AiFinPayAgent.new({
     budgetCaps: {
       per_call_usd: 0.50,
       daily_usd: 5,
     },
   });

   const response = await agent.call({
     provider: "exa",
     body: { query: "what is x402" },
   });

   if (!response) throw new Error("AiFinPay call returned no response");
   const data = await response.json();
   ```

4. For an AIFP-1 gateway URL, use the paid-fetch surface:

   ```ts
   const response = await agent.fetchPaid(
     "https://gateway.aifinpay.io/merchant/resource",
   );
   ```

5. Persist the agent secret using the application's existing secret manager.
   Never print, commit, or send a recovery secret to a remote service.
6. Return the transaction reference or receipt with the application result so
   operators can reconcile paid calls.

## Payment safety

- Set both per-call and daily limits before enabling autonomous payments.
- Obtain explicit user confirmation before a paid call or transfer unless the
  user has already approved a specific budget and scope.
- Quote or preview a payment before execution when the chosen flow supports it.
- Reject unknown providers, unexpected chains, and prices above the approved
  cap.
- Keep signing local. AiFinPay is non-custodial; private keys must remain under
  the agent operator's control.
- Use idempotency keys for retried payment requests.

## Verification

After integration:

1. Run the project tests and the SDK tests relevant to the changed flow.
2. Verify wallet creation without funding it.
3. Verify a quote or dry-run path before making a real payment.
4. For a real payment, use a small approved amount and confirm the returned
   receipt or transaction reference.

## References

- SDK source and examples: https://github.com/AiFinPay/sdk
- Node package: https://www.npmjs.com/package/@aifinpay/agent
- MCP package: https://www.npmjs.com/package/@aifinpay/mcp
- AIFP-1 protocol: https://github.com/AiFinPay/Protocol-AIFP-1
- Product site: https://aifinpay.io
