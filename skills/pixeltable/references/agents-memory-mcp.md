# Agent with Memory and MCP Tools

A production recipe combining a tool-calling agent with persistent memory (chat history + knowledge bank) and external MCP server integration. The agent remembers past conversations, retrieves stored facts, and can call both local tools and remote MCP tools.

## Workflow

1. Create a chat history table with embedding index for semantic recall
2. Create a memory bank table for long-lived facts and preferences
3. Write `@pxt.query` retrieval functions for both (filtered by `user_id`)
4. Write local `@pxt.udf` tools (including a `save_memory` tool for the LLM to store facts)
5. (Optional) Load MCP tools with `pxt.mcp_udfs()` and combine with local tools
6. Bundle all tools with `pxt.tools()`
7. Create agent table with computed column chain: LLM -> invoke_tools -> context assembly -> final answer
8. After each agent response, save the conversation to chat history for future recall

## Full Pipeline

```python
import pixeltable as pxt
from pixeltable.functions.openai import chat_completions, embeddings
from pixeltable.functions.openai import invoke_tools as openai_invoke_tools
from pixeltable.functions.huggingface import sentence_transformer
from datetime import datetime

pxt.create_dir('agent_app', if_exists='ignore')

# ── 1. Memory: Chat History ─────────────────────────────────────────
# Stores every user and assistant message with embeddings for recall.

chat_history = pxt.create_table('agent_app.chat_history', {
    'role': pxt.String,         # 'user' or 'assistant'
    'content': pxt.String,
    'timestamp': pxt.Timestamp,
    'user_id': pxt.String,
}, if_exists='ignore')

embed_fn = sentence_transformer.using(model_id='all-MiniLM-L6-v2')
chat_history.add_embedding_index('content', string_embed=embed_fn, if_exists='ignore')

@pxt.query
def recall_chat_history(query_text: str, user_id: str, top_k: int = 5):
    """Retrieve past conversation turns relevant to the current query."""
    sim = chat_history.content.similarity(string=query_text)
    return (
        chat_history
        .where((chat_history.user_id == user_id) & (sim > 0.5))
        .order_by(sim, asc=False)
        .limit(top_k)
        .select(chat_history.role, chat_history.content, score=sim)
    )

# ── 2. Memory: Knowledge Bank ───────────────────────────────────────
# Stores user preferences, facts, and persistent notes.

memory_bank = pxt.create_table('agent_app.memory_bank', {
    'content': pxt.String,
    'category': pxt.String,     # 'preference', 'fact', 'note'
    'user_id': pxt.String,
    'timestamp': pxt.Timestamp,
}, if_exists='ignore')

memory_bank.add_embedding_index('content', string_embed=embed_fn, if_exists='ignore')

@pxt.query
def recall_memories(query_text: str, user_id: str, top_k: int = 3):
    """Retrieve relevant stored memories for a user."""
    sim = memory_bank.content.similarity(string=query_text)
    return (
        memory_bank
        .where((memory_bank.user_id == user_id) & (sim > 0.5))
        .order_by(sim, asc=False)
        .limit(top_k)
        .select(memory_bank.content, memory_bank.category, score=sim)
    )

# Seed memories
memory_bank.insert([
    {'content': 'User prefers concise answers with code examples.',
     'category': 'preference', 'user_id': 'user_1', 'timestamp': datetime.now()},
    {'content': 'Project uses FastAPI with Python 3.12.',
     'category': 'fact', 'user_id': 'user_1', 'timestamp': datetime.now()},
])

# ── 3. Local tools ──────────────────────────────────────────────────

@pxt.udf
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    weather_data = {
        'new york': 'Sunny, 72F', 'london': 'Cloudy, 58F',
        'tokyo': 'Rainy, 65F',    'paris': 'Partly cloudy, 68F',
    }
    return weather_data.get(city.lower(), f'Weather data not available for {city}')

@pxt.udf
def save_memory(content: str, category: str, user_id: str) -> str:
    """Save a new fact or preference to the user's memory bank."""
    memory_bank.insert([{
        'content': content, 'category': category,
        'user_id': user_id, 'timestamp': datetime.now(),
    }])
    return f'Saved to memory: {content}'

# ── 4. MCP tools (optional) ─────────────────────────────────────────
# Load tools from any MCP-compliant server and combine with local tools.

# mcp_tools = pxt.mcp_udfs('http://localhost:8000/mcp')
# tools = pxt.tools(get_weather, save_memory, recall_memories, *mcp_tools)

# Without MCP:
tools = pxt.tools(get_weather, save_memory, recall_memories)

# ── 5. Context assembly ─────────────────────────────────────────────

@pxt.udf
def build_prompt(
    question: str,
    tool_outputs: list | None,
    chat_context: list | None,
    memory_context: list | None,
) -> str:
    parts = [f"USER QUESTION: {question}"]

    if memory_context:
        mem_str = '\n'.join(
            f"- [{item.get('category', '?')}] {item.get('content', '')}"
            for item in memory_context if isinstance(item, dict)
        )
        parts.append(f"\n[USER MEMORIES]\n{mem_str}")

    if chat_context:
        chat_str = '\n'.join(
            f"- {item.get('role', '?')}: {item.get('content', '')}"
            for item in chat_context if isinstance(item, dict)
        )
        parts.append(f"\n[RECENT CONVERSATION]\n{chat_str}")

    if tool_outputs:
        parts.append(f"\n[TOOL RESULTS]\n{tool_outputs}")

    return '\n'.join(parts)

# ── 6. Agent pipeline ───────────────────────────────────────────────

agent = pxt.create_table('agent_app.agent', {
    'prompt': pxt.String,
    'user_id': pxt.String,
    'timestamp': pxt.Timestamp,
    'system_prompt': pxt.String,
    'max_tokens': pxt.Int,
    'temperature': pxt.Float,
}, if_exists='ignore')

# Step 1: Tool selection
agent.add_computed_column(
    initial_response=chat_completions(
        messages=[{'role': 'user', 'content': agent.prompt}],
        model='gpt-4o-mini',
        tools=tools,
    ), if_exists='ignore')

# Step 2: Execute tools
agent.add_computed_column(
    tool_output=openai_invoke_tools(tools, agent.initial_response),
    if_exists='ignore')

# Step 3: Retrieve memory context (runs in parallel as separate computed columns)
agent.add_computed_column(
    chat_context=recall_chat_history(agent.prompt, agent.user_id),
    if_exists='ignore')

agent.add_computed_column(
    memory_context=recall_memories(agent.prompt, agent.user_id),
    if_exists='ignore')

# Step 4: Assemble prompt
agent.add_computed_column(
    context=build_prompt(
        agent.prompt, agent.tool_output,
        agent.chat_context, agent.memory_context),
    if_exists='ignore')

# Step 5: Final response
agent.add_computed_column(
    final_response=chat_completions(
        messages=[
            {'role': 'system', 'content': agent.system_prompt},
            {'role': 'user', 'content': agent.context},
        ],
        model='gpt-4o-mini',
        max_tokens=agent.max_tokens,
        temperature=agent.temperature,
    ), if_exists='ignore')

agent.add_computed_column(
    answer=agent.final_response.choices[0].message.content,
    if_exists='ignore')
```

