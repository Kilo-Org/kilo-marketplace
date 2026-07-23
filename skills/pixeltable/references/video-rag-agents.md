# Video RAG Agent

A complete recipe that combines video processing, document/transcript retrieval, and a tool-calling agent into one pipeline. Insert a video and a question — the agent automatically searches frames, transcripts, and documents to answer it.

## Full Pipeline

```python
import pixeltable as pxt
from pixeltable.functions.video import frame_iterator, extract_audio
from pixeltable.functions.audio import audio_splitter
from pixeltable.functions.string import string_splitter
from pixeltable.functions.openai import chat_completions, transcriptions
from pixeltable.functions.huggingface import clip, sentence_transformer
from pixeltable.functions.anthropic import messages, invoke_tools
from pixeltable.functions import image as pxt_image
from datetime import datetime

pxt.create_dir('vrag', if_exists='ignore')

# ── 1. Video ingestion ──────────────────────────────────────────────

videos = pxt.create_table('vrag.videos', {
    'video': pxt.Video,
    'title': pxt.String,
}, if_exists='ignore')

# ── 2. Keyframe extraction + CLIP visual search ─────────────────────

frames = pxt.create_view('vrag.frames', videos,
    iterator=frame_iterator(videos.video, keyframes_only=True),
    if_exists='ignore')

frames.add_computed_column(
    thumbnail=pxt_image.b64_encode(
        pxt_image.thumbnail(frames.frame, size=(320, 320))),
    if_exists='ignore')

frames.add_embedding_index('frame',
    embedding=clip.using(model_id='openai/clip-vit-base-patch32'),
    if_exists='ignore')

# Describe each frame with a vision LLM
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

# ── 3. Audio extraction → transcription → sentence embedding ────────

videos.add_computed_column(
    audio=extract_audio(videos.video, format='mp3'),
    if_exists='ignore')

audio_segments = pxt.create_view('vrag.audio_segments', videos,
    iterator=audio_splitter(
        audio=videos.audio, duration=30.0, min_silence_len=0.3, trim_leading_silence=True
    ),
    if_exists='ignore')

audio_segments.add_computed_column(
    transcription=transcriptions(
        audio=audio_segments.audio_segment, model='whisper-1'),
    if_exists='ignore')

sentences = pxt.create_view('vrag.sentences',
    audio_segments.where(audio_segments.transcription != None),
    iterator=string_splitter(
        text=audio_segments.transcription.text, separators='sentence'),
    if_exists='ignore')

embed_fn = sentence_transformer.using(model_id='all-MiniLM-L6-v2')
sentences.add_embedding_index('text', string_embed=embed_fn, if_exists='ignore')

# ── 4. Query functions (become agent tools) ──────────────────────────

@pxt.query
def search_video_frames(query_text: str):
    """Search video frames by visual similarity using CLIP."""
    sim = frames.frame.similarity(string=query_text)
    return frames.order_by(sim, asc=False).limit(10).select(
        frames.description, frames.thumbnail, score=sim)

@pxt.query
def search_transcripts(query_text: str):
    """Search video transcripts by semantic similarity."""
    sim = sentences.text.similarity(string=query_text)
    return sentences.where(sim > 0.5).order_by(sim, asc=False).select(
        sentences.text, score=sim).limit(20)

@pxt.udf
def web_search(keywords: str) -> str:
    """Search the web for additional context."""
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.news(keywords=keywords, max_results=5))
        return '\n'.join(
            f"{r['title']}: {r['body']}" for r in results
        ) if results else 'No results.'

# ── 5. Context assembly ─────────────────────────────────────────────

@pxt.udf
def assemble_context(
    question: str,
    tool_outputs: list | None,
    transcript_context: list | None,
    frame_context: list | None,
) -> str:
    parts = [f"QUESTION: {question}"]

    tool_str = str(tool_outputs) if tool_outputs else 'N/A'
    parts.append(f"\n<tool_results>\n{tool_str}\n</tool_results>")

    if transcript_context:
        transcript_str = '\n'.join(
            f"- {item.get('text', '')}"
            for item in transcript_context if isinstance(item, dict)
        ) or 'N/A'
    else:
        transcript_str = 'N/A'
    parts.append(f"\n<transcript_excerpts>\n{transcript_str}\n</transcript_excerpts>")

    if frame_context:
        frame_str = '\n'.join(
            f"- {item.get('description', '')}"
            for item in frame_context if isinstance(item, dict)
        ) or 'N/A'
    else:
        frame_str = 'N/A'
    parts.append(f"\n<visual_descriptions>\n{frame_str}\n</visual_descriptions>")

    return '\n'.join(parts)

# ── 6. Agent pipeline ───────────────────────────────────────────────

tools = pxt.tools(web_search, search_transcripts, search_video_frames)

agent = pxt.create_table('vrag.agent', {
    'prompt': pxt.String,
    'timestamp': pxt.Timestamp,
    'system_prompt': pxt.String,
    'max_tokens': pxt.Int,
    'temperature': pxt.Float,
}, if_exists='ignore')

# Step 1: Initial LLM call — tool selection
agent.add_computed_column(
    initial_response=messages(
        model='claude-sonnet-4-20250514',
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': agent.prompt}]}],
        tools=tools,
        tool_choice=tools.choice(required=True),
        max_tokens=agent.max_tokens,
        model_kwargs={'system': agent.system_prompt, 'temperature': agent.temperature},
    ), if_exists='ignore')

# Step 2: Execute the tools the LLM selected
agent.add_computed_column(
    tool_output=invoke_tools(tools, agent.initial_response),
    if_exists='ignore')

# Step 3: RAG context from transcripts and frames
agent.add_computed_column(
    transcript_context=search_transcripts(agent.prompt),
    if_exists='ignore')

agent.add_computed_column(
    frame_context=search_video_frames(agent.prompt),
    if_exists='ignore')

# Step 4: Assemble all context
agent.add_computed_column(
    context=assemble_context(
        agent.prompt, agent.tool_output,
        agent.transcript_context, agent.frame_context),
    if_exists='ignore')

# Step 5: Final LLM call with full context
agent.add_computed_column(
    final_response=messages(
        model='claude-sonnet-4-20250514',
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': agent.context}]}],
        max_tokens=agent.max_tokens,
        model_kwargs={
            'system': 'Answer based on the video transcripts, visual descriptions, and tool results. Cite timestamps when possible.',
            'temperature': agent.temperature,
        },
    ), if_exists='ignore')

# Step 6: Extract answer
agent.add_computed_column(
    answer=agent.final_response.content[0].text,
    if_exists='ignore')
```

