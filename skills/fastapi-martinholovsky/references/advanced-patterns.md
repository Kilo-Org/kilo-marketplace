# FastAPI Advanced Patterns Reference

## Dependency Injection Patterns

### Layered Dependencies

```python
from fastapi import Depends

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repo)
) -> User:
    user_id = decode_token(token)
    return await repo.get(user_id)

@app.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return user
```

### Scoped Dependencies

```python
from fastapi import Depends
from uuid import uuid4

def get_request_id():
    return str(uuid4())

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = get_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response
```

---

## Background Tasks

### Async Background Processing

```python
from fastapi import BackgroundTasks

async def send_email(email: str, content: str):
    # Async email sending
    await email_service.send(email, content)

@app.post("/register")
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    new_user = await user_service.create(user)

    # Queue email for later
    background_tasks.add_task(
        send_email,
        user.email,
        "Welcome to our service!"
    )

    return new_user
```

---

## Response Optimization

### Streaming Responses

```python
from fastapi.responses import StreamingResponse

async def generate_large_file():
    for chunk in range(100):
        yield f"data chunk {chunk}\n".encode()
        await asyncio.sleep(0.1)

@app.get("/stream")
async def stream_data():
    return StreamingResponse(
        generate_large_file(),
        media_type="text/plain"
    )
```

### Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@app.get("/data")
@cache(expire=300)  # 5 minutes
async def get_cached_data():
    return await expensive_operation()
```

---

## WebSocket Integration

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## Testing Patterns

### Test Client Setup

```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def authenticated_client(async_client):
    # Login and get token
    response = await async_client.post("/token", data={
        "username": "test",
        "password": "testpass"
    })
    token = response.json()["access_token"]

    async_client.headers["Authorization"] = f"Bearer {token}"
    yield async_client
```

### Mocking Dependencies

```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_user_service():
    mock = AsyncMock()
    mock.get.return_value = User(id=1, username="test")
    return mock

def test_with_mock(client, mock_user_service):
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = client.get("/users/1")
    assert response.status_code == 200

    # Cleanup
    app.dependency_overrides.clear()
```

---

## OpenAPI Customization

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Secure API",
        version="1.0.0",
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```
