---
name: fastapi-itechmeat
description: >-
  FastAPI Python framework. Covers REST APIs, validation, dependencies,
  security. Use when building Python web APIs with FastAPI, configuring Pydantic
  models, implementing dependency injection, or setting up OAuth2/JWT
  authentication. Keywords: FastAPI, Pydantic, async, OAuth2, JWT, REST API.
metadata:
  version: 0.136.3
  release_date: '2026-05-23'
  category: development
  source:
    repository: 'https://github.com/itechmeat/llm-code'
    path: skills/fastapi
    license_path: LICENSE
    commit: 0ebb36c887c350d9d52c389503386bb781112ad8
---

# FastAPI

This skill provides comprehensive guidance for building APIs with FastAPI.

## Quick Navigation

| Topic              | Reference                           |
| ------------------ | ----------------------------------- |
| Getting started    | `references/first-steps.md`         |
| Path parameters    | `references/path-parameters.md`     |
| Query parameters   | `references/query-parameters.md`    |
| Request body       | `references/request-body.md`        |
| Validation         | `references/validation.md`          |
| Body advanced      | `references/body-advanced.md`       |
| Cookies/Headers    | `references/cookies-headers.md`     |
| Pydantic models    | `references/models.md`              |
| Forms/Files        | `references/forms-files.md`         |
| Error handling     | `references/error-handling.md`      |
| Path config        | `references/path-config.md`         |
| Dependencies       | `references/dependencies.md`        |
| Security           | `references/security.md`            |
| Middleware         | `references/middleware.md`          |
| CORS               | `references/cors.md`                |
| Database           | `references/sql-databases.md`       |
| Project structure  | `references/bigger-applications.md` |
| Background tasks   | `references/background-tasks.md`    |
| Metadata/Docs      | `references/metadata-docs.md`       |
| Testing            | `references/testing.md`             |
| Advanced responses | `references/responses-advanced.md`  |
| WebSockets         | `references/websockets.md`          |
| Templates          | `references/templates.md`           |
| Settings/Env vars  | `references/settings.md`            |
| Lifespan events    | `references/lifespan.md`            |
| OpenAPI advanced   | `references/openapi-advanced.md`    |

## When to Use

- Creating REST APIs with Python
- Adding endpoints with automatic validation
- Implementing OAuth2/JWT authentication
- Working with Pydantic models
- Adding dependency injection
- Configuring CORS, middleware
- Uploading files, handling forms
- Testing API endpoints

## Installation

Requires Python 3.10+. Install: `pip install "fastapi[standard]"` (full with uvicorn) or `pip install fastapi` (minimal). Add `python-multipart` for forms/files.

## Release Highlights (0.133.0 → 0.136.1)

- **0.134.0:** streaming JSON Lines and streaming binary data support using `yield`.
- **0.135.0:** first-class Server-Sent Events (SSE) support (`EventSourceResponse`).
- **0.135.1:** fix around `TaskGroup` usage in request async exit stack (stability fix).
- **0.136.1:** FastAPI updates its Pydantic v2 code to avoid deprecations and bumps Starlette to `1.0.0`.

## Patch Notes (0.136.2 → 0.136.3)

- SSE responses now validate event fields more strictly, so malformed `ServerSentEvent` payloads fail earlier instead of quietly streaming invalid frames.
- Header parameters no longer accept underscore-named incoming headers when `convert_underscores=True` (the default). If a client truly sends underscore headers, declare `Header(convert_underscores=False)` and verify that your proxy chain allows them.

## Quick Start

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

Run: `fastapi dev main.py`

## Core Patterns

### Type-Safe Parameters

```python
from typing import Annotated
from fastapi import Path, Query

@app.get("/items/{item_id}")
def read_item(
    item_id: Annotated[int, Path(ge=1)],
    q: Annotated[str | None, Query(max_length=50)] = None
):
    return {"item_id": item_id, "q": q}
```

### Request Body with Validation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)

@app.post("/items/", response_model=Item)
def create_item(item: Item):
    return item
```

### Dependencies

```python
from fastapi import Depends

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def list_users(db: Annotated[Session, Depends(get_db)]):
    return db.query(User).all()
```

### Authentication

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return decode_token(token)

@app.get("/users/me")
def read_me(user: Annotated[User, Depends(get_current_user)]):
    return user
```

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI: `/openapi.json`

## Best Practices

- Use `Annotated[Type, ...]` for parameters
- Define Pydantic models for request/response
- Use `response_model` for output filtering
- Add `status_code` for proper HTTP codes
- Use `tags` for API organization
- Add `dependencies` at router/app level for auth

## Prohibitions

- ❌ Return raw database models (use response models)
- ❌ Store passwords in plain text (use bcrypt/passlib)
- ❌ Mix `Body` with `Form`/`File` in same endpoint
- ❌ Use sync blocking I/O in async endpoints
- ❌ Skip HTTPException for error handling

## Links

- [Documentation](https://fastapi.tiangolo.com/)
- [Releases](https://github.com/fastapi/fastapi/releases)
- [GitHub](https://github.com/fastapi/fastapi)
- [PyPI](https://pypi.org/project/fastapi/)
