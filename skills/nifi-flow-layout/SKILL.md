---
name: "nifi-flow-layout"
description: "Beautify and standardize Apache NiFi flows. Use when a user asks to arrange NiFi processors/process groups, fix crossing connections, add human comments, apply hierarchical numbering like 10/20/30.10, or create a reusable visual layout for any NiFi flow."
metadata:
  category: data
  source:
    repository: "https://github.com/AlekseiSeleznev/nifi-mcp-universal"
    path: "skills/nifi-flow-layout"
    license_path: "LICENSE"
---

# NiFi Flow Layout

Use this universal skill when any Apache NiFi flow must be readable a year later: clear names, useful comments, compact vertical flow, and connections that do not cross blocks. The skill has no environment-specific defaults: pass the NiFi URL, credentials/certificates, and target process group explicitly.

## Workflow

1. **Inspect first**
   - Read the target process group through NiFi REST.
   - Save a JSON snapshot before changing anything.
   - Run audit/dry-run before `apply`.

2. **Apply the house style**
   - Main route goes top-to-bottom.
   - Errors/logs/Teams go to a side column.
   - Connections are orthogonal: vertical/horizontal, no diagonals.
   - Connection names stay empty. Connections do not support comments in NiFi.
   - Every commentable object gets a useful human comment: processor, process group, input port, output port.
   - Names use hierarchical numbering: `10`, `20`, `30`, then `30.10`, `30.20`, then `30.20.10`. Never use `.00`.

3. **Verify visually**
   - Use Playwright when available to capture real DOM bounding boxes and a screenshot.
   - Treat route/label overlap with processors, process groups, ports, or queued boxes as a defect.

## Scripts

- `scripts/nifi_layout.py` — REST audit, dry-run, apply, geometry tests.
- `scripts/nifi_visual_check.cjs` — Playwright screenshot and DOM bounding-box capture.
- `references/layout-rules.md` — detailed rules and routing decisions.

## Typical commands

```bash
python3 scripts/nifi_layout.py \
  --base-url https://nifi.example.com/nifi-api \
  --group-id <process-group-id> \
  --cert /path/client.crt --key /path/client.key \
  --mode audit --recursive
```

```bash
python3 scripts/nifi_layout.py \
  --base-url https://nifi.example.com/nifi-api \
  --group-id <process-group-id> \
  --cert /path/client.crt --key /path/client.key \
  --mode dry-run --recursive --backup-dir ./nifi-backups
```

```bash
python3 scripts/nifi_layout.py \
  --base-url https://nifi.example.com/nifi-api \
  --group-id <process-group-id> \
  --cert /path/client.crt --key /path/client.key \
  --mode apply --recursive --backup-dir ./nifi-backups
```

## Non-negotiable visual rules from real reviews

- Verify with Playwright screenshots after changes; REST geometry is not enough.
- For dense fan-in, evaluate all useful target sides. Do not force every branch into one side or one shared point.
- If a lower source crosses the central bus/labels when entering from the left, try right-side entry, but only after checking the full candidate route for component and label blockers.
- Treat connection labels as real obstacles. Lines must not pass through `Name`/`Queued` boxes, even if they do not touch processors.
- Side handler returns should avoid queue labels between main-lane processors. Use a clear side/bottom lane instead of a short route that hides under labels.
- Side handler → output port should not add tiny doglegs when the output centerline is clear; prefer the compact side route.
- Always inspect screenshots for the whole affected area, not only one cropped defect. If the flow is larger than a viewport, pan/scroll and capture more screenshots.

## Safety rules

- Do not print secrets or certificate passphrases.
- Verify TLS certificates by default in both REST and Playwright checks. Use `--verify /path/to/ca.pem` for a private CA; use `--insecure` only as an explicit unsafe development override.
- Do not edit processor business properties unless the user explicitly asked.
- Default to `audit`/`dry-run`; use `apply` only when implementation is requested.
- Preserve revisions and current processor state; only update names, comments, positions, connection bends, labelIndex, and empty connection names.
- Before `apply`, always write a backup flow JSON using `--backup-dir`.
## PUIG hardening additions (2026-05-04)

- `scripts/nifi_layout.py` supports `--single-group`, `--group-order top-down`, `--report-dir`, `--screenshots-dir`, `--visual-gate`, and PKCS#12 auth via `--p12`.
- Apply mode is state-preserving by default: processor/port metadata updates do not stop running components; connection updates first try without stopping and only retry by stopping the two endpoint components when the connection queue is empty.
- `scripts/nifi_visual_check.cjs` supports `--tile-grid CxR` and `--tile-dir` for large-canvas evidence.
- Dense fan-in, same-column side chains, right-column handler returns, hard label packing, 12px visual label/component clearance, and 32px visual line spacing were tuned on the PUIG SAP OData → 1C:UT canvas to prevent merged wires, processor overlaps, queued-label overlaps, and near-touching lines.
- Treat visual X/T line crossings as hard defects; use wider bus lanes instead of ambiguous intersections.
- Non-adjacent segments of the same connection must also keep wide spacing; self-overlapping U-turns are defects.
