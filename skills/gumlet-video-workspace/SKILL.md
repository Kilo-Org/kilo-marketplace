---
name: gumlet-video-workspace
description: >-
  Manage Gumlet video workspaces and their folders using the Gumlet CLI. Use
  this skill to list, get, create, update, or delete workspaces and folders, and
  to move assets into or out of folders. Requires the Gumlet CLI to be installed
  and authenticated via `gumlet login`.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-video-workspace
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## List all workspaces

```sh
gumlet video workspace list
gumlet video workspace list --output table
```

## Get details of a workspace

```sh
gumlet video workspace get --workspace-id <id>
```

## Create a new workspace

```sh
gumlet video workspace create --name "My Workspace"
```

## Rename a workspace

```sh
gumlet video workspace update --workspace-id <id> --name "New Name"
```

## Delete a workspace

```sh
gumlet video workspace delete --workspace-id <id>
```

## Manage folders

Replace `WORKSPACE_ID`, `PARENT_ID`, and `FOLDER_ID` with the IDs from your account.

```sh
gumlet video workspace folder create --workspace-id WORKSPACE_ID --name "Clips" --parent-id PARENT_ID
gumlet video workspace folder list --workspace-id WORKSPACE_ID --parent-id null
gumlet video workspace folder get --workspace-id WORKSPACE_ID --folder-id FOLDER_ID
gumlet video workspace folder update --workspace-id WORKSPACE_ID --folder-id FOLDER_ID --name "Clips" --root
gumlet video workspace folder update --workspace-id WORKSPACE_ID --folder-id FOLDER_ID --asset-ids asset_1,asset_2
gumlet video workspace folder remove-assets --workspace-id WORKSPACE_ID --asset-ids asset_1,asset_2
gumlet video workspace folder delete --workspace-id WORKSPACE_ID --folder-id FOLDER_ID
```

Omit `--parent-id` on create to create a root folder. On list, `--parent-id null`
filters for root folders. On update, `--root` moves a folder to the root level
and requires `--name` (use the current name to keep it). It cannot be combined
with `--parent-id`. Every update requires `--name` or `--asset-ids`.
`remove-assets` unfiles the specified assets without deleting them.

## Notes

- `-o table` shows a human-readable table. Default JSON includes the unmodified API fields and any pagination metadata in the response.
- The `--workspace-id` flag is required for `get`, `update`, and `delete`.
