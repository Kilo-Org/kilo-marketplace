---
name: gumlet-image-source
description: >-
  Manage Gumlet image sources using the Gumlet CLI. Use this skill to list all
  image sources, get details of a specific source, create a new image source
  connected to a storage backend (Amazon S3, GCS, web proxy, DigitalOcean
  Spaces, Wasabi, Azure, Cloudflare, Backblaze, etc.), update an existing
  source's configuration, or delete a source. Requires the Gumlet CLI to be
  installed and authenticated via `gumlet login`.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-image-source
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## List all image sources

```sh
gumlet image source list
gumlet image source list --output table
```

## Get details of a source

```sh
gumlet image source get --source-id <id>
```

## Create a new image source

Keep any provider credentials in a private JSON file or pipe them from a
secret store. Don't place them in command arguments or commit them.

### Amazon S3

```sh
gumlet image source add \
  --namespace mycompany \
  --type amazon \
  --config-file ./amazon-source.json
```

### Web proxy

```sh
gumlet image source add \
  --namespace mycompany \
  --type proxy \
  --config '{"whitelisted_domains":["example.com"]}'
```

### Google Cloud Storage

```sh
gumlet image source add \
  --namespace mycompany \
  --type gcs \
  --config-file ./gcs-source.json
```

### DigitalOcean Spaces

```sh
gumlet image source add \
  --namespace mycompany \
  --type dostorage \
  --config-file ./spaces-source.json
```

## Update an existing source

```sh
gumlet image source update --source-id <id> --type amazon --config-file - < ./amazon-source.json
```

## Delete a source

```sh
gumlet image source delete --source-id <id>
```

## Flags

| Flag | Required | Description |
|---|---|---|
| `--namespace` | ✅ (add only) | Subdomain (e.g. `mycompany` → `mycompany.gumlet.io`) |
| `--type` | ✅ (add/update) | Source type: `amazon`, `proxy`, `gcs`, `dostorage`, `wasabi`, `cloudinary`, `azure`, `linode`, `backblaze`, `cloudflare` |
| `--config-file` | ❌ | Read a provider JSON object from a file or `-` for stdin |
| `--config` | ❌ | Inline provider JSON object; use only for nonsensitive values |
| `--source-id` | ✅ (get/update/delete) | ID of the source |

## Notes

- Use `--output table` for a human-readable view.
- Provider JSON fields vary by source type. Use only one of `--config-file` and `--config`.
