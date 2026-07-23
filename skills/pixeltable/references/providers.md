# Pixeltable AI Provider Reference

Complete examples for all 25+ built-in AI provider integrations. All functions live in `pixeltable.functions.*`.

## Quick Reference

Use this table to find the correct import, function, and output accessor for each provider:

| Provider | Import | Function | Extract answer |
|----------|--------|----------|----------------|
| OpenAI | `from pixeltable.functions.openai import chat_completions` | `chat_completions(messages=..., model='gpt-4o-mini')` | `.choices[0].message.content` |
| OpenAI Embeddings | `from pixeltable.functions.openai import embeddings` | `embeddings(input=..., model='text-embedding-3-small')` | `.data[0].embedding` |
| OpenAI TTS | `from pixeltable.functions.openai import speech` | `speech(input=..., model='tts-1', voice='alloy')` | *(returns Audio directly)* |
| OpenAI Transcription | `from pixeltable.functions.openai import transcriptions` | `transcriptions(audio=..., model='whisper-1')` | `.text` |
| OpenAI DALL-E | `from pixeltable.functions.openai import image_generations` | `image_generations(prompt=..., model='dall-e-3')` | `.data[0].url` |
| Anthropic | `from pixeltable.functions.anthropic import messages` | `messages(messages=..., model='claude-sonnet-4-20250514', max_tokens=1024)` | `.content[0].text` |
| Gemini | `from pixeltable.functions.gemini import generate_content, embed_content` | `generate_content(contents=..., model='gemini-2.5-flash')` | *(returns text directly)* |
| Together | `from pixeltable.functions.together import chat_completions` | `chat_completions(messages=..., model='meta-llama/...')` | `.choices[0].message.content` |
| Fireworks | `from pixeltable.functions.fireworks import chat_completions` | `chat_completions(messages=..., model='accounts/fireworks/...')` | `.choices[0].message.content` |
| Ollama | `from pixeltable.functions.ollama import chat, generate, embed` | `chat(messages=..., model='llama3.1')` | `.message.content` |
| Mistral | `from pixeltable.functions.mistralai import chat_completions` | `chat_completions(messages=..., model='mistral-large-latest')` | `.choices[0].message.content` |
| Groq | `from pixeltable.functions.groq import chat_completions` | `chat_completions(messages=..., model='llama-3.1-70b-versatile')` | `.choices[0].message.content` |
| DeepSeek | `from pixeltable.functions.deepseek import chat_completions` | `chat_completions(messages=..., model='deepseek-chat')` | `.choices[0].message.content` |
| OpenRouter | `from pixeltable.functions.openrouter import chat_completions` | `chat_completions(messages=..., model='anthropic/claude-sonnet-4-20250514')` | `.choices[0].message.content` |
| Hugging Face CLIP | `from pixeltable.functions.huggingface import clip` | `clip.using(model_id='openai/clip-vit-base-patch32')` | *(use as embedding index)* |
| Hugging Face ST | `from pixeltable.functions.huggingface import sentence_transformer` | `sentence_transformer.using(model_id='all-MiniLM-L6-v2')` | *(use as embedding index)* |
| Whisper (Local) | `from pixeltable.functions.whisper import transcribe` | `transcribe(audio=..., model='base')` | *(returns text directly)* |
| WhisperX (Local) | `from pixeltable.functions.whisperx import transcribe` | `transcribe(audio=..., model='large-v2', diarize=True)` | *(returns JSON with segments)* |
| Voyage AI | `from pixeltable.functions.voyageai import embed` | `embed(input=..., model='voyage-2')` | *(returns embedding directly)* |
| Jina AI | `from pixeltable.functions.jina import embeddings` | `embeddings(text=..., model='jina-embeddings-v3')` | *(use as embedding index)* |
| Twelve Labs | `from pixeltable.functions.twelvelabs import embed` | `embed(video_segment=..., model_name='marengo3.0')` | *(use as video embedding index)* |
| BFL FLUX | `from pixeltable.functions.bfl import generate` | `generate(prompt=..., width=1024, height=1024)` | *(returns Image directly)* |
| RunwayML | `from pixeltable.functions.runwayml import text_to_video` | `text_to_video(prompt=..., model='gen4.5')` | `.astype(pxt.Video)` |
| fal.ai | `from pixeltable.functions.fal import run` | `run(input=json, app='fal-ai/flux/schnell')` | *(returns JSON)* |
| Reve | `from pixeltable.functions.reve import create` | `create(prompt=...)` | *(returns Image directly)* |
| Fabric | `from pixeltable.functions.fabric import chat_completions` | `chat_completions(messages=..., model='gpt-4.1')` | `.choices[0].message.content` |
| llama.cpp | `from pixeltable.functions.llama_cpp import create_chat_completion` | `create_chat_completion(messages=..., repo_id='...', repo_filename='*q5_k_m.gguf')` | `.choices[0].message.content` |
| vLLM (Local) | `from pixeltable.functions.vllm import chat_completions, generate` | `chat_completions(messages=..., model='Qwen/Qwen2.5-0.5B-Instruct')` | *(returns VllmRequestOutput dict)* |
| YOLOX | `from pixeltable.functions.yolox import yolox` | `yolox(image=...)` | *(returns detection JSON)* |
| Replicate | `from pixeltable.functions.replicate import run` | `run(input=json, model='owner/model')` | *(returns JSON)* |
| Bedrock | `from pixeltable.functions.bedrock import converse` | `converse(messages=..., model='...')` | `.output.message.content[0].text` |

