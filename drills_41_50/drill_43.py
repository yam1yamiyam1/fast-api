import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Any, Callable, Dict  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_43():
    # =========================================================================
    # "The VIP Dashboard"
    # =========================================================================
    # A dashboard function should only care about showing data.
    # It should NOT handle authentication itself.
    #
    # Instead, a dispatcher handles auth first:
    # - Takes a token from the request
    # - Runs checker functions to convert that token into real objects (like a User)
    # - If a checker fails, block the request immediately with "Auth Error"
    # - If all checkers pass, hand the resolved objects to the handler
    #
    # REQUIREMENTS:
    #
    # 1. A registry: APP_ROUTES = {}
    #
    # 2. A Pydantic model User with two fields:
    #    - username: str
    #    - tier: str
    #
    # 3. An async checker function get_current_user(token: str):
    #    - if token == "secret-123", return User(username="Alice", tier="VIP")
    #    - otherwise raise ValueError("Invalid token")
    #
    # 4. A decorator @get(path, dependencies):
    #    - dependencies is a dict mapping argument name to checker function
    #      e.g. {"current_user": get_current_user}
    #    - create an object in APP_ROUTES with handler as func, and dependencies as dependencies
    #      e.g. APP_ROUTES["/dashboard"] = {"handler": vip_dashboard, "dependencies": {...}}
    #
    # 5. Apply @get to vip_dashboard (already written below, do not modify):
    #    - path = "/dashboard"
    #    - dependencies = {"current_user": get_current_user}
    #
    # 6. An async dispatch(path, request_token):
    #    - if path not in APP_ROUTES, print "404" and stop
    #    - create an empty dict: resolved = {}
    #    - loop through dependencies, for each (arg_name, checker_func):
    #        - call checker_func with request_token (it is async, so await it)
    #        - save the result: resolved[arg_name] = result
    #        - if it raises any Exception, print "Auth Error: <msg>" and stop
    #    - after the loop, call the handler with **resolved
    # =========================================================================

    # --- YOUR CODE HERE ---

    # 1. APP_ROUTES registry
    APP_ROUTES = {}

    # 2. User model
    class User(BaseModel):
        username: str
        tier: str

    # 3. get_current_user checker
    async def get_current_user(token: str):
        if token != "secret-123":
            raise ValueError("Invalid token")
        return User(username="Alice", tier="VIP")

    # 4. @get decorator
    def get(path: str, dependencies: dict):
        def decorator(func: Callable) -> Callable:
            APP_ROUTES[path] = {"handler": func, "dependencies": dependencies}
            return func

        return decorator

    # 5. Apply @get to vip_dashboard here (write the decorator line only, handler is below)

    # --- DO NOT MODIFY ---
    @get(path="/dashboard", dependencies={"current_user": get_current_user})
    async def vip_dashboard(current_user):
        print(
            f"Welcome to the dashboard, {current_user.username}! Your tier is {current_user.tier}."
        )

    # 6. dispatch function
    async def dispatch(path: str, request_token: str):
        if path not in APP_ROUTES:
            print("404")
            return
        route = APP_ROUTES[path]
        dependencies = route["dependencies"]
        resolved = {}
        for arg_name, func in dependencies.items():
            try:
                resolved[arg_name] = await func(request_token)
            except Exception as e:
                print(f"Auth Error: {e}")
                return
        return await route["handler"](**resolved)

    # --- TESTS (do not modify) ---
    print("\nTest 1: Valid Visitor")
    await dispatch("/dashboard", request_token="secret-123")

    print("\nTest 2: Fake Ticket")
    await dispatch("/dashboard", request_token="wrong-password")

    print("\nTest 3: Lost Visitor")
    await dispatch("/nowhere", request_token="secret-123")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid Visitor
    # Welcome to the dashboard, Alice! Your tier is VIP.
    #
    # Test 2: Fake Ticket
    # Auth Error: Invalid token
    #
    # Test 3: Lost Visitor
    # 404
    # =========================================================================
    test = await get_current_user("secret-123")
    print(test.model_dump())


if __name__ == "__main__":
    asyncio.run(run_drill_43())
