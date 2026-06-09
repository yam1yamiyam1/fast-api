# Project 2 — Stage 3 Spec
## Stock Exchange — Lifespan + Background Tasks + Concurrency

---

## What gets added

Lifespan management, a background task queue, and a concurrency limiter
on the handler call.

---

## Lifespan behavior

- The router gains set_lifespan() which accepts an async context manager
  function decorated with @asynccontextmanager.
- start() enters the lifespan context. Anything before the yield runs on startup.
- stop() exits the lifespan context. Anything after the yield runs on shutdown.
- The lifespan populates APP_STATE on startup and updates it on shutdown.
- If no lifespan is set, start() and stop() do nothing.

---

## Background tasks behavior

- dispatch accepts an optional background_tasks list of callables.
- Each callable is scheduled with asyncio.create_task after the handler returns.
- Background tasks are fire-and-forget — dispatch does not await them.
- Sync callables are wrapped in asyncio.to_thread before create_task.
- Async callables get create_task directly.

---

## Concurrency limiter behavior

- The router holds an asyncio.Semaphore initialized in __init__.
- The semaphore limit is configurable via max_concurrency arg, default 10.
- The semaphore wraps only the handler call — not middleware, not deps,
  not response validation.

---

## APP_STATE

- A module-level dict in main.py, shared across the whole app.
- The lifespan sets APP_STATE["status"] = "open" on startup.
- The lifespan sets APP_STATE["status"] = "closed" on shutdown.
- Handlers can read from it directly.

---

## Dispatch pipeline after Stage 3

lifespan start (once, at app startup)
  → match route
  → run middleware
  → resolve deps
  → validate body
  → semaphore acquire → call handler → semaphore release
  → schedule background tasks
  → validate response
  → return result
lifespan stop (once, at app shutdown)
