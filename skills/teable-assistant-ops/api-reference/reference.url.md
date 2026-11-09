# Teable Resource URL Reference

Parse a Teable URL into its resource type + IDs, or build a URL to a resource.

A Project is the API `base`, identified by a `bse`-prefixed ID. Keep `baseId` and `/base/` in URLs and API calls.

Paths are relative — workspace links under `/base/{baseId}/...`, public shares under
`/share/{shareId}/...`; for an absolute URL, prefix the workspace origin (`PUBLIC_ORIGIN` /
`TEABLE_ENDPOINT`).

## Patterns

Build = fill the Path; parse = match a URL to its row. `[...]` = optional segment; validate
every ID against its prefix.

| Resource | Path | IDs (prefix) |
|----------|------|--------------|
| Table | `/base/{baseId}/table/{tableId}[/{viewId}]` | project `bse`, table `tbl`, view `viw` |
| Record | `/base/{baseId}/table/{tableId}[/{viewId}]?recordId={recordId}` | record `rec` — query param, never a path segment |
| Automation | `/base/{baseId}/automation/{workflowId}` | workflow `wfl` |
| Automation run | `/base/{baseId}/automation/{workflowId}?runId={runId}` | run — cuid, no prefix |
| Routine | `/base/{baseId}/routine/{routineId}` | routine `rtn` |
| Routine run | `/base/{baseId}/routine/{routineId}?runId={runId}` | run `rrn` |
| App | `/base/{baseId}/app/{appId}` | app `app` — in-platform editor, NOT the live/published app (see Caveats) |
| Shared view | `/share/{shareId}/view` | share `shr` |
| Shared project | `/share/{shareId}/base/{baseId}/table/{tableId}/{viewId}` | share `shr` |

## Parsing

Strip any leading `https://{origin}`, match the path to a row, and read IDs from the segments
in order (`recordId` only from `?recordId=`). A prefix that doesn't fit its slot means the URL
is malformed or legacy — e.g. legacy `/base/{baseId}/{tableId}/{viewId}` (no `table` keyword)
redirects to the `/table/...` form.

Example: `https://{origin}/base/bseAbc/table/tblXyz/viwQrs?recordId=rec123`
→ project `bseAbc`, table `tblXyz`, view `viwQrs`, record `rec123`.

## Caveats

Published/public app URLs are NOT constructible from `appId`: the default host embeds it
(`https://{appId}.{system-domain}`), but a custom prefix or domain, the instance-specific
`{system-domain}` suffix, and non-default deploy providers all break this — never template it.
Fetch the app (app get/list tool) and read `accessUrl` (else `systemDomainUrl` /
`customDomain` / `metaData.publicUrl` / `metaData.previewUrl`).
