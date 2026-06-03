import asyncio  # noqa: F401
import re  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_62():
    # =========================================================================
    # SCENARIO: The City Directory
    # =========================================================================
    # A city directory API handles requests with dynamic path parameters.
    # Instead of exact string keys like "cola", routes are patterns like
    # "/cities/{city_id}" that match incoming paths and extract variables.
    #
    # This drill is about one thing: matching a path pattern against a real
    # path and extracting the dynamic parts as a dict.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: ROUTES = []
    #    - NOTE: this is a LIST not a dict — because patterns must be checked
    #      in order, and dicts don't guarantee match priority
    #    - each entry is a tuple: (pattern, handler)
    #
    # 2. A function path_to_regex(pattern: str) -> re.Pattern:
    #    - converts a path pattern like "/cities/{city_id}/districts/{district_id}"
    #      into a compiled regex that captures the dynamic parts as named groups
    #    - hint: replace {param_name} with (?P<param_name>[^/]+)
    #    - the full path must match — anchor with ^ and $
    #    - example:
    #        path_to_regex("/cities/{city_id}")
    #        → re.compile(r"^/cities/(?P<city_id>[^/]+)$")
    #
    # 3. A decorator @route(pattern: str):
    #    - converts pattern to regex using path_to_regex
    #    - appends (compiled_regex, func) to ROUTES
    #    - returns func unchanged
    #
    # 4. Three async handler functions (you write these):
    #    - async def get_city(city_id: str) -> dict:
    #        - returns {"city": city_id, "population": "unknown"}
    #    - async def get_district(city_id: str, district_id: str) -> dict:
    #        - returns {"city": city_id, "district": district_id}
    #    - async def get_landmark(city_id: str, landmark_id: str) -> dict:
    #        - returns {"city": city_id, "landmark": landmark_id, "open": True}
    #
    # 5. Apply @route to each handler:
    #    - @route("/cities/{city_id}")               → get_city
    #    - @route("/cities/{city_id}/districts/{district_id}") → get_district
    #    - @route("/cities/{city_id}/landmarks/{landmark_id}") → get_landmark
    #
    # 6. An async dispatch(path: str) -> dict | None:
    #    - loop through ROUTES in order
    #    - try to match the path against each compiled regex
    #    - if match found:
    #        - extract named groups as a dict (hint: match.groupdict())
    #        - call and await the handler passing the extracted params as **kwargs
    #        - return the result
    #    - if no match found, print "  404: {path}" and return None
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    ROUTES = []

    def path_to_regex(pattern: str) -> re.Pattern:
        mod_str = re.sub(r"\{([^}]+)\}", r"(?P<\g<1>>[^/]+)", pattern)
        return re.compile(f"^{mod_str}$")

    def route(pattern: str):
        def decorator(func: Callable) -> Callable:
            ROUTES.append((path_to_regex(pattern), func))
            return func

        return decorator

    @route("/cities/{city_id}")
    async def get_city(city_id: str) -> dict:
        return {"city": city_id, "population": "unknown"}

    @route("/cities/{city_id}/districts/{district_id}")
    async def get_district(city_id: str, district_id: str) -> dict:
        return {"city": city_id, "district": district_id}

    @route("/cities/{city_id}/landmarks/{landmark_id}")
    async def get_landmark(city_id: str, landmark_id: str) -> dict:
        return {"city": city_id, "landmark": landmark_id, "open": True}

    async def dispatch(path: str) -> dict | None:
        for regex, handler in ROUTES:
            match = regex.match(path)
            if match:
                kwargs = match.groupdict()
                return await handler(**kwargs)
        print(f"  404: {path}")
        return None

    # --- TESTS (do not modify) ---
    print("Test 1: Match single param")
    result = await dispatch("/cities/manila")
    print(f"  Result: {result}")

    print("\nTest 2: Match two params — district")
    result = await dispatch("/cities/manila/districts/tondo")
    print(f"  Result: {result}")

    print("\nTest 3: Match two params — landmark")
    result = await dispatch("/cities/cebu/landmarks/magellan-cross")
    print(f"  Result: {result}")

    print("\nTest 4: No match")
    result = await dispatch("/countries/ph")
    print(f"  Result: {result}")

    print("\nTest 5: Different city, same pattern")
    result = await dispatch("/cities/davao")
    print(f"  Result: {result}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Match single param
    #   Result: {'city': 'manila', 'population': 'unknown'}
    #
    # Test 2: Match two params — district
    #   Result: {'city': 'manila', 'district': 'tondo'}
    #
    # Test 3: Match two params — landmark
    #   Result: {'city': 'cebu', 'landmark': 'magellan-cross', 'open': True}
    #
    # Test 4: No match
    #   404: /countries/ph
    #   Result: None
    #
    # Test 5: Different city, same pattern
    #   Result: {'city': 'davao', 'population': 'unknown'}
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_62())
