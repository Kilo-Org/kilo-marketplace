---
name: mailtrap-setting-up-sending-domain
description: Verify a sending domain in Mailtrap for production email delivery. Use when setting up DNS records for email sending, configuring SPF, DKIM, and DMARC, or troubleshooting domain verification issues.
license: MIT
metadata:
  category: business-marketing
  author: mailtrap
  source:
    repository: https://github.com/mailtrap/mailtrap-skills
    path: skills/setting-up-sending-domain/SKILL.md
---

# Setting Up a Sending Domain with Mailtrap

This skill covers verifying a sending domain in Mailtrap for production email delivery.

## When to Use This Skill

- Setting up a new sending domain for production email
- Configuring SPF, DKIM, and DMARC DNS records
- Troubleshooting domain verification failures
- Improving email deliverability

## Required DNS Records

Mailtrap requires three DNS records to verify your domain:

**SPF** — Authorizes Mailtrap to send on your behalf:
**DKIM** — Signs outgoing emails cryptographically:
**DMARC** — Sets policy for failed authentication:

## Verification Steps

1. Add your domain in Mailtrap → Sending → Domains
2. Add the DNS records shown in the Mailtrap dashboard to your DNS provider
3. DNS propagation typically takes 24-48 hours
4. Click "Verify" in Mailtrap once records are in place

## Related Skills

`mailtrap-sending-emails`, `mailtrap-authorizing-api-requests`
