---
name: gumlet-video-live
description: >-
  Manage Gumlet live streaming workspaces and assets, including stream
  lifecycle, status history, and thumbnail upload URLs. Requires an
  authenticated Gumlet CLI.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-video-live
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## Manage live workspaces

```sh
gumlet video live workspace list -o table
gumlet video live workspace create --name "Studio"
gumlet video live workspace update --live-workspace-id LIVE_WORKSPACE_ID \
  --video-workspace-id VIDEO_WORKSPACE_ID
gumlet video live workspace delete --live-workspace-id LIVE_WORKSPACE_ID
```

The update can change the name or link a video-on-demand workspace. Verify the
ID before deleting a workspace.

## Manage streams

```sh
gumlet video live asset create --live-workspace-id LIVE_WORKSPACE_ID \
  --resolution 720p --title "Demo" --orientation landscape
gumlet video live asset update --live-asset-id LIVE_ASSET_ID --start-at 2026-12-01T15:00:00Z
gumlet video live asset list --live-workspace-id LIVE_WORKSPACE_ID --status created,active -o table
gumlet video live asset get --live-asset-id LIVE_ASSET_ID -o table
gumlet video live asset start --live-asset-id LIVE_ASSET_ID
gumlet video live asset complete --live-asset-id LIVE_ASSET_ID
gumlet video live asset history --live-asset-id LIVE_ASSET_ID
gumlet video live asset delete --live-asset-id LIVE_ASSET_ID
```

Use `--page-number` and `--page-size` for numbered pages, or reuse the JSON
response's `next_page_token` as `--next-page-token`. Scheduling uses RFC 3339.
Pass `--mp4-access=true` when you want a downloadable MP4.

## Get presigned thumbnail upload URLs

```sh
gumlet video live asset thumbnail-upload-urls --live-asset-id LIVE_ASSET_ID \
  --statuses preparing,disconnected,end --output json
```

This command only returns URLs. It does not upload files. Raw JSON from live
commands can contain stream keys, ingest URLs, and presigned URLs; do not
include it in shared logs or chat. Use `-o table` for status without credentials.
