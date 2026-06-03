import asyncio  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_47():
    # =========================================================================
    # SCENARIO: The Online Checkout
    # =========================================================================
    # An online store has multiple checkout routes. Before any handler runs,
    # dispatch must first validate the raw dict payload into a Pydantic model.
    # If the data is invalid, block immediately. If valid, run the checks,
    # then pass everything to the handler.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: ROUTES = {}
    #
    # 2. A Pydantic model Order with three fields:
    #    - item: str
    #    - qty: int
    #    - price: float
    #
    # 3. Two check functions (NOT async):
    #    - check_stock(order: Order) -> str
    #      - if order.qty > 10, raise ValueError("Not enough stock")
    #      - otherwise return f"Stock OK: {order.qty} units"
    #    - check_price(order: Order) -> str
    #      - if order.price <= 0, raise ValueError("Invalid price")
    #      - otherwise return f"Price OK: ${order.price}"
    #
    # 4. A decorator @register(path, checks: dict)
    #    - create an object in ROUTES with handler as func, and checks as checks
    #    - return func
    #
    # 5. An async handler checkout_handler(stock, price) (you write this):
    #    - prints each argument on its own line, indented with two spaces
    #
    # 6. Apply @register to checkout_handler:
    #    path = "/checkout"
    #    checks = {"stock": check_stock, "price": check_price}
    #
    # 7. An async dispatch(path: str, raw_payload: dict):
    #    - if path not found, print "404" and stop
    #    - validate raw_payload into an Order object
    #      - if ValidationError, print "Invalid data" and stop
    #    - create resolved = {}
    #    - loop through checks, call each one passing the Order object
    #      (NOT the raw dict — the validated Order)
    #    - collect results into resolved
    #    - if a check raises ValueError, print "Check Error: <msg>" and stop
    #    - call the handler with **resolved
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    ROUTES = {}

    class Order(BaseModel):
        item: str
        qty: int
        price: float

    def check_stock(order: Order) -> str:
        if order.qty > 10:
            raise ValueError("Not enough stock")
        return f"Stock OK: {order.qty} units"

    def check_price(order: Order) -> str:
        if order.price <= 0:
            raise ValueError("Invalid price")
        return f"Price OK: ${order.price}"

    def register(path, checks: dict):
        def decorator(func: Callable) -> Callable:
            ROUTES[path] = {"handler": func, "checks": checks}
            return func

        return decorator

    @register(path="/checkout", checks={"stock": check_stock, "price": check_price})
    async def checkout_handler(stock, price):
        print(f"  {stock}")
        print(f"  {price}")

    async def dispatch(path: str, raw_payload: dict):
        if path not in ROUTES:
            print("404")
            return
        route = ROUTES[path]
        try:
            validated_order = Order(**raw_payload)
            resolved = {}
            for arg_name, func in route["checks"].items():
                resolved[arg_name] = func(validated_order)
        except ValidationError:
            print("Invalid data")
            return
        except ValueError as msg:
            print(f"Check Error: {msg}")
            return
        return await route["handler"](**resolved)

    # --- TESTS (do not modify) ---
    print("Test 1: Valid order")
    await dispatch("/checkout", {"item": "laptop", "qty": 2, "price": 999.99})

    print("\nTest 2: Bad data (qty is a string)")
    await dispatch("/checkout", {"item": "laptop", "qty": "two", "price": 999.99})

    print("\nTest 3: Check failure (too much qty)")
    await dispatch("/checkout", {"item": "laptop", "qty": 50, "price": 999.99})

    print("\nTest 4: Check failure (invalid price)")
    await dispatch("/checkout", {"item": "laptop", "qty": 2, "price": -5.0})

    print("\nTest 5: Unknown path")
    await dispatch("/unknown", {"item": "laptop", "qty": 2, "price": 999.99})

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid order
    #   Stock OK: 2 units
    #   Price OK: $999.99
    #
    # Test 2: Bad data (qty is a string)
    #   Invalid data
    #
    # Test 3: Check failure (too much qty)
    #   Check Error: Not enough stock
    #
    # Test 4: Check failure (invalid price)
    #   Check Error: Invalid price
    #
    # Test 5: Unknown path
    #   404
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_47())
