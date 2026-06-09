# Gap Analysis — After Project 2 (Stock Exchange)

## Confirmed solid
- Pydantic models, Field constraints, Literal, nested models
- Registry pattern, RouteEntry dataclass, register()
- _match logic, path regex, 404 vs 405 separation
- _resolve_deps, sync/async detection via inspect.iscoroutinefunction
- asyncio.Semaphore, asyncio.create_task, asyncio.to_thread
- Middleware chain, context dict, add_middleware()
- Lifespan __aenter__ / __aexit__ pattern (after explanation)
- Handler kwargs: params + body + deps merged correctly
- Response model validation in dispatch

## Confirmed weak — drill these in 81–100
1. Mutable default arguments — used {} in signatures and dataclass fields twice
2. Missing self on methods — forgot it on _match, _resolve_deps, path_to_regex
3. Raises inside loops — put 404/405 raises inside the for loop on first attempt
4. 404 vs 405 logic swapped — got the condition backwards on first attempt
5. dispatch pipeline ordering — called handler only inside request_model block
6. Unpacking confusion — wrote {**entry} instead of building context dict manually
7. String vs int params — forgot regex always returns strings, needed cast reminder
8. async with for lifespan — tried to split enter/exit with async with instead of __aenter__/__aexit__
9. : None vs = None — wrote annotation instead of assignment in __init__ twice

## Drill 81–100 priorities
- Multi-concept combos (3-4 patterns per drill)
- Async context managers under different scenarios
- Dispatch pipeline variants — reordering, short-circuiting
- Registry patterns with edge cases
- Mutable defaults in varied contexts until automatic
- Self discipline on class methods
