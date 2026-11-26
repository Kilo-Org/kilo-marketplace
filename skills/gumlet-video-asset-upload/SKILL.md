---
name: gumlet-video-asset-upload
description: >-
  Upload a local video file to Gumlet as a new video asset using the Gumlet CLI.
  Use this skill when you need to upload a video file from the local filesystem
  to Gumlet for transcoding and delivery. The CLI handles the two-step process
  automatically: creating the upload session and streaming the file to the
  returned pre-signed URL. A real-time progress indicator is shown during
  upload. Requires the Gumlet CLI to be installed and authenticated via gumlet
  login.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-video-asset-upload
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## Basic upload

Use a nonempty local file. Title defaults to the filename when `--title` is not provided.

```sh
gumlet video asset upload --file ./video.mp4 --workspace-id <id>
```

## Upload with metadata

```sh
gumlet video asset upload \
  --file ./video.mp4 \
  --workspace-id <id> \
  --title "Product Demo" \
  --description "Demo video for Q2 launch" \
  --format ABR \
  --tag demo,product
```

## Upload and add directly to a playlist

```sh
gumlet video asset upload \
  --file ./video.mp4 \
  --workspace-id <id> \
  --playlist-id <playlist_id>
```

## Flags

| Flag | Required | Description |
|---|---|---|
| `--file` | ✅ | Path to the local video file |
| `--workspace-id` | ✅ | Workspace (collection) ID |
| `--format` | ❌ | `ABR` (HLS + DASH) or `MP4`. Default: `ABR` |
| `--title` | ❌ | Asset title. Defaults to filename |
| `--description` | ❌ | Asset description |
| `--profile-id` | ❌ | Video profile ID |
| `--playlist-id` | ❌ | Add asset to this playlist after upload |
| `--tag` | ❌ | Comma-separated tags |

## After upload

Successful upload returns `{"asset_id":"…","uploaded":true}` by default.
Progress goes to stderr. File transfer is separate from transcoding; check processing status with:

```sh
gumlet video asset get --asset-id <returned_asset_id>
```

If file transfer fails after the asset is created, the error includes its ID. Check that asset before starting a new upload.
