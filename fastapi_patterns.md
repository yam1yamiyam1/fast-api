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
