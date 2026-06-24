# Cookie and Header Parameters

Handling HTTP cookies and headers in FastAPI.

## Cookie Parameters

```python
from typing import Annotated
from fastapi import Cookie, FastAPI

app = FastAPI()

@app.get("/items/")
async def read_items(ads_id: Annotated[str | None, Cookie()] = None):
    return {"ads_id": ads_id}
```

### Key Points

- **Import**: `from fastapi import Cookie`
- **Required**: Use `Cookie()` to distinguish from query params
- **Validation**: Same as `Query()`, `Path()`
- **Browser limitation**: Swagger UI cannot test cookies (JavaScript restriction)

### Optional Cookie

```python
@app.get("/items/")
async def read_items(
    session_id: Annotated[str | None, Cookie()] = None,
    tracking_id: Annotated[str | None, Cookie()] = None
):
    return {"session": session_id, "tracking": tracking_id}
```

## Header Parameters

```python
from typing import Annotated
from fastapi import FastAPI, Header

app = FastAPI()

@app.get("/items/")
async def read_items(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}
```

### Automatic Conversion

FastAPI converts:

- `user_agent` → `User-Agent`
- `x_token` → `X-Token`

```python
# Python variable: x_custom_header
# HTTP Header: X-Custom-Header (automatic conversion)
@app.get("/items/")
async def read_items(x_custom_header: Annotated[str | None, Header()] = None):
    return {"header": x_custom_header}
```

### Disable Underscore Conversion

```python
@app.get("/items/")
async def read_items(
    strange_header: Annotated[str | None, Header(convert_underscores=False)] = None
):
    return {"strange_header": strange_header}
```

⚠️ Warning: Some proxies/servers disallow headers with underscores.

`0.136.3` note:

- With the default `Header()` behavior (`convert_underscores=True`), FastAPI now rejects incoming underscore-named headers instead of silently accepting them through the hyphen-conversion path.
- If a legacy client really sends `X_Custom_Header`, opt into `Header(convert_underscores=False)` explicitly and verify every proxy/load balancer in front of FastAPI preserves underscore headers.

### Duplicate Headers

For headers that can appear multiple times:

```python
@app.get("/items/")
async def read_items(x_token: Annotated[list[str] | None, Header()] = None):
    return {"X-Token values": x_token}
```

Request with:

```
X-Token: foo
X-Token: bar
```

Response:

```json
{ "X-Token values": ["bar", "foo"] }
```

## Common Headers

### Authorization

```python
@app.get("/protected/")
async def protected(authorization: Annotated[str | None, Header()] = None):
    if not authorization:
        raise HTTPException(401, "Missing authorization")
    # Parse "Bearer <token>"
    return {"auth": authorization}
```

### Content-Type

```python
@app.post("/webhook/")
async def webhook(
    content_type: Annotated[str | None, Header()] = None,
    body: bytes = Body(...)
):
    if content_type == "application/json":
        # Handle JSON
        pass
    return {"content_type": content_type}
```

#### Strict JSON `Content-Type` checking (FastAPI 0.132.0)

FastAPI 0.132.0 enables **strict JSON `Content-Type` checking** by default. If a request includes a JSON body but does not send a valid JSON `Content-Type` header (for example `application/json`), FastAPI will reject the request.

If you need the previous (more permissive) behavior for legacy clients, disable the check at app creation time:

```python
from fastapi import FastAPI

app = FastAPI(strict_content_type=False)
```

### Custom Headers

```python
@app.get("/items/")
async def read_items(
    x_request_id: Annotated[str | None, Header()] = None,
    x_correlation_id: Annotated[str | None, Header()] = None
):
    return {"request_id": x_request_id, "correlation_id": x_correlation_id}
```

## Cookie/Header Parameter Models (FastAPI 0.115+)

### Cookie Model

```python
from pydantic import BaseModel

class Cookies(BaseModel):
    session_id: str
    tracking_id: str | None = None

@app.get("/items/")
async def read_items(cookies: Annotated[Cookies, Cookie()]):
    return cookies
```

### Header Model

```python
class CommonHeaders(BaseModel):
    x_request_id: str
    x_correlation_id: str | None = None
    user_agent: str | None = None

@app.get("/items/")
async def read_items(headers: Annotated[CommonHeaders, Header()]):
    return headers
```

## Setting Response Cookies/Headers

### Set Cookie

```python
from fastapi import Response

@app.post("/login/")
async def login(response: Response):
    response.set_cookie(
        key="session_id",
        value="abc123",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    return {"message": "logged in"}
```

### Set Header

```python
@app.get("/items/")
async def read_items(response: Response):
    response.headers["X-Custom-Header"] = "custom-value"
    return {"items": []}
```

## Recipes

### API Key in Header

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != "secret-api-key":
        raise HTTPException(403, "Invalid API key")
    return api_key

@app.get("/protected/", dependencies=[Depends(verify_api_key)])
async def protected_route():
    return {"message": "Access granted"}
```

### Request Tracing

```python
import uuid

@app.middleware("http")
async def add_request_id(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

## Comparison Table

| Feature          | Cookie       | Header              |
| ---------------- | ------------ | ------------------- |
| Import           | `Cookie`     | `Header`            |
| Auto-conversion  | No           | Underscore → Hyphen |
| Case-sensitive   | Yes          | No                  |
| Multiple values  | No           | Yes (list type)     |
| Browser testable | No (Swagger) | Yes                 |