**Key patterns**: OpenAI-compatible providers (Together, Fireworks, Ollama, Mistral, Groq, DeepSeek, OpenRouter, Fabric) all return `.choices[0].message.content`. Anthropic returns `.content[0].text`. Embedding functions are used with `add_embedding_index()`, not accessed directly. Image generation functions (BFL, Reve) return `pxt.Image` directly.

---

## Full Examples

### OpenAI

### Chat Completions

```python
from pixeltable.functions.openai import chat_completions

# Basic
t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore',
)

# With system message
t.add_computed_column(
    response=chat_completions(
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': t.prompt}
        ],
        model='gpt-4o',
        max_tokens=1000,
        temperature=0.7
    ).choices[0].message.content,
    if_exists='ignore',
)

# Vision (image analysis)
t.add_computed_column(
    description=chat_completions(
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': 'Describe this image.'},
                {'type': 'image_url', 'image_url': {'url': t.image}}
            ]
        }],
        model='gpt-4o'
    ).choices[0].message.content,
    if_exists='ignore',
)

# JSON mode
t.add_computed_column(
    structured=chat_completions(
        messages=[{'role': 'user', 'content': t.text}],
        model='gpt-4o-mini',
        response_format={'type': 'json_object'}
    ).choices[0].message.content,
    if_exists='ignore',
)
```

### Embeddings

```python
from pixeltable.functions.openai import embeddings

t.add_computed_column(
    embed=embeddings(input=t.text, model='text-embedding-3-small').data[0].embedding,
    if_exists='ignore',
)

# As index
t.add_embedding_index('text', embedding=embeddings.using(model='text-embedding-3-small'), if_exists='ignore')
```

### Image Generation (DALL-E)

```python
from pixeltable.functions.openai import image_generations

t.add_computed_column(
    generated=image_generations(prompt=t.description, model='dall-e-3', size='1024x1024').data[0].url,
    if_exists='ignore',
)
```

### Speech (TTS)

```python
from pixeltable.functions.openai import speech

t.add_computed_column(audio=speech(input=t.text, model='tts-1', voice='alloy'), if_exists='ignore')
```

### Transcription

```python
from pixeltable.functions.openai import transcriptions

t.add_computed_column(transcript=transcriptions(audio=t.audio_file, model='whisper-1').text, if_exists='ignore')
```

## Anthropic

```python
from pixeltable.functions.anthropic import messages

# Basic
t.add_computed_column(
    response=messages(
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': t.prompt}]}],
        model='claude-sonnet-4-20250514',
        max_tokens=1024
    ).content[0].text,
    if_exists='ignore',
)

# With system prompt
t.add_computed_column(
    response=messages(
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': t.prompt}]}],
        model='claude-sonnet-4-20250514',
        system='You are an expert analyst.',
        max_tokens=2048
    ).content[0].text,
    if_exists='ignore',
)

# With tool calling
from pixeltable.functions.anthropic import messages, invoke_tools

tools = pxt.tools(search_fn, lookup_fn)
t.add_computed_column(
    response=messages(
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': t.prompt}]}],
        model='claude-sonnet-4-20250514',
        tools=tools,
        tool_choice=tools.choice(required=True),
        max_tokens=1024,
    ),
    if_exists='ignore',
)
t.add_computed_column(
    tool_results=invoke_tools(tools, t.response),
    if_exists='ignore',
)
```

## Google Gemini

```python
from pixeltable.functions.gemini import generate_content, embed_content

# Text generation
t.add_computed_column(response=generate_content(contents=t.prompt, model='gemini-2.5-flash'), if_exists='ignore')

# Embeddings (for add_embedding_index)
t.add_embedding_index(
    'text',
    string_embed=embed_content.using(model='gemini-embedding-2-preview'),
)

# Multimodal: pass images alongside text
t.add_computed_column(
    vision=generate_content(contents=[t.image, t.prompt], model='gemini-2.5-flash'),
    if_exists='ignore',
)
```

## Together AI

