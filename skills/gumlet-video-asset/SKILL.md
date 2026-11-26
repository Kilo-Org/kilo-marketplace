---
name: gumlet-video-asset
description: >-
  Manage Gumlet video assets using the Gumlet CLI. Use this skill to create
  assets from URLs, list, inspect, update, manage thumbnails, delete, or recover
  assets, or to tag or delete assets in bulk. Requires the Gumlet CLI to be
  installed and authenticated via `gumlet login`.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-video-asset
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## Create an asset from a URL

```sh
gumlet video asset create --workspace-id WORKSPACE_ID \
  --input https://example.com/video.mp4 --title "Demo"
gumlet video asset create --workspace-id WORKSPACE_ID \
  --input https://example.com/video.mp4 --profile-id PROFILE_ID
```

Defaults to `--format ABR` unless `--profile-id` is set without `--format`.
Optional flags include `--format` (`ABR` or `MP4`), `--title`, `--description`,
`--profile-id`, `--playlist-id`, `--folder-id`, `--tag`, `--resolution`,
`--mp4-access`, `--audio-only`, `--enable-drm`, and `--metadata-file` (JSON
object file or `-` for stdin).

## List assets in a workspace

```sh
gumlet video asset list --workspace-id <id>
gumlet video asset list --workspace-id <id> --output table
```

### Optional filters

| Flag | Description |
|---|---|
| `--status` | Filter by status: `ready`, `processing`, `upload-pending` |
| `--tag` | Filter by tag |
| `--title` | Filter by title |
| `--folder-id` | Filter by folder ID; pass `--folder-id=` for unfiled assets |
| `--page-size` | Results per page, 1–100 |
| `--page-number` | Page number, starting at 1 |
| `--next-page-token` | Cursor from the last JSON response, instead of a page number |
| `--sort-by` | `created_at`, `uploaded_at`, `title`, `duration`, or `status` |
| `--order-by` | `asc` or `desc` |
| `--playlist-id` | Filter by playlist |

```sh
gumlet video asset list --workspace-id <id> --status ready --page-size 20 --output table
gumlet video asset list --workspace-id <id> --tag promo
```

## Get details of a single asset

Returns the full API response in JSON mode, including nested fields for the title and output URLs when available.

```sh
gumlet video asset get --asset-id <id>
```

## Update an asset

```sh
gumlet video asset update --asset-id ASSET_ID --title "New title" --description=
gumlet video asset update --asset-id ASSET_ID --metadata-file ./metadata.json \
  --call-to-actions-file ./actions.json
gumlet video asset update --asset-id ASSET_ID --remove-subtitles en,fr
```

Only supplied fields are sent. The metadata file must contain a JSON object;
the calls-to-action file must contain a JSON array of objects. Either flag
supports `-` for stdin, but both cannot read stdin at once.

## Manage thumbnails

```sh
# Upload a local image file as the thumbnail
gumlet video asset thumbnail-upload --asset-id ASSET_ID --file ./thumb.png

# Select a frame from the video (supports fractional seconds)
gumlet video asset thumbnail-select --asset-id ASSET_ID --frame-at-second 2.5
```

`thumbnail-upload` requests a presigned URL and uploads the file automatically,
returning `{"asset_id":"…","uploaded":true}` without printing the signed URL.

## Delete an asset

```sh
gumlet video asset delete --asset-id <id>
```

## Recover a deleted asset

```sh
gumlet video asset list-recoverable --workspace-id WORKSPACE_ID --page-number 1 --page-size 20
gumlet video asset recover --asset-id DELETED_ASSET_ID
```

## Tag or delete multiple assets

```sh
gumlet video asset bulk-tag --workspace-id WORKSPACE_ID --asset-ids asset_1,asset_2 \
  --add-tags featured --remove-tags draft
gumlet video asset bulk-delete --workspace-id WORKSPACE_ID --asset-ids asset_1,asset_2
```

Use either or both tag flags. Double-check the workspace and asset IDs before
bulk deletion.

## Notes

- `--workspace-id` is required for `create`, `list`, `list-recoverable`, and bulk commands.
- `--asset-id` is required for `get`, `update`, `thumbnail-upload`, `thumbnail-select`, `recover`, and `delete`.
- Use `--output table` for a human-readable view.
- Cursor pagination requires the default or `created_at` sort and no title filter. Repeat the filters and page size when passing a cursor.
