---
name: mailtrap-testing-with-sandbox
description: Test email sending safely in development and staging using Mailtrap Sandbox. Use when setting up email testing environments, verifying email content without real delivery, or capturing test emails in CI/CD pipelines.
license: MIT
metadata:
  category: business-marketing
  author: mailtrap
  source:
    repository: https://github.com/mailtrap/mailtrap-skills
    path: skills/testing-with-sandbox/SKILL.md
---

# Testing Emails with Mailtrap Sandbox

This skill covers safe email testing in development and staging environments using Mailtrap Sandbox.

## When to Use This Skill

- Setting up email testing in local development or staging
- Verifying email content, formatting, and templates without real delivery
- Capturing emails in CI/CD pipelines
- Preventing test emails from reaching real inboxes

## How Sandbox Works

Mailtrap Sandbox captures all outgoing emails in a virtual inbox. Emails are never delivered to real recipients, making it safe to test with any email address.

## Setup

1. Create a Sandbox inbox at mailtrap.io
2. Copy the Sandbox API token from inbox settings
3. Use the Sandbox API endpoint instead of the production one:

```javascript
// Sandbox endpoint (dev/staging)
const ENDPOINT = `https://sandbox.api.mailtrap.io/api/send/${process.env.MAILTRAP_INBOX_ID}`;

// Production endpoint
const ENDPOINT = "https://send.api.mailtrap.io/api/send";
```

## Environment Separation Pattern

```javascript
const endpoint = process.env.NODE_ENV === "production"
  ? "https://send.api.mailtrap.io/api/send"
  : `https://sandbox.api.mailtrap.io/api/send/${process.env.MAILTRAP_INBOX_ID}`;
```

## Related Skills

`mailtrap-sending-emails`, `mailtrap-authorizing-api-requests`
