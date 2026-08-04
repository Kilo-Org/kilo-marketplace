# Path Parameters

Capture dynamic values from URL paths.

## Basic Syntax

```python
@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
```

## Type Annotations

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

Benefits:

- **Data conversion**: String "3" → integer 3
- **Data validation**: Invalid values return clear error
- **Editor support**: Autocomplete, type checking
- **Auto documentation**: Types shown in OpenAPI docs

## Validation Error Response

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "item_id"],
      "msg": "Input should be a valid integer",
      "input": "foo"
    }
  ]
}
```

## Order Matters

Fixed paths must be declared before parameterized paths:

```python
# ✅ Correct order
@app.get("/users/me")  # First - specific
async def read_user_me():
    return {"user_id": "current user"}

@app.get("/users/{user_id}")  # Second - generic
async def read_user(user_id: str):
    return {"user_id": user_id}
```

## Predefined Values with Enum

```python
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning"}
    return {"model_name": model_name}
```

Working with Enum values:

- Compare: `model_name is ModelName.alexnet`
- Get value: `model_name.value` → `"alexnet"`
- Returns JSON serialized string

## Path Parameters Containing Paths

Use `:path` converter for file paths:

```python
@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
```

URL: `/files//home/user/file.txt` (note double slash)

## Supported Types

- `str`, `int`, `float`, `bool`
- `UUID`
- Custom types via Pydantic
