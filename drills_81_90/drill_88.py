import asyncio  # noqa: F401
import inspect  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, Callable, Optional  # noqa: F401


def run_drill_88():
    """
    SCENARIO: Library Borrowing Desk
    =================================
    The library desk resolves services before calling a handler — a logger,
    a membership checker, and so on. Each service is a dependency: a callable
    that may be sync or async. The desk resolves all deps first, merges them
    with request params, then calls the handler with the combined kwargs.

    NEW CONCEPT: Dependency injection with sync/async detection
    -----------------------------------------------------------
    A dependency is any callable. Before calling the handler, resolve each
    dep by calling it (awaiting if async, calling directly if sync).
    Use inspect.iscoroutinefunction(fn) to detect async deps.
    Pattern:
        resolved = {}
        for name, dep in deps.items():
            if inspect.iscoroutinefunction(dep):
                resolved[name] = await dep()
            else:
                resolved[name] = dep()
    Then merge: kwargs = {**params, **resolved} and call handler(**kwargs).
    Rule: params and deps are merged manually — never pass the dicts as
    positional arguments.

    REQUIREMENTS
    ============

    1. BorrowRequest
       - A dataclass representing a borrowing request arriving at the desk.
       - member_id: str — the library card number of the person borrowing.
       - book_id: str — the catalogue identifier of the requested book.
       - params: dict — additional query parameters attached to the request;
         must use field(default_factory=dict), never a mutable default.

    2. LibraryDesk
       - A class representing the borrowing desk.
       - __init__(self):
           - self.deps: dict — the map of dependency name (str) to callable;
             initialised as an empty dict using = {}, never a type annotation
             alone.
       - def add_dep(self, name: str, fn: Callable) -> None
           - name: str — the key under which this dependency will be injected.
           - fn: Callable — the dependency callable (sync or async).
           - Stores fn under name in self.deps.
       - async def resolve_deps(self) -> dict
           - Iterates self.deps. For each entry, if the callable is async
             (detected via inspect.iscoroutinefunction), awaits it; otherwise
             calls it directly. Returns a dict of name → resolved value.
             Never mutates self.deps.
       - async def handle(self, request: BorrowRequest, handler: Callable) -> Any
           - request: BorrowRequest — the incoming borrowing request.
           - handler: Callable — the desk function to call with merged kwargs.
           - Calls resolve_deps() to get resolved dep values, then builds
             kwargs by merging request.params and the resolved deps manually
             (no unpacking of the BorrowRequest object itself), then calls
             handler(**kwargs) — awaiting if async, calling directly if sync.
             Returns the handler's result.

    3. Dependency functions (plain functions, not methods)

       def get_logger() -> str
           - Returns "logger:active".

       async def get_membership(member_id: str = "") -> str  ← default="" so callable with no args
           - Returns "membership:valid".

    4. Handler functions (plain functions, not methods)

       def borrow_handler(logger: str, membership: str) -> str
           - logger: str — the resolved logger value injected as a kwarg.
           - membership: str — the resolved membership value injected as a kwarg.
           - Returns "Borrowed — <logger> — <membership>".

       async def async_borrow_handler(logger: str, membership: str) -> str
           - logger: str — the resolved logger value injected as a kwarg.
           - membership: str — the resolved membership value injected as a kwarg.
           - Returns "Async borrowed — <logger> — <membership>".

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class BorrowRequest:
        member_id: str
        book_id: str
        params: dict = field(default_factory=dict)

    class LibraryDesk:
        def __init__(self):
            self.deps = {}

        def add_dep(self, name: str, fn: Callable):
            self.deps[name] = fn

        async def resolve_deps(self):
            result = {}
            for name, dep_fn in self.deps.items():
                if inspect.iscoroutinefunction(dep_fn):
                    result[name] = await dep_fn()
                else:
                    result[name] = dep_fn()
            return result

        async def handle(self, request: BorrowRequest, handler: Callable):
            resolved = await self.resolve_deps()
            params = request.params
            kwargs = {**params, **resolved}
            if inspect.iscoroutinefunction(handler):
                return await handler(**kwargs)
            else:
                return handler(**kwargs)

    def get_logger():
        return "logger:active"

    async def get_membership(member_id: str = ""):
        return "membership:valid"

    def borrow_handler(logger: str, membership: str):
        return f"Borrowed — {logger} — {membership}"

    def async_borrow_handler(logger: str, membership: str):
        return f"Async borrowed — {logger} — {membership}"

    async def main():
        desk = LibraryDesk()
        desk.add_dep("logger", get_logger)
        desk.add_dep("membership", get_membership)

        # Test 1: resolve_deps returns correct values, async dep awaited
        resolved = await desk.resolve_deps()
        print("Test 1: deps resolved correctly")
        print(f"  resolved={resolved}")
        assert resolved == {"logger": "logger:active", "membership": "membership:valid"}
        print("  PASS")

        # Test 2: sync handler called with merged kwargs
        req2 = BorrowRequest(member_id="M-001", book_id="B-101")
        result2 = await desk.handle(req2, borrow_handler)
        print("Test 2: sync handler called with injected deps")
        print(f"  result={result2!r}")
        assert result2 == "Borrowed — logger:active — membership:valid"
        print("  PASS")

        # Test 3: async handler awaited with merged kwargs
        req3 = BorrowRequest(member_id="M-002", book_id="B-202")
        result3 = await desk.handle(req3, async_borrow_handler)
        print("Test 3: async handler awaited with injected deps")
        print(f"  result={result3!r}")
        assert result3 == "Async borrowed — logger:active — membership:valid"
        print("  PASS")

        # Test 4: request.params merged into kwargs
        req4 = BorrowRequest(member_id="M-003", book_id="B-303", params={"shelf": "A2"})

        def shelf_handler(logger: str, membership: str, shelf: str) -> str:
            return f"Shelf {shelf} — {logger}"

        result4 = await desk.handle(req4, shelf_handler)
        print("Test 4: request.params merged into handler kwargs")
        print(f"  result={result4!r}")
        assert result4 == "Shelf A2 — logger:active"
        print("  PASS")

        # Test 5: BorrowRequest params default not shared between instances
        r1 = BorrowRequest(member_id="M-1", book_id="B-1")
        r2 = BorrowRequest(member_id="M-2", book_id="B-2")
        r1.params["note"] = "urgent"
        print("Test 5: params mutable default isolation")
        print(f"  r1.params={r1.params}")
        print(f"  r2.params={r2.params}")
        assert r1.params == {"note": "urgent"}
        assert r2.params == {}
        print("  PASS")

    asyncio.run(main())


run_drill_88()


# EXPECTED OUTPUT
# ===============
# Test 1: deps resolved correctly
#   resolved={'logger': 'logger:active', 'membership': 'membership:valid'}
#   PASS
# Test 2: sync handler called with injected deps
#   result='Borrowed — logger:active — membership:valid'
#   PASS
# Test 3: async handler awaited with injected deps
#   result='Async borrowed — logger:active — membership:valid'
#   PASS
# Test 4: request.params merged into handler kwargs
#   result='Shelf A2 — logger:active'
#   PASS
# Test 5: params mutable default isolation
#   r1.params={'note': 'urgent'}
#   r2.params={}
#   PASS
