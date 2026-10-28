# Integration Patterns

Concrete guidance for integrating VDS queries into production applications.

The `query_tableau_data_py` client library is designed for REPL exploration and reusable scripts. When consumers integrate it into async frameworks (Streamlit, FastAPI, Django Channels) or long-lived services, the sync/async protocol boundary becomes the primary integration concern. This guide covers that boundary and the correct patterns for crossing it.

---

## Python: Session Is Sync-Only

`Session` implements `__enter__` / `__exit__` only. It is a **synchronous** context manager backed by stdlib `http.client` — there is no async I/O anywhere in the transport layer.

```python
# CORRECT — synchronous context manager
with Session(SdkConfig()) as session:
    result = session.query(request)
```

```python
# WRONG — will crash at runtime
async with Session(SdkConfig()) as session:  # TypeError
    result = await session.query(request)
```

The error you will see in production:

```
TypeError: 'Session' object does not support the asynchronous context manager protocol
```

This is intentional. The client library uses `http.client` (stdlib) for zero-dependency HTTP transport. Adding `__aenter__` / `__aexit__` without replacing the transport would create a mixed-protocol footgun — the methods would still block the event loop.

---

## Python: Wrapping for Async Frameworks

### Pattern 1: `asyncio.to_thread` (Streamlit, FastAPI)

The simplest and recommended pattern. Offloads the entire sync Session lifecycle to a thread, keeping your event loop free.

```python
import asyncio
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.session import Session
from query_tableau_data_py.models import QueryRequest, QueryField

async def fetch_sales_data() -> list[dict]:
    """Run a VDS query without blocking the async event loop."""

    def _sync_query():
        with Session(SdkConfig()) as session:
            request = QueryRequest(
                datasource_luid="<luid>",
                fields=[
                    QueryField(field_caption="Region"),
                    QueryField(field_caption="Sales", function="SUM"),
                ],
            )
            result = session.query(request)
            return result.rows

    return await asyncio.to_thread(_sync_query)
```

Use this when:
- You have a short-lived request handler (Streamlit callback, FastAPI endpoint)
- You need one Session per request (fresh auth, no connection sharing)

### Pattern 2: `run_in_executor` (long-lived processes)

For services that need explicit control over the thread pool — e.g., bounding concurrency to avoid overwhelming Tableau with parallel connections.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from query_tableau_data_py.config import SdkConfig
from query_tableau_data_py.session import Session

# Limit concurrent Tableau connections
_tableau_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="tableau")

async def fetch_data(request):
    loop = asyncio.get_running_loop()

    def _sync_query():
        with Session(SdkConfig()) as session:
            return session.query(request)

    return await loop.run_in_executor(_tableau_pool, _sync_query)
```

Use this when:
- You need to bound concurrency (rate-limit protection)
- Multiple async tasks query Tableau concurrently
- You want named threads for observability

---

## Python: Testing — Mock Must Match the Protocol

When testing code that uses `Session`, the mock **must** implement the synchronous context manager protocol. If the mock supports `async with` (as `MagicMock` does by default in some configurations), tests will pass — but production will crash.

### Correct: Sync mock

```python
from unittest.mock import patch, MagicMock

def test_my_data_function():
    with patch("my_app.data.Session") as MockSession:
        # Configure the sync context manager protocol
        mock_session = MagicMock()
        MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
        MockSession.return_value.__exit__ = MagicMock(return_value=False)

        # Configure return values
        mock_session.query.return_value = expected_result

        # Test your code
        result = my_data_function()
        assert result == expected_result
```

### Wrong: Async mock (causes production crash)

```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_my_data_function():
    with patch("my_app.data.Session") as MockSession:
        # BUG: AsyncMock supports async with — tests pass, production crashes
        mock_session = AsyncMock()
        MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        MockSession.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_session.query.return_value = expected_result
        result = await my_data_function()
        # Test passes! But real Session doesn't have __aenter__
```

**Why the wrong pattern passes tests:** `AsyncMock` and `MagicMock` will happily implement whatever protocol you configure. The mock object has no idea that the real `Session` class only supports `with`. Your tests validate mock behaviour, not production behaviour.

**Rule:** If the real class is sync-only, your mock must be sync-only. Match the protocol.

---

## Anti-patterns

### Do not subclass Session for async

```python
# DO NOT DO THIS
class AsyncSession(Session):
    async def __aenter__(self):
        return self.__enter__()  # Still blocks the event loop!

    async def __aexit__(self, *args):
        return self.__exit__(*args)
```

This compiles and runs — but `__aenter__` calls `__enter__`, which performs synchronous HTTP (sign-in). Your event loop is blocked for the entire network round-trip. The `async` keyword provides no benefit here; it only hides the blocking call from linters and reviewers.

Use `asyncio.to_thread()` instead. It genuinely offloads blocking work to a separate thread.

---

## General Guidance

These principles apply regardless of language implementation (Python today, JS in the future):

| Concern | Guidance |
|---------|----------|
| **Thread safety** | Session instances are **not** thread-safe. Use one Session per thread. Do not share a Session across `asyncio.to_thread` calls. |
| **Connection lifecycle** | Prefer short-lived sessions (one per request/task). The auth token is valid for ~240 minutes, but holding connections open invites stale-socket errors. |
| **Error propagation** | Exceptions from `_sync_query()` propagate through `asyncio.to_thread` unchanged. Catch `QueryExecutionError`, `AuthenticationError`, etc. in your async handler as you would synchronously. |
| **Idempotent teardown** | `Session.__exit__` is idempotent — calling it multiple times is safe. If your wrapper has complex error handling, don't worry about double-close. |
