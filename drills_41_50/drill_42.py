import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Any, Callable, Dict, List  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_42():
    # =========================================================================
    # THE SCENARIO: API Router with Pre-Execution Hooks (Middleware)
    # =========================================================================
    # You need to build a system where incoming requests pass through a series
    # of middleware (hooks) before reaching the main handler.
    #
    # SYSTEM REQUIREMENTS:
    # 1. A central registry `APP` (a dictionary).
    # 2. A Pydantic model `OrderPayload` requiring `item_id` (str) and `qty` (int).
    # 3. A decorator `@route(path: str, middleware: list[Callable])`.
    #    - It must register the path in `APP`.
    #    - It must store both the handler function and the middleware list.
    # 4. An async `dispatch(path: str, raw_data: dict)` function that:
    #    - Looks up the path in `APP`. Prints "404 Not Found" if missing and returns.
    #    - Executes each middleware function in order (awaiting them), passing `raw_data`.
    #      * If a middleware raises an Exception, catch it, print
    #        "Middleware Error: <ExceptionMessage>", and ABORT execution.
    #    - If all middleware passes, validate `raw_data` into an `OrderPayload` object.
    #      * If Pydantic throws ValidationError, print "Validation Error" and ABORT.
    #    - Finally, execute the main handler with the validated `OrderPayload`.
    # =========================================================================

    # --- WRITE YOUR CODE BELOW ---

    # 1. Define APP
    APP = {}

    # 2. Define OrderPayload inside here
    class OrderPayload(BaseModel):
        item_id: str
        qty: int

    # 3. Define @route decorator
    def route(path: str, middleware: list[Callable]):
        def decorator(func: Callable) -> Callable:
            APP[path] = {"handler": func, "middleware": middleware}
            return func

        return decorator

    # 4. Define dispatch
    async def dispatch(path: str, raw_data: dict):
        if path not in APP:
            print("404 Not Found")
            return

        route_info = APP[path]
        middlewares, handler = route_info["middleware"], route_info["handler"]

        for middleware in middlewares:
            try:
                await middleware(raw_data)
            except Exception as e:
                print(f"Middleware Error: {str(e)}")
                return

        try:
            payload = OrderPayload(**raw_data)
        except ValidationError:
            print("Validation Error")
            return

        await handler(payload)

    # -------------------------------------------------------------------------
    # PRE-WRITTEN TEST COMPONENTS (USE THESE IN YOUR @route)
    # -------------------------------------------------------------------------
    async def fraud_check_hook(data: dict):
        if data.get("item_id") == "SKU-BAD":
            raise PermissionError("Fraud detected")

    async def check_inventory_hook(data: dict):
        if data.get("qty", 0) > 99:
            raise ValueError("Insufficient stock")

    # TODO: Apply your @route decorator to `process_order` covering the path "/order".
    # Use both hooks in this specific order: [fraud_check_hook, check_inventory_hook]
    @route(path="/order", middleware=[fraud_check_hook, check_inventory_hook])
    async def process_order(order):
        print(f"Order processed successfully for {order.qty}x {order.item_id}!")

    # --- EXECUTION TESTS (Do not modify these) ---
    print("\nTest 1: Valid Order")
    await dispatch("/order", {"item_id": "SKU-123", "qty": 5})

    print("\nTest 2: Fraudulent Item (Fails Middleware 1)")
    await dispatch("/order", {"item_id": "SKU-BAD", "qty": 5})

    print("\nTest 3: Out of Stock (Fails Middleware 2)")
    await dispatch("/order", {"item_id": "SKU-123", "qty": 150})

    print("\nTest 4: Bad Data (Fails Pydantic Validation)")
    await dispatch("/order", {"item_id": "SKU-123", "qty": "five"})

    print("\nTest 5: Bad Path")
    await dispatch("/unknown", {"item_id": "SKU-123", "qty": 1})

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid Order
    # Order processed successfully for 5x SKU-123!
    #
    # Test 2: Fraudulent Item (Fails Middleware 1)
    # Middleware Error: Fraud detected
    #
    # Test 3: Out of Stock (Fails Middleware 2)
    # Middleware Error: Insufficient stock
    #
    # Test 4: Bad Data (Fails Pydantic Validation)
    # Validation Error
    #
    # Test 5: Bad Path
    # 404 Not Found
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_42())
