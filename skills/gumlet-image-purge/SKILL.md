---
name: gumlet-image-purge
description: >-
  Purge selected image paths from the Gumlet CDN cache using a source ID and the
  Gumlet CLI. Requires the Gumlet CLI to be installed and authenticated via
  `gumlet login`.
metadata:
  category: development
  author: Gumlet
  source:
    repository: 'https://github.com/gumlet/cli'
    path: skills/gumlet-image-purge
    license_path: LICENSE
    ref: main
    commit: f37718a55fe1f138f49bf25715c21f210db94ea6
---

## Purge specific image paths

```sh
gumlet image source list -o table
gumlet image purge --source-id SOURCE_ID \
  --urls "/photo.jpg,/banner.png"
```

Both flags are required. Replace the deprecated `--subdomain` flag with the
source ID returned by `image source list`. Pass comma-separated image paths,
not full URLs, and leave out query strings and fragments. There is no
whole-source purge mode.
