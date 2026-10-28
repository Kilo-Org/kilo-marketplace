# OpenAPI Advanced

Callbacks, webhooks, custom operation IDs, SDK generation.

## OpenAPI Callbacks

Document external API callbacks your API will trigger:

```python
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, HttpUrl

app = FastAPI()

class Invoice(BaseModel):
    id: str
    customer: str
    total: float

class InvoiceEvent(BaseModel):
    description: str
    paid: bool

class InvoiceEventReceived(BaseModel):
    ok: bool

# Create callback router (documentation only)
callback_router = APIRouter()

@callback_router.post(
    "{$callback_url}/invoices/{$request.body.id}",
    response_model=InvoiceEventReceived
)
def invoice_notification(body: InvoiceEvent):
    """External API should implement this endpoint"""
    pass  # No code needed - documentation only

# Main endpoint with callbacks
@app.post("/invoices/", callbacks=callback_router.routes)
def create_invoice(invoice: Invoice, callback_url: HttpUrl | None = None):
    """
    Create invoice. Will call callback_url when payment processed.
    """
    return {"msg": "Invoice created"}
```

Callback path expression: `{$callback_url}` from query param, `{$request.body.id}` from request body.

## OpenAPI Webhooks

Document webhooks your API sends (OpenAPI 3.1):

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Subscription(BaseModel):
    username: str
    plan: str

@app.webhooks.post("new-subscription")
def new_subscription(body: Subscription):
    """
    Webhook sent when new user subscribes.
    External systems should implement this endpoint.
    """
    pass
```

Shows in `/docs` under Webhooks section.

## Custom Operation IDs

Clean method names for SDK generation:

```python
from fastapi import FastAPI
from fastapi.routing import APIRoute

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

app = FastAPI(generate_unique_id_function=custom_generate_unique_id)

@app.get("/items/", tags=["items"])
def get_items():  # Operation ID: items-get_items
    return []
```

## Path Operation Config

```python
@app.get(
    "/items/{item_id}",
    operation_id="get_single_item",  # Custom ID
    summary="Get Item",
    description="Retrieve item by ID",
    deprecated=True,  # Mark as deprecated
    include_in_schema=True  # Set False to hide
)
def read_item(item_id: str):
    return {"id": item_id}
```

## Exclude from OpenAPI

```python
@app.get("/internal", include_in_schema=False)
def internal_endpoint():
    return {"secret": "data"}
```

## OpenAPI Extra

Add arbitrary OpenAPI fields:

```python
@app.post(
    "/items/",
    openapi_extra={
        "x-custom-field": "value",
        "requestBody": {
            "content": {
                "application/x-yaml": {
                    "schema": {"type": "object"}
                }
            },
            "required": True
        }
    }
)
def create_item():
    return {}
```

## SDK Generation

### Using Hey API (TypeScript)

```bash
npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/client
```

### Using OpenAPI Generator

```bash
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./client
```

### Preprocess OpenAPI for Cleaner Names

```python
import json
from pathlib import Path

# Download openapi.json first
file = Path("openapi.json")
spec = json.loads(file.read_text())

# Remove tag prefix from operation IDs
for path_data in spec["paths"].values():
    for operation in path_data.values():
        tag = operation["tags"][0]
        op_id = operation["operationId"]
        # items-get_items -> get_items
        operation["operationId"] = op_id.removeprefix(f"{tag}-")

file.write_text(json.dumps(spec))
```

## Sub-Applications (Mounts)

Independent apps with separate OpenAPI:

```python
app = FastAPI()
subapi = FastAPI()

@app.get("/app")
def main_root():
    return {"message": "Main app"}

@subapi.get("/sub")
def sub_root():
    return {"message": "Sub app"}

app.mount("/subapi", subapi)
# Main docs: /docs
# Sub docs: /subapi/docs
```

## WSGI Integration (Flask/Django)

```python
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask

flask_app = Flask(__name__)

@flask_app.route("/")
def flask_root():
    return "Hello from Flask"

app = FastAPI()

@app.get("/v2")
def fastapi_root():
    return {"message": "FastAPI"}

app.mount("/v1", WSGIMiddleware(flask_app))
# /v1/* -> Flask
# /v2   -> FastAPI
```
