import asyncio  # noqa: F401
import re  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_64():
    # =========================================================================
    # SCENARIO: The Audit Logger
    # =========================================================================
    # An API needs to run code BEFORE and AFTER every handler executes.
    # Before: log that a request started
    # After: log that a request finished, including the result
    #
    # This is the before/after hook pattern — the foundation of middleware.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: ROUTES = {}
    #    - keys are path strings
    #    - values are dicts: {"handler": func, "before": list, "after": list}
    #
    # 2. A decorator @route(path, before=[], after=[]):
    #    - before: list of sync functions to call before the handler
    #      each receives (path, method) as arguments
    #    - after: list of sync functions to call after the handler
    #      each receives (path, method, result) as arguments
    #    - stores handler + both lists in ROUTES under path
    #    - returns func unchanged
    #
    # 3. Two before hooks (NOT async, you write these):
    #    - log_request(path: str, method: str) -> None:
    #        - prints f"  [before] {method} {path}"
    #    - check_auth(path: str, method: str) -> None:
    #        - prints f"  [auth] checking {method} {path}"
    #
    # 4. Two after hooks (NOT async, you write these):
    #    - log_response(path: str, method: str, result) -> None:
    #        - prints f"  [after] {method} {path} → {result}"
    #    - audit_trail(path: str, method: str, result) -> None:
    #        - prints f"  [audit] logged: {result}"
    #
    # 5. An async handler get_user() -> dict (you write this):
    #    - returns {"user": "alice", "role": "admin"}
    #
    # 6. Apply @route to get_user:
    #    path   = "/users/me"
    #    before = [log_request, check_auth]
    #    after  = [log_response, audit_trail]
    #
    # 7. An async dispatch(path: str, method: str) -> dict | None:
    #    - if path not found, print "  404: {path}" and return None
    #    - run each before hook in order, passing (path, method)
    #    - call and await the handler
    #    - run each after hook in order, passing (path, method, result)
    #    - return the result
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    ROUTES = {}

    def route(path: str, before=[], after=[]):
        def decorator(func: Callable) -> Callable:
            ROUTES[path] = {"handler": func, "before": before, "after": after}
            return func

        return decorator

    def log_request(path: str, method: str):
        print(f"  [before] {method} {path}")

    def check_auth(path: str, method: str):
        print(f"  [auth] checking {method} {path}")

    def log_response(path: str, method: str, result):
        print(f"  [after] {method} {path} -> {result}")

    def audit_trail(path: str, method: str, result):
        print(f"  [audit] logged: {result}")

    @route(
        path="/users/me",
        before=[log_request, check_auth],
        after=[log_response, audit_trail],
    )
    async def get_user() -> dict:
        return {"user": "alice", "role": "admin"}

    async def dispatch(path: str, method: str) -> dict | None:
        if path not in ROUTES:
            print(f"  404: {path}")
            return None
        route = ROUTES[path]
        for b_hook in route["before"]:
            b_hook(path, method)
        result = await route["handler"]()
        for a_hook in route["after"]:
            a_hook(path, method, result)
        return result

    # --- TESTS (do not modify) ---
    print("Test 1: Full request lifecycle")
    result = await dispatch("/users/me", "GET")
    print(f"  Final result: {result}")

    print("\nTest 2: Unknown path")
    result = await dispatch("/unknown", "GET")
    print(f"  Final result: {result}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Full request lifecycle
    #   [before] GET /users/me
    #   [auth] checking GET /users/me
    #   [after] GET /users/me → {'user': 'alice', 'role': 'admin'}
    #   [audit] logged: {'user': 'alice', 'role': 'admin'}
    #   Final result: {'user': 'alice', 'role': 'admin'}
    #
    # Test 2: Unknown path
    #   404: /unknown
    #   Final result: None
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_64())
