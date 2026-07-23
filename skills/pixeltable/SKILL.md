---
name: pixeltable
description: >
  Build multimodal AI applications with Pixeltable — declarative tables replace
  LangChain + pandas + vector DB with one system. Automates chunking, embedding,
  retrieval, tool-calling agents, and 25+ AI provider integrations (OpenAI,
  Anthropic, Gemini, etc.) via computed columns that run on insert. Use when
  building RAG pipelines, processing images/video/audio/documents, orchestrating
  LLM inference, or deploying agents with persistent memory. Covers incremental
  computation, version control, similarity search, the `pxt` CLI (inspect,
  debug, serve, deploy), FastAPI serving, and production patterns. Do NOT use
  for general Python or direct PostgreSQL administration.
license: Apache-2.0
metadata:
  author: Pixeltable
  version: 2.5.5
  type: documentation
  executes-code: false
  category: data
  tags:
    - multimodal
    - ai
    - data
    - tables
    - embeddings
    - rag
    - udf
    - video
    - audio
    - images
    - documents
    - agents
    - tools
    - fastapi
    - declarative
    - computed-columns
    - vector-search
  documentation: 'https://docs.pixeltable.com/'
  support: 'https://github.com/pixeltable/pixeltable/discussions'
  priority: 6
  pathPatterns:
    - '**/*.py'
  importPatterns:
    - pixeltable
    - import pixeltable as pxt
    - from pixeltable
  bashPatterns:
    - '^\s*pxt(?:\s|$)'
  promptSignals:
    phrases:
      - pixeltable
      - computed column
      - embedding index
      - add_embedding_index
      - create_view
      - document_splitter
      - invoke_tools
      - pxt serve
      - pxt shell
      - pxt errors
      - pxt dashboard
    minScore: 6
  source:
    repository: 'https://github.com/pixeltable/pixeltable-skill'
    path: skills/pixeltable-skill
    ref: main
    commit: ec4c931a24a4b3e423b66f8dd8c381c57e2f39b1
---

## What is Pixeltable?

Open-source Python library for **declarative multimodal AI data infrastructure** — tables, computed columns, embedding indexes, and 25+ AI providers in one interface.

