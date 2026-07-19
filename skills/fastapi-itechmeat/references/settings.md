# Settings & Environment Variables

Configuration management with Pydantic Settings.

## Install

```bash
pip install pydantic-settings
```

## Basic Settings Class

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My API"
    admin_email: str
    items_per_user: int = 50

settings = Settings()  # Reads from env vars

# Usage
@app.get("/info")
def info():
    return {"app_name": settings.app_name}
```

## Environment Variables

Variables are case-insensitive:

```bash
# Set env vars
export ADMIN_EMAIL="admin@example.com"
export APP_NAME="MyApp"

# Or inline
ADMIN_EMAIL="admin@example.com" fastapi run main.py
```

## Settings in Separate Module

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

settings = Settings()

# main.py
from .config import settings

app = FastAPI(debug=settings.debug)
```

## Settings as Dependency

```python
from functools import lru_cache
from fastapi import Depends

class Settings(BaseSettings):
    api_key: str
    database_url: str

@lru_cache  # Create once, reuse
def get_settings():
    return Settings()

@app.get("/config")
def read_config(settings: Annotated[Settings, Depends(get_settings)]):
    return {"key": settings.api_key}
```

## .env File Support

```python
# .env
DATABASE_URL="postgresql://localhost/db"
SECRET_KEY="mysecret"
DEBUG=true
```

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env")
```

Requires: `pip install python-dotenv`

## Nested Settings

```python
class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    name: str = "app"

class Settings(BaseSettings):
    db: DatabaseSettings = DatabaseSettings()

    model_config = SettingsConfigDict(env_nested_delimiter="__")

# Set via: DB__HOST=myhost DB__PORT=5433
```

## Override in Tests

```python
# test_main.py
from fastapi.testclient import TestClient
from .config import Settings
from .main import app, get_settings

def get_settings_override():
    return Settings(admin_email="test@example.com")

app.dependency_overrides[get_settings] = get_settings_override

client = TestClient(app)

def test_app():
    response = client.get("/info")
    assert response.json()["admin_email"] == "test@example.com"
```

## lru_cache Explained

```python
@lru_cache
def get_settings():
    return Settings()  # Only called once
```

Without `@lru_cache`, each request reads .env file again. With it, settings loaded once and cached.

## Validation

Pydantic validates types automatically:

```python
class Settings(BaseSettings):
    port: int  # Must be integer
    allowed_hosts: list[str] = ["localhost"]

# ALLOWED_HOSTS='["host1.com", "host2.com"]'
```

## Sensitive Values

```python
from pydantic import SecretStr

class Settings(BaseSettings):
    password: SecretStr

settings = Settings()
print(settings.password)  # SecretStr('**********')
print(settings.password.get_secret_value())  # actual value
```
