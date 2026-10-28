# Security

Authentication and authorization patterns in FastAPI.

## Security Schemes (OpenAPI)

FastAPI supports standard OpenAPI security schemes:

| Scheme          | Description                       |
| --------------- | --------------------------------- |
| `apiKey`        | Key in query, header, or cookie   |
| `http`          | HTTP auth (Basic, Bearer, Digest) |
| `oauth2`        | OAuth2 flows                      |
| `openIdConnect` | OpenID Connect auto-discovery     |

## OAuth2 Password Flow (Simple)

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # Validate user credentials
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: Annotated[str, Depends(oauth2_scheme)]):
    user = get_user_from_token(token)
    return user
```

## Get Current User Pattern

```python
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = decode_token(token)
    if user is None:
        raise credentials_exception
    return user

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user
```

## JWT Tokens

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

## Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

## HTTP Basic Auth

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    # Use compare_digest to prevent timing attacks
    correct_user = secrets.compare_digest(
        credentials.username.encode("utf8"),
        b"admin"
    )
    correct_pass = secrets.compare_digest(
        credentials.password.encode("utf8"),
        b"secret"
    )
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"}
        )
    return credentials.username

@app.get("/admin")
def admin_area(username: Annotated[str, Depends(get_current_username)]):
    return {"message": f"Hello {username}"}
```

Important: Always use `secrets.compare_digest()` - regular `==` is vulnerable to timing attacks.

## OAuth2 Scopes

Fine-grained permissions with scopes:

```python
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "items:read": "Read items",
        "items:write": "Create/update items",
        "users:read": "Read user info"
    }
)

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    # Build WWW-Authenticate header
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value}
    )

    # Decode and verify token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    # Check scopes
    token_scopes = payload.get("scopes", [])
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value}
            )

    return get_user(payload["sub"])

# Use Security() instead of Depends() for scopes
@app.get("/items/")
async def read_items(
    user: Annotated[User, Security(get_current_user, scopes=["items:read"])]
):
    return items

@app.post("/items/")
async def create_item(
    item: Item,
    user: Annotated[User, Security(get_current_user, scopes=["items:write"])]
):
    return item
```

## Token with Scopes

```python
def create_access_token(data: dict, scopes: list[str]):
    to_encode = data.copy()
    to_encode.update({
        "scopes": scopes,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400)

    # Grant requested scopes (validate against user permissions)
    token = create_access_token(
        data={"sub": user.username},
        scopes=form_data.scopes
    )
    return {"access_token": token, "token_type": "bearer"}
```
