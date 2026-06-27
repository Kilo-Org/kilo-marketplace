# API Metadata and Documentation URLs

Customize OpenAPI metadata and documentation UI.

## API Metadata

```python
from fastapi import FastAPI

description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""

app = FastAPI(
    title="ChimichangApp",
    description=description,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
```

### Metadata Fields

| Field              | Type | Description                           |
| ------------------ | ---- | ------------------------------------- |
| `title`            | str  | API title                             |
| `summary`          | str  | Short summary (OpenAPI 3.1.0+)        |
| `description`      | str  | Full description (Markdown supported) |
| `version`          | str  | Your API version (e.g., "2.5.0")      |
| `terms_of_service` | str  | URL to ToS                            |
| `contact`          | dict | Contact info                          |
| `license_info`     | dict | License info                          |

### License Identifier (OpenAPI 3.1.0+)

```python
license_info={
    "name": "Apache 2.0",
    "identifier": "MIT",  # Instead of URL
}
```

## Tag Metadata

```python
tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

app = FastAPI(openapi_tags=tags_metadata)

@app.get("/users/", tags=["users"])
async def get_users():
    return [{"name": "Harry"}, {"name": "Ron"}]

@app.get("/items/", tags=["items"])
async def get_items():
    return [{"name": "wand"}, {"name": "flying broom"}]
```

Tag order in docs follows list order (not alphabetical).

## OpenAPI URL

```python
# Default: /openapi.json
app = FastAPI(openapi_url="/api/v1/openapi.json")

# Disable OpenAPI entirely
app = FastAPI(openapi_url=None)
```

## Docs URLs

```python
# Defaults: /docs (Swagger), /redoc (ReDoc)
app = FastAPI(
    docs_url="/documentation",  # Swagger UI
    redoc_url="/redocumentation",  # ReDoc
)

# Disable docs
app = FastAPI(docs_url=None, redoc_url=None)
```

## Static Files

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Mount Parameters

| Parameter            | Description               |
| -------------------- | ------------------------- |
| `"/static"`          | URL path prefix           |
| `directory="static"` | Local directory           |
| `name="static"`      | Internal name for FastAPI |

### What is Mounting?

Mounting adds a complete independent application at a specific path. Mounted apps are:

- Completely independent
- Not included in main app's OpenAPI
- Handle all sub-paths themselves

## Debugging

### VS Code / PyCharm Debug Setup

```python
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    a = "a"
    b = "b" + a
    return {"hello world": b}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### VS Code Debug Config

1. Go to "Debug" panel
2. "Add configuration..." → Python
3. Select "Python: Current File (Integrated Terminal)"
4. Set breakpoints and run

### PyCharm Debug

1. Open "Run" menu
2. Select "Debug..."
3. Choose the file (e.g., `main.py`)

### About `__name__ == "__main__"`

- Runs code only when file is executed directly: `python myapp.py`
- Does NOT run when imported: `from myapp import app`

## Recipes

### Production vs Development Docs

```python
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)
```

### Custom OpenAPI Schema

```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Custom Title",
        version="1.0.0",
        description="Custom description",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Serve Static with HTML

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")
```
