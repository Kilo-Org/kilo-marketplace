---
name: mailtrap-sending-emails
description: Send transactional and bulk emails via Mailtrap Email API and SMTP. Use when implementing email sending features, configuring API/SMTP credentials, choosing between transactional and bulk sending, or troubleshooting delivery issues.
license: MIT
metadata:
  category: business-marketing
  author: mailtrap
  source:
    repository: https://github.com/mailtrap/mailtrap-skills
    path: skills/sending-emails/SKILL.md
---

# Sending Emails with Mailtrap

This skill covers sending transactional and bulk emails via the Mailtrap Email API and SMTP integration.

## When to Use This Skill

- Implementing email sending features (signup confirmations, password resets, notifications, invoices)
- Configuring Mailtrap Email API or SMTP credentials in an application
- Choosing between transactional and bulk sending modes
- Troubleshooting email delivery issues

## Email API vs SMTP

**Email API (recommended):** Use Mailtrap's REST API for sending. Faster, more reliable, and provides detailed delivery analytics.

**SMTP:** Use when your framework or library only supports SMTP, or when migrating from another SMTP provider.

## Sending via Email API

```javascript
const response = await fetch("https://send.api.mailtrap.io/api/send", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.MAILTRAP_API_TOKEN}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    from: { email: "hello@yourdomain.com", name: "Your App" },
    to: [{ email: recipient }],
    subject: "Your subject here",
    html: "<p>Your email content</p>",
  }),
});
```

## Sending via SMTP

Use these credentials in your SMTP configuration:

- **Host:** `live.smtp.mailtrap.io`
- **Port:** 587 (TLS) or 465 (SSL)
- **Username:** `api`
- **Password:** Your Mailtrap API token

## Transactional vs Bulk

- **Transactional:** One-to-one emails triggered by user actions (password resets, receipts). Use the `transactional` stream.
- **Bulk:** Marketing or batch emails sent to many recipients. Use the `bulk` stream.

## Best Practices

- Always verify your sending domain before going to production (see `mailtrap-setting-up-sending-domain`)
- Use the Mailtrap Sandbox for testing so emails never reach real inboxes (see `mailtrap-testing-with-sandbox`)
- Store your API token in environment variables, never hardcode it

## Related Skills

`mailtrap-authorizing-api-requests`, `mailtrap-setting-up-sending-domain`, `mailtrap-testing-with-sandbox`, `mailtrap-managing-contacts`
