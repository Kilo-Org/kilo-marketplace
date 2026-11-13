---
name: sent-messaging
description: >-
  Send a message through Sent or retrieve a message and its activity history
  with the Sent MCP tools. Use for direct message operations and lifecycle
  checks; use messaging-performance-analyzer for aggregate delivery diagnosis.
metadata:
  category: development
  source:
    repository: 'https://github.com/sentdm/sent-plugin'
    path: skills/sent-messaging
    license_path: LICENSE
    ref: main
    commit: 867b6c839f6ec511e168fdfe6301af681c382dc6
---

# Sent Messaging

Operate direct message workflows with `messages.send`, `messages.get`, and `messages.activities.list`.

## Establish connection and scope

1. Let the MCP client perform OAuth 2.1/PKCE authorization. Never request, accept, print, or store tokens, API keys, authorization headers, client IDs, or secrets.
2. Surface the organization and Sender Profile selected by the active connection before a mutation. If the client context does not expose both, use `sent-account-readiness` to inspect the authorized scope before continuing.
3. Reauthorize in the client when the requested organization or Sender Profile differs from the active grant. Do not simulate a scope switch with payload fields.
4. Minimize sensitive output. Mask phone numbers where practical and do not repeat message bodies after the operator has reviewed them.

If MCP is unsupported or authorization fails, keep the skill usable for payload planning. Explain that execution requires a compatible client or reauthorization; never ask the user to paste a credential.

## Inspect a message

- Use `messages.get` for the current record when a message identifier is known.
- Use `messages.activities.list` for lifecycle events and delivery evidence.
- State that an accepted or queued send is not proof of delivery. Report delivered only when the returned state or activity establishes delivery.
- Return identifiers, timestamps, and status evidence needed to answer the question, masking recipient data and omitting the message body unless it is necessary.

For aggregate trends, funnels, or root-cause analysis across many delivery records, hand off to `messaging-performance-analyzer`.

## Prepare a send

1. Resolve the intended channel, Sender Profile, recipient, template or content, variables, scheduling inputs, and any idempotency field the tool supports. Do not invent missing values.
2. For a high-volume send, use `sent-account-readiness` to check `balance.get` before preparing the mutation. Stop if the available balance or account readiness is insufficient or unclear.
3. Build the exact `messages.send` arguments without calling the tool.
4. Show a payload preview that includes the selected organization, Sender Profile, channel, exact destination, content or template identifier, variables, and scheduling/idempotency inputs. Show sensitive content once only; mask it where the operator can still verify the target.
5. Ask for explicit confirmation for this exact payload. General approval given earlier in the conversation is not sufficient.
6. Call `messages.send` immediately after that confirmation. If any payload value, scope, or elapsed context changes, discard the confirmation and preview again.

Never call `messages.send` without the preview and explicit confirmation immediately before the call.

## Handle results and retries

- Report the message identifier and the returned acceptance state. Say "accepted" or "queued" when that is all the response establishes; do not say "delivered."
- Use `messages.get` or `messages.activities.list` when the user asks for subsequent delivery state.
- Treat every retry as a new mutation: reconstruct the payload, show a fresh preview, and obtain new explicit confirmation immediately before the retry.
- Never blindly retry an ambiguous send. If the first call times out or its outcome is unknown, inspect `messages.get` and `messages.activities.list` when an identifier exists. Without conclusive evidence, report the unknown outcome and duplication risk. Only attempt another send after the operator chooses to do so and completes a new preview and confirmation.