```python
from pixeltable.functions.together import chat_completions

t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo'
    ).choices[0].message.content,
    if_exists='ignore',
)
```

## Fireworks

```python
from pixeltable.functions.fireworks import chat_completions

t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='accounts/fireworks/models/llama-v3p1-70b-instruct'
    ).choices[0].message.content,
    if_exists='ignore',
)
```

## Ollama (Local)

```python
from pixeltable.functions.ollama import chat, generate, embed

# Chat
t.add_computed_column(
    response=chat(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='llama3.1'
    ).message.content,
    if_exists='ignore',
)

# Text generation
t.add_computed_column(
    completion=generate(prompt=t.prompt, model='llama3.1').response,
    if_exists='ignore',
)

# Embeddings
t.add_computed_column(embedding=embed(input=t.text, model='nomic-embed-text'), if_exists='ignore')
```

## Mistral AI

```python
from pixeltable.functions.mistralai import chat_completions

t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='mistral-large-latest'
    ).choices[0].message.content,
    if_exists='ignore',
)
```

## Groq

```python
from pixeltable.functions.groq import chat_completions

t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='llama-3.1-70b-versatile'
    ).choices[0].message.content,
    if_exists='ignore',
)
```

## DeepSeek

```python
from pixeltable.functions.deepseek import chat_completions

t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='deepseek-chat'
    ).choices[0].message.content,
    if_exists='ignore',
)
```

## OpenRouter

```python
from pixeltable.functions.openrouter import chat_completions

t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='anthropic/claude-sonnet-4-20250514'
    ).choices[0].message.content,
    if_exists='ignore',
)
```

## Hugging Face

### CLIP (Multimodal Embeddings)

```python
from pixeltable.functions.huggingface import clip

embed_fn = clip.using(model_id='openai/clip-vit-base-patch32')
t.add_embedding_index('image', embedding=embed_fn, if_exists='ignore')

sim = t.image.similarity(string='a photo of a dog')
results = t.order_by(sim, asc=False).limit(5).select(t.image, sim).collect()
```

### Sentence Transformers

```python
from pixeltable.functions.huggingface import sentence_transformer

embed_fn = sentence_transformer.using(model_id='all-MiniLM-L6-v2')
t.add_embedding_index('text', embedding=embed_fn, if_exists='ignore')

# For multilingual / high-quality (recommended for production)
embed_fn = sentence_transformer.using(model_id='intfloat/multilingual-e5-large-instruct')
t.add_embedding_index('text', string_embed=embed_fn, if_exists='ignore')
```

### Object Detection (DETR)

```python
from pixeltable.functions.huggingface import detr_for_object_detection

detect = detr_for_object_detection.using(model_id='facebook/detr-resnet-50')
t.add_computed_column(detections=detect(t.image, threshold=0.8), if_exists='ignore')
```

## Whisper (Local)

```python
from pixeltable.functions.whisper import transcribe

t.add_computed_column(transcript=transcribe(audio=t.audio, model='base'), if_exists='ignore')
```

## Voyage AI

```python
from pixeltable.functions.voyageai import embed

t.add_computed_column(embed=embed(input=t.text, model='voyage-2'), if_exists='ignore')
```

## WhisperX (Local)

Enhanced local transcription with word-level timestamps and speaker diarization.

```python
from pixeltable.functions.whisperx import transcribe

# Basic transcription
t.add_computed_column(
    transcript=transcribe(audio=t.audio, model='large-v2'),
    if_exists='ignore')

# With speaker diarization (requires HF_TOKEN for pyannote)
t.add_computed_column(
    transcript=transcribe(audio=t.audio, model='large-v2', diarize=True),
    if_exists='ignore')
```

## Jina AI

Embeddings and reranking for search pipelines.

```python
from pixeltable.functions.jina import embeddings, rerank

# Embeddings (multilingual, 89+ languages)
t.add_embedding_index('text',
    embedding=embeddings.using(model='jina-embeddings-v3', task='retrieval.passage'),
    if_exists='ignore')

# Reranking search results
t.add_computed_column(
    ranked=rerank(
        query=t.query,
        documents=t.candidates,
        model='jina-reranker-v2-base-multilingual',
        top_n=3,
        return_documents=True,
    ), if_exists='ignore')
```

## Twelve Labs

Video understanding via multimodal embeddings.

```python
from pixeltable.functions.twelvelabs import embed

# Add video embedding index for semantic video search
t.add_embedding_index('video',
    embedding=embed.using(model_name='marengo3.0'),
    if_exists='ignore')

# Search videos by text query
sim = t.video.similarity(string='person giving a presentation')
results = t.order_by(sim, asc=False).limit(5).select(t.video, sim).collect()
```

## BFL FLUX

Image generation and editing with Black Forest Labs FLUX models.

