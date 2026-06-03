import asyncio  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_67():
    # =========================================================================
    # SCENARIO: The Data Center
    # =========================================================================
    # A data center API needs to run setup and teardown code around its
    # entire lifetime — not per-request, but once when the server starts
    # and once when it shuts down. This is the lifespan pattern.
    #
    # In FastAPI this is done with asynccontextmanager. You yield once —
    # everything before yield is startup, everything after is shutdown.
    #
    # REQUIREMENTS:
    #
    # 1. A state dict: APP_STATE = {}
    #    - used to share startup-initialized resources with handlers
    #
    # 2. An async context manager lifespan():
    #    - decorated with @asynccontextmanager
    #    - BEFORE yield:
    #        - prints "  [startup] connecting to database"
    #        - prints "  [startup] loading config"
    #        - sets APP_STATE["db"] = "connected"
    #        - sets APP_STATE["config"] = {"max_connections": 10}
    #    - AFTER yield (in finally):
    #        - prints "  [shutdown] closing database"
    #        - sets APP_STATE["db"] = None
    #
    # 3. A registry: ROUTES = {}
    #
    # 4. A decorator @route(path: str):
    #    - stores handler in ROUTES under path
    #    - returns func unchanged
    #
    # 5. Two async handlers (you write these):
    #    - async def get_db_status() -> dict:
    #        - returns {"db": APP_STATE.get("db"), "config": APP_STATE.get("config")}
    #    - async def get_health() -> dict:
    #        - returns {"status": "ok", "db_connected": APP_STATE.get("db") == "connected"}
    #
    # 6. Apply @route:
    #    - @route("/db/status") -> get_db_status
    #    - @route("/health")    -> get_health
    #
    # 7. An async dispatch(path: str) -> dict | None:
    #    - if path not in ROUTES, return {"error": "not found"}
    #    - call and await the handler
    #    - return the result
    #
    # 8. An async run_server():
    #    - uses `async with lifespan():` to wrap all dispatch calls
    #    - inside the block, dispatches three requests (see tests)
    #    - the lifespan prints happen outside the dispatch calls
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    APP_STATE = {}

    @asynccontextmanager
    async def lifespan():
        print("  [startup] connecting to database")
        print("  [startup] loading config")
        APP_STATE["db"] = "connected"
        APP_STATE["config"] = {"max_connections": 10}
        try:
            yield
        finally:
            print("  [shutdown] closing database")
            APP_STATE["db"] = None

    ROUTES = {}

    def route(path: str):
        def decorator(func: Callable):
            ROUTES[path] = func
            return func

        return decorator

    @route("/db/status")
    async def get_db_status():
        return {"db": APP_STATE.get("db"), "config": APP_STATE.get("config")}

    @route("/health")
    async def get_health():
        return {"status": "ok", "db_connected": APP_STATE.get("db") == "connected"}

    async def dispatch(path: str):
        if path not in ROUTES:
            return {"error": "not found"}
        route = ROUTES[path]
        result = await route()
        return result

    async def run_server():
        async with lifespan():
            print("  [request] GET /health")
            result1 = await dispatch("/health")
            print(f"  {result1}")

            # 2. /db/status request
            print("  [request] GET /db/status")
            result2 = await dispatch("/db/status")
            print(f"  {result2}")

            # 3. /unknown request
            print("  [request] GET /unknown")
            result3 = await dispatch("/unknown")
            print(f"  {result3}")

    # --- TESTS (do not modify) ---
    print("Test 1: Run server with lifespan")
    await run_server()

    print("\nTest 2: State is cleaned up after lifespan exits")
    assert APP_STATE.get("db") is None, "db should be None after shutdown"
    print("  db after shutdown: None")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Run server with lifespan
    #   [startup] connecting to database
    #   [startup] loading config
    #   [request] GET /health
    #   {'status': 'ok', 'db_connected': True}
    #   [request] GET /db/status
    #   {'db': 'connected', 'config': {'max_connections': 10}}
    #   [request] GET /unknown
    #   {'error': 'not found'}
    #   [shutdown] closing database
    #
    # Test 2: State is cleaned up after lifespan exits
    #   db after shutdown: None
    # =========================================================================

    # run_server should dispatch these three requests in order:
    # 1. print "  [request] GET /health", then dispatch("/health"), then print result
    # 2. print "  [request] GET /db/status", then dispatch("/db/status"), then print result
    # 3. print "  [request] GET /unknown", then dispatch("/unknown"), then print result


if __name__ == "__main__":
    asyncio.run(run_drill_67())
