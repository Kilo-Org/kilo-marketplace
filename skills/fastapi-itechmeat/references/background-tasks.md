# Background Tasks

Run tasks after returning the response.

## Use Cases

- Send email notifications
- Process uploaded files
- Update caches
- Log analytics

## Basic Usage

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_notification(email: str, message: str = ""):
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}
```

## Add Task Parameters

```python
background_tasks.add_task(
    function,       # Task function
    arg1,           # Positional args
    arg2,
    key1=value1,    # Keyword args
    key2=value2,
)
```

## Task Function Types

- Use `def` for I/O-bound tasks (file write, sync calls)
- Use `async def` for async operations (FastAPI handles both)

```python
# Sync task
def process_file(path: str):
    with open(path) as f:
        # process...

# Async task
async def call_external_api(url: str):
    async with httpx.AsyncClient() as client:
        await client.get(url)
```

## With Dependency Injection

```python
from typing import Annotated
from fastapi import BackgroundTasks, Depends, FastAPI

app = FastAPI()

def write_log(message: str):
    with open("log.txt", mode="a") as log:
        log.write(message)

def get_query(background_tasks: BackgroundTasks, q: str | None = None):
    if q:
        message = f"found query: {q}\n"
        background_tasks.add_task(write_log, message)
    return q

@app.post("/send-notification/{email}")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks,
    q: Annotated[str, Depends(get_query)]
):
    message = f"message to {email}\n"
    background_tasks.add_task(write_log, message)
    return {"message": "Message sent"}
```

All tasks from dependencies and path operations are merged and run after response.

## Heavy Background Jobs

For complex workloads, consider:

- **Celery** - Distributed task queue with RabbitMQ/Redis
- **Redis Queue (RQ)** - Simple Redis-based queue
- **Dramatiq** - Alternative to Celery

Use these when you need:

- Tasks running on multiple processes/servers
- Retries and failure handling
- Scheduled/periodic tasks
- Task result tracking

## When to Use BackgroundTasks

✅ Good for:

- Small, quick tasks
- Access to same app variables/objects
- No need for separate worker process

❌ Better use Celery for:

- Long-running computations
- Tasks needing multiple workers/servers
- Complex retry logic

## Import Note

```python
# Use BackgroundTasks (plural) not BackgroundTask
from fastapi import BackgroundTasks  # ✓
# NOT from starlette.background import BackgroundTask
```
