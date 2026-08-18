---
name: upstash-cli
description: >-
  Run the Upstash CLI (`upstash`) against the Upstash Developer API for Redis,
  Vector, Search, QStash, and teams. Use when listing or managing databases,
  backups, vector/search indexes, QStash instances, team members, stats, or any
  non-interactive Upstash automation with JSON output and terminal commands.
metadata:
  category: development
  author: upstash
  source:
    repository: 'https://github.com/upstash/skills'
    path: skills/upstash-cli
    license_path: LICENSE
    ref: main
    commit: fb4e6019638d5746b86a54f1bb7144dbb324480a
---

The Upstash CLI (`upstash`) manages Upstash services via the Upstash Developer API. All commands are non-interactive and emit JSON on stdout. Errors go to stderr as `{ "error": "..." }` with exit code `1`.

## Install

```bash
npm i -g @upstash/cli
```

## Authentication

Recommended: run `upstash login` once per machine. Prompts for email and a Developer API key (create one at https://console.upstash.com/account/api), verifies them, and saves to `~/.config/upstash/config.json`.

```bash
upstash login
```

Alternatives — env vars (also auto-loaded from a `.env` in cwd), or `--email` / `--api-key` inline, or `--env-path <path>` to point at a specific `.env`:

```bash
export UPSTASH_EMAIL=you@example.com
export UPSTASH_API_KEY=your_api_key
```

Precedence: flags > env vars > `.env` > saved config. Prefer a **read-only** API key for agents when possible — mutations fail at the API, the same way they would in the console.

## Resource ID flags

| Flag | Products |
|------|----------|
| `--db-id <id>` | Redis |
| `--index-id <id>` | Vector, Search |
| `--qstash-id <id>` | QStash |
| `--team-id <id>` | Team |

## Redis

```bash
upstash redis list
upstash redis get --db-id <id> [--hide-credentials]
upstash redis create --name <name> --region <region> [--read-regions <r1> <r2>]
upstash redis delete --db-id <id> [--dry-run]
upstash redis rename --db-id <id> --name <new-name>
upstash redis reset-password --db-id <id>
upstash redis stats --db-id <id>

upstash redis enable-tls --db-id <id>
upstash redis {enable,disable}-eviction --db-id <id>
upstash redis {enable,disable}-autoupgrade --db-id <id>
upstash redis change-plan --db-id <id> --plan <free|payg|pro|paid>
upstash redis update-budget --db-id <id> --budget <cents>
upstash redis update-regions --db-id <id> --read-regions <r1> <r2>
upstash redis move-to-team --db-id <id> --team-id <id>
```

Regions — AWS: `us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`, `ca-central-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `sa-east-1`, `ap-south-1`, `ap-northeast-1`, `ap-southeast-1`, `ap-southeast-2`, `af-south-1`. GCP: `us-central1`, `us-east4`, `europe-west1`, `asia-northeast1`.

### Redis backups

```bash
upstash redis backup list --db-id <id>
upstash redis backup create --db-id <id> --name <name>
upstash redis backup delete --db-id <id> --backup-id <id> [--dry-run]
upstash redis backup restore --db-id <id> --backup-id <id>
upstash redis backup {enable,disable}-daily --db-id <id>
```

### Redis exec (REST, not the Developer API key)

```bash
upstash redis exec --db-url <url> --db-token <token> SET key value
upstash redis exec --db-url <url> --db-token <token> --json '["SET","key","value"]'
```

`--db-url` / `--db-token` fall back to `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN`. Get both from `endpoint` and `rest_token` in `upstash redis get --db-id <id>`.

## Team

```bash
upstash team list
upstash team create --name <name> [--copy-cc]
upstash team delete --team-id <id> [--dry-run]
upstash team members --team-id <id>
upstash team add-member --team-id <id> --member-email <email> --role <admin|dev|finance>
upstash team remove-member --team-id <id> --member-email <email> [--dry-run]
```

## Vector

```bash
upstash vector list
upstash vector get --index-id <id>
upstash vector create --name <name> --region <region> --similarity-function <fn> --dimension-count <n> [--type payg] [--index-type <type>] [--embedding-model <m>] [--sparse-embedding-model <m>]
upstash vector delete --index-id <id> [--dry-run]
upstash vector rename --index-id <id> --name <new-name>
upstash vector reset-password --index-id <id>
upstash vector set-plan --index-id <id> --plan <free|payg|fixed>
upstash vector transfer --index-id <id> --target-account <id>
upstash vector stats                             # aggregate across all indexes
upstash vector index-stats --index-id <id> [--period <1h|3h|12h|1d|3d|7d|30d>]
```

Regions: `eu-west-1`, `us-east-1`, `us-central1`. Similarity: `COSINE`, `EUCLIDEAN`, `DOT_PRODUCT`. Index types: `DENSE`, `SPARSE`, `HYBRID`. Dense models: `BGE_SMALL_EN_V1_5`, `BGE_BASE_EN_V1_5`, `BGE_LARGE_EN_V1_5`, `BGE_M3`. Sparse models: `BM25`, `BGE_M3`. For `HYBRID` with managed embeddings, set `--dimension-count 0`.

## Search

```bash
upstash search list
upstash search get --index-id <id>
upstash search create --name <name> --region <region> --type <free|payg|fixed>
upstash search delete --index-id <id> [--dry-run]
upstash search rename --index-id <id> --name <new-name>
upstash search reset-password --index-id <id>
upstash search transfer --index-id <id> --target-account <id>
upstash search stats
upstash search index-stats --index-id <id> [--period <1h|3h|12h|1d|3d|7d|30d>]
```

Regions: `eu-west-1`, `us-central1`.

## QStash

```bash
upstash qstash list                              # run first; maps region → id
upstash qstash get --qstash-id <id>
upstash qstash rotate-token --qstash-id <id>
upstash qstash set-plan --qstash-id <id> --plan <paid|qstash_fixed_1m|qstash_fixed_10m|qstash_fixed_100m>
upstash qstash stats --qstash-id <id> [--period <1h|3h|12h|1d|3d|7d|30d>]
upstash qstash ipv4                              # CIDR blocks for allowlisting
upstash qstash move-to-team --qstash-id <id> --target-team-id <id>
upstash qstash update-budget --qstash-id <id> --budget <dollars>    # 0 = no limit
upstash qstash {enable,disable}-prodpack --qstash-id <id>
```

## Conventions

- Pipe any output to `jq` for field extraction, e.g. `upstash redis list | jq '.[].database_id'`.
- Use `--dry-run` first on any `delete` or `remove-member`.
- Use `--hide-credentials` on `redis get` when the password isn't needed.
