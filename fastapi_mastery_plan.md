# FastAPI Mastery Plan — Job-Focused

## Source of Truth

This file is the single source of truth. Update after every session.

---

## Strategy

- Drills build mental models. Projects get you hired.
- One new concept per drill. Blank page. No hints.
- If you can't finish in 20 min, prerequisite is shaky — repeat it.
- **Apply after Project 1 ships — not after drill 200.**
- Track your times. Over 25 min = go back one drill.
- From drill 67 onwards — tests use `assert`, not print-and-eyeball.

---

## Progress Tracker

```
Current Drill:     68 (in progress)
Current Phase:     Phase 1 — Python Internals
Current Block:     Dynamic Dispatch Deep Dive (61–70)
Next Mechanic:     Dependency graph — one dep calls another
Completed Blocks:  OOP Decorators (51–60), Dispatch returns values (61),
                   Path pattern matching (62), Multi-verb routing (63),
                   Before/after hooks (64), Global error handler (65)
Project 1:         Not started — begins after drill 80
```

---

## Revised Roadmap (Job-Focused)

| Phase              | What                                                        | When                    |
| ------------------ | ----------------------------------------------------------- | ----------------------- |
| Drills 51–80       | OOP decorators + dynamic dispatch + first mixes             | Now                     |
| **Project 1**      | FastAPI CRUD API (users, posts, JWT auth) deployed + GitHub | After drill 80          |
| **Apply for jobs** | Don't wait for drill 200                                    | After Project 1 ships   |
| Drills 81–100      | Fill gaps exposed by Project 1                              | Parallel with project   |
| Drills 101–130     | Real FastAPI (Depends, auth, DB)                            | After Project 1 ships   |
| **Project 2**      | Production API, full test suite, Docker, deployed           | After drill 130         |
| Drills 131–160     | Testing, production hardening, infra                        | Parallel with project 2 |
| Portfolio          | 2 projects on GitHub, README, live URL                      | Before applying broadly |

---

## Drill Map

| Range   | Topic                                       | Status         |
| ------- | ------------------------------------------- | -------------- |
| 01–10   | Pydantic fundamentals                       | ✅             |
| 11–20   | Async/Await fundamentals                    | ✅             |
| 21–30   | Wrapper decorators                          | ✅             |
| 31–40   | Registry decorators                         | ✅             |
| 41–50   | Toy dispatch + toy middleware + toy DI      | ✅             |
| 51–60   | OOP decorators                              | ✅             |
| 61–70   | Dynamic dispatch deep dive                  | 🔄 in progress |
| 71–80   | First mixes (2 concepts)                    | ⬜             |
| 81–100  | Harder combos — gap filling after Project 1 | ⬜             |
| 101–130 | Real FastAPI (core + auth + DB)             | ⬜             |
| 131–160 | Production hardening (testing + infra)      | ⬜             |
| 161–199 | Speed drills + synthesis                    | ⬜             |
| 200     | Final boss                                  | ⬜             |

---

## Phase 1: Python Internals (Drills 51–80)

### OOP Decorators (51–60) ✅

- `args[0]` is `self`
- read `self.state` inside decorator
- mutate `self.state` safely with `try/finally`
- same decorator on multiple methods with different rules — DRY factory pattern
- `@wraps` — assert `__name__`, `__doc__`, `__wrapped__`
- sync + async branch via `inspect.iscoroutinefunction`
- log calls to `self.history` — reads and mutates instance state
- class-level registry — store unbound functions, bind via `args[0]`
- dispatch inside class + Pydantic + domain exception (`InvalidPayloadError`)
- final boss — async class, registry, dispatch, Pydantic, `@wraps`, `try/finally`, per-instance state

### Dynamic Dispatch Deep Dive (61–70) 🔄

- dispatch returns values — test the return path ✅ drill 61
- path params — `/users/{id}` pattern matching with `re` ✅ drill 62
- GET vs POST same path — method-aware routing, 404 vs 405 ✅ drill 63
- before/after hook points on dispatch ✅ drill 64
- global error handler — `ERROR_HANDLERS` registry ✅ drill 65
- prefix groups — `Router` class with `.route()` method ✅ drill 66
- async context manager — lifespan pattern ✅ drill 67
- dependency graph — one dep calls another
- response model — validate output with Pydantic
- final boss — mini HTTP router, all above combined

### First Mixes (71–80) ⬜

- Pydantic + OOP decorator
- async rate limiter with `asyncio.sleep`
- class-based router — registry + OOP + dispatch
- nested Pydantic models in dispatch
- parallel dependency resolution with `gather`
- custom exception hierarchy — base → domain → HTTP-mappable
- `contextvars` — request-scoped state without passing everywhere
- async queue — background task pattern
- semaphore inside decorator — concurrency limiter
- final boss — async class router, parallel deps, nested Pydantic, custom exceptions

---

## Phase 2: Real FastAPI (Drills 101–130)

> **Start Project 1 at drill 80, start applying after it ships**

### Core FastAPI (101–110)

