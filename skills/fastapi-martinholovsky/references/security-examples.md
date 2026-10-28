# FastAPI Security Examples Reference

## CVE Details and Mitigations

### CVE-2024-47874: Starlette Multipart DoS

**Severity**: HIGH (CVSS 8.7)
**Affected**: Starlette < 0.40.0
**CWE**: CWE-400 (Resource Exhaustion)

**Description**: Multipart form fields without filename are buffered entirely in memory without high-water mark limits, allowing memory exhaustion.

**Mitigation**:
```bash
pip install 'starlette>=0.40.0' 'fastapi>=0.115.3'
```

```python
# Additional protection: request size limits
@app.middleware("http")
async def limit_body_size(request, call_next):
    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB

    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > MAX_BODY_SIZE:
            return JSONResponse(413, {"detail": "Request too large"})

    return await call_next(request)
```

---

## Complete OWASP Examples

### A01: Broken Access Control

```python
from fastapi import Depends, HTTPException

def require_role(role: str):
    async def checker(user: User = Depends(get_current_user)):
        if role not in user.roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("admin"))
):
    # Only admins can delete
    await user_service.delete(user_id)
```

### A02: Cryptographic Failures

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### A03: Injection

```python
# SQL Injection Prevention
from sqlalchemy import select

async def get_user(db, username: str):
    stmt = select(User).where(User.username == username)
    return (await db.execute(stmt)).scalar_one_or_none()

# Command Injection Prevention
import subprocess

def safe_command(filename: str):
    if not filename.isalnum():
        raise ValueError("Invalid filename")
    subprocess.run(["cat", filename], check=True)
```

### A05: Security Misconfiguration

```python
from fastapi import FastAPI
from secure import SecureHeaders

secure_headers = SecureHeaders(
    hsts=True,
    xfo="DENY",
    xxp=True,
    content="nosniff",
    csp="default-src 'self'"
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    secure_headers.framework.fastapi(response)
    return response
```

### A07: Authentication Failures

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/token")
@limiter.limit("5/minute")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate(form.username, form.password)
    if not user:
        raise HTTPException(401, "Incorrect credentials")
    return {"access_token": create_token(user), "token_type": "bearer"}
```

---

## Additional Security Patterns

### API Key Authentication

```python
from fastapi import Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(401, "API key required")

    key = await get_api_key(api_key)
    if not key or not key.is_active:
        raise HTTPException(403, "Invalid API key")

    return key

@app.get("/data")
async def get_data(key: APIKey = Depends(verify_api_key)):
    return {"data": "secret"}
```

### Request Validation Middleware

```python
@app.middleware("http")
async def validate_requests(request: Request, call_next):
    # Check content type
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith(("application/json", "multipart/form-data")):
            return JSONResponse(415, {"detail": "Unsupported media type"})

    return await call_next(request)
```

### Secure Database Operations

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    os.environ["DATABASE_URL"],
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True  # Check connections
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```
