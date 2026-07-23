# Anti-Patterns: Training-Distribution Biases LLMs Bring to Pixeltable

LLMs are trained on millions of imperative Python examples using pandas, LangChain, standalone vector DBs, and raw loops. These priors are **wrong for Pixeltable**. This page lists every common bias and the correct idiomatic shape.

## The 5 Macro Biases (High Priority)

These are structural — getting any one wrong means the entire solution is non-idiomatic.

### 1. Framework addiction (LangChain / LlamaIndex / Haystack / LangGraph)

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

splitter = RecursiveCharacterTextSplitter(chunk_size=512)
chunks = splitter.split_documents(docs)
vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())
chain = RetrievalQA.from_chain_type(ChatOpenAI(), retriever=vectorstore.as_retriever())
```

**Right:**
```python
import pixeltable as pxt
from pixeltable.functions.document import document_splitter
from pixeltable.functions.openai import chat_completions, embeddings

docs = pxt.create_table('app.docs', {'doc': pxt.Document}, if_exists='ignore')
chunks = pxt.create_view('app.chunks', docs,
    iterator=document_splitter(docs.doc, separators='token_limit', limit=512),
    if_exists='ignore')
chunks.add_embedding_index('text', embedding=embeddings(model='text-embedding-3-small'), if_exists='ignore')
```

**Why:** Pixeltable handles chunking, embedding, indexing, and retrieval natively. Adding a framework on top creates redundant abstraction, breaks incremental updates, and loses version control.

---

### 2. pandas as working store

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
import pandas as pd

df = pd.read_csv('data.csv')
df['summary'] = df['text'].apply(lambda x: call_openai(x))
df['embedding'] = df['text'].apply(lambda x: get_embedding(x))
df.to_parquet('output.parquet')
```

**Right:**
```python
import pixeltable as pxt
from pixeltable.functions.openai import chat_completions, embeddings

t = pxt.create_table('app.data', source='data.csv', if_exists='ignore')
t.add_computed_column(summary=chat_completions(
    messages=[{'role': 'user', 'content': 'Summarize: ' + t.text}],
    model='gpt-4o-mini'
).choices[0].message.content, if_exists='ignore')
t.add_embedding_index('text', embedding=embeddings(model='text-embedding-3-small'), if_exists='ignore')

# Export ONLY at the end if needed
df = t.select(t.text, t.summary).collect().to_pandas()
```

**Why:** pandas has no persistence, no incremental computation, no automatic retry on API failures, and no version control. Pixeltable tables persist, recompute only new/failed rows, and maintain full history.

---

### 3. For-loops calling AI models

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
results = []
for _, row in df.iterrows():
    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': row['text']}]
    )
    results.append(response.choices[0].message.content)
df['summary'] = results
```

**Right:**
```python
from pixeltable.functions.openai import chat_completions

