````markdown
# Dependencies

Dependency Injection system for shared logic, database connections, security.

## Basic Dependency

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

## How It Works

1. Define a function (dependency) that takes parameters
2. Use `Depends(function)` in path operation parameters
3. FastAPI calls the dependency, gets result, passes to your function

## Reusable Type Alias

```python
CommonsDep = Annotated[dict, Depends(common_parameters)]

@app.get("/items/")
async def read_items(commons: CommonsDep):
    return commons
```

## Classes as Dependencies

```python
class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(commons: Annotated[CommonQueryParams, Depends()]):
    # Shortcut: Depends() without argument when class == type hint
    return {"q": commons.q, "skip": commons.skip}
```

Any "callable" works: function, class, or object with `__call__`.

## Sub-dependencies

Dependencies can depend on other dependencies:

```python
def query_extractor(q: str | None = None):
    return q

def query_or_cookie_extractor(
    q: Annotated[str, Depends(query_extractor)],
    last_query: Annotated[str | None, Cookie()] = None
):
    return q or last_query

@app.get("/items/")
async def read_query(query: Annotated[str, Depends(query_or_cookie_extractor)]):
    return {"q": query}
```

### use_cache Parameter

```python
# Default: use_cache=True - same instance reused in request
dep1: Annotated[dict, Depends(get_db)]
dep2: Annotated[dict, Depends(get_db)]  # Same instance as dep1

# Force new instance
dep2: Annotated[dict, Depends(get_db, use_cache=False)]
```

## Dependencies in Decorators

For side-effect dependencies (auth checks, logging) that don't return values:

```python
async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="Invalid token")

@app.get("/items/", dependencies=[Depends(verify_token)])
async def read_items():
    return [{"item": "Foo"}]
```

## Global Dependencies

Apply to all routes:

```python
app = FastAPI(dependencies=[Depends(verify_token)])
```

## Dependencies with yield

For setup/cleanup (e.g., database sessions):

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
async def read_items(db: Annotated[Session, Depends(get_db)]):
    return db.query(Item).all()
```

### Execution Order

1. Code before `yield` runs first
2. `yield db` passes value to endpoint
3. Endpoint executes
4. Code after `yield` runs (cleanup)

### Exception Handling

```python
async def get_db():
    db = DBSession()
    try:
        yield db
    except SomeException:
        db.rollback()
        raise
    finally:
        db.close()
```

⚠️ Cannot raise HTTPException AFTER yield - response already sent.

### Sub-dependencies with yield

Exit order is reverse of entry (LIFO):

```
Enter dependency_a → Enter dependency_b → Endpoint → Exit dependency_b → Exit dependency_a
```

## Recipes

### Database Session per Request

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

### Authentication Chain

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.get("/users/me")
async def read_users_me(user: Annotated[User, Depends(get_current_active_user)]):
    return user
```

### Parameterized Dependency

```python
def pagination_params(max_limit: int = 100):
    def inner(skip: int = 0, limit: int = 10):
        return {"skip": skip, "limit": min(limit, max_limit)}
    return inner

@app.get("/items/")
async def read_items(pagination: Annotated[dict, Depends(pagination_params(50))]):
    return pagination
```

### Callable Class Dependency

```python
class FixedContentQueryChecker:
    def __init__(self, fixed_content: str):
        self.fixed_content = fixed_content

    def __call__(self, q: str = ""):
        if q:
            return self.fixed_content in q
        return False

checker = FixedContentQueryChecker(fixed_content="bar")

@app.get("/query-checker/")
async def check_query(fixed_content_included: Annotated[bool, Depends(checker)]):
    return {"fixed_content_in_query": fixed_content_included}
```

Instance with `__call__` allows storing state between requests.

## Use Cases

- Database sessions
- Authentication/Authorization
- Rate limiting
- Logging
- Shared query parameters
- Feature flags
- Configuration injection
````
