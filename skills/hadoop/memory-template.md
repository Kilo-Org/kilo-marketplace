# Memory Template — Hadoop

Create `~/hadoop/memory.md` with this structure:

```markdown
# Hadoop Memory

## Status
status: ongoing
version: 1.0.0
last: YYYY-MM-DD
integration: pending | done | declined

## Environment
<!-- Distribution, version, cluster count -->

## Clusters
<!-- Quick reference to cluster-specific files -->
| Name | Purpose | Notes File |
|------|---------|------------|
| prod | Production ETL | clusters/prod.md |

## Common Workflows
<!-- Jobs they run frequently, pain points -->

## Preferences
<!-- How they like to work, tools they use -->

## Notes
<!-- Things learned from conversations -->

---
*Updated: YYYY-MM-DD*
```

## Status Values

| Value | Meaning | Behavior |
|-------|---------|----------|
| `ongoing` | Still learning their setup | Gather context opportunistically |
| `complete` | Know their environment well | Work normally |
| `paused` | User said "not now" | Don't ask, work with what you have |
| `never_ask` | User said stop | Never ask for more context |

## Cluster File Template

Create `~/hadoop/clusters/{name}.md` for each cluster:

```markdown
# Cluster: {Name}

## Overview
- Distribution:
- Version:
- Nodes: X NameNodes, Y DataNodes
- Purpose:

## Key Settings
| Parameter | Value | Notes |
|-----------|-------|-------|
| dfs.replication | 3 | |
| yarn.nodemanager.resource.memory-mb | 32768 | |

## Known Issues
<!-- Recurring problems and solutions -->

## Access
<!-- How to connect, which user, etc. -->

---
*Updated: YYYY-MM-DD*
```

## Key Principles

- **No config keys visible** — use natural language descriptions
- **Learn from conversations** — don't interrogate, observe
- **Most users stay `ongoing`** — clusters evolve, keep learning
- Update `last` on each use
