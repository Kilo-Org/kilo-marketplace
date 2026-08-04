---
title: dg api asset get
triggers:
  - "details about a specific asset"
---

```bash
dg api asset get <ASSET_KEY>
```

For prefixed asset keys, use slash-separated syntax: `dg api asset get my_prefix/my_asset`.

`--status` — includes materialization status information. Not included by default as it requires additional API calls.
