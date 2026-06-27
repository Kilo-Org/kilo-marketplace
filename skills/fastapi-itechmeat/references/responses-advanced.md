# Advanced Responses

Custom responses, status codes, cookies, headers for FastAPI.

## Return Response Directly

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

@app.get("/item/")
def read_item():
    # Use jsonable_encoder for datetime, Pydantic models etc
    data = jsonable_encoder({"created": datetime.now()})
    return JSONResponse(content=data)
```

## Custom Response Types

````python
from fastapi.responses import (
    HTMLResponse,      # text/html
    PlainTextResponse, # text/plain
    JSONResponse,      # application/json (default)
    ORJSONResponse,    # Fast JSON (pip install orjson)
    UJSONResponse,     # Fast JSON (pip install ujson)
    RedirectResponse,  # HTTP redirect
    StreamingResponse, # Streaming content
    FileResponse       # File downloads
)

# HTML Response
@app.get("/", response_class=HTMLResponse)
def get_html():
    return "<h1>Hello</h1>"

# Streaming Response
@app.get("/stream")
def stream():
    def generate():
        for i in range(10):
            yield f"chunk {i}\n"
    return StreamingResponse(generate(), media_type="text/plain")

# File Response
@app.get("/file")
def get_file():
    return FileResponse(
        path="report.pdf",
        filename="download.pdf",
        media_type="application/pdf"
    )

# Redirect
@app.get("/old")
def redirect():
    return RedirectResponse(url="/new", status_code=301)

## Streaming with `yield` (0.134.0+)

FastAPI can stream incrementally without buffering the whole response. Choose the pattern based on the client protocol.

### Stream JSON Lines (JSONL)

Use `yield` to emit one JSON item per line (content type is `application/jsonl`). If you annotate the return type (e.g. `AsyncIterable[Item]`), FastAPI will validate/serialize via Pydantic and document the schema.

```python
from collections.abc import AsyncIterable
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None

@app.get("/items/stream")
async def stream_items() -> AsyncIterable[Item]:
    for i in range(3):
        yield Item(name=f"item-{i}")
````

Notes:

- JSON Lines is not the same as a JSON array; clients must parse line-by-line.
- If you omit the return type annotation, FastAPI falls back to `jsonable_encoder` for serialization.

### Stream bytes / binary data

For raw bytes (audio/video/chunks), use `StreamingResponse` and set `media_type`. If the streaming code is blocking (disk/network reads), prefer `def` so FastAPI can run it in a threadpool.

```python
from collections.abc import Iterable
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/audio")
def stream_audio() -> StreamingResponse:
    def iter_bytes() -> Iterable[bytes]:
        yield b"..."  # chunk 1
        yield b"..."  # chunk 2
    return StreamingResponse(iter_bytes(), media_type="audio/mpeg")
```

### Server-Sent Events (SSE) (0.135.0+)

SSE uses `text/event-stream` and is browser-native via `EventSource`. In FastAPI, set `response_class=EventSourceResponse` and `yield` items.

```python
from collections.abc import AsyncIterable
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent

app = FastAPI()

@app.get("/events", response_class=EventSourceResponse)
async def events() -> AsyncIterable[ServerSentEvent]:
    yield ServerSentEvent(comment="stream start")
    for i in range(3):
        yield ServerSentEvent(data={"i": i}, event="tick", id=str(i), retry=5000)
```

Operational notes:

- `ServerSentEvent.data` is JSON-encoded; use `raw_data` for raw text payloads.
- Clients can resume after disconnect using `Last-Event-ID`.
- For proxy behavior: consider keep-alive pings, `Cache-Control: no-cache`, and disabling buffering (e.g. `X-Accel-Buffering: no` for Nginx).
- `0.136.2+` validates SSE fields more strictly. Prefer building events with `ServerSentEvent(...)` instead of hand-assembling ad hoc payload dicts, and test any optional `event`, `id`, or `retry` fields you generate dynamically.

````

## Default Response Class

```python
from fastapi.responses import ORJSONResponse

# App-wide default
app = FastAPI(default_response_class=ORJSONResponse)

# Endpoint-specific
@app.get("/items/", response_class=ORJSONResponse)
def read_items():
    return [{"id": 1}]
````

## Additional Status Codes

```python
from fastapi import status
from fastapi.responses import JSONResponse

@app.put("/items/{item_id}")
def upsert_item(item_id: str, item: Item):
    if item_id in items:
        items[item_id] = item
        return item  # 200 default
    else:
        items[item_id] = item
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=jsonable_encoder(item)
        )
```

## Dynamic Status Code

```python
from fastapi import Response

@app.put("/items/{item_id}")
def update_item(item_id: str, response: Response):
    if item_id not in items:
        response.status_code = status.HTTP_201_CREATED
    return {"item_id": item_id}
```

## Response Cookies

```python
from fastapi import Response

# Via Response parameter
@app.post("/login")
def login(response: Response):
    response.set_cookie(
        key="session",
        value="abc123",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    return {"message": "logged in"}

# Via direct Response
@app.post("/login")
def login():
    response = JSONResponse(content={"message": "logged in"})
    response.set_cookie(key="session", value="abc123")
    return response

# Delete cookie
@app.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="session")
    return {"message": "logged out"}
```

## Response Headers

```python
from fastapi import Response

# Via Response parameter
@app.get("/items/")
def read_items(response: Response):
    response.headers["X-Custom"] = "value"
    response.headers["Cache-Control"] = "max-age=3600"
    return {"items": []}

# Via direct Response
@app.get("/items/")
def read_items():
    return JSONResponse(
        content={"items": []},
        headers={"X-Custom": "value"}
    )
```

Note: Custom headers with `X-` prefix. For CORS, expose custom headers in `CORSMiddleware(expose_headers=[...])`.

## Multiple Response Docs (OpenAPI)

```python
from fastapi import HTTPException
from pydantic import BaseModel

class Item(BaseModel):
    name: str

class Message(BaseModel):
    message: str

@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        200: {"model": Item, "description": "Item found"},
        404: {"model": Message, "description": "Item not found"},
        422: {"description": "Validation error"}
    }
)
def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

## Combine Response Info

```python
responses = {
    404: {"description": "Not found"},
    403: {"description": "Forbidden"}
}

@app.get("/users/{user_id}", responses={**responses, 200: {"model": User}})
def read_user(user_id: int):
    ...
```
