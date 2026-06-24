# First Steps

Core concepts for creating a minimal FastAPI application.

## Minimal Application

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## Key Components

### 1. FastAPI Instance

- `app = FastAPI()` creates the main application instance
- This is the entry point for all API functionality
- FastAPI inherits from Starlette (all Starlette features available)

### 2. Path Operation Decorator

- `@app.get("/")` defines a route handler
- Supports all HTTP methods:
  - `@app.get()` - read data
  - `@app.post()` - create data
  - `@app.put()` - update data
  - `@app.delete()` - delete data
  - `@app.patch()`, `@app.options()`, `@app.head()`, `@app.trace()`

### 3. Path Operation Function

- Can be `async def` or regular `def`
- Returns dict, list, str, int, Pydantic models
- Automatic JSON serialization

## Running the Server

```bash
fastapi dev main.py
```

Server runs at `http://127.0.0.1:8000`

## Auto-Generated Documentation

| URL             | Documentation            |
| --------------- | ------------------------ |
| `/docs`         | Swagger UI (interactive) |
| `/redoc`        | ReDoc (alternative)      |
| `/openapi.json` | Raw OpenAPI schema       |

## OpenAPI Integration

- FastAPI auto-generates OpenAPI 3.1.0 schema
- Schema includes paths, parameters, request/response models
- Powers interactive documentation
- Can generate client SDKs

## Terminology

| Term           | Meaning                                            |
| -------------- | -------------------------------------------------- |
| Path           | URL endpoint (e.g., `/items/foo`)                  |
| Operation      | HTTP method (GET, POST, etc.)                      |
| Path Operation | Combination of path + method                       |
| Schema         | Data structure definition (OpenAPI or JSON Schema) |
