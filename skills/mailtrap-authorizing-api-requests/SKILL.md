---
name: mailtrap-authorizing-api-requests
description: Authenticate API requests to Mailtrap using Bearer tokens. Use when setting up Mailtrap API credentials, configuring environment variables, resolving authentication errors, or managing token scopes.
license: MIT
metadata:
  category: business-marketing
  author: mailtrap
  source:
    repository: https://github.com/mailtrap/mailtrap-skills
    path: skills/authorizing-api-requests/SKILL.md
---

# Authorizing API Requests to Mailtrap

This skill covers authenticating requests to the Mailtrap API using Bearer tokens.

## When to Use This Skill

- Setting up Mailtrap API credentials for the first time
- Configuring environment variables for API authentication
- Resolving 401 Unauthorized errors from the Mailtrap API
- Understanding token scopes for different API operations

## Authentication Method

All Mailtrap API requests use Bearer token authentication:

```javascript
headers: {
  "Authorization": `Bearer ${process.env.MAILTRAP_API_TOKEN}`,
  "Content-Type": "application/json",
}
```

## Getting Your API Token

1. Log in to mailtrap.io
2. Go to Settings → API Tokens
3. Create a new token or copy an existing one
4. Store it in your environment variables as `MAILTRAP_API_TOKEN`

## Token Scopes

- **Sending tokens:** For sending emails via the Email API
- **Sandbox tokens:** For testing via the Sandbox API (separate token per inbox)
- **Account tokens:** For managing contacts, domains, and account settings

## Best Practices

- Never hardcode tokens in source code
- Use separate tokens for production and sandbox environments
- Rotate tokens periodically and immediately if compromised
- Use environment variables or a secrets manager

## Related Skills

`mailtrap-sending-emails`, `mailtrap-testing-with-sandbox`
