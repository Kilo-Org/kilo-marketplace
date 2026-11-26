---
name: gumlet-video-playlist
description: >-
  Manage Gumlet video playlists using the Gumlet CLI. Use this skill to list,
  create, update, or delete playlists, and to view, add, remove, or reorder
  playlist assets. Requires the Gumlet CLI to be installed and authenticated via
  `gumlet login`.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-video-playlist
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## List playlists in a workspace

```sh
gumlet video playlist list --workspace-id <id>
gumlet video playlist list --workspace-id <id> --output table
```

## Create a playlist

```sh
gumlet video playlist create --workspace-id <id> --title "Best of 2026"
gumlet video playlist create --workspace-id <id> --title "Best of 2026" --description "Top videos of the year"
```

## Update a playlist

Supply `--playlist-id` and at least one field to update. Only supplied fields change.

```sh
gumlet video playlist update --playlist-id <id> --title "Renamed Playlist"
gumlet video playlist update --playlist-id <id> --description "Updated description"
gumlet video playlist update --playlist-id <id> --channel-visibility=true
gumlet video playlist update --playlist-id <id> --channel-visibility=false
```

## Get assets in a playlist

```sh
gumlet video playlist get-assets --playlist-id <id>
gumlet video playlist get-assets --playlist-id <id> --output table
```

## Add assets to a playlist

```sh
# Add a single asset
gumlet video playlist add-asset --playlist-id <id> --asset-ids asset_abc

# Add multiple assets
gumlet video playlist add-asset --playlist-id <id> --asset-ids asset_1,asset_2,asset_3

# Add multiple assets with explicit positions
gumlet video playlist add-asset --playlist-id <id> --asset-ids asset_1,asset_2 --positions 1,2
```

> When `--positions` is provided, the count must match the number of `--asset-ids`.

## Reorder a playlist

```sh
gumlet video playlist reorder --playlist-id PLAYLIST_ID --asset-id ASSET_ID \
  --page-number 1 --page-size 20 --asset-position 0
gumlet video playlist reorder --playlist-id PLAYLIST_ID --sort-by created_at --sort-order desc
```

Choose one mode: move an asset to a zero-based position within a page, or
sort the entire playlist by `title` or `created_at` in `asc` or `desc` order.
Page numbers start at 1, and page sizes can be 1–200.

## Remove assets from a playlist

```sh
gumlet video playlist remove-asset --playlist-id <id> --asset-ids asset_1,asset_2
```

## Delete a playlist

```sh
gumlet video playlist delete --playlist-id <id>
```

## Notes

- `--workspace-id` is required for `list` and `create`.
- `--playlist-id` is required for all other subcommands.
- Use `--output table` for a human-readable view.
