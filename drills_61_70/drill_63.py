import asyncio  # noqa: F401
import re  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_63():
    # =========================================================================
    # SCENARIO: The Blog API
    # =========================================================================
    # A blog API handles the same path with different HTTP methods.
    # GET /posts/{post_id} → read a post
    # POST /posts/{post_id} → update a post
    # DELETE /posts/{post_id} → delete a post
    #
    # The registry now needs to store BOTH the path pattern AND the method.
    # dispatch receives both a path and a method, and must match both.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: ROUTES = []
    #    - each entry is a tuple: (method, compiled_regex, handler)
    #
    # 2. Reuse path_to_regex(pattern: str) -> re.Pattern from drill 62:
    #    - replaces {param} with (?P<param>[^/]+)
    #    - anchors with ^ and $
    #
    # 3. A decorator @route(method: str, pattern: str):
    #    - method is uppercase string: "GET", "POST", "DELETE"
    #    - appends (method, compiled_regex, func) to ROUTES
    #    - returns func unchanged
    #
    # 4. Three async handler functions (you write these):
    #    - async def read_post(post_id: str) -> dict:
    #        - returns {"action": "read", "post_id": post_id}
    #    - async def update_post(post_id: str) -> dict:
    #        - returns {"action": "updated", "post_id": post_id}
    #    - async def delete_post(post_id: str) -> dict:
    #        - returns {"action": "deleted", "post_id": post_id}
    #
    # 5. Apply @route to each handler:
    #    - @route("GET",    "/posts/{post_id}") → read_post
    #    - @route("POST",   "/posts/{post_id}") → update_post
    #    - @route("DELETE", "/posts/{post_id}") → delete_post
    #
    # 6. An async dispatch(method: str, path: str) -> dict | None:
    #    - loop through ROUTES in order
    #    - match BOTH method AND path pattern
    #    - if both match:
    #        - extract path params via groupdict()
    #        - call and await the handler with **kwargs
    #        - return the result
    #    - if path matches but method does not, print "  405: method not allowed" and return None
    #    - if nothing matches at all, print "  404: {path}" and return None
    #
    # NOTE: the 405 check means you need to track whether the path matched
    # any pattern at all, regardless of method
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    ROUTES = []

    def path_to_regex(pattern: str) -> re.Pattern:
        mod_str = re.sub(r"\{([^}]+)\}", r"(?P<\g<1>>[^/]+)", pattern)
        return re.compile(f"^{mod_str}$")

    def route(method: str, pattern: str):
        def decorator(func: Callable) -> Callable:
            ROUTES.append((method, path_to_regex(pattern), func))
            return func

        return decorator

    @route(method="GET", pattern="/posts/{post_id}")
    async def read_post(post_id: str) -> dict:
        return {"action": "read", "post_id": post_id}

    @route(method="POST", pattern="/posts/{post_id}")
    async def update_post(post_id: str) -> dict:
        return {"action": "updated", "post_id": post_id}

    @route(method="DELETE", pattern="/posts/{post_id}")
    async def delete_post(post_id: str) -> dict:
        return {"action": "deleted", "post_id": post_id}

    async def dispatch(method: str, path: str) -> dict | None:
        path_matched = False
        for r_method, regex, handler in ROUTES:
            match = regex.match(path)
            method_match = r_method == method
            if match:
                path_matched = True
                if method_match:
                    kwargs = match.groupdict()
                    return await handler(**kwargs)
        if path_matched:
            print("  405: method not allowed")
            return None
        else:
            print(f"  404: {path}")
            return None

    # --- TESTS (do not modify) ---
    print("Test 1: GET post")
    result = await dispatch("GET", "/posts/42")
    print(f"  Result: {result}")

    print("\nTest 2: POST (update) post")
    result = await dispatch("POST", "/posts/42")
    print(f"  Result: {result}")

    print("\nTest 3: DELETE post")
    result = await dispatch("DELETE", "/posts/42")
    print(f"  Result: {result}")

    print("\nTest 4: Wrong method — 405")
    result = await dispatch("PUT", "/posts/42")
    print(f"  Result: {result}")

    print("\nTest 5: Unknown path — 404")
    result = await dispatch("GET", "/comments/42")
    print(f"  Result: {result}")

    print("\nTest 6: Different post_id")
    result = await dispatch("GET", "/posts/hello-world")
    print(f"  Result: {result}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: GET post
    #   Result: {'action': 'read', 'post_id': '42'}
    #
    # Test 2: POST (update) post
    #   Result: {'action': 'updated', 'post_id': '42'}
    #
    # Test 3: DELETE post
    #   Result: {'action': 'deleted', 'post_id': '42'}
    #
    # Test 4: Wrong method — 405
    #   405: method not allowed
    #   Result: None
    #
    # Test 5: Unknown path — 404
    #   404: /comments/42
    #   Result: None
    #
    # Test 6: Different post_id
    #   Result: {'action': 'read', 'post_id': 'hello-world'}
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_63())
