# drill_82.py
import asyncio  # noqa: F401
import inspect  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, Callable  # noqa: F401


async def handler_runner(fn: Callable, **kwargs):
    if inspect.iscoroutinefunction(fn):
        return await fn(**kwargs)
    else:
        return fn(**kwargs)


async def run_drill_82():
    """
    Scenario: Courthouse
    A courthouse routing system handles legal case requests.
    Judges (handlers) are registered by case type and courtroom number.
    The dispatcher resolves a dependency, runs middleware, then calls the handler.

    Requirements:
    - RouteEntry dataclass holds: case_type (str), courtroom (int), handler (Callable).
      No mutable defaults anywhere.
    - CaseRegistry class:
        - Internal routes list, initialized safely.
        - register(case_type, courtroom, handler) — adds a RouteEntry.
        - find(case_type, courtroom) — searches routes:
            - Returns the matching RouteEntry if found.
            - If case_type exists but courtroom doesn't match any entry: raises ValueError("wrong courtroom").
            - If case_type not found at all: raises ValueError("no handler").
            - Raises must not fire before the full loop completes its search.
        - dispatch(case_type, courtroom, payload, deps) — pipeline:
            1. Resolve dependency: call deps["get_judge"]() — sync or async, handle both.
            2. Run middleware: call deps["log"](case_type) — always sync.
            3. Find the route entry via find().
            4. Call the handler with (payload=payload, judge=resolved_judge).
               Handler may be sync or async — handle both.
            5. Return handler result.
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class RouteEntry:
        case_type: str
        courtroom: int
        handler: Callable

    class CaseRegistry:
        def __init__(self):
            self.routes = []

        def register(self, case_type: str, courtroom: int, handler: Callable):
            self.routes.append(RouteEntry(case_type, courtroom, handler))

        def find(self, case_type: str, courtroom: int):
            case_type_found = False
            for entry in self.routes:
                if entry.case_type == case_type:
                    case_type_found = True
                    if entry.courtroom == courtroom:
                        return entry
            if case_type_found:
                raise ValueError("wrong courtroom")
            else:
                raise ValueError("no handler")

        async def dispatch(
            self, case_type: str, courtroom: int, payload: str, deps: dict
        ):
            res_judge = await handler_runner(deps["get_judge"])
            deps["log"](case_type)
            entry = self.find(case_type, courtroom)
            result = await handler_runner(
                entry.handler, payload=payload, judge=res_judge
            )
            return result

    # Tests
    call_log = []

    def sync_get_judge():
        return "Judge Smith"

    async def async_get_judge():
        return "Judge Patel"

    def log_middleware(case_type):
        call_log.append(f"log:{case_type}")

    def sync_handler(payload, judge):
        return f"{judge} ruled on {payload}"

    async def async_handler(payload, judge):
        return f"{judge} async-ruled on {payload}"

    registry = CaseRegistry()
    registry.register("civil", 1, sync_handler)
    registry.register("criminal", 2, async_handler)

    print("Test 1: sync dep + sync handler")
    result = await registry.dispatch(
        "civil",
        1,
        "contract dispute",
        {"get_judge": sync_get_judge, "log": log_middleware},
    )
    assert result == "Judge Smith ruled on contract dispute", result
    print(f"  result: {result}")
    print("  PASS")

    print("Test 2: async dep + async handler")
    result = await registry.dispatch(
        "criminal",
        2,
        "theft case",
        {"get_judge": async_get_judge, "log": log_middleware},
    )
    assert result == "Judge Patel async-ruled on theft case", result
    print(f"  result: {result}")
    print("  PASS")

    print("Test 3: middleware ran in order")
    assert call_log == ["log:civil", "log:criminal"], call_log
    print(f"  log: {call_log}")
    print("  PASS")

    print("Test 4: wrong courtroom raises ValueError")
    try:
        await registry.dispatch(
            "civil",
            9,
            "wrong room",
            {"get_judge": sync_get_judge, "log": log_middleware},
        )
        assert False, "should have raised"
    except ValueError as e:
        assert str(e) == "wrong courtroom", str(e)
        print(f"  error: {e}")
        print("  PASS")

    print("Test 5: unknown case_type raises ValueError")
    try:
        await registry.dispatch(
            "family", 1, "custody", {"get_judge": sync_get_judge, "log": log_middleware}
        )
        assert False, "should have raised"
    except ValueError as e:
        assert str(e) == "no handler", str(e)
        print(f"  error: {e}")
        print("  PASS")

    print("Test 6: no mutable default in RouteEntry")
    import dataclasses

    for f in dataclasses.fields(RouteEntry):
        assert not isinstance(f.default, (list, dict, set)), (
            f"mutable default on field: {f.name}"
        )
    print("  PASS")

    print("Test 7: two registries are independent")
    r2 = CaseRegistry()
    r2.register("tax", 3, sync_handler)
    assert len(registry.routes) == 2
    assert len(r2.routes) == 1
    print(f"  registry routes: {len(registry.routes)}, r2 routes: {len(r2.routes)}")
    print("  PASS")


asyncio.run(run_drill_82())


# Expected output:
# Test 1: sync dep + sync handler
#   result: Judge Smith ruled on contract dispute
#   PASS
# Test 2: async dep + async handler
#   result: Judge Patel async-ruled on theft case
#   PASS
# Test 3: middleware ran in order
#   log: ['log:civil', 'log:criminal']
#   PASS
# Test 4: wrong courtroom raises ValueError
#   error: wrong courtroom
#   PASS
# Test 5: unknown case_type raises ValueError
#   error: no handler
#   PASS
# Test 6: no mutable default in RouteEntry
#   PASS
# Test 7: two registries are independent
#   registry routes: 2, r2 routes: 1
#   PASS
