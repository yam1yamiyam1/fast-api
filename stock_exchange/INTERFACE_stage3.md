# Project 2 — Stage 3 Interface Sheet
## Stock Exchange — Lifespan + Background Tasks + Concurrency

Additions and changes only. models.py and exceptions.py unchanged.

---

## main.py — additions

APP_STATE — dict
  Purpose: shared state dict populated by lifespan, readable by handlers
  Initial value: empty dict

lifespan — async generator function, decorated with @asynccontextmanager
  Purpose: sets APP_STATE["status"] = "open" before yield,
    APP_STATE["status"] = "closed" after yield
  args: none
  yields: nothing

router.set_lifespan(lifespan) — call this after defining lifespan
  Purpose: registers the lifespan with the router

---

## router.py — additions and changes

Router.__init__ — updated
  Purpose: same as before, now also initializes semaphore and lifespan fields
  new arg: max_concurrency int, default 10
  semaphore: asyncio.Semaphore(max_concurrency)
  _lifespan_fn: None
  _lifespan_ctx: None

Router.set_lifespan — method
  Purpose: stores the lifespan callable on the router
  args: async context manager function
  returns: nothing

Router.start — async method
  Purpose: if _lifespan_fn is set, calls it and enters the context manager,
    stores the context object in _lifespan_ctx
  returns: nothing

Router.stop — async method
  Purpose: if _lifespan_ctx is set, exits the context manager
  returns: nothing

Router._schedule_tasks — async method
  Purpose: iterates background_tasks list, wraps sync callables in
    asyncio.to_thread before scheduling, async callables scheduled directly,
    all scheduled via asyncio.create_task
  args: list of callables
  returns: nothing

Router.dispatch — updated signature
  Purpose: same pipeline as Stage 2, now wraps handler call with semaphore
    and schedules background tasks after handler returns
  new arg: background_tasks — list of callables or None, default None
  semaphore scope: wraps only the handler call
  background tasks: scheduled after handler returns, before response validation
