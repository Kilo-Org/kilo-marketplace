# CORS (Cross-Origin Resource Sharing)

Enable cross-origin requests from frontend to backend.

## What is Origin?

Origin = protocol + domain + port

Different origins:

- `http://localhost` (port 80)
- `http://localhost:8080` (port 8080)
- `https://localhost` (HTTPS)

## Basic CORS Setup

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "https://myapp.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Configuration Options

| Parameter            | Default   | Description                                          |
| -------------------- | --------- | ---------------------------------------------------- |
| `allow_origins`      | `[]`      | List of allowed origins                              |
| `allow_origin_regex` | `None`    | Regex for origins (e.g., `https://.*\.example\.org`) |
| `allow_methods`      | `["GET"]` | Allowed HTTP methods                                 |
| `allow_headers`      | `[]`      | Allowed request headers                              |
| `allow_credentials`  | `False`   | Allow cookies/auth headers                           |
| `expose_headers`     | `[]`      | Headers visible to browser                           |
| `max_age`            | `600`     | Preflight cache time (seconds)                       |

## Common Configurations

### Development (Allow All)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

⚠️ Can't use `["*"]` with `allow_credentials=True`

### Production (Specific Origins)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myapp.com",
        "https://www.myapp.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Regex Pattern

```python
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.myapp\.com",
)
```

## How CORS Works

### Preflight Requests

- Browser sends `OPTIONS` request first
- Includes `Origin` and `Access-Control-Request-Method` headers
- Backend responds with allowed origins/methods
- Browser then sends actual request

### Simple Requests

- GET, HEAD, POST with standard headers
- No preflight needed
- Backend adds CORS headers to response

## Credentials Warning

When `allow_credentials=True`:

- Cannot use `["*"]` for origins, methods, or headers
- Must explicitly list all allowed values

```python
# ❌ Invalid
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Conflict!
)

# ✅ Valid
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com"],
    allow_credentials=True,
)
```

## Debugging CORS

Check browser console for:

- `Access-Control-Allow-Origin` header missing
- Origin not in allowed list
- Method not allowed
- Credential issues

Use browser DevTools Network tab to inspect preflight requests.
