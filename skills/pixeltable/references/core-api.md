# Pixeltable Core API Reference

Complete reference for table operations, querying, computed columns, views, embedding indexes, UDFs, tools, and configuration.

## Contents

- [Table Creation](#table-creation) (basic, primary key, UUID, from source)
- [Querying](#querying) (select, where, order by, aggregates, group_by, pandas, Pydantic)
- [Computed Columns](#computed-columns)
- [Views](#views) (filtered, document chunking, video frames, string splitting, audio splitting)
- [Built-in Functions](#built-in-image-functions) (image, video, string)
- [Embedding Indexes](#embedding-indexes) (add index, similarity search, distance metrics)
- [UDFs](#udfs) (basic, optional args, batch, retrieval)
- [User-Defined Aggregates (UDA)](#user-defined-aggregates-uda) (custom `@pxt.uda`, group_by, built-ins)
- [Update and Delete](#update-and-delete)
- [Table Operations](#table-operations)
- [Snapshots](#snapshots)
- [Tools and Agents](#tools-and-agents) (create tools, agent pipeline, MCP)
- [Serving (FastAPIRouter)](#serving-fastapirouter) (add_insert_route, add_update_route, add_query_route, add_delete_route, background jobs, pxt serve)
- [Export](#export-csv-json-parquet-lancedb-iceberg) (CSV, JSON, Parquet, LanceDB, Iceberg, SQL)
- [Configuration](#configuration) (API keys, config.toml, rate limiting, media destinations, pxtfs://)
- [Performance Tips](#performance-tips)

---

## Table Creation

### Basic Table

```python
import pixeltable as pxt

t = pxt.create_table('dir.table_name', {
    'col1': pxt.String,
    'col2': pxt.Int,
    'col3': pxt.Float,
    'col4': pxt.Bool,
    'col5': pxt.Image,
    'col6': pxt.Video,
    'col7': pxt.Audio,
    'col8': pxt.Document,
    'col9': pxt.Json,
    'col10': pxt.Array[(3, 4), pxt.Float],  # 3x4 float array
    'col11': pxt.Timestamp,
    'col12': pxt.Date,
    'col13': pxt.UUID,
    'col14': pxt.Binary,
}, if_exists='ignore')
```

### Table with Primary Key

```python
t = pxt.create_table('dir.table', {
    'id': pxt.Required[pxt.String],
    'data': pxt.String,
}, primary_key=['id'], if_exists='ignore')
```

### Table with Auto-Generated UUID Primary Key

Production-ready pattern using uuid7() for automatic unique IDs:

```python
from pixeltable.functions.uuid import uuid7

t = pxt.create_table('dir.items', {
    'content': pxt.String,
    'uuid': uuid7(),            # auto-generated on insert
    'timestamp': pxt.Timestamp,
}, primary_key=['uuid'], if_exists='ignore')

# No need to provide uuid when inserting
from datetime import datetime
t.insert([{'content': 'Hello', 'timestamp': datetime.now()}])
```

### Table from Data Source

```python
t = pxt.create_table('dir.from_csv', source='data.csv')
t = pxt.create_table('dir.from_parquet', source='data.parquet')
t = pxt.create_table('dir.data', source='data.csv',
    schema_overrides={'image_col': pxt.Image, 'doc_col': pxt.Document})
```

## Querying

### Select

```python
results = t.collect()                                          # all columns
results = t.select(t.col1, t.col2).collect()                  # specific columns
results = t.select(t.col1, doubled=t.col2 * 2).collect()      # with expressions
```

### Where (Filter)

```python
results = t.where(t.col2 > 10).select(t.col1).collect()
results = t.where((t.col2 > 10) & (t.col1 != 'exclude')).collect()
results = t.where(t.col1.like('%pattern%')).collect()
```

### Order By / Limit / Count / Sample

```python
results = t.order_by(t.col2, asc=False).limit(10).collect()
total = t.count()
filtered = t.where(t.score > 0.5).count()

# Pagination with offset
page2 = t.order_by(t.col2).limit(10, offset=10).collect()

# Random sample (reproducible with seed)
sample = t.sample(n=100, seed=42).select(t.col1, t.col2).collect()
```

### Aggregates and Group By

UDAs and built-in aggregates run in **queries**, not `add_computed_column`:

```python
# Global aggregate (built-in or custom @pxt.uda)
t.select(t.amount.sum()).collect()
t.select(avg_int(t.value)).collect()

# Per-group aggregation
t.group_by(t.region).select(t.region, total=t.amount.sum()).collect()
t.group_by(t.category).select(t.category, avg_val=avg_int(t.value)).collect()
```

See [User-Defined Aggregates (UDA)](#user-defined-aggregates-uda) for defining custom aggregates.

### Conversions

```python
df = t.select(t.col1, t.col2).collect().to_pandas()                           # to pandas
items = list(t.select(title=t.title, score=t.score).collect().to_pydantic(M))  # to Pydantic (names must match)
t.insert([pydantic_model_instance])                                            # insert Pydantic models
first_5 = t.head(5)

# return_rows=True: get computed columns back from insert without a follow-up query
status = t.insert([row], return_rows=True)
data = status.rows[0]  # dict with ALL columns including computed
```

## Computed Columns

```python
# Simple expression
t.add_computed_column(upper_name=t.name.upper(), if_exists='ignore')

# Using a UDF
t.add_computed_column(result=my_udf(t.input_col), if_exists='ignore')

# Using an AI provider
from pixeltable.functions.openai import chat_completions
t.add_computed_column(
    summary=chat_completions(
        messages=[{'role': 'user', 'content': t.text}],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore'
)

# Drop column
t.drop_column('column_name')

# Recompute failed or outdated columns (critical for error recovery)
t.recompute_columns(columns=['summary'])
t.recompute_columns(columns=['summary'], where=t.summary.errortype != None)
```

## Views

### Filtered View

```python
v = pxt.create_view('dir.active', t.where(t.is_active == True), if_exists='ignore')
```

### Document Chunking

```python
from pixeltable.functions.document import document_splitter

# Separators: 'token_limit', 'sentence', 'heading', 'page', or combine: 'page, sentence'
chunks = pxt.create_view('dir.chunks', t,
    iterator=document_splitter(t.doc, separators='token_limit', limit=300),
    if_exists='ignore')

# With metadata extraction and image extraction (PDF)
chunks = pxt.create_view('dir.chunks', t,
    iterator=document_splitter(t.doc, separators='page, sentence',
        metadata='title,heading,page', elements=['text', 'image']),
    if_exists='ignore')
```

### Video Frame Extraction

```python
from pixeltable.functions.video import frame_iterator

frames = pxt.create_view('dir.frames', t, iterator=frame_iterator(t.video, fps=1.0), if_exists='ignore')
# Options: fps=N, num_frames=N, keyframes_only=True
# Output columns: frame (Image), frame_idx, pos_msec, pos_frame
```

### String / Audio Splitting

```python
from pixeltable.functions.string import string_splitter
from pixeltable.functions.audio import audio_splitter

sentences = pxt.create_view('dir.sentences', t,
    iterator=string_splitter(text=t.content, separators='sentence'), if_exists='ignore')
# Exactly one of duration or max_size; optional min_silence_len / trim_leading_silence.
# Outputs: segment_start, segment_end, audio_segment
audio_segments = pxt.create_view('dir.audio_segments', t,
    iterator=audio_splitter(
        audio=t.audio, duration=30.0, min_silence_len=0.3, trim_leading_silence=True
    ), if_exists='ignore')
# Or: audio_splitter(audio=t.audio, max_size=24 * 1024 * 1024)
```

## Built-in Image Functions

```python
from pixeltable.functions import image as pxt_image

# Thumbnail generation
t.add_computed_column(
    thumb=pxt_image.thumbnail(t.image, size=(320, 320)),
    if_exists='ignore')

# Base64 encoding (useful for API responses and Anthropic vision)
t.add_computed_column(
    b64=pxt_image.b64_encode(t.image),
    if_exists='ignore')

# Combined: thumbnail + base64 (common pattern for APIs)
t.add_computed_column(
    thumbnail=pxt_image.b64_encode(
        pxt_image.thumbnail(t.image, size=(320, 320))
    ),
    if_exists='ignore')

# Base64 with explicit format
t.add_computed_column(
    png_b64=pxt_image.b64_encode(t.image, 'png'),
    if_exists='ignore')
```

## Built-in Image Functions (Additional)

```python
from pixeltable.functions.image import draw_bounding_boxes

# Draw detection results on images (pairs with DETR/YOLOX output)
t.add_computed_column(
    annotated=draw_bounding_boxes(t.image, t.detections),
    if_exists='ignore')
```

## Built-in Video Functions

```python
from pixeltable.functions.video import (
    extract_audio, resize, crop, concat_videos, concat_videos_agg,
    make_video, with_audio, pan, mix_audio, overlay_image,
)

# Extract audio track from video
t.add_computed_column(
    audio=extract_audio(t.video, format='mp3'),
    if_exists='ignore')

# Resize video
t.add_computed_column(
    resized=resize(t.video, width=640, height=480),
    if_exists='ignore')

# Crop video region
t.add_computed_column(
    cropped=crop(t.video, x=100, y=100, w=400, h=300),
    if_exists='ignore')

# Concatenate two videos (scalar UDF — fixed pair of inputs)
t.add_computed_column(
    combined=concat_videos(t.intro_video, t.main_video),
    if_exists='ignore')

# Concatenate many videos from rows (UDA — ordered by timestamp column)
frames.select(concat_videos_agg(frames.timestamp, frames.video)).collect()

# Combine a sequence of frame images into one video (UDA)
frames.select(make_video(frames.frame, fps=30)).collect()

# Replace audio track on a video
t.add_computed_column(
    with_new_audio=with_audio(t.video, t.narration),
    if_exists='ignore')

# Ken Burns pan effect on an image (creates video from still image)
t.add_computed_column(
    clip=pan(t.image, duration=5.0, zoom_start=1.0, zoom_end=1.3),
    if_exists='ignore')

# Mix (overlay) two audio tracks
t.add_computed_column(
    mixed=mix_audio(t.narration, t.background_music),
    if_exists='ignore')

# Overlay image (watermark) on video
t.add_computed_column(
    watermarked=overlay_image(t.video, t.logo, x=10, y=10),
    if_exists='ignore')
```

## Built-in String Functions

```python
from pixeltable.functions import string as pxt_str

# String length
t.add_computed_column(text_len=pxt_str.len(t.content), if_exists='ignore')
```

## Embedding Indexes

### Add Index

```python
from pixeltable.functions.huggingface import clip, sentence_transformer

# CLIP (multimodal: text + image)
embed_fn = clip.using(model_id='openai/clip-vit-base-patch32')
t.add_embedding_index('image_col', embedding=embed_fn, if_exists='ignore')

# Sentence Transformers (text)
embed_fn = sentence_transformer.using(model_id='all-MiniLM-L6-v2')
t.add_embedding_index('text_col', embedding=embed_fn, if_exists='ignore')

# Sentence Transformers (multilingual, high quality, recommended for production)
embed_fn = sentence_transformer.using(model_id='intfloat/multilingual-e5-large-instruct')
t.add_embedding_index('text_col', string_embed=embed_fn, if_exists='ignore')

# OpenAI embeddings
from pixeltable.functions.openai import embeddings
t.add_embedding_index('text_col', embedding=embeddings.using(model='text-embedding-3-small'), if_exists='ignore')
```

### Similarity Search

```python
# Text
sim = t.text_col.similarity(string='search query')
results = t.order_by(sim, asc=False).limit(10).select(t.text_col, sim).collect()

# Text with threshold filter
sim = t.text_col.similarity(string='search query')
results = t.where(sim > 0.5).order_by(sim, asc=False).limit(10).select(t.text_col, sim).collect()

# Image with text (multimodal)
sim = t.image_col.similarity(string='a red car')
results = t.order_by(sim, asc=False).limit(5).select(t.image_col, sim).collect()

# Image with image
sim = t.image_col.similarity(image='path/to/query.jpg')
results = t.order_by(sim, asc=False).limit(5).select(t.image_col, sim).collect()
```

### Distance Metrics

```python
t.add_embedding_index('col', embedding=fn, metric='cosine')  # default
t.add_embedding_index('col', embedding=fn, metric='ip')      # inner product
t.add_embedding_index('col', embedding=fn, metric='l2')      # euclidean
```

## B-Tree Indexes

For efficient range queries and equality lookups on non-embedding columns:

```python
# Add B-tree index for fast filtering
t.add_btree_index('category', if_exists='ignore')
t.add_btree_index('timestamp', if_exists='ignore')

# Drop an index
t.drop_index('index_name')
```

## UDFs

### Basic

```python
@pxt.udf
def my_function(x: str) -> str:
    return x.upper()
```

### With Optional Args

```python
from typing import Optional

@pxt.udf
def safe_process(value: Optional[str], default: str = '') -> str:
    return value if value is not None else default
```

### Batch UDF

```python
from pixeltable.func import Batch

@pxt.udf(batch_size=32)
def batch_process(texts: Batch[str]) -> Batch[list[float]]:
    return model.encode(texts).tolist()
```

### User-Defined Aggregates (UDA)

Use `@pxt.uda` for **multi-row → single-value** logic (variance, string concat, frame→video). Use `@pxt.udf` for **one-row → one-value** transforms in computed columns.

```python
@pxt.uda
class avg_int(pxt.Aggregator):
    def __init__(self):
        self.sum = 0
        self.count = 0

    def update(self, val: int) -> None:
        if val is not None:
            self.sum += val
            self.count += 1

    def value(self) -> float:
        return self.sum / self.count if self.count > 0 else 0.0

# Use in queries — not add_computed_column
t.select(avg_int(t.value)).collect()
t.group_by(t.category).select(t.category, avg_val=avg_int(t.value)).collect()
```

**UDA class contract:** subclass `pxt.Aggregator` and implement `__init__`, `update`, and `value`. Parameters to `__init__` must be **constants** (not column expressions).

**`@pxt.uda` decorator kwargs:**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `requires_order_by` | `False` | First positional arg is the order key; rows are processed in that order |
| `allows_std_agg` | `True` | Can run as a plain `SELECT agg(col)` |
| `allows_window` | `False` | Supports `order_by=` / `group_by=` window-style calls |
| `type_substitutions` | `None` | Overloaded aggregator signatures |

**Built-in UDAs** (import from the same modules as scalar functions):

```python
from pixeltable.functions.video import make_video, concat_videos_agg
from pixeltable.functions.json import make_list
from pixeltable.functions.vision import mean_ap

frames.select(make_video(frames.frame, fps=30)).collect()
clips.select(concat_videos_agg(clips.timestamp, clips.video)).collect()
t.select(make_list(t.metadata)).collect()
evals.select(mean_ap(evals.eval_dicts)).collect()
```

### Retrieval UDF (for AI Tool Use)

```python
lookup_fn = pxt.retrieval_udf(t, name='lookup_items', description='Look up items by name',
    parameters=['name'], limit=5)
```

### Custom Iterator

Define custom iterators that produce multiple output rows from a single input:

```python
@pxt.iterator
class SlidingWindowIterator:
    """Produce overlapping windows from a text."""
    def __init__(self, text: str, window_size: int = 100, stride: int = 50):
        self.text = text
        self.window_size = window_size
        self.stride = stride

    def __next__(self) -> dict:  # yields {'window': str}
        ...
```

### List Iterator

Split a list/array column into one row per element:

```python
from pixeltable.functions import list_iterator

# Explode a JSON array column into individual rows
items = pxt.create_view('dir.items', t,
    iterator=list_iterator(t.tags),
    if_exists='ignore')
```

## Update and Delete

```python
t.update({'score': 1.0}, where=t.category == 'important')
t.delete(where=t.is_active == False)
```

### return_rows=True (insert-then-read)

Get all column values (including computed columns) back from `insert()`, `update()`, or `batch_update()` without a follow-up query:

```python
# Anti-pattern: insert then query
t.insert([row])
result = t.where(t.id == value).select(...).collect()
data = result[0]

# Correct: return_rows=True
status = t.insert([row], return_rows=True)
data = status.rows[0]  # dict with ALL columns including computed
```

For typed access, use Pydantic `model_validate()` with `extra="ignore"` (row dicts contain every column):

```python
from pydantic import BaseModel

class AgentResult(BaseModel):
    model_config = {"extra": "ignore"}
    answer: str | None = None
    tool_output: Any = None

status = agent.insert([{"prompt": user_input}], return_rows=True)
result = AgentResult.model_validate(status.rows[0])
```

**When to use which:**
- `return_rows=True` -- insert/update and read computed columns back in one call
- `to_pydantic()` -- reading from a `ResultSet` (after `.collect()`)
- `model_validate()` -- reading from `status.rows` (plain dicts from `return_rows=True`)

## Table Operations

```python
t.rename_column('old_name', 'new_name')
t.add_column(new_col=pxt.String)
t.drop_column('col_name')
t.describe()
t.columns()

# Directory management
pxt.list_dirs()
pxt.list_tables()
contents = pxt.get_dir_contents('my_dir')
```

## Recompute Columns

Re-run computed columns on existing rows. Critical for retrying after API errors or rate limits:

```python
# Recompute all rows for a column
t.recompute_columns(columns=['summary'])

# Recompute only failed rows (most common pattern)
t.recompute_columns(columns=['summary'], where=t.summary.errortype != None)

# Recompute specific rows matching a condition
t.recompute_columns(columns=['label'], where=t.category == 'pending')
```

## Snapshots and Version History

Point-in-time copies of tables:

```python
snap = pxt.create_snapshot('dir.snap_v1', t, if_exists='ignore')
# Query the snapshot like any table
snap.select(snap.col1).collect()

# View table version history
versions = t.get_versions()
```

## Tools and Agents

### Create Tools from UDFs and Query Functions

```python
@pxt.udf
def web_search(keywords: str) -> str:
    """Search the web for information."""
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.news(keywords=keywords, max_results=5))
        return '\n'.join(f"{r['title']}: {r['body']}" for r in results) if results else 'No results.'

@pxt.query
def search_docs(query_text: str):
    """Search documents by semantic similarity."""
    sim = chunks.text.similarity(string=query_text)
    return chunks.order_by(sim, asc=False).limit(10).select(chunks.text, score=sim)

tools = pxt.tools(web_search, search_docs)
```

### Full Tool-Calling Agent Pipeline

The agent pipeline uses chained computed columns. Inserting a row triggers the entire pipeline:

```python
from pixeltable.functions.anthropic import messages, invoke_tools

agent = pxt.create_table('project.agent', {
    'prompt': pxt.String,
    'timestamp': pxt.Timestamp,
    'initial_system_prompt': pxt.String,
    'final_system_prompt': pxt.String,
    'max_tokens': pxt.Int,
    'temperature': pxt.Float,
}, if_exists='ignore')

# Step 1: Initial LLM call with tool selection
agent.add_computed_column(
    initial_response=messages(
        model='claude-sonnet-4-20250514',
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': agent.prompt}]}],
        tools=tools,
        tool_choice=tools.choice(required=True),
        max_tokens=agent.max_tokens,
        model_kwargs={
            'system': agent.initial_system_prompt,
            'temperature': agent.temperature,
        },
    ),
    if_exists='ignore',
)

# Step 2: Execute the tools the LLM selected
agent.add_computed_column(
    tool_output=invoke_tools(tools, agent.initial_response),
    if_exists='ignore',
)

# Step 3: RAG context retrieval
agent.add_computed_column(
    doc_context=search_docs(agent.prompt),
    if_exists='ignore',
)

# Step 4: Assemble context with a UDF
agent.add_computed_column(
    context=assemble_context(agent.prompt, agent.tool_output, agent.doc_context),
    if_exists='ignore',
)

# Step 5: Final LLM call with full context
agent.add_computed_column(
    final_response=messages(
        model='claude-sonnet-4-20250514',
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': agent.context}]}],
        max_tokens=agent.max_tokens,
        model_kwargs={
            'system': agent.final_system_prompt,
            'temperature': agent.temperature,
        },
    ),
    if_exists='ignore',
)

# Step 6: Extract answer text
agent.add_computed_column(
    answer=agent.final_response.content[0].text,
    if_exists='ignore',
)
```

### Using the Agent Pipeline

```python
from datetime import datetime

agent.insert([{
    'prompt': 'What are the latest developments in quantum computing?',
    'timestamp': datetime.now(),
    'initial_system_prompt': 'Identify the best tool(s) to answer the query.',
    'final_system_prompt': 'Provide a clear answer. Cite sources when possible.',
    'max_tokens': 1024,
    'temperature': 0.7,
}])

result = agent.order_by(agent.timestamp, asc=False).limit(1).select(agent.answer).collect()
```

### MCP Integration

```python
udfs = pxt.mcp_udfs('http://localhost:8080/sse')
```

---

## Serving (FastAPIRouter)

`pixeltable.serving.FastAPIRouter` (v0.6+) is a subclass of FastAPI's `APIRouter` that generates endpoints from tables and `@pxt.query` functions. No Pydantic models or hand-written handlers needed.

### add_insert_route

```python
from pixeltable.serving import FastAPIRouter
import pixeltable as pxt

router = FastAPIRouter(prefix="/api/data", tags=["data"])
docs = pxt.get_table("app.documents")

# Synchronous insert — returns inserted row fields
router.add_insert_route(docs, path="/upload/image",
    uploadfile_inputs=["image"], inputs=["timestamp"], outputs=["uuid", "thumbnail"])

# Background insert — returns job handle for polling
router.add_insert_route(docs, path="/upload/document",
    uploadfile_inputs=["document"], inputs=["timestamp"], outputs=["uuid"],
    background=True)
# Client receives { "job_url": "http://host/jobs/{id}" }
# Poll GET /jobs/{id} → { "status": "pending" | "done" | "error", "result": {...} }
```

Parameters:
- `uploadfile_inputs` — column names sent as `UploadFile` (multipart form)
- `inputs` — column names sent as form fields
- `outputs` — column names to return after insert
- `background=True` — return immediately with a job URL; client polls for result

### add_query_route

```python
@pxt.query
def search_docs(query_text: str):
    sim = chunks.text.similarity(string=query_text)
    return chunks.where(sim > 0.3).order_by(sim, asc=False).select(
        text=chunks.text, score=sim).limit(20)

router.add_query_route(path="/search", query=search_docs, method="post")
# POST /api/data/search {"query_text": "..."} → { "rows": [...] }

@pxt.query
def list_docs():
    return docs.select(uuid=docs.uuid, name=docs.document).order_by(docs.timestamp, asc=False)

router.add_query_route(path="/list", query=list_docs, method="get")
# GET /api/data/list → { "rows": [...] }
```

### add_update_route

```python
# Update by primary key — recomputes dependent computed columns
router.add_update_route(docs, path="/update", inputs=["title"], outputs=["uuid", "title", "summary"])
# POST /api/data/update {"uuid": "...", "title": "..."} → updated row fields
```

### add_compute_route

Materialize computed columns for a request **without persisting** the row (same shape as insert):

```python
# Preview / dry-run: run the table's computed columns, return the row, do not insert
router.add_compute_route(
    docs, path="/preview", inputs=["document"], outputs=["document", "summary"]
)
# POST /api/data/preview {"document": "..."} → computed fields; table unchanged

# Or call the table API directly in Python:
rows = docs.compute([{'document': 'report.pdf'}])
```

For declarative TOML / `pxt serve`, `type = "compute"` is currently an insert alias — use the Python `FastAPIRouter` API for true non-persisting compute.

### add_delete_route

```python
# Delete by primary key
router.add_delete_route(docs, path="/delete")
# POST /api/data/delete {"uuid": "..."} → { "num_rows": 1 }

# Delete by non-PK column
router.add_delete_route(chat, path="/delete-conversation", match_columns=["conversation_id"])
```

### Architecture pattern

```
setup_pixeltable.py  — flat module: creates tables, views, indexes on import
routers/data.py      — pxt.get_table() + @pxt.query + add_*_route
routers/search.py    — pxt.get_table() + @pxt.query + add_*_route
main.py              — import setup_pixeltable; from routers import data, search
```

See [workflows.md → FastAPIRouter](workflows.md#fastapirouter-declarative-serving-v06) for a complete example.

### pxt serve (CLI)

Declarative HTTP serving without application code. Requires `pip install 'pixeltable[serve]'`.

Define routes in `pyproject.toml` (`[[tool.pixeltable.service]]`) or a standalone `service.toml` (`[[service]]`), then:

```bash
pxt serve my-service                    # from pyproject.toml
pxt serve my-service --config service.toml --port 9000
pxt serve my-service --dry-run --json   # CI validation
```

Query routes use `module:attribute` colon paths (e.g. `schema:search_docs`), resolved at startup. Full command reference, single-endpoint modes, and flag tables: [cli.md](cli.md).

See [HTTP Serving Guide](https://docs.pixeltable.com/howto/deployment/serving) for TOML field reference and [Starter Kit `serving/`](https://github.com/pixeltable/pixeltable-starter-kit/tree/main/serving) for a working example.

---

## Export (CSV, JSON, Parquet, LanceDB, Iceberg)

```python
import pixeltable as pxt

t = pxt.get_table('myapp/documents')

# Export to CSV
pxt.io.export_csv(t, '/data/documents.csv')

# Export to JSON
pxt.io.export_json(t, '/data/documents.json')

# Export to Parquet
pxt.io.export_parquet(t, '/data/documents.parquet')

# Export to LanceDB (vector DB)
pxt.io.export_lancedb(t, db_uri='/data/lance', table_name='docs')

# Export to Apache Iceberg (requires: pip install pyiceberg)
# pxt.io.export_iceberg(t, catalog=iceberg_catalog, table_name='ns.my_table')

# Export filtered query results
results = t.where(t.score > 0.8).select(t.title, t.score)
pxt.io.export_csv(results, '/data/filtered.csv')

# Other formats
df = t.collect().to_pandas()           # Pandas DataFrame
ds = t.to_pytorch_dataset(['image'])   # PyTorch DataLoader
coco = t.to_coco_dataset()            # COCO format
```

---

## Export to SQL Databases

```python
from pixeltable.io.sql import export_sql

# Export full table to SQLite
export_sql(t, 'my_table', db_connect_str='sqlite:///data.db')

# Export filtered query with column rename
export_sql(
    t.where(t.score > 0.8).select(product_name=t.name, price=t.price),
    'filtered_products',
    db_connect_str='sqlite:///data.db',
)

# Append to existing SQL table
export_sql(t, 'products', db_connect_str=connection_string, if_exists='insert')

# Replace existing SQL table
export_sql(t, 'products', db_connect_str=connection_string, if_exists='replace')

# Cloud databases (PostgreSQL, Snowflake, etc.)
export_sql(t, 'products', db_connect_str='postgresql+psycopg://user:pass@host:5432/db')
```

---

## Configuration

### API Keys

```python
# Via init
pxt.init({'openai.api_key': 'sk-...', 'anthropic.api_key': 'sk-ant-...'})

# Via environment variables (recommended)
# OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY / GEMINI_API_KEY,
# TOGETHER_API_KEY, FIREWORKS_API_KEY, MISTRAL_API_KEY, GROQ_API_KEY,
# DEEPSEEK_API_KEY, VOYAGE_API_KEY, REPLICATE_API_TOKEN, HF_TOKEN,
# OPENROUTER_API_KEY, FAL_API_KEY, REVE_API_KEY, TWELVELABS_API_KEY,
# BEDROCK_API_KEY
```

### config.toml

Located at `~/.pixeltable/config.toml`:

```toml
[pixeltable]
file_cache_size_g = 250
time_zone = "America/Los_Angeles"
hide_warnings = true
verbosity = 2

[openai]
api_key = 'sk-...'
# For Azure OpenAI, add these to the same [openai] section:
# base_url = 'https://my-deployment.openai.azure.com/'
# api_version = '2024-02-01'

# Per-model rate limits (requests per minute)
[openai.rate_limits]
gpt-4o = 500
gpt-4o-mini = 1000
tts-1 = 50
dall-e-3 = 10

[anthropic]
api_key = 'sk-ant-...'

[mistral]
api_key = 'my-mistral-key'
rate_limit = 600
```

### Rate Limiting

Default: 600 requests per minute per provider. Configure in `config.toml`:

```toml
# Single rate limit for all models of a provider
[fireworks]
rate_limit = 300

# Per-model rate limits
[openai.rate_limits]
gpt-4o = 500
gpt-4o-mini = 1000
```

Custom resource pools for non-built-in APIs:

```python
@pxt.udf(resource_pool='request-rate:my_service')
def call_custom_api(prompt: str) -> str:
    return requests.post('https://example.com/generate', json={'prompt': prompt}).json()['text']
```

### Media Destinations (Cloud Storage)

Store media files in S3, GCS, Azure, or other cloud storage instead of locally:

```toml
# config.toml — global default
[pixeltable]
input_media_dest = "s3://my-bucket/input/"
output_media_dest = "s3://my-bucket/output/"
```

```bash
# Or via environment variables
export PIXELTABLE_INPUT_MEDIA_DEST="s3://my-bucket/input/"
export PIXELTABLE_OUTPUT_MEDIA_DEST="s3://my-bucket/output/"
```

```python
# Per-column destination (overrides global default)
t.add_computed_column(
    thumbnail=pxt_image.thumbnail(t.image, size=(256, 256)),
    destination='s3://my-bucket/thumbnails/',
    if_exists='ignore',
)
```

Supported providers: Amazon S3, Google Cloud Storage (`gs://`), Azure Blob Storage (`wasbs://`), Cloudflare R2, Backblaze B2, Tigris.

**Pixeltable Cloud (home bucket):** Free R2-backed storage. No AWS credentials needed:

```python
# Use pxtfs:// URI as a destination
t.add_computed_column(
    thumbnail=pxt_image.thumbnail(t.image, size=(256, 256)),
    destination='pxtfs://org:db/home/thumbnails/',
)
```

```bash
# Or set globally
export PIXELTABLE_API_KEY="pxt_..."
export PIXELTABLE_OUTPUT_MEDIA_DEST="pxtfs://org:db/home/"
```

See [Cloud Storage docs](https://docs.pixeltable.com/integrations/cloud-storage).

## Common Pitfalls

### Deprecated/Wrong Imports

```python
# WRONG — openai.vision does not exist
from pixeltable.functions.openai import vision
description = vision(prompt='Describe', image=t.image)

# CORRECT — use chat_completions with multimodal messages
from pixeltable.functions.openai import chat_completions
description = chat_completions(
    messages=[{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'Describe this image.'},
            {'type': 'image_url', 'image_url': {'url': t.image}}
        ]
    }],
    model='gpt-4o-mini'
).choices[0].message.content

# WRONG — FrameIterator class import
from pixeltable.iterators import FrameIterator
pxt.create_view('v', t, iterator=FrameIterator.create(video=t.video, fps=1))

# CORRECT — function import
from pixeltable.functions.video import frame_iterator
pxt.create_view('v', t, iterator=frame_iterator(t.video, fps=1), if_exists='ignore')
```

### Cast to String Before Embedding

AI functions often return `Json` or complex objects. Embedding indexes require `String` columns:

```python
# WRONG — transcriptions returns a Json object, not a String
t.add_computed_column(transcript=openai.transcriptions(audio=t.audio, model='whisper-1'), if_exists='ignore')
t.add_embedding_index('transcript', embedding=embed_fn)  # silently fails

# CORRECT — extract .text and cast
t.add_computed_column(
    transcript=openai.transcriptions(audio=t.audio, model='whisper-1').text.astype(pxt.String),
    if_exists='ignore')
t.add_embedding_index('transcript', embedding=embed_fn, if_exists='ignore')
```

This applies to any computed column used as an embedding source — always ensure it evaluates to `pxt.String`.

### The `if_exists='ignore'` Trap

If you create a column with buggy logic, fixing the code and re-running does **NOT** update the column. `if_exists='ignore'` silently skips the already-existing (broken) column:

```python
# Bug: wrong model name
t.add_computed_column(summary=openai.chat_completions(..., model='nonexistent'), if_exists='ignore')

# Fixing the code and re-running does NOTHING — old column persists
t.add_computed_column(summary=openai.chat_completions(..., model='gpt-4o-mini'), if_exists='ignore')

# FIX: drop the column first, then recreate
t.drop_column('summary')
t.add_computed_column(summary=openai.chat_completions(..., model='gpt-4o-mini'), if_exists='ignore')

# OR: wipe the entire namespace during development
pxt.drop_dir('my_project', force=True)
```

### Other Pitfalls

```python
# Image in messages: use image_url, never raw pxt.Image
messages=[{'role': 'user', 'content': [
    {'type': 'text', 'text': 'Describe.'},
    {'type': 'image_url', 'image_url': {'url': t.image}}  # NOT {'type': 'image', 'data': t.image}
]}]

# Similarity: always use string= keyword
sim = t.content.similarity(string=query_text)  # NOT .similarity(query_text)
```

Schema corruption (`IntegrityError`): try `pxt.drop_dir('my_project', force=True)` first. Last resort (development only — run manually with backup, never in production): upgrade pixeltable (`pip install -U pixeltable`), then delete only the `~/.pixeltable` directory.

### `@pxt.query` Eager Compilation

`@pxt.query` compiles the function body at **decoration time** by calling it with expression placeholders. This means:

```python
# WRONG — .collect() executes during decoration, not at call time
@pxt.query
def find_similar(ref_id: str):
    ref = t.where(t.uuid == ref_id).select(t.embedding).collect()  # FAILS at decoration
    return t.order_by(t.embedding.similarity(ref[0]['embedding'])).limit(5)

# CORRECT — use a plain def for imperative logic that needs .collect()
def find_similar(ref_id: str) -> list[dict]:
    ref = t.where(t.uuid == ref_id).select(t.embedding).collect()
    return list(t.order_by(t.embedding.similarity(ref[0]['embedding'])).limit(5).collect())

# WRONG — references a table that may not exist yet
@pxt.query
def search():
    t = pxt.get_table('maybe.missing')  # FAILS if table doesn't exist at decoration time
    return t.select(t.col)
```

### Nullable Primary Keys

Primary key columns must be non-nullable. Bare `pxt.String` is nullable by default:

```python
# WRONG — nullable PK rejected at table creation
t = pxt.create_table('dir.items', {
    'id': pxt.String,  # nullable!
}, primary_key=['id'])

# CORRECT — explicit non-nullable
t = pxt.create_table('dir.items', {
    'id': pxt.Required[pxt.String],
}, primary_key=['id'])

# CORRECT — uuid7() computed default (recommended)
from pixeltable.functions.uuid import uuid7
t = pxt.create_table('dir.items', {
    'content': pxt.String,
    'uuid': uuid7(),
}, primary_key=['uuid'])
```

### Thread-Safety in FastAPI

`Table` objects are bound to the thread that created them. In FastAPI (which dispatches sync endpoints to a thread pool), call `pxt.get_table()` inside each endpoint:

```python
# WRONG — module-level Table used across threads
docs = pxt.get_table('app.documents')

@app.get('/count')
def count():
    return {'count': docs.count()}  # fails: wrong thread

# CORRECT — get a fresh handle per request
@app.get('/count')
def count():
    docs = pxt.get_table('app.documents')
    return {'count': docs.count()}
```

### `document_splitter` with `token_limit`

The `token_limit` separator requires the `tiktoken` package:

```bash
pip install tiktoken
```

Without it, `document_splitter(t.doc, separators='token_limit', ...)` raises `RequestError: This feature requires the tiktoken package`.

## Performance Tips

- Batch inserts for efficiency
- Use `on_error='ignore'` to continue past row failures
- Use `batch_size` in `@pxt.udf(batch_size=32)` for GPU models
- Embedding indexes use HNSW for fast approximate nearest neighbor search
- Use `t.insert(source='file.csv')` instead of loading into memory for large datasets
- Use `keyframes_only=True` in `frame_iterator` for efficient video processing
- Use `thumbnail()` + `b64_encode()` for API-friendly image responses
- Configure rate limits in `config.toml` to avoid 429 errors on provider APIs
- Use `recompute_columns(where=t.col.errortype != None)` to retry only failed rows
- Use `add_btree_index()` on columns used frequently in `where()` filters
- Cast AI function outputs to `pxt.String` with `.astype(pxt.String)` before embedding indexing
- During development, use `pxt.drop_dir('dir', force=True)` to reset schema cleanly
