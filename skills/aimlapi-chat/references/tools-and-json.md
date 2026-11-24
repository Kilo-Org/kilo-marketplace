# Tools and structured output

The shapes are the OpenAI ones on `/v1/chat/completions` and `/v1/responses`, and the Anthropic ones on `/v1/messages`. Whether a given model supports tools or JSON schema output is in its `docsJson` (look for `tools` and `response_format`).

## Tool loop, Chat Completions

```python
import json
import os
from openai import OpenAI

client = OpenAI(base_url="https://api.aimlapi.com/v1", api_key=os.environ["AIMLAPI_API_KEY"])

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]

messages = [{"role": "user", "content": "What's the weather in Lisbon?"}]
first = client.chat.completions.create(model="openai/gpt-4o-mini", messages=messages, tools=tools, max_tokens=300)
choice = first.choices[0]

if choice.finish_reason == "tool_calls":
    messages.append(choice.message)
    for call in choice.message.tool_calls:
        args = json.loads(call.function.arguments)        # validate before use
        result = {"city": args["city"], "temp_c": 19}       # your function
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
    final = client.chat.completions.create(model="openai/gpt-4o-mini", messages=messages, tools=tools, max_tokens=300)
    print(final.choices[0].message.content)
```

- Send the same `tools` on the follow-up request.
- A model may return several tool calls at once; answer each `tool_call_id`.
- `tool_choice`: `"auto"` (default), `"none"`, `"required"`, or `{"type": "function", "function": {"name": "…"}}`.
- Arguments are model output: parse them defensively and validate before acting.

## Tool loop, Messages (Anthropic SDK)

```python
import os
import anthropic

client = anthropic.Anthropic(base_url="https://api.aimlapi.com", api_key=os.environ["AIMLAPI_API_KEY"])

tools = [{
    "name": "get_weather",
    "description": "Current weather for a city",
    "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
}]
messages = [{"role": "user", "content": "What's the weather in Lisbon?"}]
first = client.messages.create(model="anthropic/claude-haiku-5-5", max_tokens=300, tools=tools, messages=messages)

if first.stop_reason == "tool_use":
    messages.append({"role": "assistant", "content": first.content})
    results = [
        {"type": "tool_result", "tool_use_id": block.id, "content": '{"temp_c": 19}'}
        for block in first.content if block.type == "tool_use"
    ]
    messages.append({"role": "user", "content": results})
    final = client.messages.create(model="anthropic/claude-haiku-5-5", max_tokens=300, tools=tools, messages=messages)
    print(final.content[0].text)
```

## JSON that follows a schema

Chat Completions:

```python
completion = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Extract the city and date: 'Meet me in Porto on 3 May'"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "meeting",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"city": {"type": "string"}, "date": {"type": "string"}},
                "required": ["city", "date"],
                "additionalProperties": False,
            },
        },
    },
    max_tokens=200,
)
data = json.loads(completion.choices[0].message.content)
```

Responses: the schema goes in `text.format`. Messages: in `output_config.format`, on models whose schema lists it.

`{"type": "json_object"}` asks for any valid JSON without a schema; prefer `json_schema` when the model supports it.

## Embeddings

```python
vectors = client.embeddings.create(model="openai/text-embedding-3-small", input=["first text", "second text"])
print(len(vectors.data[0].embedding))
```

Pick a model with `type` `openai/embeddings` (`aimlapi-models`).

## Test it free

In sandbox mode (`aimlapi-sandbox`) a request with `tools` returns a tool call whose arguments match your schema, and the follow-up with a `role: "tool"` message returns a final text. A request with a JSON schema returns JSON that follows it. That checks your parsing code without paying for tokens.