`pip install pixeltable` (Python >= 3.10) | [Docs](https://docs.pixeltable.com/) | [GitHub](https://github.com/pixeltable/pixeltable)

## STOP — Do NOT Use These With Pixeltable

**Pixeltable replaces the entire imperative stack you're about to reach for.** If you find yourself importing any of these, you are off-path:

1. **Do NOT use LangChain / LlamaIndex / Haystack / LangGraph** — Pixeltable has built-in document chunking (`document_splitter`), embedding indexes (`add_embedding_index`), retrieval (`.similarity()`), and tool-calling (`pxt.tools()` + `invoke_tools()`). There is zero reason to add a framework on top.
2. **Do NOT use pandas as a working data store** — Pixeltable tables ARE the store. Use `.collect().to_pandas()` only for final export/visualization, never as an intermediate.
3. **Do NOT write `for row in ...:` loops calling AI models** — wrap the call in a computed column. Pixeltable handles batching, rate limiting, caching, and retry automatically.
4. **Do NOT install a separate vector database** (Pinecone, Chroma, FAISS, Qdrant, Weaviate, pgvector) — call `t.add_embedding_index(col, embedding=fn)` and search with `.similarity()`. The index lives inside the table.
5. **Do NOT write `while not done:` agent loops** — model the agent as a table where inserting a row triggers the entire computed-column chain (LLM → tool selection → tool execution → final answer) declaratively.

See [anti-patterns.md](references/anti-patterns.md) for the full 15-bias reference with wrong/right code examples.

---

## Task Router

Jump to the right section based on what you're building:

| If the user wants to... | Read |
|--------------------------|------|
| Create tables, insert data, query | **Core Concepts** (below) and [core-api.md](references/core-api.md) |
| Add AI-powered columns (summarize, classify, embed) | **Computed Columns** (below) and [providers.md](references/providers.md) |
| Chunk documents, extract video frames, split audio | **Views and Iterators** (below) and [core-api.md → Views](references/core-api.md#views) |
| Build semantic search / embedding indexes | **Embedding Indexes** (below) and [core-api.md → Embedding Indexes](references/core-api.md#embedding-indexes) |
| Build a RAG pipeline | [workflows.md → RAG Pipeline](references/workflows.md#rag-pipeline) |
| Build a tool-calling agent | **Tool-Calling Agent Pipeline** (below) and [workflows.md → Tool-Calling Agent](references/workflows.md#tool-calling-agent-full-production-example) |
| Build an agent with persistent memory | [agents-memory-mcp.md](references/agents-memory-mcp.md) — chat history, knowledge bank, user scoping |
| Use MCP tools with an agent | [agents-memory-mcp.md → Adding MCP Tools](references/agents-memory-mcp.md#adding-mcp-tools) |
| Use `invoke_tools()` with OpenAI, Groq, Gemini, Bedrock | [agents-memory-mcp.md → Multi-Provider](references/agents-memory-mcp.md#multi-provider-invoke_tools) |
| Build a video RAG agent (video + search + agent) | [video-rag-agents.md](references/video-rag-agents.md) — dedicated combined recipe |
| Spin up a quick video frame search app | **Starting a New Project** (`--template video-search`) → `pxt serve videointel` |
| Process video (frames, transcription, visual search) | [workflows.md → Video Analysis Pipeline](references/workflows.md#video-analysis-pipeline) |
| Process images (classify, tag, search) | [workflows.md → Image Classification and Search](references/workflows.md#image-classification-and-search) |
| Process audio (transcribe, summarize) | [workflows.md → Audio Transcription](references/workflows.md#audio-transcription-and-analysis) |
| Wrangle data for ML training (label, version, export) | [ml-data-pipeline.md](references/ml-data-pipeline.md) — ingest, enrich, snapshot, PyTorch export |
| Export to PyTorch, Parquet, or pandas | [ml-data-pipeline.md → Export for Training](references/ml-data-pipeline.md#export-for-training) |
| Look up structured data with `retrieval_udf` | [ml-data-pipeline.md → Retrieval UDFs](references/ml-data-pipeline.md#retrieval-udfs-for-structured-data-lookup) |
| Retry failed computed columns | **Error Handling** (below) — `recompute_columns()` |
| Use agentic patterns (chaining, routing, parallelization, eval-optimize) | [agentic-patterns.md](references/agentic-patterns.md) — 6 patterns + 2 reasoning strategies |
| Run batch processing (ingest, compute, export, exit) | [workflows.md → Batch Processing](references/workflows.md#batch-processing-pattern) |
| Configure rate limits, media storage, API keys | [core-api.md → Configuration](references/core-api.md#configuration) |
| Export to CSV, JSON, Parquet, LanceDB | [core-api.md → Export](references/core-api.md#export-csv-json-parquet-lancedb) |
| Export to SQL databases (Postgres, Snowflake, SQLite) | [core-api.md → Export to SQL](references/core-api.md#export-to-sql-databases) |
| Compare multiple AI providers | [workflows.md → Multi-Provider Comparison](references/workflows.md#multi-provider-comparison) |
| Build a FastAPI web app (hand-written endpoints) | [workflows.md → FastAPI App Pattern](references/workflows.md#fastapi-app-pattern) |
| Serve tables/queries via FastAPIRouter (v0.6+) | [workflows.md → FastAPIRouter](references/workflows.md#fastapirouter-declarative-serving-v06) and [core-api.md → Serving](references/core-api.md#serving-fastapirouter) |
| Inspect/debug/serve/deploy via CLI (`pxt ls`, `errors`, `serve`, `deploy`, `dashboard`) | [cli.md](references/cli.md) |
| Store media in Pixeltable Cloud (`pxtfs://`) | [core-api.md → Media Destinations](references/core-api.md#media-destinations-cloud-storage) |
| Write UDFs or query functions | **UDFs** / **Query Functions** (below) and [core-api.md → UDFs](references/core-api.md#udfs) |
| Write custom aggregates (`@pxt.uda`) | [core-api.md → User-Defined Aggregates](references/core-api.md#user-defined-aggregates-uda) |
| Use `pxt.tools()` and `invoke_tools()` for agents | **Tool-Calling Agent Pipeline** (below) and [core-api.md → Tools and Agents](references/core-api.md#tools-and-agents) |
| Avoid common mistakes (wrong imports, broken schemas, serialization) | **Common Pitfalls** (below) and [core-api.md → Common Pitfalls](references/core-api.md#common-pitfalls) |
| Understand what NOT to use with Pixeltable (LangChain, pandas, vector DBs) | [anti-patterns.md](references/anti-patterns.md) — 15 training-distribution biases with wrong/right code |
| Look up a specific provider's import and output shape | [providers.md → Quick Reference](references/providers.md#quick-reference) |

## Critical Warnings — Read Before Writing Code

1. **`openai.vision` does not exist** — use `openai.chat_completions` with `image_url` content blocks
2. **Cast to `pxt.String` before embedding** — use `.text.astype(pxt.String)` on AI function outputs before `add_embedding_index`
3. **`if_exists='ignore'` won't fix bugs** — if a computed column has wrong logic, you must `drop_column()` then recreate; re-running is a silent no-op
4. **Import `frame_iterator` as a function** — `from pixeltable.functions.video import frame_iterator`, NOT `from pixeltable.iterators import FrameIterator`
5. **Use `string=` keyword in similarity** — always `t.col.similarity(string=query)`, not positional

See [Common Pitfalls](#common-pitfalls) below for full details and code examples.

## Starting a New Project

Scaffold a complete project from the [Starter Kit](https://github.com/pixeltable/pixeltable-starter-kit) with `uvx pixeltable-new` (0.4.2+). Run `uvx pixeltable-new --list` first to see the options available on your installed version, then pick one. Legacy aliases (`video-intel`, etc.) still work in 0.4.2+ but prefer canonical names below.

**Application templates** — a full app (schema + API/UI) for a use case:

```bash
uvx pixeltable-new --template knowledge-base my-kb        # serving + backend: docs/images/video/audio upload, unified search + RAG Q&A
uvx pixeltable-new --template chat-agent my-agent         # serving + backend: persistent agent, durable memory, tool calling, MCP-ready
uvx pixeltable-new --template audio-transcription my-pod  # serving + backend: transcription, summarization, semantic search
uvx pixeltable-new --template video-search my-video       # serving: frames, transcription, detection, search → pxt serve videointel
uvx pixeltable-new --template media-indexing my-pipe      # batch: ingest from S3, process all modalities, export
uvx pixeltable-new --template image-dataset my-dataset    # batch: auto-annotate, curate, version, export to PyTorch
uvx pixeltable-new --template full-stack-showcase my-app  # serving + backend: complete reference app (Gemini + DETR + Whisper, React UI)
```

**Video-search quickstart:** `uv sync` → `uv run python schema.py` → `uv run pxt serve videointel` (service name is `videointel`, not `pipeline`).

**Structural patterns** — bare API/pipeline scaffolds (each template builds on one of these):

```bash
uvx pixeltable-new myapp                # serving (default): declarative API from schema.py
uvx pixeltable-new myapp --backend      # FastAPI scaffold (headless): setup_pixeltable.py + main.py
uvx pixeltable-new myapp --batch        # batch processing script with export_sql
```

Pick a fresh directory name (the generator refuses to overwrite an existing one) and follow the **Next steps** it prints. Template slugs are descriptive use-case names; if `--list` on your machine shows different names or a `--template` fetch fails (network, or a version skew between your installed `pixeltable-new` and the starter kit), use a name from `--list` or fall back to the structural pattern the template builds on — do NOT retry guessed template names.

## Core Concepts

### Tables and Column Types

```python
import pixeltable as pxt

pxt.create_dir('my_project', if_exists='ignore')

t = pxt.create_table('my_project.documents', {
    'title': pxt.String,
    'content': pxt.String,
    'image': pxt.Image,
    'video': pxt.Video,
    'audio': pxt.Audio,
    'doc': pxt.Document,
    'metadata': pxt.Json,
    'score': pxt.Float,
    'count': pxt.Int,
    'is_active': pxt.Bool,
    'created_at': pxt.Timestamp,
}, if_exists='ignore')
```

Available types: `String`, `Int`, `Float`, `Bool`, `Image`, `Video`, `Audio`, `Document`, `Json`, `Array`, `Timestamp`, `Date`, `UUID`, `Binary`. Use `pxt.Required[pxt.String]` for non-nullable.

### Tables with Auto-Generated Keys

Use `uuid7()` for auto-generated primary keys (recommended for production):

```python
from pixeltable.functions.uuid import uuid7

t = pxt.create_table('my_project.items', {
    'content': pxt.String,
    'uuid': uuid7(),           # auto-generated on insert
    'timestamp': pxt.Timestamp,
}, primary_key=['uuid'], if_exists='ignore')
```

### Inserting Data

```python
t.insert([{'title': 'Doc 1', 'content': 'Hello world', 'score': 0.95}])  # list of dicts
t.insert(title='Doc 2', content='Single row', score=0.75)                 # keyword syntax
t.insert(source='path/to/data.csv')                                       # from file
```

### Computed Columns

Auto-run on insert. Chain AI providers, UDFs, or expressions:

```python
from pixeltable.functions.openai import chat_completions

t.add_computed_column(
    summary=chat_completions(
        messages=[{'role': 'user', 'content': t.content}],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore'
)

t.add_computed_column(upper_title=t.title.upper(), if_exists='ignore')
```

### Querying

```python
results = t.select(t.title, t.score).collect()
results = t.where(t.score > 0.8).select(t.title, t.content).collect()
results = t.order_by(t.score, asc=False).limit(10).select(t.title).collect()
count = t.count()
df = t.select(t.title, t.score).collect().to_pandas()
items = list(t.select(title=t.title, score=t.score).collect().to_pydantic(MyModel))
```

### Views and Iterators

Split rows into sub-rows (chunking, frame extraction, audio splitting):

```python
from pixeltable.functions.document import document_splitter
from pixeltable.functions.video import frame_iterator
from pixeltable.functions.string import string_splitter
from pixeltable.functions.audio import audio_splitter

# Chunk documents into 300-token pieces (requires: pip install tiktoken)
chunks = pxt.create_view(
    'my_project.doc_chunks', t,
    iterator=document_splitter(t.doc, separators='token_limit', limit=300),
    if_exists='ignore'
)

# Extract video frames at 1 fps
frames = pxt.create_view(
    'my_project.video_frames', t,
    iterator=frame_iterator(t.video, fps=1.0),
    if_exists='ignore'
)

# Split text into sentences
sentences = pxt.create_view(
    'my_project.sentences', t,
    iterator=string_splitter(t.content, separators='sentence'),
    if_exists='ignore'
)

# Split audio into ~30s segments (exactly one of duration or max_size required).
# Optional: min_silence_len / silence_thresh / trim_leading_silence for speech-aware cuts;
# or max_size=24*1024*1024 for API byte budgets. Outputs: segment_start, segment_end, audio_segment.
audio_segments = pxt.create_view(
    'my_project.audio_segments', t,
    iterator=audio_splitter(
        audio=t.audio, duration=30.0, min_silence_len=0.3, trim_leading_silence=True
    ),
    if_exists='ignore'
)

# Filtered view (no iterator needed)
active = pxt.create_view(
    'my_project.active', t.where(t.is_active == True),
    if_exists='ignore'
)
```

### Embedding Indexes and Similarity Search

```python
from pixeltable.functions.huggingface import clip, sentence_transformer

embed_fn = clip.using(model_id='openai/clip-vit-base-patch32')
t.add_embedding_index('content', embedding=embed_fn, if_exists='ignore')

# Search
sim = t.content.similarity(string='search query')
results = t.order_by(sim, asc=False).limit(5).select(t.title, t.content, sim).collect()

# Image search with text (multimodal CLIP)
sim = t.image.similarity(string='a photo of a cat')
results = t.order_by(sim, asc=False).limit(5).select(t.image, sim).collect()
```

### Built-in Image and Video Functions

```python
from pixeltable.functions import image as pxt_image
from pixeltable.functions.video import extract_audio

# Image thumbnails and encoding
t.add_computed_column(
    thumbnail=pxt_image.b64_encode(
        pxt_image.thumbnail(t.image, size=(320, 320))
    ),
    if_exists='ignore'
)

# Extract audio from video
t.add_computed_column(
    audio=extract_audio(t.video, format='mp3'),
    if_exists='ignore'
)
```

### User-Defined Functions (UDFs)

`@pxt.udf` — one input row → one output; use in `add_computed_column` and agent tools.
`@pxt.uda` — many rows → one value; use in `select()` / `group_by()` queries only. See [core-api.md → UDAs](references/core-api.md#user-defined-aggregates-uda).

```python
@pxt.udf
def clean_text(text: str) -> str:
    return text.strip().lower()

@pxt.udf
def safe_length(text: str | None) -> str:
    return 0 if text is None else len(text)

t.add_computed_column(cleaned=clean_text(t.content), if_exists='ignore')
```

### Query Functions (also usable as agent tools)

```python
@pxt.query
def search_documents(query_text: str, limit: int = 10):
    sim = t.content.similarity(string=query_text)
    return t.order_by(sim, asc=False).limit(limit).select(t.title, t.content, sim)

results = search_documents('machine learning').collect()
```

## Tool-Calling Agent Pipeline

Inserting a row triggers the entire computed column chain automatically.

```python
import pixeltable as pxt
from pixeltable.functions.anthropic import messages, invoke_tools
from datetime import datetime

tools = pxt.tools(web_search, search_documents)  # @pxt.udf + @pxt.query

@pxt.udf
def assemble_context(question: str, tool_outputs: list | None, doc_context: list | None) -> str:
    tool_str = str(tool_outputs) if tool_outputs else 'N/A'
    doc_str = '\n'.join(
        f"- {item.get('text', '')}" for item in (doc_context or []) if isinstance(item, dict)
    ) or 'N/A'
    return (f"QUESTION: {question}\n\n"
            f"<tool_results>\n{tool_str}\n</tool_results>\n\n"
            f"<retrieved_documents>\n{doc_str}\n</retrieved_documents>")

agent = pxt.create_table('my_project.agent', {
    'prompt': pxt.String, 'timestamp': pxt.Timestamp,
    'system_prompt': pxt.String, 'max_tokens': pxt.Int, 'temperature': pxt.Float,
}, if_exists='ignore')

# LLM selects tools → execute tools → RAG retrieval → assemble → final answer
agent.add_computed_column(initial_response=messages(
    model='claude-sonnet-4-20250514',
    messages=[{'role': 'user', 'content': [{'type': 'text', 'text': agent.prompt}]}],
    tools=tools, tool_choice=tools.choice(required=True),
    max_tokens=agent.max_tokens,
    model_kwargs={'system': agent.system_prompt, 'temperature': agent.temperature},
), if_exists='ignore')

agent.add_computed_column(tool_output=invoke_tools(tools, agent.initial_response), if_exists='ignore')
agent.add_computed_column(doc_context=search_documents(agent.prompt), if_exists='ignore')
agent.add_computed_column(context=assemble_context(agent.prompt, agent.tool_output, agent.doc_context), if_exists='ignore')

agent.add_computed_column(final_response=messages(
    model='claude-sonnet-4-20250514',
    messages=[{'role': 'user', 'content': [{'type': 'text', 'text': agent.context}]}],
    max_tokens=agent.max_tokens,
    model_kwargs={'system': agent.system_prompt, 'temperature': agent.temperature},
), if_exists='ignore')

agent.add_computed_column(answer=agent.final_response.content[0].text, if_exists='ignore')

# Usage
agent.insert([{'prompt': 'What is quantum computing?', 'timestamp': datetime.now(),
               'system_prompt': 'You are a helpful assistant.', 'max_tokens': 1024}])
result = agent.where(agent.prompt == 'What is quantum computing?').select(agent.answer).collect()
```

## AI Provider Integrations

25+ providers in `pixeltable.functions.*` — see [providers.md → Quick Reference](references/providers.md#quick-reference) for the full table and examples.

## Import/Export

See [core-api.md → Import](references/core-api.md) and [core-api.md → Export](references/core-api.md#export-csv-json-parquet-lancedb).

## Idempotent Operations and Error Handling

CRITICAL: Always use `if_exists='ignore'` on every `create_*` and `add_*` call.

```python
# Fault-tolerant inserts
status = t.insert(rows, on_error='ignore')
# Inspect errors
t.where(t.summary.errortype != None).select(t.title, t.summary.errormsg).collect()
# Retry failed columns
t.recompute_columns(columns=['summary'], where=t.summary.errortype != None)
```

## Common Pitfalls

| # | Wrong | Correct |
|---|-------|---------|
| 1 | `openai.vision(prompt=..., image=t.image)` | `openai.chat_completions(messages=[{'role':'user','content':[{'type':'text','text':'...'}, {'type':'image_url','image_url':{'url':t.image}}]}], model='gpt-4o-mini').choices[0].message.content` |
| 2 | `from pixeltable.iterators import FrameIterator` | `from pixeltable.functions.video import frame_iterator` |
| 3 | `t.add_embedding_index('transcript', ...)` on Json col | Extract `.text.astype(pxt.String)` first, then index |
| 4 | Fix code + re-run with `if_exists='ignore'` | Must `t.drop_column('col')` then recreate — re-run is a no-op |
| 5 | `{'type':'image', 'data': t.image}` in messages | Use `{'type':'image_url', 'image_url':{'url': t.image}}` |
| 6 | `t.content.similarity(query)` (positional) | `t.content.similarity(string=query)` (keyword) |
| 7 | Schema corruption (`IntegrityError`) | Try `pxt.drop_dir('my_project', force=True)` first; last resort (dev only, manual, with backup): upgrade pixeltable, then delete only the `~/.pixeltable` directory — never in production |
| 8 | `.collect()` or `pxt.get_table()` inside `@pxt.query` | `@pxt.query` compiles the body at decoration time with expression placeholders — don't call `.collect()`, `insert()`, or reference tables that may not exist. Use a plain `def` for imperative logic |
| 9 | `'id': pxt.String` as primary key | PK columns must be non-nullable. Use `pxt.Required[pxt.String]` or `uuid7()` as a computed default |
| 10 | Module-level `Table` object used in FastAPI endpoint | `Table` objects are thread-bound. Call `pxt.get_table()` inside each endpoint function, not at module level |
| 11 | `@pxt.query` with `.select(..., sim=sim)` | Use `score=sim` — aliasing the output column `sim` breaks `.collect()` and `pxt serve` query routes |
| 12 | Returning raw `pxt.Image`/`pxt.Video` from `pxt serve` query routes | Return `b64_encode(thumbnail(...))` strings — raw media columns fail Pydantic serialization |

Full examples in [core-api.md → Common Pitfalls](references/core-api.md#common-pitfalls).

## pxt CLI (v0.6+)

Inspect, debug, and serve without Python boilerplate. Backed by a local daemon (`127.0.0.1:22089`; override `PXT_PORT`). Use `--json` for scripting; `pxt <cmd> --help` for flags — never guess.

```bash
pxt ls -l | pxt describe my_dir/my_table | pxt errors my_dir/my_table
pxt rows my_dir/my_table -n 5 | pxt shell          # many commands
pxt serve my-service --config service.toml         # HTTP API
pxt dashboard | pxt deploy production
```

SDK for pipelines; CLI for inspection, debugging, serving, and CI validation (`--dry-run --json`). Full reference: [cli.md](references/cli.md).

## Building Apps with Pixeltable

- Pixeltable IS the data layer — no ORM, no SQLAlchemy
- **Prefer `FastAPIRouter`** (v0.6+) over hand-written endpoints — `add_insert_route`, `add_query_route`, `add_delete_route` generate endpoints from tables and `@pxt.query` functions
- Use `background=True` on `add_insert_route` for long-running inserts (returns a job handle, client polls for completion)
- In `@pxt.query` functions served via `pxt serve`, alias similarity as `score=sim` (not `sim=sim`) and return thumbnails—not raw `Image` columns
- FastAPI endpoints: use `def` not `async def` (Pixeltable is synchronous)
- Business logic in `@pxt.udf` / `@pxt.query`, not in endpoint handlers
- Schema in one file, queries co-located with routes in each router file
- Insert a row → entire computed column chain runs automatically

```python
from pixeltable.serving import FastAPIRouter
import pixeltable as pxt

router = FastAPIRouter(prefix="/api/data", tags=["data"])
docs = pxt.get_table("app.documents")

router.add_insert_route(docs, path="/upload", uploadfile_inputs=["document"],
                        inputs=["timestamp"], outputs=["uuid"], background=True)
router.add_delete_route(docs, path="/delete")

@pxt.query
def list_docs():
    return docs.select(uuid=docs.uuid, name=docs.document).order_by(docs.timestamp, asc=False)

router.add_query_route(path="/list", query=list_docs, method="get")
```

Reference: [Pixeltable Starter Kit](https://github.com/pixeltable/pixeltable-starter-kit) | [workflows.md → FastAPIRouter](references/workflows.md#fastapirouter-declarative-serving-v06) | [core-api.md → Serving](references/core-api.md#serving-fastapirouter)

## Resources

- [Starter Kit](https://github.com/pixeltable/pixeltable-starter-kit) — 3 patterns (`serving`, `backend`, `batch`) + 7 templates (`knowledge-base`, `chat-agent`, `audio-transcription`, `video-search`, `media-indexing`, `image-dataset`, `full-stack-showcase`); scaffold with `uvx pixeltable-new --template <name> my-app`
- [MCP Server](https://github.com/pixeltable/mcp-server-pixeltable-developer) — Explore Pixeltable tables via MCP
- [LLM Docs](https://docs.pixeltable.com/llms-full.txt) | [llms.txt](https://www.pixeltable.com/llms.txt)

## Reference Files

| File | Coverage |
|------|----------|
| [cli.md](references/cli.md) | **`pxt` CLI** — inspect, query, debug, serve, deploy, dashboard, `--json` scripting |
| [core-api.md](references/core-api.md) | Tables, querying, views, embeddings, UDFs, **UDAs**, tools, **serving (FastAPIRouter)**, B-tree indexes, recompute, config, SQL export |
| [providers.md](references/providers.md) | Quick-reference table + full examples for all 25+ AI providers |
| [workflows.md](references/workflows.md) | RAG, video analysis, image classification, audio, multi-provider, agent, **batch processing**, FastAPI, **FastAPIRouter**, export |
| [video-rag-agents.md](references/video-rag-agents.md) | Video + transcript/frame retrieval + tool-calling agent |
| [agents-memory-mcp.md](references/agents-memory-mcp.md) | Agent with persistent memory, MCP integration, multi-provider invoke_tools |
| [ml-data-pipeline.md](references/ml-data-pipeline.md) | Ingest, enrich, version, export to PyTorch/Parquet/pandas |
| [agentic-patterns.md](references/agentic-patterns.md) | 6 architectural patterns + 2 reasoning strategies |
| [anti-patterns.md](references/anti-patterns.md) | 15 training-distribution biases LLMs bring; wrong/right code for each |