## Usage

```python
# Ask a question — memory and tools are used automatically
agent.insert([{
    'prompt': 'What is the weather in Tokyo? Remember that I like brief answers.',
    'user_id': 'user_1',
    'timestamp': datetime.now(),
    'system_prompt': 'You are a helpful assistant. Use tools and memories to personalize your response.',
    'max_tokens': 512,
    'temperature': 0.7,
}])

result = agent.order_by(agent.timestamp, asc=False).limit(1).select(agent.answer).collect()

# Save the conversation to chat history for future recall
agent_row = agent.order_by(agent.timestamp, asc=False).limit(1).select(
    agent.prompt, agent.answer, agent.user_id, agent.timestamp).collect()
row = agent_row[0]

chat_history.insert([
    {'role': 'user', 'content': row['prompt'],
     'user_id': row['user_id'], 'timestamp': row['timestamp']},
    {'role': 'assistant', 'content': row['answer'],
     'user_id': row['user_id'], 'timestamp': datetime.now()},
])
```

## Adding MCP Tools

Connect to any MCP-compliant server to extend the agent with external tools:

```python
# Load tools from an MCP server
mcp_tools = pxt.mcp_udfs('http://localhost:8000/mcp')

# Inspect available tools
for tool in mcp_tools:
    print(f'- {tool.name}: {tool.comment()}')

# Combine with local tools
tools = pxt.tools(get_weather, save_memory, recall_memories, *mcp_tools)
```

