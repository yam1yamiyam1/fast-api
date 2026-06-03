import asyncio  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_66():
    # =========================================================================
    # SCENARIO: The Train Station
    # =========================================================================
    # A train station API has two service desks — domestic and international.
    # Each desk handles its own routes but shares one central dispatcher.
    # Instead of hardcoding the full path everywhere, each desk is a Router
    # with its own prefix that registers routes into a shared registry.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: ROUTES = {}
    #
    # 2. A class Router:
    #    - __init__(self, prefix: str):
    #        - self.prefix = prefix
    #    - method route(self, path: str):
    #        - a decorator that stores the handler in ROUTES
    #          under self.prefix + path as the key
    #        - returns func unchanged
    #
    # 3. Two Router instances:
    #    - domestic   = Router(prefix="/domestic")
    #    - international = Router(prefix="/international")
    #
    # 4. Four async handlers (you write these):
    #    - async def domestic_schedule() -> dict:
    #        - returns {"desk": "domestic", "trains": ["TR-01", "TR-02"]}
    #    - async def domestic_tickets() -> dict:
    #        - returns {"desk": "domestic", "available": 120}
    #    - async def international_schedule() -> dict:
    #        - returns {"desk": "international", "trains": ["EX-01", "EX-02"]}
    #    - async def international_tickets() -> dict:
    #        - returns {"desk": "international", "available": 45}
    #
    # 5. Apply decorators:
    #    - @domestic.route("/schedule")   -> domestic_schedule
    #    - @domestic.route("/tickets")    -> domestic_tickets
    #    - @international.route("/schedule") -> international_schedule
    #    - @international.route("/tickets")  -> international_tickets
    #
    # 6. An async dispatch(path: str) -> dict | None:
    #    - if path not in ROUTES, return {"error": "not found", "path": path}
    #    - call and await the handler
    #    - return the result
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    ROUTES = {}

    class Router:
        def __init__(self, prefix: str):
            self.prefix = prefix

        def route(self, path: str):
            def decorator(func: Callable) -> Callable:
                ROUTES[self.prefix + path] = func
                return func

            return decorator

    domestic = Router(prefix="/domestic")
    international = Router(prefix="/international")

    @domestic.route("/schedule")
    async def domestic_schedule():
        return {"desk": "domestic", "trains": ["TR-01", "TR-02"]}

    @domestic.route("/tickets")
    async def domestic_tickets():
        return {"desk": "domestic", "available": 120}

    @international.route("/schedule")
    async def international_schedule():
        return {"desk": "international", "trains": ["EX-01", "EX-02"]}

    @international.route("/tickets")
    async def international_tickets():
        return {"desk": "international", "available": 45}

    async def dispatch(path: str):
        if path not in ROUTES:
            return {"error": "not found", "path": path}
        route = ROUTES[path]
        result = await route()
        return result

    # --- TESTS (do not modify) ---
    print("Test 1: Domestic schedule")
    result = await dispatch("/domestic/schedule")
    print(f"  Result: {result}")

    print("\nTest 2: International schedule")
    result = await dispatch("/international/schedule")
    print(f"  Result: {result}")

    print("\nTest 3: Domestic tickets")
    result = await dispatch("/domestic/tickets")
    print(f"  Result: {result}")

    print("\nTest 4: International tickets")
    result = await dispatch("/international/tickets")
    print(f"  Result: {result}")

    print("\nTest 5: Unknown path")
    result = await dispatch("/vip/lounge")
    print(f"  Result: {result}")

    print("\nTest 6: All registered routes")
    print(f"  Routes: {sorted(ROUTES.keys())}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Domestic schedule
    #   Result: {'desk': 'domestic', 'trains': ['TR-01', 'TR-02']}
    #
    # Test 2: International schedule
    #   Result: {'desk': 'international', 'trains': ['EX-01', 'EX-02']}
    #
    # Test 3: Domestic tickets
    #   Result: {'desk': 'domestic', 'available': 120}
    #
    # Test 4: International tickets
    #   Result: {'desk': 'international', 'available': 45}
    #
    # Test 5: Unknown path
    #   Result: {'error': 'not found', 'path': '/vip/lounge'}
    #
    # Test 6: All registered routes
    #   Routes: ['/domestic/schedule', '/domestic/tickets',
    #            '/international/schedule', '/international/tickets']
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_66())
