---
name: mailtrap-managing-contacts
description: Manage email contacts, lists, and segments via the Mailtrap Contacts API. Use when importing contacts, creating contact lists, segmenting audiences, or syncing contacts from a CRM.
license: MIT
metadata:
  category: business-marketing
  author: mailtrap
  source:
    repository: https://github.com/mailtrap/mailtrap-skills
    path: skills/managing-contacts/SKILL.md
---

# Managing Contacts with Mailtrap

This skill covers managing email contacts, lists, and segments via the Mailtrap Contacts API.

## When to Use This Skill

- Importing or syncing contacts from a CRM or database
- Creating and managing contact lists for bulk sending
- Segmenting audiences for targeted email campaigns
- Adding or updating individual contacts programmatically

## Creating a Contact

```javascript
const response = await fetch("https://mailtrap.io/api/contacts", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.MAILTRAP_API_TOKEN}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    email: "user@example.com",
    first_name: "Jane",
    last_name: "Doe",
    list_ids: ["your-list-id"],
  }),
});
```

## Managing Lists

Create lists in the Mailtrap dashboard under Contacts → Lists, then reference list IDs when adding contacts via the API.

## Related Skills

`mailtrap-sending-emails`, `mailtrap-authorizing-api-requests`
