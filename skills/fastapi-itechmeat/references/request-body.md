# Request Body

Send JSON data from client to API using Pydantic models.

## Basic Example

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

## Pydantic Model Rules

- Required fields: no default value
- Optional fields: `= None`
- Fields with defaults: `= value`

Valid JSON for above model:

```json
{"name": "Foo", "price": 45.2}
{"name": "Foo", "description": "A thing", "price": 45.2, "tax": 3.5}
```

## What FastAPI Does Automatically

1. Reads request body as JSON
2. Converts types (string → int, etc.)
3. Validates data structure
4. Returns clear errors for invalid data
5. Provides editor autocomplete for model attributes
6. Generates JSON Schema for OpenAPI docs

## Using the Model

```python
@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()  # Convert to dict
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
```

## Combining Parameters

FastAPI distinguishes parameter types automatically:

```python
@app.put("/items/{item_id}")
async def update_item(
    item_id: int,              # Path parameter
    item: Item,                # Request body (Pydantic model)
    q: str | None = None       # Query parameter
):
    return {"item_id": item_id, **item.model_dump(), "q": q}
```

Recognition rules:

- Declared in path → **path parameter**
- Pydantic model → **request body**
- Singular type (str, int, etc.) → **query parameter**

## HTTP Methods for Body

- `POST` - Create (most common)
- `PUT` - Update/Replace
- `PATCH` - Partial update
- `DELETE` - Delete (rarely has body)

⚠️ `GET` with body is discouraged (undefined behavior in specs).
