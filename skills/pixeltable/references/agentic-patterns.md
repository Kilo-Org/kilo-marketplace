# Agentic Patterns

Six architectural patterns and two reasoning strategies for building AI agents with Pixeltable. Every pattern uses declarative computed columns — no async code, no orchestration framework, no loop management.

**Core principle**: Your agent _is_ a table. Each step is a computed column. The engine resolves dependencies, parallelizes independent columns, caches results, and persists every intermediate step automatically.

## Contents

- [Prompt Chaining](#prompt-chaining) — sequential multi-step generation
- [Routing](#routing) — classify intent, dispatch to specialized handlers
- [Parallelization](#parallelization) — independent analyses on same input
- [Tool Use](#tool-use) — LLM selects and calls external functions
- [Evaluator-Optimizer](#evaluator-optimizer) — generate, judge, refine
- [Orchestrator-Worker](#orchestrator-worker) — decompose, delegate, synthesize
- [ReAct](#react-reasoning--acting) — reason-act-observe loop
- [Planning](#planning) — plan upfront, then execute

---

## Prompt Chaining

Sequential steps where each output feeds into the next.

```python
import pixeltable as pxt
from pixeltable.functions.openai import chat_completions

chain = pxt.create_table('demo.chain', {'topic': pxt.String}, if_exists='ignore')

# Step 1: Generate outline
chain.add_computed_column(
    outline=chat_completions(
        messages=[{'role': 'user', 'content': 'Create a 3-point outline about: ' + chain.topic}],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')

# Step 2: Write draft from outline (depends on step 1)
chain.add_computed_column(
    draft=chat_completions(
        messages=[{'role': 'user', 'content': 'Write article based on outline:\n\n' + chain.outline}],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')

# Step 3: Polish draft (depends on step 2)
chain.add_computed_column(
    final=chat_completions(
        messages=[{'role': 'user', 'content': 'Edit for clarity and conciseness:\n\n' + chain.draft}],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')

chain.insert([{'topic': 'benefits of declarative AI pipelines'}])
```

**When to use**: Content generation, data transformation pipelines, multi-step extraction.

## Routing

Classify input and dispatch to specialized handlers.

```python
router = pxt.create_table('demo.router', {'query': pxt.String}, if_exists='ignore')

# Classify intent
router.add_computed_column(
    intent=chat_completions(
        messages=[{
            'role': 'user',
            'content': 'Classify into exactly one word — technical, billing, or general:\n\n' + router.query
        }],
        model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')

# Route to specialized prompt
@pxt.udf
def route_prompt(intent: str, query: str) -> list[dict]:
    prompts = {
        'technical': 'You are a senior technical support engineer.',
        'billing': 'You are a billing specialist. Be empathetic.',
        'general': 'You are a friendly customer service representative.',
    }
    system = prompts.get(intent.strip().lower(), prompts['general'])
    return [{'role': 'system', 'content': system}, {'role': 'user', 'content': query}]

router.add_computed_column(
    routed_messages=route_prompt(router.intent, router.query),
    if_exists='ignore')

router.add_computed_column(
    response=chat_completions(
        messages=router.routed_messages, model='gpt-4o-mini'
    ).choices[0].message.content,
    if_exists='ignore')
```

**When to use**: Customer support, multi-domain Q&A, content moderation.

## Parallelization

Multiple independent analyses on the same input — auto-parallelized by the engine.

```python
parallel = pxt.create_table('demo.parallel', {'text': pxt.String}, if_exists='ignore')

# Three independent columns (no dependencies → run concurrently)
parallel.add_computed_column(
    sentiment=chat_completions(
        messages=[{'role': 'user', 'content': 'Sentiment (positive/negative/neutral):\n\n' + parallel.text}],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

parallel.add_computed_column(
    entities=chat_completions(
        messages=[{'role': 'user', 'content': 'Extract named entities as JSON:\n\n' + parallel.text}],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

parallel.add_computed_column(
    summary=chat_completions(
        messages=[{'role': 'user', 'content': 'Summarize in one sentence:\n\n' + parallel.text}],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

# Merge results (depends on all three → runs after they complete)
@pxt.udf
def merge(sentiment: str, entities: str, summary: str) -> dict:
    return {'sentiment': sentiment.strip(), 'entities': entities.strip(), 'summary': summary.strip()}

parallel.add_computed_column(
    report=merge(parallel.sentiment, parallel.entities, parallel.summary),
    if_exists='ignore')
```

**When to use**: Document analysis, multi-aspect evaluation, feature extraction.

## Tool Use

LLM chooses which tools to call; Pixeltable executes them automatically.

```python
from pixeltable.functions.openai import chat_completions, invoke_tools

@pxt.udf
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    data = {'tokyo': 'Rainy, 65F', 'london': 'Cloudy, 58F', 'paris': 'Sunny, 72F'}
    return data.get(city.lower(), f'No data for {city}')

@pxt.udf
def get_stock_price(symbol: str) -> str:
    """Get current stock price."""
    prices = {'AAPL': '$178.50', 'GOOGL': '$141.25', 'MSFT': '$378.90'}
    return prices.get(symbol.upper(), f'No data for {symbol}')

tools = pxt.tools(get_weather, get_stock_price)

agent = pxt.create_table('demo.tool_agent', {'query': pxt.String}, if_exists='ignore')

agent.add_computed_column(
    response=chat_completions(
        messages=[{'role': 'user', 'content': agent.query}],
        model='gpt-4o-mini', tools=tools,
    ), if_exists='ignore')

agent.add_computed_column(
    tool_output=invoke_tools(tools, agent.response),
    if_exists='ignore')

agent.insert([
    {'query': "What's the weather in Tokyo?"},
    {'query': "What's Apple's stock price?"},
])
```

**When to use**: Any agent that needs external data or actions. See also [agents-memory-mcp.md](agents-memory-mcp.md) for memory and MCP integration.

## Evaluator-Optimizer

Generate → judge → refine loop as three chained columns.

```python
evaluator = pxt.create_table('demo.evaluator', {'brief': pxt.String}, if_exists='ignore')

# Generate first draft
evaluator.add_computed_column(
    draft=chat_completions(
        messages=[{'role': 'user', 'content': 'Write a marketing tagline for:\n\n' + evaluator.brief}],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

# LLM-as-judge evaluates the draft
evaluator.add_computed_column(
    evaluation=chat_completions(
        messages=[{
            'role': 'user',
            'content': 'Rate clarity and creativity (1-10) with feedback:\n\nTagline: ' + evaluator.draft
        }],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

# Refine based on feedback
evaluator.add_computed_column(
    refined=chat_completions(
        messages=[{
            'role': 'user',
            'content': 'Improve based on feedback:\n\nOriginal: ' + evaluator.draft + '\n\nFeedback: ' + evaluator.evaluation
        }],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')
```

**When to use**: Content quality control, code review pipelines, iterative refinement.

## Orchestrator-Worker

Central agent decomposes tasks, specialized worker tables handle sub-tasks.

```python
# Worker A: Summarizer (reusable table-as-UDF)
summarizer = pxt.create_table('demo.summarizer', {'text': pxt.String}, if_exists='ignore')
summarizer.add_computed_column(
    summary=chat_completions(
        messages=[{'role': 'user', 'content': 'Summarize:\n\n' + summarizer.text}],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

# Worker B: Fact-checker
checker = pxt.create_table('demo.checker', {'claim': pxt.String}, if_exists='ignore')
checker.add_computed_column(
    assessment=chat_completions(
        messages=[{'role': 'user', 'content': 'Is this plausible? Reply PLAUSIBLE or DUBIOUS:\n\n' + checker.claim}],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

# Wrap worker tables as callable UDFs
summarize_fn = pxt.udf(summarizer, return_value=summarizer.summary)
fact_check_fn = pxt.udf(checker, return_value=checker.assessment)

# Orchestrator: calls workers in parallel, then synthesizes
orchestrator = pxt.create_table('demo.orchestrator', {'article': pxt.String}, if_exists='ignore')
orchestrator.add_computed_column(summary=summarize_fn(text=orchestrator.article), if_exists='ignore')
orchestrator.add_computed_column(fact_check=fact_check_fn(claim=orchestrator.article), if_exists='ignore')

orchestrator.add_computed_column(
    briefing=chat_completions(
        messages=[{
            'role': 'user',
            'content': 'Write editorial note:\n\nSummary: ' + orchestrator.summary + '\n\nFact-check: ' + orchestrator.fact_check
        }],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')
```

**Key technique**: `pxt.udf(table, return_value=table.col)` wraps an entire table pipeline as a callable function. Workers are reusable across multiple orchestrators.

**When to use**: Research assistants, report generation, multi-agent systems.

## ReAct (Reasoning + Acting)

Agent alternates between reasoning and acting in a loop. Each step is a row.

```python
@pxt.udf
def lookup_population(country: str) -> str:
    """Look up country population."""
    populations = {'united states': '331 million', 'brazil': '214 million', 'germany': '84 million'}
    return populations.get(country.lower(), 'Not available')

react_tools = pxt.tools(lookup_population)

react = pxt.create_table('demo.react', {
    'step': pxt.Int, 'prompt': pxt.String, 'system_prompt': pxt.String,
}, if_exists='ignore')

react.add_computed_column(
    response=chat_completions(
        messages=[
            {'role': 'system', 'content': react.system_prompt},
            {'role': 'user', 'content': react.prompt}
        ],
        model='gpt-4o-mini', tools=react_tools,
    ), if_exists='ignore')

react.add_computed_column(
    answer=react.response.choices[0].message.content,
    if_exists='ignore')

react.add_computed_column(
    tool_output=invoke_tools(react_tools, react.response),
    if_exists='ignore')

# Reasoning loop — each iteration is a new row
SYSTEM = "Answer step by step. Use tools when needed. Say FINAL ANSWER when done."
question = "Which has a larger population, Brazil or Germany?"
history = []

for step in range(1, 5):
    prompt = question + ('\n\nObservations so far:\n' + '\n'.join(history) if history else '')
    react.insert([{'step': step, 'prompt': prompt, 'system_prompt': SYSTEM}])

    row = react.where(react.step == step).select(react.answer, react.tool_output).collect()[0]
    if row['tool_output']:
        history.append(f'Step {step}: {row["tool_output"]}')
    if row['answer'] and 'FINAL' in row['answer'].upper():
        break
```

**When to use**: Multi-step research, complex reasoning requiring external data.

## Planning

Generate a complete plan upfront, then execute all steps.

```python
import json

planner = pxt.create_table('demo.planner', {'question': pxt.String}, if_exists='ignore')

# Generate plan as JSON
planner.add_computed_column(
    plan_text=chat_completions(
        messages=[{
            'role': 'user',
            'content': 'Break into 2-3 research steps. Return JSON: {"steps": ["step1", "step2"]}\n\n' + planner.question
        }],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')

# Format plan into execution prompt
@pxt.udf
def format_plan(plan_json: str, question: str) -> str:
    try:
        data = json.loads(plan_json)
        steps = data if isinstance(data, list) else data.get('steps', [])
        step_list = '\n'.join(f'{i+1}. {s}' for i, s in enumerate(steps))
    except Exception:
        step_list = '1. ' + question
    return f'Answer each sub-question, then synthesize:\n\nOriginal: {question}\n\n{step_list}'

planner.add_computed_column(
    exec_prompt=format_plan(planner.plan_text, planner.question),
    if_exists='ignore')

planner.add_computed_column(
    answer=chat_completions(
        messages=[{'role': 'user', 'content': planner.exec_prompt}],
        model='gpt-4o-mini'
    ).choices[0].message.content, if_exists='ignore')
```

**When to use**: Complex questions, multi-step research, structured problem solving.

## Comparison with Traditional Frameworks

| Concept | Pixeltable | LangChain / CrewAI / LangGraph |
|---------|-----------|-------------------------------|
| Pipeline step | Computed column | Function in a chain/loop |
| Parallel execution | Independent columns (automatic) | `asyncio.gather` / explicit |
| Persistence | Built-in — every intermediate stored | Separate logging/DB layer |
| Caching | Automatic — same input never recomputed | Manual memoization |
| Reusable sub-agent | `pxt.udf(table, return_value=...)` | Agent class with `.run()` |
| Error recovery | `recompute_columns(where=errortype != None)` | Re-run entire pipeline |
| Observability | Query any column on any row | Attach tracing callbacks |

Patterns compose naturally — an orchestrator can use routing in its dispatch, tool use within workers, and ReAct reasoning inside tool loops, all without special glue code.
