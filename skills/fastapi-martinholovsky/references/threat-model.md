# FastAPI Threat Model

## Threat Model Overview

**Domain Risk Level**: HIGH

### Assets to Protect
1. **API Endpoints** - Business logic, data access - **Sensitivity**: HIGH
2. **Authentication** - User sessions, tokens - **Sensitivity**: CRITICAL
3. **User Data** - PII, credentials - **Sensitivity**: CRITICAL
4. **System Resources** - Memory, CPU - **Sensitivity**: MEDIUM (DoS risk)

### Attack Surface
- Public API endpoints
- Authentication/token endpoints
- File upload handlers
- WebSocket connections
- Database queries

---

## Attack Scenario 1: Multipart Form DoS (CVE-2024-47874)

**Threat Category**: OWASP A10:2025 / CWE-400

**Threat Level**: HIGH

**Attack Flow**:
```
1. Attacker sends multipart/form-data request
2. Form field has no filename (not file upload)
3. Starlette buffers entire field in memory
4. No high-water mark pause implemented
5. Attacker sends multiple concurrent large requests
6. Server memory exhausted, service crashes
```

**Mitigation**:
```python
# Upgrade to Starlette 0.40.0+
# Add request size limits
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(middleware=[
    Middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])
])

# Limit request body size
@app.middleware("http")
async def limit_request_size(request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
        return JSONResponse(status_code=413, content={"detail": "Request too large"})
    return await call_next(request)
```

---

## Attack Scenario 2: Authentication Brute Force

**Threat Category**: OWASP A07:2025 / CWE-307

**Threat Level**: HIGH

**Attack Flow**:
```
1. Attacker targets /login endpoint
2. Sends automated credential stuffing requests
3. Without rate limiting, thousands of attempts/second
4. Eventually guesses valid credentials
```

**Mitigation**:
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, creds: LoginRequest):
    user = await auth_service.authenticate(creds)
    if not user:
        # Log failed attempt
        logger.warning(f"Failed login: {creds.username} from {request.client.host}")
        # Generic error message
        raise HTTPException(401, "Invalid credentials")
    return {"token": create_token(user)}
```

---

## Attack Scenario 3: JWT Token Manipulation

**Threat Category**: OWASP A02:2025 / CWE-347

**Threat Level**: HIGH

**Attack Flow**:
```
1. Attacker obtains valid JWT
2. Changes algorithm to "none"
3. Modifies payload (e.g., user_id, role)
4. Server accepts unsigned token
5. Attacker gains elevated privileges
```

**Mitigation**:
```python
from jose import jwt, JWTError

def decode_token(token: str) -> dict:
    try:
        # Explicitly specify allowed algorithms
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],  # Never allow "none"
            options={"require_exp": True}
        )
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

---

## Attack Scenario 4: CORS Misconfiguration

**Threat Category**: OWASP A05:2025 / CWE-346

**Threat Level**: MEDIUM

**Attack Flow**:
```
1. API configured with allow_origins=["*"] + allow_credentials=True
2. Attacker creates malicious website
3. User visits attacker site while logged into API
4. Attacker's JavaScript makes authenticated requests
5. User's cookies sent, attacker steals data
```

**Mitigation**:
```python
# Never wildcard with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"]
)
```

---

## Attack Scenario 5: SQL Injection via Query Parameters

**Threat Category**: OWASP A03:2025 / CWE-89

**Threat Level**: CRITICAL

**Mitigation**:
```python
from sqlalchemy import select

@app.get("/users")
async def search_users(search: str, db: AsyncSession = Depends(get_db)):
    # SAFE: ORM with parameterized query
    stmt = select(User).where(User.name.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    return result.scalars().all()
```

---

## STRIDE Analysis

| Category | Threats | Mitigations | Priority |
|----------|---------|-------------|----------|
| **Spoofing** | JWT manipulation, stolen tokens | Strong JWT config, token rotation | HIGH |
| **Tampering** | Request body modification | HTTPS, input validation | HIGH |
| **Repudiation** | No audit trail | Log auth events, request IDs | MEDIUM |
| **Information Disclosure** | Verbose errors, CORS | Safe errors, restrictive CORS | HIGH |
| **Denial of Service** | Multipart DoS, brute force | Upgrade Starlette, rate limit | CRITICAL |
| **Elevation of Privilege** | SQL injection, auth bypass | Parameterized queries, JWT validation | CRITICAL |
