import asyncio  # noqa: F401
import re  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_65():
    # =========================================================================
    # SCENARIO: The Crash-Proof API
    # =========================================================================
    # An API needs a global error handler — a single fallback that catches
    # any unhandled exception from any handler and returns a safe error response
    # instead of crashing the entire server.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: ROUTES = {}
    #
    # 2. An error handler registry: ERROR_HANDLERS = {}
    #    - keys are exception types
    #    - values are sync functions that receive the exception and return a dict
    #
    # 3. A decorator @route(path: str):
    #    - stores handler in ROUTES under path
    #    - returns func unchanged
    #
    # 4. A decorator @error_handler(exc_type):
    #    - stores handler in ERROR_HANDLERS under exc_type
    #    - returns func unchanged
    #
    # 5. Three async handlers (you write these):
    #    - async def get_product() -> dict:
    #        - returns {"product": "laptop", "price": 999}
    #    - async def get_broken() -> dict:
    #        - raises ValueError("product not found")
    #    - async def get_crashed() -> dict:
    #        - raises RuntimeError("database connection lost")
    #
    # 6. Apply @route to each handler:
    #    - @route("/products/1")  -> get_product
    #    - @route("/products/2")  -> get_broken
    #    - @route("/products/3")  -> get_crashed
    #
    # 7. Two error handler functions (you write these):
    #    - handle_value_error(exc: ValueError) -> dict:
    #        - returns {"error": "not found", "detail": str(exc)}
    #    - handle_runtime_error(exc: RuntimeError) -> dict:
    #        - returns {"error": "server error", "detail": str(exc)}
    #
    # 8. Apply @error_handler to each:
    #    - @error_handler(ValueError)    -> handle_value_error
    #    - @error_handler(RuntimeError)  -> handle_runtime_error
    #
    # 9. An async dispatch(path: str) -> dict | None:
    #    - if path not found, return {"error": "not found", "detail": path}
    #    - call and await the handler inside a try block
    #    - if it raises, check ERROR_HANDLERS for the exception type
    #      - if a handler exists, call it with the exception and return the result
    #      - if no handler exists, re-raise the exception
    #    - return the result on success
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    ROUTES = {}

    ERROR_HANDLERS = {}

    def route(path: str):
        def decorator(func: Callable) -> Callable:
            ROUTES[path] = func
            return func

        return decorator

    def error_handler(exc_type):
        def decorator(func: Callable) -> Callable:
            ERROR_HANDLERS[exc_type] = func
            return func

        return decorator

    @route("/products/1")
    async def get_product():
        return {"product": "laptop", "price": 999}

    @route("/products/2")
    async def get_broken():
        raise ValueError("product not found")

    @route("/products/3")
    async def get_crashed():
        raise RuntimeError("database connection lost")

    @error_handler(ValueError)
    def handle_value_error(exc: ValueError):
        return {"error": "not found", "detail": str(exc)}

    @error_handler(RuntimeError)
    def handle_runtime_error(exc: RuntimeError):
        return {"error": "server error", "detail": str(exc)}

    async def dispatch(path: str) -> dict | None:
        if path not in ROUTES:
            return {"error": "not found", "detail": path}
        route = ROUTES[path]
        try:
            result = await route()
            return result
        except Exception as e:
            if type(e) in ERROR_HANDLERS:
                result = ERROR_HANDLERS[type(e)](e)
                return result
            raise

    # --- TESTS (do not modify) ---
    print("Test 1: Successful handler")
    result = await dispatch("/products/1")
    print(f"  Result: {result}")

    print("\nTest 2: Handler raises ValueError — caught by error handler")
    result = await dispatch("/products/2")
    print(f"  Result: {result}")

    print("\nTest 3: Handler raises RuntimeError — caught by error handler")
    result = await dispatch("/products/3")
    print(f"  Result: {result}")

    print("\nTest 4: Unknown path — returns not found dict")
    result = await dispatch("/products/99")
    print(f"  Result: {result}")

    print("\nTest 5: Unhandled exception type — re-raises")
    del ERROR_HANDLERS[RuntimeError]  # ← add this
    try:
        await dispatch("/products/3")
    except RuntimeError as e:
        print(f"  Re-raised: {e}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Successful handler
    #   Result: {'product': 'laptop', 'price': 999}
    #
    # Test 2: Handler raises ValueError — caught by error handler
    #   Result: {'error': 'not found', 'detail': 'product not found'}
    #
    # Test 3: Handler raises RuntimeError — caught by error handler
    #   Result: {'error': 'server error', 'detail': 'database connection lost'}
    #
    # Test 4: Unknown path — returns not found dict
    #   Result: {'error': 'not found', 'detail': '/products/99'}
    #
    # Test 5: Unhandled exception type — re-raises
    #   Re-raised: database connection lost
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_65())
