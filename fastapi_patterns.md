# FastAPI Patterns — Cumulative Reference

---

## Route Registration (D91)

**What it does:** registers a function as a handler for a method + path pair.

```python
app = FastAPI()

@app.get("/items")
def list_items(): ...

@app.post("/items")
def create_item(body: MyModel): ...
```

One decorator = one (method, path) pair. GET and POST on the same path need two separate decorators.

---

## Path Parameters (D92)

**What it does:** extracts a segment from the URL and coerces its type.

```python
@app.get("/items/{item_id}")
def get_item(item_id: int): ...
# GET /items/5  →  item_id=5 (int, not str)
# GET /items/abc  →  422 automatically
```

Parameter name in the decorator must match the function argument name exactly.

---

## Query Parameters (D92)

**What it does:** reads ?key=value from the URL, coerces type, supports Optional.

```python
@app.get("/items")
def list_items(active: Optional[bool] = None): ...
# GET /items?active=true  →  active=True
# GET /items              →  active=None
```

Any function argument not in the path is treated as a query param.

---

## Request Body (D93)

**What it does:** parses and validates the JSON request body automatically.

```python
class ItemIn(BaseModel):
    name: str
    price: float = Field(gt=0)

@app.post("/items")
def create_item(body: ItemIn): ...
# Invalid body  →  422 automatically, before your function runs
```

Annotate the parameter with a BaseModel subclass — FastAPI treats it as the body.

---

## Response Model (D94)

**What it does:** validates and filters the return value before sending to client.

```python
class ItemOut(BaseModel):
    id: int
    name: str

@app.post("/items", response_model=ItemOut)
def create_item(body: ItemIn):
    return {**body.model_dump(), "id": 1, "internal_notes": "fragile"}
    # internal_notes stripped — client never sees it
```

Extra keys stripped. Missing required fields → 500 at runtime.

---

## HTTPException (D95)

**What it does:** aborts the request and sends an error response with a status code.

```python
raise HTTPException(status_code=404, detail="item not found")
raise HTTPException(status_code=403, detail="forbidden")
raise HTTPException(status_code=409, detail="already exists")
```

Replaces the custom AppError hierarchy from pure Python. FastAPI catches it automatically.

---

## Depends() — single (D96)

**What it does:** calls a function before the endpoint, injects its return value.

```python
def get_zone(zone_id: int) -> str:
    if zone_id not in ZONES:
        raise HTTPException(status_code=404, detail="zone not found")
    return ZONES[zone_id]

@app.get("/tanks")
def list_tanks(zone: str = Depends(get_zone)): ...
```

The dependency's parameters are resolved from the request just like an endpoint's.

---

## Depends() — chained (D97)

**What it does:** one dependency takes the result of another as its input.

```python
def get_vessel(vessel_id: int) -> dict: ...

def get_manifest(vessel: dict = Depends(get_vessel)) -> dict: ...

@app.get("/cargo")
def get_cargo(manifest: dict = Depends(get_manifest)): ...
```

Declare Depends() inside the dependent function's signature, not in the endpoint.

---

## BackgroundTasks (D98)

**What it does:** runs a function after the response is sent to the client.

```python
def log_audit(app_id: int): ...

@app.post("/apply")
def apply(bg: BackgroundTasks):
    bg.add_task(log_audit, app_id)
    return {"status": "received"}
```

Inject BackgroundTasks as a parameter. Response goes first, task runs after.

---

## Lifespan (D99)

**What it does:** runs code before first request (startup) and after last request (shutdown).

```python
APP_STATE = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    APP_STATE["db"] = connect()
    try:
        yield
    finally:
        APP_STATE.clear()

app = FastAPI(lifespan=lifespan)
```

Use `with TestClient(app) as client:` to trigger both lifecycle events in tests.

---

## Depends() — class-based (D100)

**What it does:** uses a class instance as a dependency — stateful, configurable.

```python
class Paginator:
    def __init__(self, page: int = 1, size: int = 10):
        self.page = page
        self.size = size

@app.get("/items")
def list_items(p: Paginator = Depends()):
    start = (p.page - 1) * p.size
    return items[start: start + p.size]
```

