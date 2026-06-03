import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_79():
    # =========================================================================
    # SCENARIO: The Museum
    # =========================================================================
    # A museum has exhibit rooms with limited capacity. Only a fixed number
    # of visitors may be inside a room at the same time. A decorator enforces
    # the cap — any visitor over the limit waits at the door until a slot opens.
    # The exhibit handler itself knows nothing about capacity limits.
    #
    # NEW CONCEPT: semaphore inside decorator — concurrency limiter
    # - asyncio.Semaphore(n) allows at most n coroutines through at once
    # - `async with sem:` acquires a slot on enter, releases on exit
    # - The semaphore lives in the decorator's closure — one shared counter
    #   for all calls to that decorated function
    # - If all slots are taken, new callers wait (they don't get rejected)
    # - This is how you cap parallel DB connections, API calls, etc.
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model VisitorPass:
    #    - visitor_id: str
    #    - exhibit: str
    #
    # 2. A shared list: visit_log = []
    #    - handlers append to it so tests can verify concurrency behavior
    #
    # 3. A decorator factory limit_capacity(max_visitors: int):
    #    - creates one asyncio.Semaphore(max_visitors) in the closure
    #    - wraps func
    #    - acquires the semaphore with `async with` before calling func
    #    - releases automatically on exit
    #    - returns the result
    #
    # 4. A class ExhibitRoom:
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.current_visitors = 0
    #    - async method enter(self, pass_: VisitorPass) -> dict:
    #        - decorated with @limit_capacity(max_visitors=2)
    #        - increments self.current_visitors
    #        - appends f"{pass_.visitor_id} entered {self.name}" to visit_log
    #        - simulates a visit with asyncio.sleep(0.05)
    #        - decrements self.current_visitors
    #        - returns {"visitor": pass_.visitor_id, "exhibit": self.name, "status": "visited"}
    #
    # 5. An async dispatch(room: ExhibitRoom, raw_payload: dict) -> dict:
    #    - validate raw_payload into VisitorPass
    #      - if ValidationError, return {"error": "invalid pass"}
    #    - call and await room.enter(pass_)
    #    - return the result
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class VisitorPass(BaseModel):
        visitor_id: str
        exhibit: str

    visit_log = []

    def limit_capacity(max_visitors: int):
        max = asyncio.Semaphore(max_visitors)

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with max:
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    class ExhibitRoom:
        def __init__(self, name: str):
            self.name = name
            self.current_visitors = 0

        @limit_capacity(max_visitors=2)
        async def enter(self, pass_: VisitorPass):
            self.current_visitors += 1
            visit_log.append(f"{pass_.visitor_id} entered {self.name}")
            await asyncio.sleep(0.05)
            self.current_visitors -= 1
            return {
                "visitor": pass_.visitor_id,
                "exhibit": self.name,
                "status": "visited",
            }

    async def dispatch(room: ExhibitRoom, raw_payload: dict):
        try:
            valid_pass = VisitorPass(**raw_payload)
            return await room.enter(valid_pass)
        except ValidationError:
            return {"error": "invalid pass"}

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    visit_log = []  # noqa: F841 — used inside enter()
    room = ExhibitRoom(name="Egyptian Hall")  # noqa: F821

    print("Test 1: single visitor enters successfully")
    result = await dispatch(room, {"visitor_id": "V-001", "exhibit": "mummies"})  # noqa: F821
    print(f"  {result}")
    assert result == {
        "visitor": "V-001",
        "exhibit": "Egyptian Hall",
        "status": "visited",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 2: semaphore limits to max 2 concurrent visitors")
    visit_log.clear()
    concurrent_counts = []

    async def visit(visitor_id):
        result = await dispatch(room, {"visitor_id": visitor_id, "exhibit": "mummies"})  # noqa: F821
        concurrent_counts.append(room.current_visitors)
        return result

    # launch 5 visitors concurrently — semaphore should cap at 2 inside at once
    await asyncio.gather(*[visit(f"V-{i:03}") for i in range(5)])
    print(f"  visit_log: {visit_log}")
    print("  peak concurrent (during sleep): should be <= 2")
    assert len(visit_log) == 5, f"Expected 5 log entries, got {len(visit_log)}"
    # after each finishes, current_visitors is back to 0 — check it was never > 2
    # (we can't directly measure peak mid-sleep, but all 5 must complete)
    assert room.current_visitors == 0, (
        f"Expected 0 after all done, got {room.current_visitors}"
    )
    print("  PASS")

    print("\nTest 3: invalid pass")
    result = await dispatch(room, {"visitor_id": "V-999"})  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "invalid pass"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 4: two rooms have independent semaphores")
    room2 = ExhibitRoom(name="Greek Hall")  # noqa: F821
    r1, r2 = await asyncio.gather(
        dispatch(room, {"visitor_id": "A", "exhibit": "x"}),  # noqa: F821
        dispatch(room2, {"visitor_id": "B", "exhibit": "y"}),  # noqa: F821
    )
    print(f"  room1 result: {r1}")
    print(f"  room2 result: {r2}")
    assert r1["exhibit"] == "Egyptian Hall"
    assert r2["exhibit"] == "Greek Hall"
    print("  PASS")

    print("\nTest 5: decorator preserved method name")
    assert room.enter.__name__ == "enter", f"Got {room.enter.__name__!r}"
    print("  PASS")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: single visitor enters successfully
    #   {'visitor': 'V-001', 'exhibit': 'Egyptian Hall', 'status': 'visited'}
    #   PASS
    #
    # Test 2: semaphore limits to max 2 concurrent visitors
    #   visit_log: [... 5 entries ...]
    #   peak concurrent (during sleep): should be <= 2
    #   PASS
    #
    # Test 3: invalid pass
    #   {'error': 'invalid pass'}
    #   PASS
    #
    # Test 4: two rooms have independent semaphores
    #   room1 result: {'visitor': 'A', 'exhibit': 'Egyptian Hall', 'status': 'visited'}
    #   room2 result: {'visitor': 'B', 'exhibit': 'Greek Hall', 'status': 'visited'}
    #   PASS
    #
    # Test 5: decorator preserved method name
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_79())
