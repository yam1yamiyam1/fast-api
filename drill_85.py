import asyncio  # noqa: F401
import inspect  # noqa: F401
from typing import Any, Callable, Optional  # noqa: F401


def run_drill_85():
    """
    SCENARIO: Train Station Dispatch Board
    ======================================
    A train station maintains a dispatch board that maps platform numbers
    to handler functions. Operators register a handler for each platform.
    When a train arrives, the board looks up the platform and calls the
    correct handler. The board must handle duplicate registrations and
    unknown platforms gracefully.

    NEW CONCEPT: Registry pattern with edge cases
    ---------------------------------------------
    A registry maps keys to callables. Edge cases you must handle:
      1. Duplicate key — registering the same key twice raises ValueError.
      2. Unknown key — looking up a missing key raises KeyError.
      3. The registry dict lives on the instance, never as a mutable default
         argument or class-level attribute — always initialised in __init__.
    Pattern: register(key, fn) stores; lookup(key) retrieves or raises.

    REQUIREMENTS
    ============

    1. PlatformRegistry
       - A class representing the station's dispatch board.
       - __init__(self):
           - self._routes: dict — the internal map from platform number
             (int) to handler callable; initialised as an empty dict using
             = {}, never passed as a default argument and never defined
             at class level.
       - def register(self, platform: int, handler: Callable) -> None
           - platform: int — the platform number being assigned a handler.
           - handler: Callable — the function to call when a train arrives
             at this platform.
           - If platform is already in self._routes, raise ValueError with
             message: "Platform <platform> already registered".
           - Otherwise store handler under platform in self._routes.
       - def lookup(self, platform: int) -> Callable
           - platform: int — the platform number whose handler is needed.
           - If platform is not in self._routes, raise KeyError with
             message: "No handler for platform <platform>".
           - Otherwise return the handler stored under platform.
       - def dispatch(self, platform: Any, train_id: str) -> str
           - platform: Any — the platform number where the train arrived;
             must be cast to int before lookup if received as a string.
           - train_id: str — the identifier printed on the arriving train.
           - Calls lookup(platform) to get the handler, then calls
             handler(train_id) and returns its result.

    2. Handler functions (plain functions, not methods)

       def express_handler(train_id: str) -> str
           - train_id: str — the identifier of the arriving express train.
           - Returns "Express <train_id> cleared for boarding".

       def freight_handler(train_id: str) -> str
           - train_id: str — the identifier of the arriving freight train.
           - Returns "Freight <train_id> directed to loading bay".

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---
    class PlatformRegistry:
        def __init__(self):
            self._routes = {}

        def register(self, platform: int, handler: Callable):
            if platform in self._routes:
                raise ValueError(f"Platform {platform} already registered")
            self._routes[platform] = handler

        def lookup(self, platform: int):
            if platform not in self._routes:
                raise KeyError(f"No handler for platform {platform}")
            return self._routes[platform]

        def dispatch(self, platform: Any, train_id: str):
            return self.lookup(int(platform))(train_id)

    def express_handler(train_id: str):
        return f"Express {train_id} cleared for boarding"

    def freight_handler(train_id: str):
        return f"Freight {train_id} directed to loading bay"

    # Test 1: register and dispatch to correct handler
    board = PlatformRegistry()
    board.register(1, express_handler)
    board.register(2, freight_handler)
    result1 = board.dispatch(1, "EX-101")
    print("Test 1: express handler dispatched")
    print(f"  result={result1!r}")
    assert result1 == "Express EX-101 cleared for boarding"
    print("  PASS")

    # Test 2: dispatch to second platform
    result2 = board.dispatch(2, "FR-202")
    print("Test 2: freight handler dispatched")
    print(f"  result={result2!r}")
    assert result2 == "Freight FR-202 directed to loading bay"
    print("  PASS")

    # Test 3: duplicate registration raises ValueError
    print("Test 3: duplicate platform raises ValueError")
    try:
        board.register(1, express_handler)
        assert False, "should have raised"
    except ValueError as e:
        print(f"  error={str(e)!r}")
        assert str(e) == "Platform 1 already registered"
    print("  PASS")

    # Test 4: unknown platform raises KeyError
    print("Test 4: unknown platform raises KeyError")
    try:
        board.lookup(99)
        assert False, "should have raised"
    except KeyError as e:
        print(f"  error={e.args[0]!r}")
        assert e.args[0] == "No handler for platform 99"
    print("  PASS")

    # Test 5: platform received as string — must cast to int before lookup
    result5 = board.dispatch("1", "EX-303")
    print("Test 5: string platform cast to int")
    print(f"  result={result5!r}")
    assert result5 == "Express EX-303 cleared for boarding"
    print("  PASS")

    # Test 6: _routes not shared between registry instances
    board2 = PlatformRegistry()
    board2.register(1, freight_handler)
    print("Test 6: _routes isolation between instances")
    print(f"  board platform 1 handler={board.lookup(1).__name__!r}")
    print(f"  board2 platform 1 handler={board2.lookup(1).__name__!r}")
    assert board.lookup(1) is express_handler
    assert board2.lookup(1) is freight_handler
    print("  PASS")


run_drill_85()


# EXPECTED OUTPUT
# ===============
# Test 1: express handler dispatched
#   result='Express EX-101 cleared for boarding'
#   PASS
# Test 2: freight handler dispatched
#   result='Freight FR-202 directed to loading bay'
#   PASS
# Test 3: duplicate platform raises ValueError
#   error='Platform 1 already registered'
#   PASS
# Test 4: unknown platform raises KeyError
#   error='No handler for platform 99'
#   PASS
# Test 5: string platform cast to int
#   result='Express EX-303 cleared for boarding'
#   PASS
# Test 6: _routes isolation between instances
#   board platform 1 handler='express_handler'
#   board2 platform 1 handler='freight_handler'
#   PASS
