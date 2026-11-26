---
name: gumlet-channel-viewer
description: >-
  List, invite, and remove viewers for members-only Gumlet video channels using
  the CLI. Requires an authenticated Gumlet CLI.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-channel-viewer
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

```sh
gumlet video channel viewer list --workspace-id WORKSPACE_ID -o table
gumlet video channel viewer invite --workspace-id WORKSPACE_ID --viewers-file ./viewers.json
gumlet video channel viewer remove --workspace-id WORKSPACE_ID \
  --emails one@example.com,two@example.com
```

Use the video workspace ID. For invitations, provide a JSON array of 1–200
objects with `email` and `name`, or pass `--viewers-file -` to read from stdin.
For removal, specify up to 200 email addresses. Verify the workspace and
recipients before inviting or removing viewers. CSV is not supported.

For pagination, use `--page-number` (starting at 1) or `--next-page-token`
from the last JSON response, and optionally `--page-size` (1–100).
