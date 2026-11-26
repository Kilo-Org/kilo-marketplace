---
name: gumlet-account
description: >-
  Read current user details, organization details, audit logs, invoice history,
  and upcoming billing information using the authenticated Gumlet CLI.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-account
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## User, organization, and billing

```sh
gumlet user get
gumlet org get
gumlet billing invoice history
gumlet billing invoice upcoming
```

These commands are read-only. `org get` returns plan, billing cycle, SSO
status, and video/image plan details. Invoice history returns `stripe_invoices`
and the `unpaid_invoices` indicator. Upcoming invoice data may include current
usage and billing dates.

## Audit logs

Requires an `owner` or `admin` role.

```sh
gumlet audit-log list --start-at 2026-08-01 --end-at 2026-08-31 -o table
gumlet audit-log list --start-at 2026-08-01 --end-at 2026-08-31 \
  --user-email ops@example.com --activity-type video_uploaded,workspace_created \
  --page-number 1 --page-size 100
```

`--start-at` and `--end-at` are required dates in `YYYY-MM-DD` format.
`--page-size` accepts 10–500 (default 100). Table output omits IP addresses;
use `-o json` for full event details and pagination metadata.

Keep account, audit log, and invoice output out of shared logs.
