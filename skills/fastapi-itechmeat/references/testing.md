# Testing

Test FastAPI applications using TestClient and pytest.

## Setup

```bash
pip install httpx pytest
```

## Basic Test

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

## Key Points

- Test functions use `def`, not `async def`
- Client calls are synchronous (no `await`)
- TestClient is from Starlette, re-exported by FastAPI

`0.136.1` note:

- FastAPI now rides on Starlette `1.0.0`. If tests rely on Starlette internals or older TestClient behavior beyond the FastAPI re-exported API, re-test those assumptions after upgrading.

## Project Structure

```
app/
├── __init__.py
├── main.py
└── test_main.py
```

```python
# test_main.py
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
```

## Request Methods

```python
# GET with query params
response = client.get("/items/?skip=0&limit=10")

# POST with JSON body
response = client.post(
    "/items/",
    json={"name": "Foo", "price": 42.0}
)

# With headers
response = client.get(
    "/items/foo",
    headers={"X-Token": "secret-token"}
)

# With cookies
response = client.get(
    "/items/",
    cookies={"session": "abc123"}
)

# Form data
response = client.post(
    "/login/",
    data={"username": "user", "password": "pass"}
)

# File upload
with open("file.txt", "rb") as f:
    response = client.post(
        "/upload/",
        files={"file": ("filename.txt", f, "text/plain")}
    )
```

## Testing Errors

```python
def test_read_item_not_found():
    response = client.get("/items/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_create_item_invalid():
    response = client.post(
        "/items/",
        json={"name": "Foo"}  # Missing required field
    )
    assert response.status_code == 422  # Validation error
```

## Override Dependencies

```python
from fastapi.testclient import TestClient
from app.main import app, get_db

def override_get_db():
    return TestDatabase()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_with_mock_db():
    response = client.get("/items/")
    assert response.status_code == 200

# Reset overrides after test
app.dependency_overrides = {}
```

## Override Settings

```python
from .config import Settings
from .main import app, get_settings

def get_settings_override():
    return Settings(admin_email="test@example.com")

app.dependency_overrides[get_settings] = get_settings_override
```

## Async Tests

For async database calls or when testing async code:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from .main import app

@pytest.mark.anyio
async def test_async():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
```

Requires: `pip install anyio pytest-anyio httpx`

Note: `AsyncClient` doesn't trigger lifespan events. Use `asgi-lifespan` if needed:

```python
from asgi_lifespan import LifespanManager

@pytest.mark.anyio
async def test_with_lifespan():
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get("/")
```

## Testing WebSockets

```python
def test_websocket():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("hello")
        data = websocket.receive_text()
        assert data == "Echo: hello"
```

## Testing Lifespan Events

```python
def test_app_lifespan():
    with TestClient(app) as client:
        # Startup runs when entering context
        response = client.get("/")
        assert response.status_code == 200
    # Shutdown runs when exiting context
```

## Run Tests

```bash
pytest
pytest -v  # Verbose
pytest test_main.py::test_read_main  # Specific test
pytest -x  # Stop on first failure
pytest --tb=short  # Shorter traceback
```