t.add_computed_column(
    summary=chat_completions(
        messages=[{'role': 'user', 'content': t.text}],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore'
)
```

**Why:** Computed columns handle batching, rate limiting (configured in `~/.pixeltable/config.toml`), automatic caching (never re-calls for unchanged rows), error isolation per row, and retry via `recompute_columns()`. A for-loop has none of this.

---

### 4. Separate vector database

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.Client()
ef = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ['OPENAI_API_KEY'])
collection = client.create_collection("docs", embedding_function=ef)
collection.add(documents=texts, ids=ids)
results = collection.query(query_texts=["search query"], n_results=5)
```

**Right:**
```python
from pixeltable.functions.openai import embeddings

t.add_embedding_index('text',
    embedding=embeddings(model='text-embedding-3-small'),
    if_exists='ignore')

sim = t.text.similarity(string='search query')
results = t.order_by(sim, asc=False).limit(5).select(t.text, sim).collect()
```

**Why:** The embedding index lives inside the table — it updates automatically when rows are inserted, shares the same version history, and requires no separate service. Querying uses the same expression language as everything else.

---

### 5. While-loop agent patterns

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
messages = [{"role": "user", "content": user_query}]
while True:
    response = openai.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
    if response.choices[0].finish_reason == "stop":
        break
    tool_calls = response.choices[0].message.tool_calls
    for tc in tool_calls:
        result = execute_tool(tc)
        messages.append({"role": "tool", "content": result, "tool_call_id": tc.id})
```

**Right:**
```python
from pixeltable.functions.openai import chat_completions, invoke_tools

tools = pxt.tools(search_docs, get_weather)

agent = pxt.create_table('app.agent', {'prompt': pxt.String}, if_exists='ignore')
agent.add_computed_column(response=chat_completions(
    messages=[{'role': 'user', 'content': agent.prompt}],
    model='gpt-4o', tools=tools, tool_choice=tools.choice(required=True)
), if_exists='ignore')
agent.add_computed_column(tool_output=invoke_tools(tools, agent.response), if_exists='ignore')
agent.add_computed_column(final=chat_completions(
    messages=[{'role': 'user', 'content': agent.prompt + '\n\nContext: ' + agent.tool_output.astype(pxt.String)}],
    model='gpt-4o'
).choices[0].message.content, if_exists='ignore')

agent.insert([{'prompt': 'What is the weather in NYC?'}])
```

**Why:** The declarative chain persists every intermediate result, enables debugging by inspecting any column, retries individual steps without re-running the whole chain, and maintains a complete audit trail. The while-loop loses all intermediate state on failure.

---

## The Full 15-Bias Reference

| # | LLM's prior reaches for | Correct Pixeltable shape | Why the prior is wrong |
|---|--------------------------|--------------------------|------------------------|
| 1 | LangChain / LlamaIndex / Haystack / LangGraph | `create_view` + iterator + `add_embedding_index` + `pxt.tools()` | Redundant abstraction; breaks incremental updates |
| 2 | `pandas.DataFrame` as working store | Pixeltable table is the store; `.to_pandas()` for export only | No persistence, no incremental, no versioning |
| 3 | `for row in ...:` calling AI per row | Computed column | No batching, no rate limits, no caching, no retry |
| 4 | Pinecone / Chroma / FAISS / Qdrant / pgvector | `t.add_embedding_index(col, embedding=fn)` | Separate service; no auto-update; no version control |
| 5 | Embeddings as `list[list[float]]` in memory | Stored as computed column with type `pxt.Array` | Volatile; lost on restart; can't query |
| 6 | `while not done:` agent loop | Table where insert triggers computed-column chain | Loses intermediate state; no audit trail |
| 7 | `cv2.VideoCapture` / Pillow loops for media | `frame_iterator` + `pixeltable.functions.image.*` | No persistence; manual frame management |
| 8 | `psycopg2` / `sqlalchemy` against `~/.pixeltable/pgdata` | SDK only (never touch embedded Postgres) | Corrupts internal schema; breaks versioning |
| 9 | `async def` FastAPI endpoints calling Pixeltable | `def` endpoints (Pixeltable is synchronous) | Deadlocks or silent failures under async |
| 10 | Drop + recreate tables as "initialization" | `if_exists='ignore'` on `create_table` / `create_view` | Data loss; breaks incremental computation |
| 11 | `if_exists='ignore'` to "update" column logic | `t.drop_column('col')` then recreate | `if_exists='ignore'` is a no-op if column exists |
| 12 | Threading `api_key=` into every provider call | Environment variables or `~/.pixeltable/config.toml` | Leaks keys; breaks portability |
| 13 | `openai-whisper` / `faster-whisper` imperative | `whisper.transcribe` or `openai.transcriptions` as computed column | No caching; manual error handling |
| 14 | Pydantic / dataclass schemas for table definition | `{'col': pxt.Type}` dict | Pixeltable has its own type system; Pydantic adds nothing |
| 15 | Chat history in Python `list` or Redis | Table with embedding index for semantic memory retrieval | Volatile or disconnected from the data layer |

## Per-Bias Code Examples (6–15)

### 5. Embeddings as raw lists

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
embeddings_cache = []
for text in texts:
    emb = openai.embeddings.create(input=text, model="text-embedding-3-small")
    embeddings_cache.append(emb.data[0].embedding)
# Now what? Save to pickle? Rebuild on every restart?
```

**Right:**
```python
from pixeltable.functions.openai import embeddings
t.add_embedding_index('text', embedding=embeddings(model='text-embedding-3-small'), if_exists='ignore')
```

### 7. cv2 / Pillow loops for video/image processing

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
import cv2
cap = cv2.VideoCapture('video.mp4')
frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if frame_count % 30 == 0:
        frames.append(frame)
```

**Right:**
```python
from pixeltable.functions.video import frame_iterator

frames = pxt.create_view('app.frames', videos,
    iterator=frame_iterator(videos.video, fps=1.0),
    if_exists='ignore')
```

### 8. Direct Postgres access

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
import psycopg2
conn = psycopg2.connect(dbname='pixeltable', host='/tmp/.s.PGSQL.5432')
cur = conn.cursor()
cur.execute("SELECT * FROM ...")  # NEVER DO THIS
```

**Right:** Always use the Pixeltable SDK. The embedded Postgres is an implementation detail.

### 9. async def with Pixeltable

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
@app.post("/query")
async def query_endpoint(q: str):
    results = t.where(t.text.contains(q)).collect()  # May deadlock
    return results
```

**Right:**
```python
@app.post("/query")
def query_endpoint(q: str):
    results = t.where(t.text.contains(q)).select(t.text).collect()
    return results.to_pandas().to_dict(orient='records')
```

### 10. Drop + recreate as init

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
pxt.drop_table('app.data', force=True)
t = pxt.create_table('app.data', {'text': pxt.String})
```

**Right:**
```python
t = pxt.create_table('app.data', {'text': pxt.String}, if_exists='ignore')
```

### 11. if_exists='ignore' to update logic

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
# Bug in summary prompt — "fix" by re-running:
t.add_computed_column(summary=fixed_expression, if_exists='ignore')
# ↑ SILENT NO-OP — column already exists with old logic
```

**Right:**
```python
t.drop_column('summary')
t.add_computed_column(summary=fixed_expression)
```

### 12. Hardcoding API keys

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
from pixeltable.functions.openai import chat_completions
t.add_computed_column(resp=chat_completions(..., api_key='sk-abc123'))
```

**Right:** Set `OPENAI_API_KEY` env var or add to `~/.pixeltable/config.toml`:
```toml
[openai]
api_key = 'sk-...'
```

### 13. Imperative whisper

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
import whisper
model = whisper.load_model("base")
for audio_file in audio_files:
    result = model.transcribe(audio_file)
    transcripts.append(result["text"])
```

**Right:**
```python
from pixeltable.functions.whisper import transcribe

t.add_computed_column(
    transcript=transcribe(t.audio, model='base').text,
    if_exists='ignore'
)
```

### 14. Pydantic schemas

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
from pydantic import BaseModel

class Document(BaseModel):
    title: str
    content: str
    embedding: list[float]

# Then trying to map this to Pixeltable somehow...
```

**Right:**
```python
t = pxt.create_table('app.docs', {
    'title': pxt.String,
    'content': pxt.String,
}, if_exists='ignore')
# Embeddings are computed, not schema-declared
t.add_embedding_index('content', embedding=embed_fn, if_exists='ignore')
```

### 15. Chat history in lists or Redis

**Wrong:**
```python
# ANTI-PATTERN — illustrative only, do not copy
chat_history = []  # Lost on restart
# or
import redis
r = redis.Redis()
r.lpush(f"chat:{user_id}", json.dumps(message))
```

**Right:**
```python
memory = pxt.create_table('app.memory', {
    'role': pxt.String,
    'content': pxt.String,
    'session_id': pxt.String,
    'timestamp': pxt.Timestamp,
}, if_exists='ignore')
memory.add_embedding_index('content',
    embedding=embeddings(model='text-embedding-3-small'),
    if_exists='ignore')

# Retrieve relevant past context
sim = memory.content.similarity(string=current_query)
context = memory.where(memory.session_id == sid).order_by(sim, asc=False).limit(5).collect()
```

---

## Cross-References

- [SKILL.md → Critical Warnings](../SKILL.md#critical-warnings--read-before-writing-code) — hallucinated API fixes
- [SKILL.md → Common Pitfalls](../SKILL.md#common-pitfalls) — wrong/right table for specific APIs
- [core-api.md → Common Pitfalls](core-api.md#common-pitfalls) — extended examples
- [Migration guides](https://docs.pixeltable.com/migrate/from-agent-frameworks) — porting from LangChain/LlamaIndex
