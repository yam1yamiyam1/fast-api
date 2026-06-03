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

### Dynamic Dispatch Deep Dive (61–70) ✅

- dispatch returns values — test the return path ✅ drill 61
- path params — `/users/{id}` pattern matching with `re` ✅ drill 62
- GET vs POST same path — method-aware routing, 404 vs 405 ✅ drill 63
- before/after hook points on dispatch ✅ drill 64
- global error handler — `ERROR_HANDLERS` registry ✅ drill 65
- prefix groups — `Router` class with `.route()` method ✅ drill 66
- async context manager — lifespan pattern ✅ drill 67
- dependency graph — one dep calls another ✅ drill 68
- response model — validate output with Pydantic ✅ drill 69
- final boss — mini HTTP router, all above combined ✅ drill 70

### First Mixes (71–80) ✅

- Pydantic + OOP decorator ✅ drill 71
- async rate limiter with `asyncio.sleep`✅ drill 72
- class-based router — registry + OOP + dispatch ✅ drill 73
- nested Pydantic models in dispatch ✅ drill 74
- parallel dependency resolution with `gather` ✅ drill 75
- custom exception hierarchy — base → domain → HTTP-mappable ✅ drill 76
- `contextvars` — request-scoped state without passing everywhere ✅ drill 77
- async queue — background task pattern ✅ drill 78
- semaphore inside decorator — concurrency limiter ✅ drill 79
- final boss — async class router, parallel deps, nested Pydantic, custom exceptions ✅ drill 80

---
