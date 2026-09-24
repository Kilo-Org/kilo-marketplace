---
name: famulor-assistants-history
description: >-
  Read Famulor assistant configurations, versions, catalogs, and omnichannel
  conversation history through the restricted Assistant & History MCP profile.
  Use for reviewing assistants or finding and summarizing call, messaging, or
  email history; never use it to change resources, send messages, place calls,
  run campaigns, manage telephony, or access billing.
license: MIT
metadata:
  author: bekservice
  version: 2.0.2
  homepage: 'https://www.famulor.io'
  category: business
  source:
    repository: 'https://github.com/bekservice/Famulor-Skill'
    path: claude-store/skills/famulor-assistants-history
    ref: main
    commit: 7acc654427795caff6ab9404b3c8be16ad50e3ef
---

# Famulor Assistants & Omnichannel History

Use the OAuth-secured Famulor MCP profile at:

```text
https://app.famulor.io/mcp?profile=assistant-history
```

This marketplace profile is intentionally read-only. It exposes exactly 11 tools:

| Tool | Use |
| --- | --- |
| `list_assistants` | List assistants visible in the authenticated workspace. |
| `get_assistant` | Read one assistant's configuration. |
| `list_assistant_versions` | List saved versions for an assistant. |
| `get_assistant_version` | Read one saved assistant version. |
| `list_prompt_templates` | List available prompt templates. |
| `get_languages` | List supported language options. |
| `get_models` | List models available to the workspace. |
| `get_voices` | List available voices. |
| `list_history` | Search unified call, messaging, and email history. |
| `get_call` | Read full details for one call returned by history. |
| `get_email_history_item` | Read the full email thread for one email history item. |

## Workflow

1. Confirm which authenticated Famulor workspace the user means when it is ambiguous.
2. Use a `list_*` tool to find the exact resource or history item instead of guessing an ID.
3. Use the matching `get_*` tool when the user needs full detail.
4. Summarize only the fields returned by the server and preserve the distinction between configured values and observed history.

`list_history` is the omnichannel overview. It may include voice calls, emails, and messaging conversations from connected channels such as Instagram or Messenger. Messaging entries can be previews rather than complete chat transcripts; never claim a full conversation unless the server actually returned it. Use `get_call` for call detail and `get_email_history_item` for an email thread.

## Safety and access boundaries

- Keep every request read-only. This profile cannot create, update, delete, send, call, launch, purchase, transfer, or configure anything.
- Do not bypass the restricted profile when a user requests a write action. Explain that the installed marketplace integration supports Assistant & History review only.
- Never infer access across workspaces. OAuth scopes, workspace membership, role, plan, retention, and server-side policy remain authoritative.
- Treat transcripts, recordings, messages, emails, contacts, and customer context as personal data. Return only what is necessary for the request.
- Use live tool schemas for arguments and availability; do not invent IDs, enum values, or fields.