- `@app.get`, `uvicorn.run`, test with `httpx`
- path params + query params + type coercion
- request body with Pydantic model
- `response_model=` — validate output
- `HTTPException` + status codes
- `Depends()` — single injected dependency
- `Depends()` chained — one dep calls another
- `Depends()` with class — stateful dependency
- `BackgroundTasks` — fire and forget
- lifespan — startup/shutdown with `asynccontextmanager`

### Auth (111–120)

- `OAuth2PasswordBearer` — extract token from header
- JWT decode — verify signature and expiry with `python-jose`
- current user dependency — token → User object
- role-based access — admin vs regular user
- refresh token pattern
- API key auth — header + query param
- `HTTPBasic` auth
- scopes — fine-grained permissions
- auth middleware — global vs per-route
- final boss — JWT + roles + scopes in one system

### Database (121–130)

- SQLAlchemy async setup — engine, session factory
- first table + Alembic migration
- CRUD — create, read, update, delete
- `get_db()` session as a dependency
- relationships — one-to-many, eager vs lazy load
- transactions — commit, rollback
- repository pattern — separate DB logic from routes
- pagination — limit/offset + cursor-based
- filters + search
- final boss — full CRUD API with auth + DB

---

## Phase 3: Production (Drills 131–160)

> **Start Project 2 at drill 131**

### Testing (131–140)

- `pytest` + `httpx.AsyncClient` — test FastAPI routes
- fixtures — test DB, test user, test token
- dependency override — swap real DB for test DB
- factory pattern for test data
- parametrized tests — one test, many cases
- mock external services with `respx`
- test auth flows end-to-end
- enforce 90%+ coverage
- load test with `locust`
- final boss — full test suite

### Production Patterns (141–155)

- `pydantic-settings` — env vars, `.env` files
- structured logging with `structlog`
- request ID middleware — trace across logs
- rate limiting — token bucket with Redis
- Redis cache layer
- background workers with `arq`
- WebSockets — real-time updates
- file upload — stream to S3
- health check + readiness endpoint
- graceful shutdown
- CORS — production config
- exception handler hierarchy — domain → HTTP
- OpenAPI customization
- API versioning — `/v1/` prefix
- final boss — production-ready API

### Infrastructure (156–160)

- Docker — containerize the app
- Docker Compose — app + DB + Redis
- GitHub Actions — CI on push
- deploy to Railway / Render / Fly.io
- final boss — full deploy pipeline

---

## Projects (non-negotiable)

### Project 1 — after drill 80

- FastAPI CRUD API
- users, posts, JWT auth
- deployed, live URL, GitHub README
- **start applying for jobs here**

### Project 2 — after drill 130

- your choice of domain
- full test suite, Docker, deployed
- something you'd show in an interview without hesitation

---

## Scenario Bank

**Used (do not reuse):**
Gym, Online Checkout, Concert Venue, Hospital, Airport, Bank Account,
Gym Turnstile, Operating Room, Restaurant Kitchen, Security System,
Smart Home, Command Center, Mission Control, Space Station, Nuclear Plant,
Vending Machine, City Directory, Blog API, Audit Logger, Crash-Proof API

**Available:**
Hotel, University, Courthouse, Shipping Port, Train Station, Pharmacy,
Stock Exchange, Power Grid, Police Station, Embassy, Library,
Immigration Checkpoint, Data Center, Fire Station, Museum, Casino,
Aquarium, Seaport, City Hall, Unemployment Office, Customs Office,
Blood Bank, Veterinary Clinic, Broadcast Studio, Satellite Control Room,
Weather Station, Airport Control Tower, Submarine, Telescope Array

---

## Drill Format Rules

- All logic inside `run_drill_N()` — no module-level state
- Tests labeled `Test 1:`, `Test 2:` etc.
- All imports have `# noqa: F401`
- Expected output block always present and accurate
- From drill 67 onwards: tests use `assert` not just print
- One new concept per drill, everything else is revision
- Never reuse a scenario from the Used list

---

## The Rules

- One new concept per drill
- Blank page, no hints
- Can't finish in 20 min → prerequisite is shaky, repeat it
- Two projects on GitHub before applying — not drills, real APIs with live URLs
- **Apply after Project 1. Not after drill 200.**

---

## Concept Reference Notes

### `asynccontextmanager`, `async with`, `yield` (introduced drill 67)

**What it solves:** run setup, then work, then guaranteed teardown — even if work crashes.

**Shape:**

```python
@asynccontextmanager
async def lifespan():
    # STARTUP — runs on enter
    db = await connect()
    try:
        yield  # pause here, hand control to the async with block
    finally:
        # SHUTDOWN — runs on exit, always, even on crash
        await db.disconnect()

async with lifespan():
    # you are inside the yielded block here
    await do_work()
```

**Rules:**

- Everything before `yield` = startup
- Everything after `yield` = shutdown
- Always wrap `yield` in `try/finally` to guarantee shutdown
- `async with` = `with` but for async context managers
- FastAPI uses this via `lifespan=` parameter on the app

**Toy vs real FastAPI:**

- Toy: `APP_STATE = {}` dict shared with handlers
- Real: `app.state.db = ...` — same idea, FastAPI manages the state object
