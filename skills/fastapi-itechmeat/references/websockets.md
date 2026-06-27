# WebSockets

Real-time bidirectional communication in FastAPI.

## Basic WebSocket

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

## Client Example (JavaScript)

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = (event) => console.log(event.data);
ws.onopen = () => ws.send("Hello");
```

## Connection Manager (Multiple Clients)

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left")
```

## WebSocket with Dependencies

```python
from fastapi import Query, Depends, WebSocket

async def verify_token(token: str = Query(...)):
    if token != "valid":
        raise WebSocketException(code=1008)
    return token

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Depends(verify_token)
):
    await websocket.accept()
    await websocket.send_text(f"Authenticated with token: {token}")
```

## Handling Disconnection

```python
from fastapi import WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

## Send/Receive Methods

```python
# Receive
data = await websocket.receive_text()    # str
data = await websocket.receive_bytes()   # bytes
data = await websocket.receive_json()    # dict/list

# Send
await websocket.send_text("hello")       # str
await websocket.send_bytes(b"...")       # bytes
await websocket.send_json({"key": "val"})  # dict/list

# Close
await websocket.close(code=1000)
```

## Testing WebSockets

```python
from fastapi.testclient import TestClient

def test_websocket():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("Hello")
        data = websocket.receive_text()
        assert data == "Echo: Hello"
```

## WebSocket Path Parameters

```python
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    await websocket.send_text(f"Joined room: {room_id}")
```

## Cookie/Header Authentication

```python
from fastapi import Cookie, Header

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session: str | None = Cookie(default=None),
    x_token: str | None = Header(default=None)
):
    if not session or not x_token:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    ...
```
