# Project 2 — Stage 2 Interface Sheet
## Stock Exchange — Middleware + Dependencies

Additions and changes to router.py only.
models.py, exceptions.py, and main.py are unchanged.

---

## router.py — additions and changes

**RouteEntry.deps** — dict, str keys, callable values
- Purpose: holds the dep callables for this route; default empty dict

**Router.middleware_list** — list
- Purpose: holds all registered middleware callables in order
- Initialized in __init__ as an empty list

**Router.add_middleware** — method
- Purpose: appends a callable to middleware_list
- args: callable (sync or async)
- returns: nothing

**Router.register** — updated signature
- Purpose: same as before, now accepts an optional deps dict
- new arg: deps — dict mapping str to callable, default empty dict
- RouteEntry must also store deps

**Router._run_middleware** — async method
- Purpose: iterates middleware_list, detects sync vs async via
  inspect.iscoroutinefunction, calls each with the context dict
- args: context dict
- returns: nothing

**Router._resolve_deps** — async method
- Purpose: iterates the route's deps dict, detects sync vs async via
  inspect.iscoroutinefunction, calls each callable with no arguments,
  collects results into a dict keyed by name
- args: deps dict
- returns: dict of resolved dep values

**Router.dispatch** — updated
- Purpose: same pipeline as Stage 1, now runs _run_middleware before body
  validation, and merges _resolve_deps results into kwargs before
  calling the handler
