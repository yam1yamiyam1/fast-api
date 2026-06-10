import asyncio  # noqa: F401
import inspect  # noqa: F401
import re  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, AsyncGenerator, Callable, Optional  # noqa: F401


def run_drill_90():
    """
    SCENARIO: Fire Station Dispatch System
    =======================================
    The fire station runs a dispatch system. When a shift opens, a context
    manager boots the system and tears it down cleanly. Incoming calls are
    routed to unit handlers via a registry. Heavy paperwork (blocking I/O)
    is offloaded to a thread. A semaphore caps simultaneous dispatches.

    NEW CONCEPT: asyncio.to_thread
    ------------------------------
    asyncio.to_thread(fn, *args) runs a blocking synchronous function in a
    thread pool without blocking the event loop.
    Pattern:
        result = await asyncio.to_thread(blocking_fn, arg1, arg2)
    Use it when you have a sync function that would block (file I/O, CPU work)
    and you don't want it to freeze the event loop.
    Rule: pass the function and its arguments separately — never call the
    function yourself before passing it: to_thread(fn, arg), not to_thread(fn(arg)).

    REQUIREMENTS
    ============

    1. DispatchRecord
       - A dataclass representing a logged dispatch event.
       - call_id: str — the unique identifier assigned to this emergency call.
       - unit: str — the fire unit code assigned to respond.
       - log: list — the list of status strings recorded for this dispatch;
         must use field(default_factory=list), never a mutable default.
       - resolved: bool — whether this dispatch has been closed out;
         default value False, written as a plain field assignment.

    2. StationRegistry
       - A class representing the unit handler registry.
       - __init__(self):
           - self._handlers: dict — the map from unit code (str) to handler
             callable; initialised as = {}, never a type annotation alone.
       - def register(self, unit: str, handler: Callable) -> None
           - unit: str — the unit code to register.
           - handler: Callable — the callable to invoke for this unit.
           - If unit is already registered, raise ValueError:
             "Unit <unit> already registered".
           - Otherwise store handler under unit.
       - def get(self, unit: str) -> Callable
           - unit: str — the unit code to look up.
           - If unit not found, raise KeyError: "No handler for unit <unit>".
           - Otherwise return the handler.

    3. DispatchSystem
       - A class representing the active dispatch desk.
       - __init__(self, registry: StationRegistry, limit: int):
           - registry: StationRegistry — the unit handler registry this
             desk uses to route calls.
           - limit: int — the maximum simultaneous dispatches allowed.
           - self.registry: StationRegistry — assigned from the registry
             argument; written as = registry, never as a type annotation alone.
           - self.semaphore: asyncio.Semaphore — the concurrency gate
             initialised with limit; written as = asyncio.Semaphore(limit),
             never as a type annotation alone.
           - self.records: list — the list of completed DispatchRecord
             objects; initialised as = [], never a type annotation alone.
       - async def dispatch(self, call_id: str, unit: str) -> DispatchRecord
           - call_id: str — the emergency call identifier to process.
           - unit: str — the unit code to look up in the registry.
           - Acquires self.semaphore with async with.
           - Inside: looks up the handler via self.registry.get(unit),
             then calls await asyncio.to_thread(handler, call_id) to run
             the handler in a thread, storing the result as record.
           - Sets record.resolved to True, appends to self.records,
             returns record.

    4. station_lifespan  (async context manager function, not a method)
       @asynccontextmanager
       async def station_lifespan(registry: StationRegistry, limit: int)
                                  -> AsyncGenerator[DispatchSystem, None]
           - registry: StationRegistry — the registry to pass to DispatchSystem.
           - limit: int — the concurrency limit to pass to DispatchSystem.
           - Before yield: create DispatchSystem(registry, limit), yield it.
           - After yield: clear system.records to [].

    5. Handler functions (plain functions, not methods)
       These are blocking sync functions intentionally — they will be run
       via asyncio.to_thread.

       def engine_handler(call_id: str) -> DispatchRecord
           - call_id: str — the call identifier for this dispatch.
           - Returns DispatchRecord(call_id=call_id, unit="E-1").

       def ladder_handler(call_id: str) -> DispatchRecord
           - call_id: str — the call identifier for this dispatch.
           - Returns DispatchRecord(call_id=call_id, unit="L-2").

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class DispatchRecord:
        call_id: str
        unit: str
        log: list = field(default_factory=list)
        resolved: bool = False

    class StationRegistry:
        def __init__(self):
            self._handlers = {}

        def register(self, unit: str, handler: Callable):
            if unit in self._handlers:
                raise ValueError(f"Unit {unit} already registered")
            self._handlers[unit] = handler

        def get(self, unit: str):
            if unit not in self._handlers:
                raise KeyError(f"No handler for unit {unit}")
            return self._handlers[unit]

    class DispatchSystem:
        def __init__(self, registry: StationRegistry, limit: int):
            self.registry = registry
            self.semaphore = asyncio.Semaphore(limit)
            self.records = []

        async def dispatch(self, call_id: str, unit: str):
            handler = self.registry.get(unit)
            async with self.semaphore:
                record = await asyncio.to_thread(handler, call_id)
            record.resolved = True
            self.records.append(record)
            return record

    @asynccontextmanager
    async def station_lifespan(registry: StationRegistry, limit: int):
        system = DispatchSystem(registry, limit)
        yield system
        system.records = []

    def engine_handler(call_id: str):
        return DispatchRecord(call_id=call_id, unit="E-1")

    def ladder_handler(call_id: str):
        return DispatchRecord(call_id=call_id, unit="L-2")

    async def main():
        registry = StationRegistry()
        registry.register("E-1", engine_handler)
        registry.register("L-2", ladder_handler)

        # Test 1: dispatch routes to correct handler via registry
        async with station_lifespan(registry, limit=2) as system:
            rec1 = await system.dispatch("CALL-001", "E-1")
            print("Test 1: engine unit dispatched")
            print(f"  call_id={rec1.call_id!r}, unit={rec1.unit!r}")
            print(f"  resolved={rec1.resolved}")
            assert rec1.call_id == "CALL-001"
            assert rec1.unit == "E-1"
            assert rec1.resolved is True
            print("  PASS")

            # Test 2: ladder unit dispatched
            rec2 = await system.dispatch("CALL-002", "L-2")
            print("Test 2: ladder unit dispatched")
            print(f"  call_id={rec2.call_id!r}, unit={rec2.unit!r}")
            assert rec2.call_id == "CALL-002"
            assert rec2.unit == "L-2"
            print("  PASS")

            # Test 3: unknown unit raises KeyError
            print("Test 3: unknown unit raises KeyError")
            try:
                await system.dispatch("CALL-003", "X-9")
                assert False, "should have raised"
            except KeyError as e:
                print(f"  error={e.args[0]!r}")
                assert e.args[0] == "No handler for unit X-9"
            print("  PASS")

            # Test 4: semaphore limits concurrency
            active = []
            peak = []

            def slow_handler(call_id: str) -> DispatchRecord:
                import time  # noqa: F401

                active.append(1)
                peak.append(len(active))
                time.sleep(0.02)
                active.pop()
                return DispatchRecord(call_id=call_id, unit="S-1")

            registry.register("S-1", slow_handler)
            tasks = [
                asyncio.create_task(system.dispatch(f"C-{i}", "S-1")) for i in range(4)
            ]
            await asyncio.gather(*tasks)
            print("Test 4: semaphore caps concurrency")
            print(f"  peak_concurrent={max(peak)}")
            assert max(peak) <= 2
            print("  PASS")

        # Test 5: lifespan teardown clears records
        print("Test 5: records cleared after lifespan exits")
        print(f"  records={system.records}")
        assert system.records == []
        print("  PASS")

        # Test 6: duplicate unit registration raises ValueError
        print("Test 6: duplicate unit raises ValueError")
        try:
            registry.register("E-1", engine_handler)
            assert False, "should have raised"
        except ValueError as e:
            print(f"  error={str(e)!r}")
            assert str(e) == "Unit E-1 already registered"
        print("  PASS")

        # Test 7: DispatchRecord log default not shared between instances
        d1 = DispatchRecord(call_id="A", unit="E-1")
        d2 = DispatchRecord(call_id="B", unit="E-1")
        d1.log.append("en route")
        print("Test 7: log mutable default isolation")
        print(f"  d1.log={d1.log}")
        print(f"  d2.log={d2.log}")
        assert d1.log == ["en route"]
        assert d2.log == []
        print("  PASS")

    asyncio.run(main())


run_drill_90()


# EXPECTED OUTPUT
# ===============
# Test 1: engine unit dispatched
#   call_id='CALL-001', unit='E-1'
#   resolved=True
#   PASS
# Test 2: ladder unit dispatched
#   call_id='CALL-002', unit='L-2'
#   PASS
# Test 3: unknown unit raises KeyError
#   error='No handler for unit X-9'
#   PASS
# Test 4: semaphore caps concurrency
#   peak_concurrent=2
#   PASS
# Test 5: records cleared after lifespan exits
#   records=[]
#   PASS
# Test 6: duplicate unit raises ValueError
#   error='Unit E-1 already registered'
#   PASS
# Test 7: log mutable default isolation
#   d1.log=['en route']
#   d2.log=[]
#   PASS
