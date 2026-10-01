---
name: mailtrap-setting-up-sending-domain
description: Verify a sending domain in Mailtrap for production email delivery. Use when setting up DNS records for email sending, configuring SPF, DKIM, and DMARC, or troubleshooting domain verification issues.
metadata:
  category: business
  author: mailtrap
  source:
    repository: https://github.com/mailtrap/mailtrap-skills
    path: skills/setting-up-sending-domain
    license_path: LICENSE
    commit: 73a7113dbab938f716b8a77b3f63b83a91d8be93
---

# Setting Up a Sending Domain with Mailtrap

This skill covers verifying a sending domain in Mailtrap for production email delivery.

## When to Use This Skill

- Setting up a new sending domain for production email
- Configuring Domain Verification, DKIM, and DMARC DNS records
- Troubleshooting domain verification failures
- Improving email deliverability

## Required DNS Records

Mailtrap generates 5 DNS records to add at your domain registrar when you add a sending domain:

**Domain Verification** (CNAME) — proves ownership of the domain. This record also covers your SPF check; you do not need to add a separate SPF record.
`mt-verify.yourdomain.com` → `xxxxxxx.mailtrap.io`

**DKIM** (2× CNAME records) — cryptographically signs outgoing emails so mailbox providers can verify authenticity.
`mt-dkim1._domainkey.yourdomain.com` → `xxxxxxx.dkim.mailtrap.io`
`mt-dkim2._domainkey.yourdomain.com` → `xxxxxxx.dkim.mailtrap.io`

**DMARC** (TXT record) — sets policy for what happens when SPF/DKIM checks fail.
`_dmarc.yourdomain.com` → `v=DMARC1; p=none; rua=mailto:you@yourdomain.com`

**Custom Tracking Domain** (CNAME, optional) — enables click/open tracking under your own domain.

Exact values are generated per-account — don't hardcode these. Retrieve them via the API:
`POST https://mailtrap.io/api/accounts/{account_id}/sending_domains`
## Verification Steps

1. Add your domain in Mailtrap → Sending → Domains
2. Add the DNS records shown in the Mailtrap dashboard to your DNS provider
3. DNS propagation typically takes 24-48 hours
4. Click "Verify" in Mailtrap once records are in place

## Related Skills

`mailtrap-sending-emails`, `mailtrap-authorizing-api-requests`
