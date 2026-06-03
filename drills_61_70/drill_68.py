import asyncio  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_68():
    # =========================================================================
    # SCENARIO: The Embassy
    # =========================================================================
    # An embassy API processes visa applications. Before a handler runs,
    # it needs to resolve a chain of dependencies:
    # 1. verify the passport token → returns a Passport object
    # 2. using the Passport, look up the applicant's travel history → returns TravelHistory
    # The handler receives both objects.
    #
    # This is a dependency graph — dep 2 depends on the result of dep 1.
    #
    # REQUIREMENTS:
    #
    # 1. Two plain classes (NOT Pydantic — just simple classes):
    #    - class Passport:
    #        - __init__(self, number: str, country: str)
    #    - class TravelHistory:
    #        - __init__(self, passport: Passport, visits: list)
    #
    # 2. Two async dependency functions:
    #    - async def get_passport(token: str) -> Passport:
    #        - if token != "valid-token", raise ValueError("Invalid passport token")
    #        - otherwise return Passport(number="PH-123", country="Philippines")
    #    - async def get_travel_history(passport: Passport) -> TravelHistory:
    #        - returns TravelHistory(passport=passport, visits=["Japan", "Korea", "USA"])
    #
    # 3. A registry: ROUTES = {}
    #
    # 4. A decorator @route(path: str):
    #    - stores handler in ROUTES under path
    #    - returns func unchanged
    #
    # 5. An async handler process_visa(passport, travel_history) -> dict:
    #    - decorated with @route("/visa/apply")
    #    - returns {
    #        "applicant": passport.number,
    #        "country": passport.country,
    #        "visits": travel_history.visits,
    #        "status": "approved"
    #      }
    #
    # 6. An async dispatch(path: str, token: str) -> dict | None:
    #    - if path not found, return {"error": "not found"}
    #    - resolve the dependency chain:
    #        step 1: await get_passport(token) → passport
    #        step 2: await get_travel_history(passport) → travel_history
    #        if get_passport raises ValueError, return {"error": str(e)}
    #    - call the handler passing passport and travel_history
    #    - return the result
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class Passport:
        def __init__(self, number: str, country: str):
            self.number = number
            self.country = country

    class TravelHistory:
        def __init__(self, passport: Passport, visits: list):
            self.passport = passport
            self.visits = visits

    async def get_passport(token: str) -> Passport:
        if token != "valid-token":
            raise ValueError("Invalid passport token")
        return Passport(number="PH-123", country="Philippines")

    async def get_travel_history(passport: Passport) -> TravelHistory:
        return TravelHistory(passport=passport, visits=["Japan", "Korea", "USA"])

    ROUTES = {}

    def route(path: str):
        def decorator(func: Callable):
            ROUTES[path] = func
            return func

        return decorator

    @route("/visa/apply")
    async def process_visa(passport, travel_history) -> dict:
        return {
            "applicant": passport.number,
            "country": passport.country,
            "visits": travel_history.visits,
            "status": "approved",
        }

    async def dispatch(path: str, token: str):
        if path not in ROUTES:
            return {"error": "not found"}
        route = ROUTES[path]
        try:
            passport = await get_passport(token)
            travel_history = await get_travel_history(passport)
        except ValueError as e:
            return {"error": str(e)}
        result = await route(passport, travel_history)
        return result

    # --- TESTS (do not modify) ---
    print("Test 1: Valid token — full chain resolves")
    result = await dispatch("/visa/apply", token="valid-token")
    print(f"  Result: {result}")

    print("\nTest 2: Invalid token — chain breaks at step 1")
    result = await dispatch("/visa/apply", token="fake-token")
    print(f"  Result: {result}")

    print("\nTest 3: Unknown path")
    result = await dispatch("/visa/status", token="valid-token")
    print(f"  Result: {result}")

    print("\nTest 4: Travel history has correct passport reference")
    result = await dispatch("/visa/apply", token="valid-token")
    assert result["applicant"] == "PH-123"
    assert result["country"] == "Philippines"
    assert "Japan" in result["visits"]
    print("  All assertions passed")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid token — full chain resolves
    #   Result: {'applicant': 'PH-123', 'country': 'Philippines',
    #            'visits': ['Japan', 'Korea', 'USA'], 'status': 'approved'}
    #
    # Test 2: Invalid token — chain breaks at step 1
    #   Result: {'error': 'Invalid passport token'}
    #
    # Test 3: Unknown path
    #   Result: {'error': 'not found'}
    #
    # Test 4: Travel history has correct passport reference
    #   All assertions passed
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_68())
