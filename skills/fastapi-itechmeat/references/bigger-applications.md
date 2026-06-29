# Bigger Applications - Multiple Files

Structure large FastAPI apps using APIRouter for modular organization.

## Project Structure

```
app/
├── __init__.py
├── main.py              # Main FastAPI app
├── dependencies.py      # Shared dependencies
├── routers/
│   ├── __init__.py
│   ├── users.py        # User routes
│   └── items.py        # Item routes
└── internal/
    ├── __init__.py
    └── admin.py        # Admin routes (shared)
```

## APIRouter

Create modular routers that work like mini FastAPI apps:

```python
# routers/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]

@router.get("/users/{username}", tags=["users"])
async def read_user(username: str):
    return {"username": username}
```

## Router with Prefix and Dependencies

Apply common settings to all routes in a router:

```python
# routers/items.py
from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_token_header

router = APIRouter(
    prefix="/items",               # All routes start with /items
    tags=["items"],               # OpenAPI tag
    dependencies=[Depends(get_token_header)],  # Auth for all routes
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def read_items():
    return fake_items_db

@router.get("/{item_id}")
async def read_item(item_id: str):
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

## Router Lifecycle Hooks (v0.128.6)

`APIRouter` supports startup and shutdown hooks (fixed in 0.128.6):

```python
from fastapi import APIRouter

async def connect_db():
    ...

async def close_db():
    ...

router = APIRouter(
    on_startup=[connect_db],
    on_shutdown=[close_db],
)
```

## Shared Dependencies

```python
# dependencies.py
from typing import Annotated
from fastapi import Header, HTTPException

async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No token provided")
```

## Main App

Include routers in the main app:

```python
# main.py
from fastapi import Depends, FastAPI
from .dependencies import get_query_token, get_token_header
from .internal import admin
from .routers import items, users

app = FastAPI(dependencies=[Depends(get_query_token)])  # Global dependency

# Include routers
app.include_router(users.router)
app.include_router(items.router)

# Include with custom prefix/dependencies
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
```

## Relative Imports

```python
# From routers/items.py, import from parent package
from ..dependencies import get_token_header  # app/dependencies.py
```

- Single dot `.` = same package
- Double dots `..` = parent package
- Triple dots `...` = grandparent (rarely needed)

## Include Router in Router

```python
# Nest routers before including in main app
router.include_router(other_router)
```

## Multiple Prefixes for Same Router

```python
# Same router at different paths (e.g., /api/v1 and /api/latest)
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/latest")
```

## Key Points

- `APIRouter` = mini `FastAPI` class with same parameters
- `prefix` must not end with `/`
- Router dependencies execute before decorator dependencies
- Path operations are "cloned" (not mounted) to include in OpenAPI schema
- Performance: including routers happens at startup (microseconds)
