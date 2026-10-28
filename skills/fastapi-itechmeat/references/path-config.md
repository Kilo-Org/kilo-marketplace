# Path Operation Configuration

Metadata and configuration for endpoint documentation.

## Response Status Code

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item

# Or use integer directly
@app.post("/items/", status_code=201)
async def create_item(item: Item):
    return item
```

Common codes: `200` OK, `201` Created, `204` No Content, `404` Not Found.

See `error-handling.md` for full status codes table.

## Tags

Group endpoints in docs:

```python
@app.post("/items/", tags=["items"])
async def create_item(item: Item):
    return item

@app.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "johndoe"}]
```

### Tags with Enum

```python
from enum import Enum

class Tags(Enum):
    items = "items"
    users = "users"

@app.get("/items/", tags=[Tags.items])
async def get_items():
    return ["Portal gun", "Plumbus"]
```

## Summary and Description

```python
@app.post(
    "/items/",
    summary="Create an item",
    description="Create an item with all the information: name, description, price, tax, tags"
)
async def create_item(item: Item):
    return item
```

### Description from Docstring

```python
@app.post("/items/", summary="Create an item")
async def create_item(item: Item):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    return item
```

Markdown supported in docstrings!

## Response Description

```python
@app.post(
    "/items/",
    response_model=Item,
    summary="Create an item",
    response_description="The created item"
)
async def create_item(item: Item):
    """Create an item with all the information."""
    return item
```

OpenAPI requires response description. FastAPI defaults to "Successful response" if omitted.

## Deprecate Endpoint

```python
@app.get("/elements/", tags=["items"], deprecated=True)
async def read_elements():
    return [{"item_id": "Foo"}]
```

Shown with strikethrough in docs.

## JSON Compatible Encoder

Convert Pydantic models to JSON-compatible dicts:

```python
from datetime import datetime
from fastapi.encoders import jsonable_encoder

class Item(BaseModel):
    title: str
    timestamp: datetime
    description: str | None = None

@app.put("/items/{id}")
def update_item(id: str, item: Item):
    json_compatible_data = jsonable_encoder(item)
    # datetime converted to ISO string
    fake_db[id] = json_compatible_data
```

### What jsonable_encoder Does

- `datetime` → ISO format string
- Pydantic model → dict
- Recursively converts nested objects
- Returns Python dict (not JSON string)

## Body Updates

### Full Update (PUT)

```python
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    stored = items[item_id]
    stored_model = Item(**stored)
    update_data = item.model_dump()
    updated = stored_model.model_copy(update=update_data)
    items[item_id] = jsonable_encoder(updated)
    return updated
```

### Partial Update (PATCH)

```python
@app.patch("/items/{item_id}")
async def update_item(item_id: int, item: ItemUpdate):
    stored = items[item_id]
    stored_model = Item(**stored)
    update_data = item.model_dump(exclude_unset=True)  # Only sent fields
    updated = stored_model.model_copy(update=update_data)
    items[item_id] = jsonable_encoder(updated)
    return updated
```

Key: `exclude_unset=True` includes only fields explicitly set by client.

## All Configuration Parameters

```python
@app.post(
    "/items/",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
    tags=["items"],
    summary="Create an item",
    description="Create a new item",
    response_description="The created item",
    deprecated=False,
    operation_id="create_item_items_post",
    include_in_schema=True,
    responses={
        201: {"description": "Created successfully"},
        400: {"description": "Bad request"}
    }
)
async def create_item(item: Item):
    return item
```

## OpenAPI Operation ID

```python
# Auto-generated: create_item_items_post
@app.post("/items/", operation_id="createItem")
async def create_item(item: Item):
    return item
```

Useful for SDK generation.

## Exclude from Schema

```python
@app.get("/internal/", include_in_schema=False)
async def internal_endpoint():
    return {"internal": "data"}
```

Not shown in OpenAPI docs.
