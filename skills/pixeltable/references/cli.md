# Pixeltable CLI Reference (`pxt`)

Agent-focused map of the `pxt` CLI (v0.6.5+). Official source: [platform/cli.md](https://docs.pixeltable.com/platform/cli.md). Always run `pxt <command> --help` for version-specific flags — never guess.

## Two surfaces

| Surface | Purpose | Requires |
|---------|---------|----------|
| **Catalog** | Inspect, query, mutate tables/views/dirs | `pip install pixeltable` |
| **Serve / deploy** | HTTP endpoints from tables and `@pxt.query` | `pip install 'pixeltable[serve]'` |

Verify: `pxt --help` and `pxt health`.

## Daemon

On the first catalog command, `pxt` auto-spawns a daemon at `127.0.0.1:22089` (~40 ms per command after warm-up). Override with `PXT_PORT`. Lifecycle: `pxt daemon status`, `pxt daemon stop`, `pxt daemon start`.

## Command categories

| Category | Commands |
|----------|----------|
| **Inspection** | `ls`, `describe`, `columns`, `computed`, `idxs`, `history`, `status`, `config` |
| **Query** | `rows`, `get`, `count`, `errors` |
| **Mutation** | `drop`, `rm`, `rename`, `mv`, `revert` |
| **Interactive** | `shell` |
| **Serving** | `serve`, `deploy` |
| **Lifecycle** | `daemon`, `dashboard`, `health` |

## Universal flags

| Flag | Description |
|------|-------------|
| `-h`, `--help` | Every command |
| `--json` | Machine-readable output on catalog commands, `serve`, `deploy`, `daemon status`. Not on `shell`, `dashboard`, or `daemon start`/`stop`. `health` is always JSON. |
| `-n`, `--dry-run` | Catalog mutations (`drop`, `rm`, `rename`, `mv`, `revert`). `pxt serve` accepts `--dry-run` only (long form). |
| `-f`, `--force` | Skip `[y/N]` on `drop`, `rm`, `revert`. Required in non-interactive/CI contexts. Not on `rename`/`mv`. |

## Agent workflows

| Task | Prefer CLI | Example |
|------|-----------|---------|
| Inspect catalog | `pxt ls -l`, `pxt describe`, `pxt columns --computed` | `pxt ls --json \| jq '.entries[] \| select(.kind == "table")'` |
| Debug failed columns | `pxt errors`, `pxt rows --cols` | `pxt errors my_dir/my_table --col embedding` |
| Check runtime/config | `pxt status`, `pxt config` | `pxt config --section openai` |
| Many commands in sequence | `pxt shell` | amortizes startup; errors don't kill session |
| Serve HTTP API | `pxt serve` | `pxt serve my-service --config service.toml --dry-run --json` |
| Visual inspection | `pxt dashboard` | read-only UI at daemon port |
| Production bundle | `pxt deploy <env>` | see [Deployment Overview](https://docs.pixeltable.com/howto/deployment/overview) |

**SDK vs CLI:** Use the Python SDK for pipelines (create tables, computed columns, inserts). Use CLI for inspection, debugging, serving, and CI validation.

## Quick reference

```bash
# inspect
pxt ls -l
pxt describe my_dir/my_table
pxt rows my_dir/my_table -n 5

# query / debug
pxt get my_dir/my_table 42
pxt count my_dir/my_table
pxt errors my_dir/my_table

# mutations (use -f in CI)
pxt drop my_dir/my_table -f
pxt revert my_dir/my_table --steps 3 -f

# interactive
pxt shell

# serve & deploy
pxt serve my-service --config service.toml
pxt deploy production
pxt dashboard
```

## Inspection highlights

- **`pxt ls`**: `-l` (metadata), `--counts` (row counts), `--tree`
- **`pxt describe`**: schema; `--json` returns full `get_metadata()` dict
- **`pxt computed`**: shorthand for `pxt columns --computed`
- **`pxt idxs`**: `--embedding` for embedding indexes only
- **`pxt history`**: `-n N` for last N versions (run before `revert`)
- **`pxt status`**: daemon PID, version, total errors; `--sizes` for disk usage

## Query highlights

- **`pxt rows`**: `-n N` (default 10), `--cols a,b,c`. Unstored computed columns skipped unless listed in `--cols` (forces eval).
- **`pxt get`**: PK lookup; composite PKs in declared order. Table must have a primary key.
- **`pxt errors`**: rows where stored computed columns failed; `--col NAME` to filter. Table must have a primary key.

## Mutation highlights

- **`pxt drop`**: tables/views; `--cascade` drops dependent views; use `pxt rm` for directories
- **`pxt rm`**: `-r` for recursive directory removal
- **`pxt revert`**: irreversible — run `pxt history` first

Table paths accept `my_dir/my_table` or `my_dir.my_table`.

## Scripting with `--json`

```bash
pxt ls --json | jq '.entries[] | select(.kind == "table")'
pxt get my_dir/my_table 42 --json | jq '.row'
pxt count my_dir/my_table --json | jq '.count'
pxt serve my-service --config service.toml --dry-run --json
```

## Serving (`pxt serve`)

Generates a FastAPI app with OpenAPI docs at `/docs`. Same capabilities as `FastAPIRouter` (insert, update, query, delete, background jobs). TOML field reference: [HTTP Serving Guide](https://docs.pixeltable.com/howto/deployment/serving).

### Subcommands

| Command | Description |
|---------|-------------|
| `pxt serve <service-name>` | Named service from TOML |
| `pxt serve insert` | Single insert endpoint |
| `pxt serve update` | Single update endpoint (table needs PK) |
| `pxt serve delete` | Single delete endpoint |
| `pxt serve query` | Single query endpoint |

### TOML config formats

**Preferred — `pyproject.toml`:**

```toml
[[tool.pixeltable.service]]
name = "my-service"
port = 8000

[[tool.pixeltable.service.routes]]
type = "query"
path = "/search"
query = "schema:search_docs"   # module:attribute (the module must be importable)
method = "post"

[[tool.pixeltable.service.routes]]
type = "insert"
table = "my_dir.my_table"
path = "/generate"
inputs = ["prompt"]
outputs = ["prompt", "result"]
```

**Standalone `service.toml`** (same route syntax, top-level `[[service]]` / `[[service.routes]]`):

```bash
pxt serve my-service --config service.toml
```

Query refs use **`module:attribute` colon syntax** (e.g. `schema:search_docs`), resolved at startup. The referenced module must be importable — declare it via `[tool.setuptools] py-modules = ["schema"]` in `pyproject.toml` (or otherwise put it on `sys.path`).

**Starter-kit service names** (pass as `pxt serve <service-name>`): `serving` / `media-indexing` -> `pipeline`, `video-search` -> `videointel`, `image-dataset` -> `datalab`, `knowledge-base` -> `kb`, `chat-agent` -> `agent`, `audio-transcription` -> `audiointel`, `full-stack-showcase` -> `sitewatch`.

### Single-endpoint mode (development)

```bash
pxt serve insert --table my_dir.my_table --path /generate \
  --inputs prompt --outputs prompt result --port 8000
pxt serve query --query schema:search_docs --path /search
```

### Common serve flags

| Flag | Description |
|------|-------------|
| `--host`, `--port`, `--prefix` | Override TOML bind settings |
| `--config` | Merge additional TOML file |
| `--dry-run` | Print resolved config; don't start server |
| `--json` | JSON on stdout (success) or stderr (errors) |
| `--background` | Return job handle immediately |
| `--return-fileresponse` | Return single media output as file download |

Mutually exclusive: `--background` + `--return-fileresponse`; `--export-sql-*` + `--return-fileresponse`.

### SQL export on serve routes

```bash
pxt serve insert --table my_dir.my_table --path /generate \
  --inputs prompt --outputs prompt result \
  --export-sql-db-connect 'postgresql+psycopg://user:pw@host/analytics' \
  --export-sql-table generations
```

### Deploy

```bash
pxt deploy <env>    # env name from Pixeltable config; --json on errors
```

## Known gotchas

1. **Never invent flags** — `pxt <cmd> --help` is authoritative
2. **CI mutations need `-f`** — `drop`, `rm`, `revert` refuse without a TTY
3. **Unstored computed columns** — skipped in `rows`/`get` unless `--cols` forces evaluation (may invoke LLMs)
4. **Revert is irreversible** — check `pxt history` first
5. **Serve extra** — `pip install 'pixeltable[serve]'` before `pxt serve` or `pxt deploy`

## Related references

- [core-api.md → Serving](core-api.md#serving-fastapirouter) — `FastAPIRouter` Python API
- [workflows.md → FastAPIRouter](workflows.md#fastapirouter-declarative-serving-v06) — full serving example
- [Configuration](https://docs.pixeltable.com/platform/configuration) — API keys, paths, env vars