Pass the class itself to Depends() — FastAPI instantiates it per request.

---

## OAuth2PasswordBearer (D101)

**What it does:** extracts a bearer token from the Authorization header.

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    ...
```

Raises 401 automatically if the header is missing. `tokenUrl` is only used for OpenAPI docs.

---

## JWT Decode (D102)

**What it does:** verifies signature and expiry on a self-contained token, no server-side lookup table needed.

```python
from jose import jwt, JWTError

try:
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
except JWTError:
    raise HTTPException(401, detail="invalid token")
```

Add `"exp"` to claims (a UTC datetime) on encode — jose checks it automatically on decode.

---

## Current User Dependency (D103)

**What it does:** resolves a typed User model from the JWT instead of a raw dict.

```python
class User(BaseModel):
    username: str
    role: str

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    return User(username=payload["sub"], role=payload["role"])
```

Downstream deps chain off this by declaring `user: User = Depends(get_current_user)`.

---

## Role-Based Access Control (D104)

**What it does:** gates endpoints by role using a reusable checker factory.

```python
def require_role(required_role: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role:
            raise HTTPException(403, detail="forbidden")
        return user
    return checker

@app.delete("/items/{id}")
def delete_item(user: User = Depends(require_role("admin"))): ...
```

Each call to `require_role()` returns a fresh dependency function.

---

## Refresh Token Pattern (D105)

**What it does:** splits tokens into short-lived access + long-lived refresh, distinguished by a `"type"` claim.

```python
def make_access_token(username: str, secret: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    return jwt.encode({"sub": username, "type": "access", "exp": exp}, secret, algorithm="HS256")

def get_refresh_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    if payload.get("type") != "refresh":
        raise HTTPException(401, detail="invalid token")
    return User(username=payload["sub"])
```

The client — not the server — decides when to call `/refresh`; the server never auto-refreshes.

---

## API Key Auth — Header + Query (D106)

**What it does:** authenticates machine clients via a static key, accepted from either a header or a query param.

```python
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query  = APIKeyQuery(name="api_key", auto_error=False)

def get_api_key(
    header_key: str | None = Depends(api_key_header),
    query_key:  str | None = Depends(api_key_query),
) -> str:
    key = header_key or query_key
    if key not in VALID_KEYS:
        raise HTTPException(403, detail="invalid api key")
    return key
```

Set `auto_error=False` on both so neither raises before your combined check runs.

---

## HTTPBasic Auth (D107)

**What it does:** extracts username+password from the Authorization: Basic header.

```python
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    stored = USERS.get(credentials.username, "")
    if not secrets.compare_digest(credentials.password, stored):
        raise HTTPException(401, detail="invalid credentials")
    return credentials.username
```

Always use `secrets.compare_digest` instead of `==` for password comparison — timing-safe.

---

## Scopes — Fine-Grained Permissions (D108)

**What it does:** gates endpoints by individual permission strings instead of coarse roles.

```python
class User(BaseModel):
    username: str
    scopes: list[str]

def require_scope(scope: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if scope not in user.scopes:
            raise HTTPException(403, detail="insufficient scope")
        return user
    return checker
```

A user can hold any combination of scopes — finer-grained than a single role string.

---

## Auth Middleware — Global vs Per-Route (D109)

**What it does:** enforces auth on every request before any route runs, with exceptions for public paths.

```python
PUBLIC_PATHS = {"/health", "/token"}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    if request.headers.get("X-API-Key", "") not in VALID_KEYS:
        return JSONResponse({"detail": "not authenticated"}, status_code=401)
    return await call_next(request)
```

Use `JSONResponse` to short-circuit from middleware — `HTTPException` raised here isn't caught by FastAPI's handlers, since middleware runs outside that layer.

---

## Combining Role + Scope (D110)

**What it does:** stacks both checks in a single dependency for endpoints that need a specific job function AND a specific permission.

```python
def require_role_and_scope(role: str, scope: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(403, detail="forbidden")
        if scope not in user.scopes:
            raise HTTPException(403, detail="insufficient scope")
        return user
    return checker
```

Check role before scope so the 403 detail reflects the first failing condition, matching client expectations about which check ran first.

---
