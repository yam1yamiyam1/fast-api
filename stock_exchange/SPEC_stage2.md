# Project 2 — Stage 2 Spec
## Stock Exchange — Middleware + Dependencies

---

## What gets added

A middleware list that runs before the handler, and a dependency injection
system that resolves deps and injects them as kwargs into the handler.

---

## Middleware behavior

- The router gains an add_middleware() method that appends a callable to a middleware list.
- Middleware callables are either sync or async — the router detects which via
  inspect.iscoroutinefunction and calls them accordingly.
- Each middleware receives the request context dict:
  {"method": method, "path": path, "body": body}
  It may mutate it or just observe it.
- Middleware runs in registration order, before body validation and before the handler.
- If middleware raises an exception, it propagates — no special catching.

---

## Dependency injection behavior

- Each route can declare a deps dict when registered: keys are kwarg names,
  values are callables.
- Before the handler is called, each dep callable is called with no arguments
  and its return value is injected into kwargs under its key.
- Deps are async or sync — same detection via inspect.iscoroutinefunction.
- Deps run after middleware, before the handler.
- If a dep raises, it propagates.

---

## Dispatch pipeline after Stage 2

match route → run middleware → resolve deps → validate body → call handler → validate response
