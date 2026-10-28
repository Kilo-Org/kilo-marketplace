# Lifespan Events

Startup/shutdown logic for FastAPI applications.

## Lifespan Context Manager (Recommended)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before accepting requests
    print("Starting up...")
    ml_model = load_model()
    app.state.model = ml_model

    yield  # Application runs here

    # Shutdown: runs when shutting down
    print("Shutting down...")
    ml_model.unload()

app = FastAPI(lifespan=lifespan)

@app.get("/predict")
def predict(x: float):
    return {"result": app.state.model.predict(x)}
```

## Shared Resources Pattern

```python
from contextlib import asynccontextmanager

# Global dict for resources
resources = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    resources["db"] = await create_db_pool()
    resources["cache"] = await create_redis_connection()

    yield

    # Cleanup
    await resources["db"].close()
    await resources["cache"].close()

app = FastAPI(lifespan=lifespan)

@app.get("/users")
async def get_users():
    db = resources["db"]
    return await db.fetch("SELECT * FROM users")
```

## Database Connection Example

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine("postgresql+asyncpg://...")
    app.state.engine = engine

    yield

    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

## Testing Lifespan Events

```python
from fastapi.testclient import TestClient

def test_lifespan():
    with TestClient(app) as client:
        # Startup runs when entering context
        response = client.get("/predict")
        assert response.status_code == 200
    # Shutdown runs when exiting context
```

For async tests:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager

@pytest.mark.anyio
async def test_async():
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
```

Requires: `pip install asgi-lifespan`

## Deprecated: Event Handlers

```python
# Old style - deprecated, use lifespan instead
@app.on_event("startup")
async def startup():
    print("Starting...")

@app.on_event("shutdown")
async def shutdown():
    print("Stopping...")
```

## Notes

- Lifespan context manager is the modern approach
- `yield` separates startup from shutdown
- Use `app.state` to store shared resources
- Cleanup in shutdown prevents resource leaks
- TestClient automatically handles lifespan events