## Usage

```python
# Insert videos
videos.insert([
    {'video': 'lecture.mp4', 'title': 'ML Lecture'},
    {'video': 'https://example.com/demo.mp4', 'title': 'Product Demo'},
])

# Ask a question — the full pipeline runs automatically
agent.insert([{
    'prompt': 'What visual examples does the lecturer use to explain gradient descent?',
    'timestamp': datetime.now(),
    'system_prompt': 'Use search_video_frames for visual content and search_transcripts for spoken content.',
    'max_tokens': 1024,
    'temperature': 0.7,
}])

result = agent.order_by(agent.timestamp, asc=False).limit(1).select(agent.answer).collect()
```

## How It Works

The pipeline is a chain of computed columns. Inserting a row into `agent` triggers these steps automatically:

1. **Initial LLM call** — Claude selects which tools to call (transcript search, frame search, web search)
2. **Tool execution** — `invoke_tools()` runs the selected `@pxt.query` / `@pxt.udf` functions
3. **RAG retrieval** — Transcript and frame similarity searches run in parallel as computed columns
4. **Context assembly** — A UDF merges tool outputs, transcript excerpts, and visual descriptions
5. **Final LLM call** — Claude synthesizes everything into a grounded answer

### Key building blocks

| Concept | Function | Purpose |
|---------|----------|---------|
| `frame_iterator` | `pxt.create_view(..., iterator=frame_iterator(...))` | Extract video keyframes |
| `audio_splitter` | `pxt.create_view(..., iterator=audio_splitter(...))` | Split audio into chunks |
| `transcriptions` | `t.add_computed_column(transcription=transcriptions(...))` | Transcribe audio chunks |
| `string_splitter` | `pxt.create_view(..., iterator=string_splitter(...))` | Split transcript into sentences |
| `add_embedding_index` | `t.add_embedding_index('col', embedding=fn)` | Enable similarity search |
| `@pxt.query` | `def search_transcripts(query_text: str): ...` | Reusable retrieval + agent tool |
| `pxt.tools()` | `tools = pxt.tools(fn1, fn2)` | Bundle functions as LLM tools |
| `invoke_tools()` | `invoke_tools(tools, response)` | Execute the tools the LLM chose |

## Adapting This Recipe

- **Swap providers**: Replace `messages` (Anthropic) with `chat_completions` (OpenAI/Together/etc.) — see [providers.md](providers.md#quick-reference) for import and output shapes
- **Add document RAG**: Add a `document_splitter` view and a `search_documents` query function to the tools list
- **Use local models**: Replace OpenAI transcription with `transcribe()` (`from pixeltable.functions.whisper import transcribe`) and use `chat` (`from pixeltable.functions.ollama import chat`) for the LLM — see [workflows.md → Local LLM Pipeline](workflows.md#local-llm-pipeline-ollama)
- **Serve via API**: Wrap the pipeline in a FastAPI endpoint — see [workflows.md → FastAPI App Pattern](workflows.md#fastapi-app-pattern)
