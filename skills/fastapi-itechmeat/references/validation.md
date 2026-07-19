# Parameter Validation

Advanced validation for Query, Path, Header, Cookie parameters.

## Query Validation with `Query`

```python
from typing import Annotated
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/items/")
async def read_items(
    q: Annotated[str | None, Query(max_length=50)] = None
):
    return {"q": q}
```

## String Validations

```python
q: Annotated[str | None, Query(
    min_length=3,
    max_length=50,
    pattern="^[a-z]+$"  # Regex pattern
)] = None
```

## Numeric Validations (Path/Query)

```python
from fastapi import Path

@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(ge=1, le=1000)],  # 1 ≤ value ≤ 1000
    size: Annotated[float, Query(gt=0, lt=100)]   # 0 < value < 100
):
    ...
```

| Parameter | Meaning               |
| --------- | --------------------- |
| `gt`      | Greater than          |
| `ge`      | Greater than or equal |
| `lt`      | Less than             |
| `le`      | Less than or equal    |

## Metadata for Documentation

```python
q: Annotated[str | None, Query(
    title="Search query",
    description="Full-text search in item names",
    min_length=3,
    max_length=50,
    deprecated=True  # Shows as deprecated in docs
)] = None
```

## Alias Parameter Name

```python
# URL: /items/?item-query=foo
@app.get("/items/")
async def read_items(
    q: Annotated[str | None, Query(alias="item-query")] = None
):
    return {"q": q}
```

## Multiple Values (List)

```python
# URL: /items/?q=foo&q=bar
@app.get("/items/")
async def read_items(
    q: Annotated[list[str] | None, Query()] = None
):
    return {"q": q}  # ["foo", "bar"]
```

With defaults:

```python
q: Annotated[list[str], Query()] = ["default1", "default2"]
```

## Required Parameters with Validation

```python
# Required (no default)
q: Annotated[str, Query(min_length=3)]

# Required but can be None
q: Annotated[str | None, Query(min_length=3)]  # No default!
```

## Custom Validation

```python
from pydantic import AfterValidator

def validate_id(value: str) -> str:
    if not value.startswith(("isbn-", "imdb-")):
        raise ValueError("ID must start with isbn- or imdb-")
    return value

@app.get("/items/")
async def read_items(
    id: Annotated[str, AfterValidator(validate_id)]
):
    ...
```

## Exclude from OpenAPI

```python
hidden: Annotated[str | None, Query(include_in_schema=False)] = None
```

## Best Practice: Use Annotated

```python
# ✅ Recommended (Python 3.9+)
q: Annotated[str | None, Query(max_length=50)] = None

# ❌ Old style (avoid)
q: str | None = Query(default=None, max_length=50)
```
