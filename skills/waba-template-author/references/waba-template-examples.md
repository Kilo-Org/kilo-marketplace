# WABA Template Examples — Reference

Worked, copy-pasteable WhatsApp template payloads grouped by Meta category.
Companion to `references/waba-template-categories.md`. Every example is a complete
**Sent `POST /v3/templates`** request body following the CreateTemplateRequest
shape. Variable placeholders use `{{1}}`, `{{2}}` in the body content, and
each variable has a named entry with `type` and `example` in `body.variables`.

> Synthetic values only — no real WABA IDs, brand names, or customer data.

## Utility

### 1. Order confirmation

Triggered by checkout. About that order. Single URL CTA bound to the order.

```json
{
  "name": "order_confirmation_v1",
  "category": "UTILITY",
  "language": "en_US",
  "body": {
    "content": "Hi {{1}}, your order #{{2}} is confirmed. We will let you know when it ships.",
    "variables": [
      { "name": "first_name", "type": "text", "example": "Jordan" },
      { "name": "order_id",   "type": "text", "example": "A1029" }
    ]
  },
  "header": { "type": "TEXT", "content": "Order #{{1}} confirmed" },
  "footer": { "content": "Reply STOP to opt out." },
  "buttons": [
    {
      "type": "URL",
      "text": "View order",
      "url": "https://example.com/orders/{{1}}"
    }
  ],
  "channels": ["whatsapp"]
}
```

Why this is approved as utility: every component refers to the order, the CTA
deep-links to that order, no promotional language, no cross-sell.

### 2. Shipping update

Triggered by carrier scan. Variables numbered 1..3 sequentially.

```json
{
  "name": "shipping_update_v2",
  "category": "UTILITY",
  "language": "en_US",
  "body": {
    "content": "Hi {{1}}, package #{{2}} is out for delivery and should arrive by {{3}}.",
    "variables": [
      { "name": "first_name",    "type": "text", "example": "Jordan" },
      { "name": "package_id",    "type": "text", "example": "A1029" },
      { "name": "delivery_eta",  "type": "text", "example": "6 PM today" }
    ]
  },
  "buttons": [
    {
      "type": "URL",
      "text": "Track package",
      "url": "https://example.com/track/{{1}}"
    }
  ],
  "channels": ["whatsapp"]
}
```

Why approved: status-only language, sample values are neutral, CTA points to the
tracking page for that specific package.

### 3. Appointment reminder

Triggered by user-booked appointment. Quick-reply buttons stay within the same
appointment — confirm or reschedule, no upsell.

```json
{
  "name": "appointment_reminder_v1",
  "category": "UTILITY",
  "language": "en_US",
  "body": {
    "content": "Hi {{1}}, this is a reminder of your appointment with {{2}} on {{3}} at {{4}}.",
    "variables": [
      { "name": "first_name",     "type": "text", "example": "Jordan" },
      { "name": "provider_name",  "type": "text", "example": "Dr. Patel" },
      { "name": "appointment_date", "type": "date", "example": "2026-05-18" },
      { "name": "appointment_time", "type": "text", "example": "10:30 AM" }
    ]
  },
  "footer": { "content": "Reply STOP to opt out." },
  "buttons": [
    { "type": "QUICK_REPLY", "text": "Confirm" },
    { "type": "QUICK_REPLY", "text": "Reschedule" }
  ],
  "channels": ["whatsapp"]
}
```

Why approved: every button action is tied to the appointment itself; no
"Book another visit" or other cross-sell.

## Marketing

### 1. Promo announcement

Business-initiated, discount code in the body. Unambiguously marketing.

```json
{
  "name": "spring_promo_v1",
  "category": "MARKETING",
  "language": "en_US",
  "body": {
    "content": "Hi {{1}}, our spring sale is on — use code {{2}} for 20% off through Sunday.",
    "variables": [
      { "name": "first_name", "type": "text", "example": "Jordan" },
      { "name": "promo_code", "type": "text", "example": "SPRING20" }
    ]
  },
  "footer": { "content": "Reply STOP to opt out." },
  "buttons": [
    {
      "type": "URL",
      "text": "Shop now",
      "url": "https://example.com/sale"
    }
  ],
  "channels": ["whatsapp"]
}
```

### 2. Re-engagement (win-back)

```json
{
  "name": "winback_30d_v1",
  "category": "MARKETING",
  "language": "en_US",
  "body": {
    "content": "Hi {{1}}, we miss you! Here is 15% off your next order with code {{2}}.",
    "variables": [
      { "name": "first_name", "type": "text", "example": "Jordan" },
      { "name": "promo_code", "type": "text", "example": "COMEBACK15" }
    ]
  },
  "buttons": [
    { "type": "QUICK_REPLY", "text": "Shop deals" },
    { "type": "QUICK_REPLY", "text": "Browse new" }
  ],
  "channels": ["whatsapp"]
}
```

### 3. Seasonal announcement (image header)

```json
{
  "name": "holiday_drop_v1",
  "category": "MARKETING",
  "language": "en_US",
  "body": {
    "content": "Hi {{1}}, our holiday collection just dropped. Take a look before it sells out.",
    "variables": [
      { "name": "first_name", "type": "text", "example": "Jordan" }
    ]
  },
  "header": {
    "type": "IMAGE",
    "content": "https://example.com/assets/holiday-2026.jpg"
  },
  "buttons": [
    {
      "type": "URL",
      "text": "See collection",
      "url": "https://example.com/holiday"
    }
  ],
  "channels": ["whatsapp"]
}
```

## Authentication

Authentication templates are submitted under Sent's `AUTHENTICATION` category.
The Cloud API-specific `OTP` button types (`COPY_CODE`, `AUTOFILL`) are
Meta-side concepts and are not part of Sent's `buttons[].type` enum
(`QUICK_REPLY | URL | PHONE_NUMBER`). At the Sent layer, model the code as a
single body variable.

### 1. One-time code

```json
{
  "name": "login_otp_v1",
  "category": "AUTHENTICATION",
  "language": "en_US",
  "body": {
    "content": "{{1}} is your verification code. For your security, do not share this code.",
    "variables": [
      { "name": "code", "type": "text", "example": "729451" }
    ]
  },
  "footer": { "content": "This code expires in 10 minutes." },
  "channels": ["whatsapp"]
}
```

### 2. Password reset confirmation (utility-shaped, plain confirmation)

If you only want a confirmation (no code), submit it as `UTILITY`:

```json
{
  "name": "password_changed_v1",
  "category": "UTILITY",
  "language": "en_US",
  "body": {
    "content": "Your account password was changed on {{1}}. If this was not you, contact support.",
    "variables": [
      { "name": "changed_at", "type": "text", "example": "Mon May 18, 10:32 AM" }
    ]
  },
  "channels": ["whatsapp"]
}
```

## Things to copy

- Variable numbering in `body.content` is always `{{1}}, {{2}}, {{3}}` in order
  of first appearance.
- `body.variables` is an array with one entry per `{{n}}`, in the same order.
  Each entry has a `name`, a `type` (`text` | `number` | `date`), and an
  `example` that matches the type.
- URL buttons take a `url`. Variables in URLs (`https://example.com/o/{{1}}`)
  reuse the body's variable ordering.
- Phone-number buttons take a `phone_number` instead of `url`.
- Footers cannot contain variables — keep compliance-only language there.
- `channels` selects the channels the template should be available on. For a
  WhatsApp-only template, use `["whatsapp"]`.
