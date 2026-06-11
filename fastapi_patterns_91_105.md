# FastAPI Patterns — Drills 91–105

---

## Route Registration
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

## Path Parameters
**What it does:** extracts a segment from the URL and coerces its type.
```python
@app.get("/items/{item_id}")
def get_item(item_id: int): ...
# GET /items/5  →  item_id=5 (int, not str)
# GET /items/abc  →  422 automatically
```
Parameter name in the decorator must match the function argument name exactly.

---

## Query Parameters
**What it does:** reads ?key=value from the URL, coerces type, supports Optional.
```python
from typing import Optional

@app.get("/items")
def list_items(active: Optional[bool] = None): ...
# GET /items?active=true  →  active=True (bool)
# GET /items              →  active=None
```
Any function argument not in the path is treated as a query param.

---

## Request Body (Pydantic model)
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

## Response Model
**What it does:** validates and filters the return value before sending to client.
```python
class ItemOut(BaseModel):
    id: int
    name: str
    # no internal_notes field

@app.post("/items", response_model=ItemOut)
def create_item(body: ItemIn):
    return {**body.model_dump(), "id": 1, "internal_notes": "fragile"}
    # internal_notes is stripped — client never sees it
```
Extra keys stripped. Missing required fields → 500 at runtime. Return dict or model instance — both work.

---

## HTTPException
**What it does:** aborts the request and sends an error response with a status code.
```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="item not found")
# Response: 404  {"detail": "item not found"}

raise HTTPException(status_code=403, detail="forbidden")
raise HTTPException(status_code=409, detail="already exists")
raise HTTPException(status_code=422, detail="invalid input")
```
Replaces the custom AppError hierarchy from pure Python. FastAPI catches it automatically.

---

## Depends() — single dependency
**What it does:** calls a function before the endpoint, injects its return value.
```python
def get_zone(zone_id: int) -> str:
    if zone_id not in ZONES:
        raise HTTPException(status_code=404, detail="zone not found")
    return ZONES[zone_id]

@app.get("/tanks")
def list_tanks(zone: str = Depends(get_zone)):
    ...
# zone_id comes from the query string — FastAPI resolves it automatically
```
The dependency function's parameters are resolved from the request just like an endpoint's.

---

## Depends() — chained
**What it does:** one dependency takes the result of another as its input.
```python
def get_vessel(vessel_id: int) -> dict:
    ...
    return vessel

def get_manifest(vessel: dict = Depends(get_vessel)) -> dict:
    ...
    return manifest

@app.get("/cargo")
def get_cargo(manifest: dict = Depends(get_manifest)):
    return manifest
# endpoint only sees the final result — chain resolved automatically
```
Declare Depends() inside the dependent function's signature, not in the endpoint.

---

## BackgroundTasks
**What it does:** runs a function after the response is sent to the client.
```python
from fastapi import BackgroundTasks

def send_email(user_id: int):   # plain function, not async
    ...

@app.post("/apply")
def apply(bg: BackgroundTasks):
    bg.add_task(send_email, user_id)
    return {"status": "received"}   # returned immediately; email sent after
```
Inject BackgroundTasks as a parameter. Call bg.add_task(fn, *args). Response goes first, task runs after.

---

## Lifespan (startup / shutdown)
**What it does:** runs code before first request (startup) and after last request (shutdown).
```python
from contextlib import asynccontextmanager

APP_STATE = {}

@asynccontextmanager
async def lifespan(app: FastAPI):   # must accept app argument
    APP_STATE["db"] = connect()     # startup
    try:
        yield
    finally:
        APP_STATE.clear()           # shutdown

app = FastAPI(lifespan=lifespan)
```
Same pattern as pure Python D67 — before yield = startup, finally after yield = shutdown.
TestClient used as `with TestClient(app) as client:` triggers both lifecycle events.

---

## OAuth2PasswordBearer
**What it does:** extracts the raw token string from the Authorization: Bearer <token> header.
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # token is the raw string — validation is your job
    ...
```
Only extracts — never validates. Missing header → 401 automatically.

---

## JWT encode / decode
**What it does:** creates signed tokens and verifies them.
```python
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta

SECRET_KEY = "my-secret"
ALGORITHM = "HS256"

# encode
token = jwt.encode(
    {"sub": "user-123", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
    SECRET_KEY,
    ALGORITHM,
)

# decode
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
except JWTError:
    raise HTTPException(status_code=401, detail="Invalid or expired token")
```
exp claim is checked automatically on decode. Bad signature, expired, or malformed → JWTError.

---

## JWT + User model dependency
**What it does:** decodes token, builds a typed User object, injects it into routes.
```python
class User(BaseModel):
    username: str
    role: str

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return User(username=payload["sub"], role=payload["role"])

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}
```

---

## Role-based access (dependency factory)
**What it does:** returns a dependency that checks the user's role before the route runs.
```python
def require_role(required_role: str):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return dependency

@app.get("/admin")
def admin_route(user: User = Depends(require_role("admin"))):
    ...
```
Factory returns a different dependency per role. 403 = authenticated but not authorized.

---

## Refresh token pattern
**What it does:** issues short-lived access tokens and long-lived refresh tokens separately.
```python
# access token — short-lived, type="access"
def make_access_token(username: str) -> str:
    return jwt.encode(
        {"sub": username, "type": "access",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
        SECRET_KEY, ALGORITHM,
    )

# refresh token — long-lived, type="refresh"
def make_refresh_token(username: str) -> str:
    return jwt.encode(
        {"sub": username, "type": "refresh",
         "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        SECRET_KEY, ALGORITHM,
    )

# protected route: reject non-access tokens
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload["type"] != "access":
        raise HTTPException(status_code=401, detail="Not an access token")
    return payload["sub"]

# refresh endpoint: accept only refresh tokens, issue new access token
class RefreshRequest(BaseModel):
    refresh_token: str   # POST body must be a Pydantic model, not a bare str

@app.post("/refresh")
def refresh(body: RefreshRequest):
    payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload["type"] != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
    return {"access_token": make_access_token(payload["sub"]), "token_type": "bearer"}
```
POST body string must be wrapped in a Pydantic model — bare str would be a query param, not body.

---

## TestClient usage
**What it does:** lets you test FastAPI routes without running a real server.
```python
from fastapi.testclient import TestClient

client = TestClient(app)                        # basic usage
client = TestClient(app, raise_server_exceptions=False)  # catch HTTP errors as responses

# with lifespan:
with TestClient(app) as client:   # triggers startup on enter, shutdown on exit
    r = client.get("/path")

# assert pattern:
assert r.status_code == 200
assert r.json() == {"key": "value"}
assert r.json()["detail"] == "not found"
```
