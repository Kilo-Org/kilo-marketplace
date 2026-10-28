# Forms and File Uploads

Form data handling and file uploads in FastAPI.

## Form Data

```python
from typing import Annotated
from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/login/")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
):
    return {"username": username}
```

### Key Points

- **Dependency**: `pip install python-multipart`
- **Import**: `from fastapi import Form`
- **Encoding**: `application/x-www-form-urlencoded`
- **Validation**: Same as `Body()`, `Query()`, `Path()`

### OAuth2 Password Flow

```python
# OAuth2 spec requires exact field names
@app.post("/token")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
):
    # Authenticate user
    return {"access_token": token}
```

## File Uploads

### bytes Parameter

```python
from typing import Annotated
from fastapi import FastAPI, File

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}
```

- Entire file stored in memory
- Good for small files only

### UploadFile Parameter

```python
from fastapi import FastAPI, UploadFile

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}
```

#### UploadFile Attributes

| Attribute      | Type                   | Description                    |
| -------------- | ---------------------- | ------------------------------ |
| `filename`     | `str`                  | Original filename              |
| `content_type` | `str`                  | MIME type (e.g., `image/jpeg`) |
| `file`         | `SpooledTemporaryFile` | Python file object             |

#### Async Methods

```python
contents = await myfile.read()      # Read all bytes
await myfile.seek(0)                # Go to start
await myfile.write(data)            # Write bytes
await myfile.close()                # Close file
```

#### Sync Access (in def functions)

```python
contents = myfile.file.read()
```

### Optional File Upload

```python
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile | None = None):
    if not file:
        return {"message": "No file sent"}
    return {"filename": file.filename}
```

### File with Metadata

```python
@app.post("/uploadfile/")
async def create_upload_file(
    file: Annotated[UploadFile, File(description="A file read as UploadFile")]
):
    return {"filename": file.filename}
```

## Multiple File Uploads

```python
from fastapi import FastAPI, File, UploadFile

@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}

# With metadata
@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[list[UploadFile], File(description="Multiple files")]
):
    return {"filenames": [file.filename for file in files]}
```

## Forms and Files Together

```python
from fastapi import FastAPI, File, Form, UploadFile

@app.post("/files/")
async def create_file(
    file: Annotated[bytes, File()],
    fileb: Annotated[UploadFile, File()],
    token: Annotated[str, Form()]
):
    return {
        "file_size": len(file),
        "fileb_content_type": fileb.content_type,
        "token": token
    }
```

## Encoding Types

| Content Type                        | When Used           |
| ----------------------------------- | ------------------- |
| `application/x-www-form-urlencoded` | Forms without files |
| `multipart/form-data`               | Forms with files    |

## Prohibitions

- ❌ Cannot mix `Body` (JSON) with `Form`/`File` in same endpoint
- ❌ Don't use `bytes` for large files (memory)

## Recipes

### File Upload with Validation

```python
from fastapi import HTTPException

ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB

@app.post("/upload/")
async def upload_file(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Invalid file type")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(400, "File too large")

    # Process file...
    return {"filename": file.filename}
```

### Save Uploaded File

```python
import shutil
from pathlib import Path

UPLOAD_DIR = Path("uploads")

@app.post("/upload/")
async def upload_file(file: UploadFile):
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "path": str(file_path)}
```
