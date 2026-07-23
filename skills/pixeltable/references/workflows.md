# Pixeltable End-to-End Workflow Templates

Complete, production-ready workflow templates combining multiple Pixeltable features.

## Contents

- [RAG Pipeline](#rag-pipeline)
- [Video Analysis Pipeline](#video-analysis-pipeline)
- [Image Classification and Search](#image-classification-and-search)
- [Audio Transcription and Analysis](#audio-transcription-and-analysis)
- [Multi-Provider Comparison](#multi-provider-comparison)
- [Tool-Calling Agent (Full Production Example)](#tool-calling-agent-full-production-example)
- [Local LLM Pipeline (Ollama)](#local-llm-pipeline-ollama)
- [FastAPI App Pattern](#fastapi-app-pattern) (hand-written endpoints)
- [FastAPIRouter — Declarative Serving (v0.6+)](#fastapirouter-declarative-serving-v06) (preferred)
- [Batch Processing Pattern](#batch-processing-pattern)
- [Export Workflow](#export-workflow)

---

### RAG Pipeline

```python
import pixeltable as pxt
from pixeltable.functions.document import document_splitter
from pixeltable.functions.openai import chat_completions, embeddings

pxt.create_dir('rag', if_exists='ignore')

docs = pxt.create_table('rag.documents', {
    'doc': pxt.Document,
    'title': pxt.String,
}, if_exists='ignore')

chunks = pxt.create_view('rag.chunks', docs,
    iterator=document_splitter(docs.doc, separators='token_limit', limit=300, metadata='title,heading'),
    if_exists='ignore')

chunks.add_embedding_index('text',
    embedding=embeddings.using(model='text-embedding-3-small'),
    if_exists='ignore')

docs.insert([
    {'doc': 'path/to/document.pdf', 'title': 'My Document'},
    {'doc': 'https://example.com/page.html', 'title': 'Web Page'},
])

@pxt.query
def retrieve(question: str, top_k: int = 5):
    sim = chunks.text.similarity(string=question)
    return chunks.order_by(sim, asc=False).limit(top_k).select(chunks.text, chunks.title, score=sim)

context = retrieve('What is machine learning?').collect()
```

### Video Analysis Pipeline

```python
import pixeltable as pxt
from pixeltable.functions.video import frame_iterator, extract_audio
from pixeltable.functions.audio import audio_splitter
from pixeltable.functions.string import string_splitter
from pixeltable.functions.openai import chat_completions, transcriptions
from pixeltable.functions.huggingface import clip, sentence_transformer
from pixeltable.functions import image as pxt_image

pxt.create_dir('video', if_exists='ignore')

videos = pxt.create_table('video.library', {
    'video': pxt.Video, 'title': pxt.String
}, if_exists='ignore')

# 1. Keyframe extraction + CLIP visual search
frames = pxt.create_view('video.frames', videos,
    iterator=frame_iterator(videos.video, keyframes_only=True),
    if_exists='ignore')

frames.add_computed_column(
    thumbnail=pxt_image.b64_encode(
        pxt_image.thumbnail(frames.frame, size=(320, 320))),
    if_exists='ignore')

frames.add_embedding_index('frame',
    embedding=clip.using(model_id='openai/clip-vit-base-patch32'),
    if_exists='ignore')

# 2. Audio extraction -> transcription -> sentence embedding
videos.add_computed_column(
    audio=extract_audio(videos.video, format='mp3'),
    if_exists='ignore')

audio_segments = pxt.create_view('video.audio_segments', videos,
    iterator=audio_splitter(
        audio=videos.audio, duration=30.0, min_silence_len=0.3, trim_leading_silence=True
    ),
    if_exists='ignore')

audio_segments.add_computed_column(
    transcription=transcriptions(
        audio=audio_segments.audio_segment, model='whisper-1'),
    if_exists='ignore')

sentences = pxt.create_view('video.sentences',
    audio_segments.where(audio_segments.transcription != None),
    iterator=string_splitter(
        text=audio_segments.transcription.text, separators='sentence'),
    if_exists='ignore')

embed_fn = sentence_transformer.using(model_id='all-MiniLM-L6-v2')
sentences.add_embedding_index('text', string_embed=embed_fn, if_exists='ignore')

# 3. Describe frames with vision LLM
frames.add_computed_column(
    description=chat_completions(
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': 'Describe this video frame in one sentence.'},
                {'type': 'image_url', 'image_url': {'url': frames.frame}}
            ]
        }],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')

# Visual search
sim = frames.frame.similarity(string='person riding a bicycle')
results = frames.order_by(sim, asc=False).limit(10).select(
    frames.frame, frames.description, sim).collect()

# Transcript search
@pxt.query
def search_transcripts(query_text: str):
    sim = sentences.text.similarity(string=query_text)
    return sentences.where(sim > 0.7).order_by(sim, asc=False).select(
        sentences.text, score=sim
    ).limit(20)
```

### Image Classification and Search

```python
import pixeltable as pxt
from pixeltable.functions.openai import chat_completions
from pixeltable.functions.huggingface import clip
from pixeltable.functions import image as pxt_image

pxt.create_dir('images', if_exists='ignore')

catalog = pxt.create_table('images.catalog', {
    'image': pxt.Image, 'filename': pxt.String,
}, if_exists='ignore')

catalog.add_computed_column(
    thumbnail=pxt_image.b64_encode(
        pxt_image.thumbnail(catalog.image, size=(320, 320))),
    if_exists='ignore')

catalog.add_computed_column(
    tags=chat_completions(
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': 'List 5 descriptive tags as a comma-separated list.'},
                {'type': 'image_url', 'image_url': {'url': catalog.image}}
            ]
        }],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')

embed_fn = clip.using(model_id='openai/clip-vit-base-patch32')
catalog.add_embedding_index('image', embedding=embed_fn, if_exists='ignore')

sim = catalog.image.similarity(string='sunset over the ocean')
results = catalog.order_by(sim, asc=False).limit(5).select(
    catalog.image, catalog.tags, sim).collect()
```

### Audio Transcription and Analysis

```python
import pixeltable as pxt
from pixeltable.functions.openai import transcriptions, chat_completions

pxt.create_dir('audio', if_exists='ignore')

recordings = pxt.create_table('audio.recordings', {
    'audio': pxt.Audio, 'speaker': pxt.String,
}, if_exists='ignore')

recordings.add_computed_column(
    transcript=transcriptions(audio=recordings.audio, model='whisper-1').text,
    if_exists='ignore')

recordings.add_computed_column(
    summary=chat_completions(
        messages=[
            {'role': 'system', 'content': 'Summarize in 2-3 sentences.'},
            {'role': 'user', 'content': recordings.transcript}
        ],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')
```

### Multi-Provider Comparison

```python
import pixeltable as pxt
from pixeltable.functions.openai import chat_completions as openai_chat
from pixeltable.functions.anthropic import messages as anthropic_msg
from pixeltable.functions.together import chat_completions as together_chat

pxt.create_dir('compare', if_exists='ignore')
prompts = pxt.create_table('compare.prompts', {'prompt': pxt.String}, if_exists='ignore')

prompts.add_computed_column(
    openai=openai_chat(
        messages=[{'role': 'user', 'content': prompts.prompt}], model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

prompts.add_computed_column(
    anthropic=anthropic_msg(
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': prompts.prompt}]}],
        model='claude-sonnet-4-20250514', max_tokens=1024
    ).content[0].text, if_exists='ignore')

prompts.add_computed_column(
    llama=together_chat(
        messages=[{'role': 'user', 'content': prompts.prompt}],
        model='meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo'
    ).choices[0].message.content, if_exists='ignore')

prompts.insert([{'prompt': 'Explain quantum computing simply.'}])
results = prompts.select(
    prompts.prompt, prompts.openai, prompts.anthropic, prompts.llama).collect()
```

### Tool-Calling Agent (Full Production Example)

Complete agent pipeline as used in the [Pixeltable Starter Kit](https://github.com/pixeltable/pixeltable-starter-kit):

```python
import pixeltable as pxt
from pixeltable.functions.anthropic import messages, invoke_tools
from pixeltable.functions.huggingface import sentence_transformer, clip
from pixeltable.functions.document import document_splitter
from pixeltable.functions import image as pxt_image
from datetime import datetime

pxt.create_dir('app', if_exists='ignore')

# --- Data pipelines ---
documents = pxt.create_table('app.documents', {'document': pxt.Document}, if_exists='ignore')
chunks = pxt.create_view('app.chunks', documents,
    iterator=document_splitter(documents.document,
        separators='page, sentence', metadata='title,heading,page'),
    if_exists='ignore')

embed_fn = sentence_transformer.using(model_id='intfloat/multilingual-e5-large-instruct')
chunks.add_embedding_index('text', string_embed=embed_fn, if_exists='ignore')

images = pxt.create_table('app.images', {'image': pxt.Image}, if_exists='ignore')
images.add_computed_column(
    thumbnail=pxt_image.b64_encode(pxt_image.thumbnail(images.image, size=(320, 320))),
    if_exists='ignore')
images.add_embedding_index('image',
    embedding=clip.using(model_id='openai/clip-vit-base-patch32'), if_exists='ignore')

# --- Query functions (become tools + RAG context) ---
@pxt.query
def search_documents(query_text: str):
    sim = chunks.text.similarity(string=query_text)
    return chunks.where(sim > 0.5).order_by(sim, asc=False).select(
        chunks.text, score=sim).limit(20)

@pxt.query
def search_images(query_text: str):
    sim = images.image.similarity(string=query_text)
    return images.where(sim > 0.25).order_by(sim, asc=False).select(
        encoded_image=pxt_image.b64_encode(
            pxt_image.thumbnail(images.image, size=(224, 224)), 'png'),
        score=sim).limit(5)

@pxt.udf
def web_search(keywords: str) -> str:
    """Search the web using DuckDuckGo."""
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.news(keywords=keywords, max_results=5))
        return '\n'.join(
            f"{r['title']}: {r['body']}" for r in results
        ) if results else 'No results.'

@pxt.udf
def assemble_context(question: str, tool_outputs: list | None, doc_context: list | None) -> str:
    tool_str = str(tool_outputs) if tool_outputs else 'N/A'
    doc_str = '\n'.join(
        f"- {item.get('text', '')}" for item in (doc_context or []) if isinstance(item, dict)
    ) or 'N/A'
    return (f"QUESTION: {question}\n\n"
            f"<tool_results>\n{tool_str}\n</tool_results>\n\n"
            f"<retrieved_documents>\n{doc_str}\n</retrieved_documents>")

# --- Agent pipeline ---
tools = pxt.tools(web_search, search_documents)

agent = pxt.create_table('app.agent', {
    'prompt': pxt.String,
    'timestamp': pxt.Timestamp,
    'system_prompt': pxt.String,
    'max_tokens': pxt.Int,
    'temperature': pxt.Float,
}, if_exists='ignore')

agent.add_computed_column(
    initial_response=messages(
        model='claude-sonnet-4-20250514',
        messages=[{'role': 'user', 'content': agent.prompt}],
        tools=tools,
        tool_choice=tools.choice(required=True),
        max_tokens=agent.max_tokens,
        model_kwargs={'system': agent.system_prompt, 'temperature': agent.temperature},
    ), if_exists='ignore')

agent.add_computed_column(tool_output=invoke_tools(tools, agent.initial_response), if_exists='ignore')
agent.add_computed_column(doc_context=search_documents(agent.prompt), if_exists='ignore')
agent.add_computed_column(
    context=assemble_context(agent.prompt, agent.tool_output, agent.doc_context),
    if_exists='ignore')

agent.add_computed_column(
    final_response=messages(
        model='claude-sonnet-4-20250514',
        messages=[{'role': 'user', 'content': agent.context}],
        max_tokens=agent.max_tokens,
        model_kwargs={'system': 'Answer based on context. Cite sources.', 'temperature': agent.temperature},
    ), if_exists='ignore')

agent.add_computed_column(answer=agent.final_response.content[0].text, if_exists='ignore')

# --- Usage ---
agent.insert([{
    'prompt': 'What are the latest AI breakthroughs?',
    'timestamp': datetime.now(),
    'system_prompt': 'Use tools to gather information, then answer.',
    'max_tokens': 1024,
    'temperature': 0.7,
}])
result = agent.order_by(agent.timestamp, asc=False).limit(1).select(agent.answer).collect()
```

### Local LLM Pipeline (Ollama)

```python
import pixeltable as pxt
from pixeltable.functions.ollama import chat, embed

pxt.create_dir('local', if_exists='ignore')
t = pxt.create_table('local.data', {'text': pxt.String}, if_exists='ignore')

t.add_computed_column(
    analysis=chat(
        messages=[{'role': 'user', 'content': 'Analyze: ' + t.text}],
        model='llama3.1'
    ).message.content, if_exists='ignore')

t.add_embedding_index('text',
    embedding=embed.using(model='nomic-embed-text'),
    if_exists='ignore')

t.insert([{'text': 'Machine learning fundamentals'}])
sim = t.text.similarity(string='neural networks')
results = t.order_by(sim, asc=False).limit(5).select(t.text, sim).collect()
```

### FastAPI App Pattern

Production-ready pattern for web apps with Pixeltable:

```python
# setup_pixeltable.py -- Run once to initialize schema
import pixeltable as pxt
from pixeltable.functions.uuid import uuid7
from pixeltable.functions.document import document_splitter
from pixeltable.functions.huggingface import sentence_transformer

pxt.drop_dir('app', force=True)
pxt.create_dir('app', if_exists='ignore')

documents = pxt.create_table('app.documents', {
    'document': pxt.Document,
    'uuid': uuid7(),
    'timestamp': pxt.Timestamp,
}, primary_key=['uuid'], if_exists='ignore')

chunks = pxt.create_view('app.chunks', documents,
    iterator=document_splitter(
        documents.document, separators='page, sentence',
        metadata='title,heading,page'),
    if_exists='ignore')

embed_fn = sentence_transformer.using(
    model_id='intfloat/multilingual-e5-large-instruct')
chunks.add_embedding_index('text', string_embed=embed_fn, if_exists='ignore')

@pxt.query
def search_documents(query_text: str):
    sim = chunks.text.similarity(string=query_text)
    return chunks.where(sim > 0.5).order_by(sim, asc=False).select(
        chunks.text, score=sim, title=chunks.title
    ).limit(20)
```

```python
# main.py -- FastAPI app (use def, not async def)
from fastapi import FastAPI
from pydantic import BaseModel
import pixeltable as pxt

app = FastAPI()

class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    text: str
    score: float
    title: str | None = None

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]

@app.post("/api/search", response_model=SearchResponse)
def search(body: SearchRequest):                    # sync, not async
    table = pxt.get_table('app.chunks')
    sim = table.text.similarity(string=body.query)
    result = (
        table.where(sim > 0.3)
        .order_by(sim, asc=False)
        .select(text=table.text, score=sim, title=table.title)
        .limit(20)
        .collect()
    )
    items = list(result.to_pydantic(SearchResult))  # direct conversion
    return SearchResponse(query=body.query, results=items)
```

### FastAPIRouter — Declarative Serving (v0.6+)

`pixeltable.serving.FastAPIRouter` generates endpoints from tables and `@pxt.query` functions — no Pydantic models, no hand-written handlers. It's a subclass of FastAPI's `APIRouter`.

```python
# setup_pixeltable.py — flat module, runs on import
import pixeltable as pxt
from pixeltable.functions.uuid import uuid7
from pixeltable.functions.document import document_splitter
from pixeltable.functions.huggingface import sentence_transformer

pxt.create_dir('app', if_exists='ignore')

docs = pxt.create_table('app.documents', {
    'document': pxt.Document, 'uuid': uuid7(), 'timestamp': pxt.Timestamp,
}, primary_key=['uuid'], if_exists='ignore')

chunks = pxt.create_view('app.chunks', docs,
    iterator=document_splitter(docs.document, separators='page, sentence', metadata='title,heading,page'),
    if_exists='ignore')

embed_fn = sentence_transformer.using(model_id='intfloat/multilingual-e5-large-instruct')
chunks.add_embedding_index('text', idx_name='chunks_embed', string_embed=embed_fn, if_exists='ignore')
```

```python
# routers/data.py — queries co-located with routes
import pixeltable as pxt
from pixeltable.serving import FastAPIRouter

router = FastAPIRouter(prefix="/api/data", tags=["data"])
docs = pxt.get_table("app.documents")
chunks = pxt.get_table("app.chunks")

# Upload with background processing (returns job handle, client polls /jobs/{id})
router.add_insert_route(docs, path="/upload",
    uploadfile_inputs=["document"], inputs=["timestamp"], outputs=["uuid"],
    background=True)

router.add_delete_route(docs, path="/delete")

@pxt.query
def list_docs():
    return docs.select(uuid=docs.uuid, name=docs.document, timestamp=docs.timestamp).order_by(docs.timestamp, asc=False)

@pxt.query
def search_docs(query_text: str):
    sim = chunks.text.similarity(string=query_text)
    return chunks.where(sim > 0.3).order_by(sim, asc=False).select(
        text=chunks.text, score=sim, title=chunks.title).limit(20)

router.add_query_route(path="/list", query=list_docs, method="get")
router.add_query_route(path="/search", query=search_docs, method="post")
```

```python
# main.py
from fastapi import FastAPI
import setup_pixeltable  # noqa: F401 — triggers schema init
from routers import data

app = FastAPI()
app.include_router(data.router)
```

Key points:
- **`add_insert_route`** — generates POST endpoint from table columns. Use `uploadfile_inputs` for file uploads, `background=True` for long-running inserts
- **`add_query_route`** — wraps a `@pxt.query` function as GET or POST. Returns `{ "rows": [...] }` automatically
- **`add_delete_route`** — generates POST endpoint for row deletion by primary key or `match_columns`
- **Schema in one file, queries in routers** — `setup_pixeltable.py` creates tables/views/indexes on import. Routers get table refs via `pxt.get_table()` and define `@pxt.query` locally
- **Only write custom endpoints** for multi-table side effects (e.g., agent insert + chat history saves)

#### return_rows=True for hand-written endpoints

When you do need a hand-written endpoint (multi-table side effects, conditional logic), use `return_rows=True` to read computed columns back without a follow-up query:

```python
from typing import Any
from pydantic import BaseModel
import pixeltable as pxt

# `router` is the FastAPIRouter defined in the example above.

class QueryRequest(BaseModel):
    prompt: str

class AgentResult(BaseModel):
    model_config = {"extra": "ignore"}
    answer: str | None = None
    tool_output: Any = None

@router.post("/query")
def agent_query(request: QueryRequest):
    agent_table = pxt.get_table("app.agent")           # get handles inside the endpoint
    chat_table = pxt.get_table("app.chat_history")
    status = agent_table.insert(
        [{"prompt": request.prompt}], return_rows=True
    )
    result = AgentResult.model_validate(status.rows[0])
    # Conditional: save to chat history based on computed result
    if result.answer:
        chat_table.insert([{"role": "assistant", "content": result.answer}])
    return result
```

`extra="ignore"` is required because `status.rows` dicts contain every column; Pydantic would reject the extras without it.

Reference: [Pixeltable Starter Kit](https://github.com/pixeltable/pixeltable-starter-kit) | [core-api.md → Serving](core-api.md#serving-fastapirouter)

### Batch Processing Pattern

Use Pixeltable as a batch processing engine: no HTTP server, no FastAPI. A Python script that creates the schema, inserts data, lets computed columns process it, exports results to a serving database, and exits. Run it as a Cloud Run Job, ECS Task, K8s Job, Lambda, or a cron container.

```python
# schema.py: declarative schema (idempotent)
import pixeltable as pxt
from pixeltable.functions.huggingface import sentence_transformer
from pixeltable.functions.string import string_splitter
from pixeltable.functions.uuid import uuid7

pxt.create_dir('pipeline', if_exists='ignore')
embed_fn = sentence_transformer.using(model_id='all-MiniLM-L6-v2')

documents = pxt.create_table('pipeline.documents', {
    'title': pxt.String,
    'body': pxt.String,
    'source_id': pxt.String,
    'uuid': uuid7(),
    'timestamp': pxt.Timestamp,
}, primary_key=['uuid'], if_exists='ignore')

sentences = pxt.create_view(
    'pipeline.sentences', documents,
    iterator=string_splitter(text=documents.body, separators='sentence'),
    if_exists='ignore',
)
sentences.add_embedding_index(
    'text', idx_name='sentences_embed', string_embed=embed_fn, if_exists='ignore'
)
```

```python
# pipeline.py: ingest, compute, export, exit
import json
from datetime import datetime
from pixeltable.io.sql import export_sql
import schema

SERVING_DB_URL = 'postgresql+psycopg://user:pass@host/db'

with open('batch.json') as f:
    batch = json.load(f)

now = datetime.now()
for row in batch['documents']:
    row.setdefault('timestamp', now)

# Insert triggers computed columns: chunking, embeddings, etc.
schema.documents.insert(batch['documents'])

# Export structured results to serving DB
export_sql(
    schema.documents.select(
        schema.documents.source_id,
        schema.documents.title,
        schema.documents.body,
    ),
    'processed_documents',
    db_connect_str=SERVING_DB_URL,
    if_exists='replace',
)

# Verify semantic search works
sim = schema.sentences.text.similarity(string='test query')
results = (schema.sentences.order_by(sim, asc=False)
           .limit(3).select(schema.sentences.text, score=sim).collect())
```

Key points:
- `schema.py` is a flat module that creates everything on import (idempotent)
- `pipeline.py` is the driver: load data, insert, export, exit
- Computed columns fire automatically on insert (chunking, embeddings, LLM calls)
- `export_sql` pushes processed data to any SQL database (Postgres, MySQL, Snowflake, SQLite)
- Set `PIXELTABLE_HOME=/tmp/pixeltable` for ephemeral containers
- Use the `destination` parameter on `add_computed_column` to route generated media to cloud buckets (S3, GCS, Azure Blob)

Reference: [Starter Kit `batch/` directory](https://github.com/pixeltable/pixeltable-starter-kit/tree/main/batch)

### Export Workflow

```python
from pixeltable.io import export_parquet

# To Parquet
export_parquet(t, 'output/my_data/')

# Query result to Parquet
query = t.where(t.score > 0.8).select(t.title, t.content, t.score)
export_parquet(query, 'output/filtered/')

# To pandas
df = t.select(t.title, t.content).collect().to_pandas()
df.to_csv('output/data.csv', index=False)
```