```python
from pixeltable.functions.bfl import generate, edit, expand, fill

# Text-to-image generation
t.add_computed_column(
    image=generate(prompt=t.description, width=1024, height=1024),
    if_exists='ignore')

# Edit an existing image
t.add_computed_column(
    edited=edit(image=t.image, prompt='Make the sky more dramatic'),
    if_exists='ignore')

# Expand image canvas (outpainting)
t.add_computed_column(
    expanded=expand(image=t.image, prompt='Extend the landscape', top=200, right=200),
    if_exists='ignore')

# Inpaint masked region
t.add_computed_column(
    filled=fill(image=t.image, mask=t.mask, prompt='A wooden bench'),
    if_exists='ignore')
```

## RunwayML

AI video generation and transformation.

```python
from pixeltable.functions.runwayml import text_to_video, image_to_video

# Generate video from text
t.add_computed_column(
    video=text_to_video(
        prompt=t.description, model='gen4.5', ratio='1280:720', duration=5,
    ).astype(pxt.Video),
    if_exists='ignore')

# Animate an image into a video
t.add_computed_column(
    video=image_to_video(
        prompt=t.description, image=t.image, model='gen4.5', ratio='1280:720',
    ).astype(pxt.Video),
    if_exists='ignore')
```

## fal.ai

Run any model on fal.ai's inference platform.

```python
from pixeltable.functions.fal import run

# Image generation with FLUX Schnell
t.add_computed_column(
    result=run(
        input={'prompt': t.description, 'image_size': 'landscape_16_9'},
        app='fal-ai/flux/schnell',
    ), if_exists='ignore')
```

## Reve

Image generation, editing, and remixing.

```python
from pixeltable.functions.reve import create, edit, remix

# Text-to-image
t.add_computed_column(
    image=create(prompt=t.description),
    if_exists='ignore')

# Edit an existing image
t.add_computed_column(
    edited=edit(image=t.image, edit_instruction='Make it look like a watercolor painting'),
    if_exists='ignore')
```

## Microsoft Fabric

Azure OpenAI models via Microsoft Fabric notebooks (no API key needed in Fabric environment).

```python
from pixeltable.functions.fabric import chat_completions, embeddings

# Chat
t.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': t.prompt}],
        model='gpt-4.1',
    ).choices[0].message.content,
    if_exists='ignore')

# Embeddings
t.add_embedding_index('text',
    embedding=embeddings.using(model='text-embedding-3-small'),
    if_exists='ignore')
```

## llama.cpp

Run local GGUF models via llama.cpp (auto-downloaded from Hugging Face).

```python
from pixeltable.functions.llama_cpp import create_chat_completion

t.add_computed_column(
    response=create_chat_completion(
        messages=[{'role': 'user', 'content': t.prompt}],
        repo_id='Qwen/Qwen2.5-0.5B-Instruct-GGUF',
        repo_filename='*q5_k_m.gguf',
    ), if_exists='ignore')
```

## Replicate

Run any model on Replicate's cloud platform.

```python
from pixeltable.functions.replicate import run

t.add_computed_column(
    result=run(input={'prompt': t.description}, model='stability-ai/sdxl'),
    if_exists='ignore')
```

## Bedrock

AWS Bedrock models.

```python
from pixeltable.functions.bedrock import converse, invoke_tools

# Chat
t.add_computed_column(
    response=converse(
        messages=[{'role': 'user', 'content': [{'text': t.prompt}]}],
        model='anthropic.claude-sonnet-4-20250514-v1:0',
    ).output.message.content[0].text,
    if_exists='ignore')

# Tool calling
tools = pxt.tools(search_fn, lookup_fn)
t.add_computed_column(
    response=converse(
        messages=[{'role': 'user', 'content': [{'text': t.prompt}]}],
        model='anthropic.claude-sonnet-4-20250514-v1:0',
        tools=tools,
    ), if_exists='ignore')
t.add_computed_column(
    tool_results=invoke_tools(tools, t.response),
    if_exists='ignore')
```

## vLLM (Local)

High-throughput local LLM inference with HuggingFace models. Requires `pip install vllm`.

```python
from pixeltable.functions.vllm import chat_completions, generate

t.add_computed_column(
    result=chat_completions(t.messages, model='Qwen/Qwen2.5-0.5B-Instruct'),
    if_exists='ignore',
)

t.add_computed_column(
    completion=generate(
        t.prompt,
        model='Qwen/Qwen2.5-0.5B-Instruct',
        sampling_params={'max_tokens': 256, 'temperature': 0.7},
    ),
    if_exists='ignore',
)
```

## YOLOX

Local object detection.

```python
from pixeltable.functions.yolox import yolox

t.add_computed_column(detections=yolox(t.image), if_exists='ignore')
```