MCP tools are called via `invoke_tools()` exactly like local UDFs — no special handling needed.

## Multi-Provider invoke_tools

The agent pipeline works with any provider that supports tool calling:

| Provider | Import | invoke_tools |
|----------|--------|-------------|
| OpenAI | `from pixeltable.functions.openai import invoke_tools as openai_invoke_tools` | `openai_invoke_tools(tools, response)` |
| Anthropic | `from pixeltable.functions.anthropic import invoke_tools as anthropic_invoke_tools` | `anthropic_invoke_tools(tools, response)` |
| Groq | `from pixeltable.functions.groq import invoke_tools as groq_invoke_tools` | `groq_invoke_tools(tools, response)` |
| Gemini | `from pixeltable.functions.gemini import invoke_tools as gemini_invoke_tools` | `gemini_invoke_tools(tools, response)` |
| Bedrock | `from pixeltable.functions.bedrock import invoke_tools as bedrock_invoke_tools` | `bedrock_invoke_tools(tools, response)` |

To switch providers, change the import and the LLM call function. The `tools` object and `invoke_tools()` pattern stay the same.

## How It Works

1. **Chat history** — Every conversation is stored in a table with an embedding index. The `recall_chat_history` query retrieves semantically relevant past turns for the current user.

2. **Memory bank** — Long-lived facts and preferences are stored separately. The `recall_memories` query retrieves relevant memories. The `save_memory` tool lets the LLM itself save new facts during conversation.

3. **User scoping** — All queries filter by `user_id`, so multiple users can share the same tables without seeing each other's data.

4. **MCP integration** — `pxt.mcp_udfs()` loads tools from any MCP server as regular Pixeltable UDFs. They're bundled with `pxt.tools()` and executed with `invoke_tools()` just like local functions.

## Adapting This Recipe

- **Add document RAG**: Create a document chunking view and add a `search_documents` query to the tools list
- **Add image memory**: Use CLIP embeddings on an image column for visual memory recall
- **Serve via API**: Wrap in a FastAPI endpoint — see [workflows.md → FastAPI App Pattern](workflows.md#fastapi-app-pattern)
- **Use Anthropic instead**: Swap `chat_completions` → `messages` and `openai_invoke_tools` → `anthropic_invoke_tools` (updating the import accordingly) — see [providers.md → Quick Reference](providers.md#quick-reference)

## Agent with Memory Checklist

- [ ] Chat history table created with `user_id`, `role`, `content`, `timestamp` columns
- [ ] Embedding index added on chat history `content` column
- [ ] Memory bank table created with `user_id`, `content`, `category` columns
- [ ] Embedding index added on memory bank `content` column
- [ ] Recall queries filter by `user_id` (multi-tenant safety)
- [ ] Recall queries use `.similarity(string=...)` with keyword argument and a minimum threshold
- [ ] `save_memory` tool has a clear docstring so the LLM knows when to store facts
- [ ] Tools bundled with `pxt.tools()` — includes both local UDFs and MCP tools if any
- [ ] `invoke_tools()` import matches the LLM provider used
- [ ] Agent response saved to chat history after each interaction (both user and assistant turns)
- [ ] Tested with multiple user IDs to verify scoping works
