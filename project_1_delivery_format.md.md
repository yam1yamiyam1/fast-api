# Project Delivery Format

The student has completed drills 1–80 in pure Python — no FastAPI yet.
The synthesis project is a pure Python project that mimics how FastAPI
works internally — same concepts, built from scratch. Do not use FastAPI,
uvicorn, or any web framework. The student is building the toy version of
FastAPI using only the Python standard library and Pydantic.

## The mental model

FastAPI is just the concepts from drills 1–80 wired together:

- Router with registered routes = drill 66, 73
- Path params + method routing = drill 62, 63
- Middleware / before hooks = drill 42, 64
- Dependency injection = drill 43, 49, 68, 75
- Pydantic request + response models = drills 1–10, 69, 74
- Error handlers = drill 65, 76
- Lifespan (startup/shutdown) = drill 67
- Background tasks = drill 78
- Concurrency limiting = drill 79
- Request-scoped state = drill 77

The project wires all of these into one coherent system for the first time.
Each piece the student already knows. The challenge is integrating them.

## What the student has built mental models for

From drills 1–50 (verified from actual code):

- Pydantic models, validation, Field constraints, nested models
- async/await, asyncio.gather, asyncio.sleep
- Wrapper decorators, registry decorators, decorator factories, @wraps
- Registry with metadata (storing handler + checks/middleware/dependencies)
- Dispatch with staged pipeline: validate → middleware → dependencies → handler
- Sync and async check/hook functions
- ValueError and ValidationError handling in dispatch

From drills 51–80 (verified from roadmap):

- OOP decorators — args[0] is self, reading/mutating self, try/finally
- sync + async branch via inspect.iscoroutinefunction
- Class-level registry with unbound functions
- Dynamic dispatch — path matching with re, method routing, 404 vs 405
- Before/after hooks, global error handlers, Router class with prefix
- Lifespan pattern with asynccontextmanager
- Dependency graph — one dep calls another
- Response model validation
- Custom exception hierarchy — base → domain → HTTP-mappable
- ContextVar — request-scoped state
- Async queue + background worker (asyncio.Queue)
- Semaphore inside decorator (asyncio.Semaphore)
- Rate limiter with asyncio.sleep
- Class-based router with its own registry and dispatch

## What to give

1. **SPEC.md** — requirements only. What the system does, what each
   component must handle, error behavior. No implementation hints,
   no code snippets. Written as a scenario, same tone as drill comments.

2. **tests/test\_\*.py** — pre-written pytest tests using plain async pytest
   (pytest-asyncio). No httpx, no FastAPI test client — pure Python.
   All tests fail at the start. Student's implementation makes them pass.

3. **Folder structure** — suggest the layout, every file is empty.
   Student populates them all.

## Delivery rules

- One stage at a time. Stage 1: core router + models. Stage 2: middleware
  - dependencies. Stage 3: lifespan + background tasks + concurrency.
- No code in the spec. No hints unless the student explicitly asks.
- Tests are the source of truth. If a test passes, the requirement is met.
- Same assert discipline as drills — student knows exactly what green looks like.
- Pick a scenario from the AVAILABLE list below only.

## What not to do

- No FastAPI, no uvicorn, no httpx, no external frameworks
- No starter code
- No "here's how you might approach this"
- Do not introduce any concept outside drills 1–80
