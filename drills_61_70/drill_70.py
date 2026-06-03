import asyncio  # noqa: F401
import re  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_70():
    # =========================================================================
    # SCENARIO: The Customs Office
    # =========================================================================
    # Final boss of the dynamic dispatch chunk. No new concepts.
    # You combine everything from drills 61-69 into one mini HTTP router.
    #
    # WHAT YOU ARE BUILDING:
    # A router that supports:
    # - prefix groups via Router class
    # - path params via regex matching
    # - method-aware routing (GET vs POST)
    # - before hooks per route
    # - global error handlers
    # - lifespan (startup/shutdown)
    # - response model validation
    # - returns values to caller
    #
    # REQUIREMENTS:
    #
    # 1. APP_STATE = {}
    #
    # 2. @asynccontextmanager lifespan():
    #    - before yield:
    #        - prints "  [startup] customs system online"
    #        - sets APP_STATE["officers"] = 3
    #    - after yield (finally):
    #        - prints "  [shutdown] customs system offline"
    #        - sets APP_STATE["officers"] = 0
    #
    # 3. Two Pydantic models:
    #    - class DeclarationForm(BaseModel):
    #        - traveler: str
    #        - items: list[str]
    #    - class CustomsResponse(BaseModel):
    #        - traveler: str
    #        - items: list[str]
    #        - status: str
    #        - officers_on_duty: int
    #
    # 4. A custom exception: InvalidResponseError(Exception)
    #
    # 5. A global error registry: ERROR_HANDLERS = {}
    #    - A decorator @error_handler(exc_type) that stores handlers
    #    - A sync handler handle_value_error(exc) -> dict:
    #        - returns {"error": "value error", "detail": str(exc)}
    #    - Apply @error_handler(ValueError) to handle_value_error
    #
    # 6. A before hook (NOT async):
    #    - log_request(path: str, method: str) -> None:
    #        - prints f"  [before] {method} {path}"
    #
    # 7. A global ROUTES = []  (list — for regex matching)
    #    - each entry: (method, compiled_regex, handler, before_hooks, response_model)
    #
    # 8. A function path_to_regex(pattern) -> re.Pattern (same as drill 62)
    #
    # 9. A class Router:
    #    - __init__(self, prefix: str)
    #    - method route(self, method, pattern, before=[], response_model=None):
    #        - appends (method, regex, func, before, response_model) to ROUTES
    #        - returns func unchanged
    #
    # 10. A Router instance:
    #     - customs = Router(prefix="/customs")
    #
    # 11. Two async dependency functions:
    #     - async def get_officer_count() -> int:
    #         - returns APP_STATE.get("officers", 0)
    #     - async def verify_traveler(traveler_id: str) -> str:
    #         - if traveler_id == "banned", raise ValueError("Traveler is banned")
    #         - otherwise return f"Verified: {traveler_id}"
    #
    # 12. Two async handlers:
    #     - async def process_declaration(
    #           form: DeclarationForm, officer_count: int, verified: str
    #       ) -> dict:
    #         - returns {
    #             "traveler": form.traveler,
    #             "items": form.items,
    #             "status": f"cleared by {verified}",
    #             "officers_on_duty": officer_count
    #           }
    #     - async def get_queue(traveler_id: str) -> dict:
    #         - returns {
    #             "traveler": traveler_id,
    #             "items": [],
    #             "status": "in queue",
    #             "officers_on_duty": APP_STATE.get("officers", 0)
    #           }
    #
    # 13. Apply @customs.route:
    #     - POST /declaration/{traveler_id}
    #       before=[log_request], response_model=CustomsResponse
    #       → process_declaration
    #     - GET /queue/{traveler_id}
    #       before=[log_request], response_model=CustomsResponse
    #       → get_queue
    #
    # 14. An async dispatch(method, path, raw_payload=None) -> dict:
    #     - loop through ROUTES
    #     - match method AND path regex
    #     - track path_matched for 405
    #     - run before hooks passing (path, method)
    #     - for POST /declaration/{traveler_id}:
    #         - validate raw_payload into DeclarationForm
    #           (if ValidationError return {"error": "invalid payload"})
    #         - resolve deps: officer_count, verified (verify_traveler(traveler_id))
    #         - if ValueError from verify_traveler, check ERROR_HANDLERS
    #         - call handler(form, officer_count, verified)
    #     - for GET /queue/{traveler_id}:
    #         - call handler(traveler_id=traveler_id)
    #     - validate response against response_model
    #       (if ValidationError raise InvalidResponseError)
    #     - return response.model_dump()
    #     - if path matched but wrong method: return {"error": "405 method not allowed"}
    #     - if no match: return {"error": "404 not found"}
    #
    # 15. An async run_server() that wraps all dispatches in lifespan()
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    APP_STATE = {}

    @asynccontextmanager
    async def lifespan():
        print("  [startup] customs system online")
        APP_STATE["officers"] = 3
        try:
            yield
        finally:
            print("  [shutdown] customs system offline")
            APP_STATE["officers"] = 0

    class DeclarationForm(BaseModel):
        traveler: str
        items: list[str]

    class CustomsResponse(BaseModel):
        traveler: str
        items: list[str]
        status: str
        officers_on_duty: int

    class InvalidResponseError(Exception):
        pass

    ERROR_HANDLERS = {}

    def error_handler(exc_type):
        def decorator(func: Callable):
            ERROR_HANDLERS[exc_type] = func
            return func

        return decorator

    @error_handler(ValueError)
    def handle_value_error(exc):
        return {"error": "value error", "detail": str(exc)}

    def log_request(path: str, method: str):
        print(f"  [before] {method} {path}")

    ROUTES = []

    def path_to_regex(pattern: str) -> re.Pattern:
        mod_str = re.sub(r"\{([^}]+)\}", r"(?P<\g<1>>[^/]+)", pattern)
        return re.compile(f"^{mod_str}$")

    class Router:
        def __init__(self, prefix: str):
            self.prefix = prefix

        def route(self, method, pattern, before=[], response_model=None):
            def decorator(func: Callable):
                ROUTES.append(
                    (
                        method,
                        path_to_regex(self.prefix + pattern),
                        func,
                        before,
                        response_model,
                    )
                )
                return func

            return decorator

    customs = Router(prefix="/customs")

    async def get_officer_count():
        return APP_STATE.get("officers", 0)

    async def verify_traveler(traveler_id: str):
        if traveler_id.lower() == "banned":
            raise ValueError("Traveler is banned")
        return f"Verified: {traveler_id}"

    # method, pattern, before=[], response_model=None
    @customs.route(
        method="POST",
        pattern="/declaration/{traveler_id}",
        before=[log_request],
        response_model=CustomsResponse,
    )
    async def process_declaration(
        form: DeclarationForm, officer_count: int, verified: str
    ):
        return {
            "traveler": form.traveler,
            "items": form.items,
            "status": f"cleared by {verified}",
            "officers_on_duty": officer_count,
        }

    @customs.route(
        method="GET",
        pattern="/queue/{traveler_id}",
        before=[log_request],
        response_model=CustomsResponse,
    )
    async def get_queue(traveler_id: str):
        return {
            "traveler": traveler_id,
            "items": [],
            "status": "in queue",
            "officers_on_duty": APP_STATE.get("officers", 0),
        }

    async def dispatch(method, path, raw_payload=None):
        path_matched = False
        for r_method, regex, func, before, model in ROUTES:
            match = regex.match(path)
            if match:
                path_matched = True
                if r_method == method:
                    for b_hook in before:
                        b_hook(path, method)
                    kwargs = match.groupdict()
                    if r_method == "POST":
                        officer_count = await get_officer_count()
                        try:
                            valid_form = DeclarationForm(**raw_payload)
                            verified = await verify_traveler(kwargs["traveler_id"])
                        except ValidationError:
                            return {"error": "invalid payload"}
                        except ValueError as e:
                            if type(e) in ERROR_HANDLERS:
                                return ERROR_HANDLERS[type(e)](e)
                        response = await func(valid_form, officer_count, verified)
                    else:
                        response = await func(**kwargs)
                    try:
                        verified_res = model(**response)
                    except ValidationError as e:
                        raise InvalidResponseError(str(e))
                    return verified_res.model_dump()

        if path_matched:
            return {"error": "405 method not allowed"}
        return {"error": "404 not found"}

    async def run_server():
        async with lifespan():
            result1 = await dispatch(
                method="POST",
                path="/customs/declaration/alice",
                raw_payload={"traveler": "Alice", "items": ["watch", "laptop"]},
            )
            print(f"  {result1}")
            result2 = await dispatch(
                method="GET",
                path="/customs/queue/bob",
            )
            print(f"  {result2}")
            result3 = await dispatch(
                method="POST",
                path="/customs/declaration/banned",
                raw_payload={"traveler": "Banned", "items": ["contraband"]},
            )
            print(f"  {result3}")
            result4 = await dispatch(
                method="GET",
                path="/customs/queue/charlie",
            )
            print(f"  {result4}")
            result5 = await dispatch(
                method="PUT",
                path="/customs/declaration/alice",
            )
            print(f"  {result5}")
            result6 = await dispatch(
                method="GET",
                path="/customs/unknown",
            )
            print(f"  {result6}")

    # --- TESTS (do not modify) ---
    print("Test 1: Full server lifecycle")
    await run_server()

    print("\nTest 2: State cleaned up after lifespan")
    assert APP_STATE.get("officers") == 0
    print("  officers after shutdown: 0")

    # =========================================================================
    # run_server() should dispatch in this order:
    #
    # POST /customs/declaration/alice  payload={"traveler": "Alice", "items": ["watch", "laptop"]}
    # GET  /customs/queue/bob
    # POST /customs/declaration/banned payload={"traveler": "Banned", "items": ["contraband"]}
    # GET  /customs/queue/charlie
    # PUT  /customs/declaration/alice  (wrong method)
    # GET  /customs/unknown            (unknown path)
    #
    # EXPECTED OUTPUT:
    #
    # Test 1: Full server lifecycle
    #   [startup] customs system online
    #   [before] POST /customs/declaration/alice
    #   {'traveler': 'Alice', 'items': ['watch', 'laptop'], 'status': 'cleared by Verified: alice', 'officers_on_duty': 3}
    #   [before] GET /customs/queue/bob
    #   {'traveler': 'bob', 'items': [], 'status': 'in queue', 'officers_on_duty': 3}
    #   [before] POST /customs/declaration/banned
    #   {'error': 'value error', 'detail': 'Traveler is banned'}
    #   [before] GET /customs/queue/charlie
    #   {'traveler': 'charlie', 'items': [], 'status': 'in queue', 'officers_on_duty': 3}
    #   {'error': '405 method not allowed'}
    #   {'error': '404 not found'}
    #   [shutdown] customs system offline
    #
    # Test 2: State cleaned up after lifespan
    #   officers after shutdown: 0
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_70())
